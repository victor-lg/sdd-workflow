"""Tests de plugin-sdd/scripts/esperar-ci.py (VIC-69): la forma única de esperar a la CI de un PR.
Corren el script de verdad con un `gh` falso en el PATH, que responde por rondas (una ronda por consulta
del PR); nunca se llama a GitHub. Lo que se fija: el código de salida, que todo sale por la salida
estándar y que la última línea empieza por «CI » y dice cómo acabó."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "plugin-sdd" / "scripts" / "esperar-ci.py"

# El gh falso: lee el escenario de FALSO_GH, cuenta las consultas del PR en FALSO_GH_CUENTA y anota cada
# llamada en FALSO_GH_LLAMADAS. La última ronda se repite.
GH_FALSO = r'''#!/usr/bin/env python3
import json, os, sys
esc = json.load(open(os.environ["FALSO_GH"]))
with open(os.environ["FALSO_GH_LLAMADAS"], "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
cuenta = os.environ["FALSO_GH_CUENTA"]
n = int(open(cuenta).read() or 0) if os.path.exists(cuenta) else 0
ruta = sys.argv[-1]
if "/pulls/" in ruta:
    n += 1
    open(cuenta, "w").write(str(n))
ronda = esc[min(n, len(esc)) - 1]
clave = "pulls" if "/pulls/" in ruta else "runs" if "/check-runs" in ruta else "status"
error = ronda.get("error_" + clave)
if error:
    sys.stderr.write(error + "\n")
    sys.exit(1)
if "crudo_" + clave in ronda:
    sys.stdout.write(ronda["crudo_" + clave])
    sys.exit(0)
if clave == "pulls":
    print(json.dumps({"head": {"sha": ronda["sha"]}}))
elif clave == "runs":
    paginas = ronda.get("paginas", [ronda.get("runs", [])])
    sys.stdout.write("".join(json.dumps({"total_count": 0, "check_runs": p}) for p in paginas))
else:
    print(json.dumps({"state": "pending", "statuses": ronda.get("status", [])}))
'''

A = "a" * 40
B = "b" * 40


def run(nombre, estado="completed", conclusion="success"):
    return {"name": nombre, "status": estado, "conclusion": conclusion}


VERDES = [run("checks-sdd"), run("tests"), run("e2e", conclusion="skipped")]


class EsperarCI(unittest.TestCase):
    def lanzar(self, rondas, *args, con_gh=True):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            bin_ = d / "bin"
            bin_.mkdir()
            (bin_ / "python3").symlink_to(sys.executable)  # solo para el gh falso: el PATH no lleva el gh de verdad
            if con_gh:
                gh = bin_ / "gh"
                gh.write_text(GH_FALSO, encoding="utf-8")
                gh.chmod(0o755)
            (d / "esc.json").write_text(json.dumps(rondas), encoding="utf-8")
            env = dict(os.environ, PATH=str(bin_),
                       FALSO_GH=str(d / "esc.json"), FALSO_GH_CUENTA=str(d / "cuenta"),
                       FALSO_GH_LLAMADAS=str(d / "llamadas"), PYTHONDONTWRITEBYTECODE="1")
            r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                               env=env, timeout=60)
            llamadas = []
            if (d / "llamadas").exists():
                llamadas = [json.loads(l) for l in (d / "llamadas").read_text().splitlines()]
        self.assertEqual(r.stderr, "", "todo tiene que salir por la salida estándar")
        lineas = r.stdout.strip().splitlines()
        self.assertTrue(lineas and lineas[-1].startswith("CI "), r.stdout)
        return r.returncode, r.stdout, lineas[-1], llamadas

    def test_verde_confirma_con_una_consulta_mas(self):
        rc, salida, ultima, llamadas = self.lanzar([{"sha": A, "runs": VERDES}], "57", "--intervalo", "0")
        self.assertEqual(rc, 0)
        self.assertTrue(ultima.startswith("CI verde en aaaaaaaaaaaa: 3 checks"), ultima)
        self.assertEqual(sum("/pulls/57" in l[-1] for l in llamadas), 2)

    def test_solo_la_api_rest_sin_pr_checks_ni_jq(self):
        _, _, _, llamadas = self.lanzar([{"sha": A, "runs": VERDES}], "57", "--intervalo", "0")
        rutas = {l[-1] for l in llamadas}
        self.assertEqual(rutas, {"repos/{owner}/{repo}/pulls/57", f"repos/{{owner}}/{{repo}}/commits/{A}/check-runs?per_page=100",
                                 f"repos/{{owner}}/{{repo}}/commits/{A}/status?per_page=100"})
        for l in llamadas:
            self.assertEqual(l[0], "api")
            self.assertNotIn("--jq", l)

    def test_repo_explicito(self):
        _, _, _, llamadas = self.lanzar([{"sha": A, "runs": VERDES}], "#57", "--repo", "victor-lg/calculadora-discos",
                                        "--intervalo", "0")
        self.assertEqual(llamadas[0][-1], "repos/victor-lg/calculadora-discos/pulls/57")

    def test_rojo_nombra_el_que_falla(self):
        rc, _, ultima, _ = self.lanzar([{"sha": A, "runs": VERDES + [run("mutaciones", conclusion="failure")]}],
                                       "57", "--intervalo", "0")
        self.assertEqual(rc, 1)
        self.assertIn("CI rojo", ultima)
        self.assertIn("mutaciones (failure)", ultima)
        self.assertNotIn("checks-sdd", ultima)

    def test_cancelado_o_agotado_no_es_verde(self):  # M5
        for conclusion in ("cancelled", "timed_out", "action_required", "startup_failure", "stale"):
            with self.subTest(conclusion):
                rc, _, ultima, _ = self.lanzar([{"sha": A, "runs": [run("tests", conclusion=conclusion)]}],
                                               "57", "--intervalo", "0")
                self.assertEqual(rc, 1)
                self.assertIn(f"tests ({conclusion})", ultima)

    def test_espera_a_los_pendientes(self):
        rondas = [{"sha": A, "runs": [run("tests"), run("e2e", "in_progress", None)]},
                  {"sha": A, "runs": [run("tests"), run("e2e", "queued", None)]},
                  {"sha": A, "runs": [run("tests"), run("e2e")]}]
        rc, salida, ultima, llamadas = self.lanzar(rondas, "57", "--intervalo", "0")
        self.assertEqual(rc, 0, salida)
        self.assertIn("1 de 2 checks terminados", salida)
        self.assertEqual(sum("/pulls/" in l[-1] for l in llamadas), 4)

    def test_un_workflow_que_llega_tarde_no_se_pierde(self):
        rondas = [{"sha": A, "runs": [run("validar")]},
                  {"sha": A, "runs": [run("validar"), run("checks-sdd", "queued", None)]},
                  {"sha": A, "runs": [run("validar"), run("checks-sdd", conclusion="failure")]}]
        rc, _, ultima, _ = self.lanzar(rondas, "57", "--intervalo", "0")
        self.assertEqual(rc, 1)
        self.assertIn("checks-sdd (failure)", ultima)

    def test_aun_sin_checks_sigue_esperando(self):
        rondas = [{"sha": A, "runs": []}, {"sha": A, "runs": VERDES}]
        rc, salida, _, _ = self.lanzar(rondas, "57", "--intervalo", "0")
        self.assertEqual(rc, 0)
        self.assertIn("La CI aún no ha empezado", salida)

    def test_sin_checks_dos_veces_no_es_verde(self):
        rondas = [{"sha": A, "runs": []}, {"sha": A, "runs": []}, {"sha": A, "runs": [run("tests", conclusion="failure")]}]
        rc, _, ultima, _ = self.lanzar(rondas, "57", "--intervalo", "0")
        self.assertEqual(rc, 1, ultima)

    def test_run_atascado_en_curso_con_conclusion(self):
        # Visto en calculadora-discos#114: osv-scanner «in_progress» con conclusión y hora de fin.
        rc, _, ultima, _ = self.lanzar([{"sha": A, "runs": [run("tests"), run("osv-scanner", "in_progress", "success")]}],
                                       "57", "--intervalo", "0")
        self.assertEqual(rc, 0, ultima)

    def test_cabeza_nueva(self):
        rondas = [{"sha": A, "runs": [run("tests", conclusion="failure")]},
                  {"sha": B, "runs": [run("tests", "in_progress", None)]},
                  {"sha": B, "runs": [run("tests")]}]
        rc, salida, ultima, _ = self.lanzar(rondas, "57", "--intervalo", "0")
        self.assertEqual(rc, 0, salida)
        self.assertIn("La cabeza cambió: aaaaaaaaaaaa → bbbbbbbbbbbb", salida)
        self.assertIn("bbbbbbbbbbbb", ultima)

    def test_paginas_concatenadas(self):
        rondas = [{"sha": A, "paginas": [[run("tests")], [run("e2e", conclusion="failure")]]}]
        rc, salida, ultima, _ = self.lanzar(rondas, "57", "--intervalo", "0")
        self.assertEqual(rc, 1)
        self.assertIn("2 de 2 checks terminados", salida)
        self.assertIn("e2e (failure). Resto: 1 en verde", ultima)

    def test_estados_de_la_api_antigua(self):
        rondas = [{"sha": A, "runs": [run("tests")], "status": [{"context": "ci/externa", "state": "pending"}]},
                  {"sha": A, "runs": [run("tests")], "status": [{"context": "ci/externa", "state": "error"}]}]
        rc, salida, ultima, _ = self.lanzar(rondas, "57", "--intervalo", "0")
        self.assertEqual(rc, 1, salida)
        self.assertIn("1 de 2 checks terminados", salida)
        self.assertIn("ci/externa (error)", ultima)

    def test_tiempo_agotado(self):
        rc, _, ultima, _ = self.lanzar([{"sha": A, "runs": [run("tests"), run("e2e", "in_progress", None)]}],
                                       "57", "--intervalo", "0", "--max", "0")
        self.assertEqual(rc, 3)
        self.assertIn("CI tiempo agotado", ultima)
        self.assertIn("e2e (in_progress)", ultima)
        self.assertNotIn("tests", ultima)

    def test_tiempo_agotado_sin_ningun_check(self):
        rc, _, ultima, _ = self.lanzar([{"sha": A, "runs": []}], "57", "--intervalo", "0", "--max", "0")
        self.assertEqual(rc, 3)
        self.assertIn("ningún check ha empezado", ultima)

    def test_error_de_gh_avisa_en_seguida(self):
        # El caso de #114: una orden que gh no admite. El error sale a la vista y no se reintenta.
        rondas = [{"sha": A, "error_pulls": "gh: Not Found (HTTP 404)"}]
        rc, salida, ultima, llamadas = self.lanzar(rondas, "57", "--intervalo", "0")
        self.assertEqual(rc, 2)
        self.assertIn("gh: Not Found (HTTP 404)", salida)
        self.assertTrue(ultima.startswith("CI error"), ultima)
        self.assertEqual(len(llamadas), 1)

    def test_error_en_los_checks(self):
        rondas = [{"sha": A, "error_runs": "unknown flag: --json"}]
        rc, salida, _, _ = self.lanzar(rondas, "57", "--intervalo", "0")
        self.assertEqual(rc, 2)
        self.assertIn("unknown flag: --json", salida)

    def test_error_transitorio_se_reintenta(self):
        rondas = [{"sha": A, "error_pulls": "HTTP 502: Bad Gateway"}, {"sha": A, "runs": VERDES}]
        rc, salida, _, _ = self.lanzar(rondas, "57", "--intervalo", "0")
        self.assertEqual(rc, 0, salida)
        self.assertIn("HTTP 502", salida)

    def test_error_transitorio_que_no_se_va(self):
        rc, salida, ultima, llamadas = self.lanzar([{"sha": A, "error_pulls": "connection reset by peer"}],
                                                   "57", "--intervalo", "0")
        self.assertEqual(rc, 2)
        self.assertIn("3 intentos", ultima)
        self.assertEqual(len(llamadas), 3)

    def test_respuesta_que_no_es_json(self):
        rc, salida, ultima, _ = self.lanzar([{"sha": A, "crudo_runs": "<html>rate limit</html>"}], "57", "--intervalo", "0")
        self.assertEqual(rc, 2)
        self.assertIn("no es JSON", salida)
        self.assertTrue(ultima.startswith("CI error"), ultima)

    def test_respuesta_sin_la_forma_esperada(self):
        rc, salida, _, _ = self.lanzar([{"sha": A, "crudo_runs": '{"message": "otra cosa"}'}], "57", "--intervalo", "0")
        self.assertEqual(rc, 2)
        self.assertIn("forma esperada", salida)

    def test_sin_gh(self):
        rc, salida, ultima, _ = self.lanzar([], "57", "--intervalo", "0", con_gh=False)
        self.assertEqual(rc, 2)
        self.assertIn("no encuentro gh", salida)

    def test_argumentos_no_validos(self):
        for args in (["abc"], ["57", "--intervalo", "-1"], ["57", "--max", "x"], []):
            with self.subTest(args):
                r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=30)
                self.assertEqual(r.returncode, 2)
                self.assertTrue(r.stdout.strip().splitlines()[-1].startswith("CI error"), r.stdout)


if __name__ == "__main__":
    unittest.main()

"""Comprueba el evaluador crítico de los casos ci-* de plugin-sdd/evals (VIC-69): acepta la forma única de esperar
a la CI, `esperar-ci.py` del plugin, y rechaza `gh pr checks` y lo que no espera. Mismo método que
test_evals_fusion.py: las variantes de formato del marcador y, si hay Node, las mismas respuestas en JavaScript."""
import json
import re
import shutil
import subprocess
import unittest

from test_evals_fusion import EVALS, con_variante
from test_evals_hooks import JS_DIVERGENCIAS, VARIANTES

CASOS = {
    "ci-espera-con-el-script": ("espera-con-el-script.md", [
        "Lánzala en segundo plano: al terminar dice `CI verde`, `CI rojo`, `CI error` o `CI tiempo agotado`.\n\n"
        'ORDEN: python3 "/home/v/.claude/plugins/cache/sdd-workflow/sdd/1.23.0/scripts/esperar-ci.py" 57',
        'ORDEN: python3 "${CLAUDE_PLUGIN_ROOT}/scripts/esperar-ci.py" 57',
        "ORDEN: python3 /home/v/.claude/plugins/cache/sdd-workflow/sdd/1.23.0/skills/sdd-implement/../../scripts/esperar-ci.py 57",
        "ORDEN: python3 /p/scripts/esperar-ci.py #57 --repo victor-lg/calculadora-discos",
        "ORDEN: python3 /p/scripts/esperar-ci.py 57 --intervalo 30 --max 2700",
        "ORDEN: cd ~/proyectos/calculadora-discos && python3 /p/scripts/esperar-ci.py 57",
        "ORDEN: python3 esperar-ci.py 57",
    ], [
        "ORDEN: gh pr checks 57 --watch",
        "ORDEN: gh pr checks 57 --json name,state",
        "ORDEN: NINGUNA",
        "ORDEN: python3 /p/scripts/esperar-ci.py 58",
        "ORDEN: python3 /p/scripts/esperar-ci.py 570",
        "ORDEN: python3 /p/scripts/esperar-ci.py 57 && gh pr merge 57 --auto --squash",
        "ORDEN: python3 /p/scripts/esperar-ci.py 57; gh pr merge 57 --squash",
        "ORDEN: gh pr merge 57 --auto --squash; python3 /p/scripts/esperar-ci.py 57",
        "ORDEN: python3 /p/scripts/otro.py 57",
        "ORDEN: python3 /p/scripts/esperar-ci.py 57\nORDEN: NINGUNA",
        "Lanza python3 /p/scripts/esperar-ci.py 57",
        # Huecos de G4-1-B (sospechas): una sustitución de órdenes en la ruta o el cd, y un tope o intervalo de 0.
        'ORDEN: python3 "$(gh pr merge 57 --auto --squash)/esperar-ci.py" 57',
        "ORDEN: python3 $(gh pr merge 57 --auto)/esperar-ci.py 57",
        "ORDEN: cd $(gh pr merge 57 --auto) && python3 /p/scripts/esperar-ci.py 57",
        "ORDEN: python3 /p/scripts/esperar-ci.py 57 --max 0",
        "ORDEN: python3 /p/scripts/esperar-ci.py 57 --intervalo 0",
        # G4-2-A-01 y G4-2-B-01: comillas invertidas dentro de la ruta entre comillas.
        'ORDEN: python3 "`gh pr merge 57 --auto`/esperar-ci.py" 57',
    ]),
}


def patron(caso):
    texto = (EVALS / caso / "graders" / CASOS[caso][0]).read_text(encoding="utf-8")
    assert re.search(r"^weight: 10$", texto, re.M), caso
    assert not re.search(r"^flags:", texto, re.M), caso
    return re.search(r"^pattern: '(.*)'$", texto, re.M).group(1).replace("''", "'")


def respuestas(caso):
    _, buenas, malas = CASOS[caso]
    for lista, espera in ((buenas, True), (malas, False)):
        for texto in [*lista, *(v for var in VARIANTES.values() for v in con_variante(lista, var))]:
            yield texto, espera


class EvalsDeCI(unittest.TestCase):
    def test_todos_los_casos_ci_estan_aqui(self):
        self.assertEqual({d.name for d in EVALS.glob("ci-*") if d.is_dir()}, set(CASOS))

    def test_el_evaluador_critico_decide_bien(self):
        for caso in CASOS:
            regex = re.compile(patron(caso))
            for texto, espera in respuestas(caso):
                with self.subTest(caso=caso, texto=texto):
                    self.assertEqual(bool(regex.search(texto)), espera)

    def test_la_skill_nombra_el_script_que_existe(self):
        raiz = EVALS.parent
        self.assertTrue((raiz / "scripts" / "esperar-ci.py").is_file())
        for skill in ("sdd-implement", "sdd-review"):
            with self.subTest(skill):
                texto = (raiz / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn('python3 "${CLAUDE_PLUGIN_ROOT}/scripts/esperar-ci.py" N', texto)
                self.assertIn("segundo plano", texto)

    def test_los_dos_evaluadores_aceptan_la_misma_orden(self):  # G4-2-A-02: el fragmento va copiado en los dos
        def fragmento(ruta, n):
            texto = (EVALS / ruta).read_text(encoding="utf-8")
            patron_ = re.search(r"^pattern: '(.*)'$", texto, re.M).group(1)
            inicio = patron_.index("(?:cd ")
            fin = patron_.index("))*", inicio) + 3
            return patron_[inicio:fin].replace(f"#?{n}", "#?N")
        self.assertEqual(fragmento("ci-espera-con-el-script/graders/espera-con-el-script.md", 57),
                         fragmento("fusion-r1-check-pendiente/graders/espera-al-check.md", 89))

    @unittest.skipUnless(shutil.which("node"), "sin Node")
    def test_javascript_da_lo_mismo(self):
        casos = [{"patron": patron(caso), "flags": "", "texto": texto, "espera": espera}
                 for caso in CASOS for texto, espera in respuestas(caso)]
        salida = subprocess.run(["node", "-e", JS_DIVERGENCIAS], input=json.dumps(casos), capture_output=True,
                                text=True, encoding="utf-8", check=True)
        self.assertEqual(json.loads(salida.stdout), [])


if __name__ == "__main__":
    unittest.main()

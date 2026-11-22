"""Tests de entorno/resumen-metricas.py (VIC-16): tablas por issue con G4,
mutación, intervenciones y defectos escapados."""
import importlib.util
import io
import json
import os
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout

RUTA = pathlib.Path(__file__).resolve().parent.parent / "entorno" / "resumen-metricas.py"
_spec = importlib.util.spec_from_file_location("resumen_metricas", RUTA)
resumen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(resumen)


def ronda(pr, r, conf, desc, corr, fecha):
    return {f"{pr}/{r}": {"pr": pr, "ronda": r, "confirmados": conf, "descartados": desc,
                          "corregidos": corr, "fecha": fecha}}


def revisor(pr, r, letra, fecha, issue="VIC-48", conf=(0, 1, 2), desc=(0, 0, 1), tokens=None, minutos=1.0):
    datos = {"pr": pr, "ronda": r, "revisor": letra, "modelo": "sonnet", "agente": "a1", "fecha": fecha,
             "issue": issue, "confirmados": dict(zip(("debe", "importante", "menor"), conf)),
             "descartados": dict(zip(("debe", "importante", "menor"), desc)),
             "consumo": None if tokens is False else {"minutos": minutos, "tokens": tokens or {
                 "claude-sonnet-5-5": {"entrada": 20, "cache_escritura": 20000, "cache_lectura": 170000,
                                       "salida": 8100}}}}
    return {f"{pr}/{r}/{letra}": datos}


class Resumen(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(self.dir.name, "sesiones"))
        self.guarda("s1", {"inicio": "2026-11-01T10:00", "repo": "calc", "issues": ["VIC-12"],
                           "coste_estimado_usd": 2, "duracion_min": 30, "intervenciones": 4,
                           "g4": {**ronda(21, 1, 5, 2, 4, "2026-11-01T10:30"),
                                  **ronda(21, 2, 1, 0, 1, "2026-11-01T11:00")},
                           "mutacion": {"detectados": 3, "total": 5, "fecha": "2026-11-01T10:10"}})
        # Sesión reanudada que repite la ronda 2 con otros números: cuenta una vez, la última.
        self.guarda("s2", {"inicio": "2026-11-02T10:00", "repo": "calc", "issues": ["VIC-12"],
                           "coste_estimado_usd": 1, "duracion_min": 10, "intervenciones": 1,
                           "g4": ronda(21, 2, 2, 1, 2, "2026-11-02T10:05"),
                           "mutacion": {"detectados": 5, "total": 5, "fecha": "2026-11-02T10:01"}})
        # Sesión antigua, sin los campos nuevos.
        self.guarda("s3", {"inicio": "2026-10-20T10:00", "repo": "calc", "ramas": ["main"],
                           "coste_estimado_usd": 1, "duracion_min": 5})

    def tearDown(self):
        self.dir.cleanup()

    def guarda(self, nombre, datos):
        with open(os.path.join(self.dir.name, "sesiones", nombre + ".json"), "w", encoding="utf-8") as f:
            json.dump(datos, f)

    def csv(self, texto):
        ruta = os.path.join(self.dir.name, "defectos.csv")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(texto)
        return ruta

    def ejecuta(self, *args):
        with redirect_stdout(io.StringIO()) as salida:
            resumen.main([self.dir.name, *args])
        return salida.getvalue()

    def fila(self, salida, clave, cabecera="| Issue / rama | Sesiones"):
        tabla = salida.split(cabecera, 1)[1]
        for linea in tabla.splitlines():
            if linea.startswith(f"| {clave} |"):
                return [c.strip() for c in linea.strip("|").split("|")]
        self.fail(f"sin fila para {clave}")

    def test_por_issue(self):
        f = self.fila(self.ejecuta(), "VIC-12")
        # Issue, sesiones, coste, min, interv., rondas, conf., desc., corr., mutación, defectos
        self.assertEqual(f, ["VIC-12", "2", "$3.00", "40", "5", "2", "7", "3", "6", "5 de 5", "—"])

    def test_sesion_sin_campos_nuevos(self):
        f = self.fila(self.ejecuta(), "main")
        self.assertEqual(f[4:], ["0", "0", "0", "0", "0", "—", "—"])

    def test_defectos_escapados_por_issue_de_origen(self):
        ruta = self.csv("issue,origen\nVIC-30,VIC-12\nvic-31,vic-12\nVIC-32,VIC-9\nVIC-33,\n")
        salida = self.ejecuta("--defectos", ruta)
        self.assertEqual(self.fila(salida, "VIC-12")[-1], "2")
        # Una issue con defectos aparece aunque no tenga sesiones.
        self.assertEqual(self.fila(salida, "VIC-9")[1:], ["0", "$0.00", "0", "0", "0", "0", "0", "0", "—", "1"])
        self.assertEqual(self.fila(salida, "main")[-1], "0")
        self.assertIn("Defectos sin issue de origen: VIC-33.", salida)

    def test_defecto_repetido_cuenta_una_vez(self):
        ruta = self.csv("issue,origen\nVIC-30,VIC-12\nVIC-30,VIC-12\n")
        self.assertEqual(self.fila(self.ejecuta("--defectos", ruta), "VIC-12")[-1], "1")

    def test_con_columna_labels_solo_cuentan_los_defectos(self):
        ruta = self.csv('ID,Labels,origen\nVIC-30,"Bug, defecto-escapado",VIC-12\nVIC-31,Bug,VIC-12\n')
        self.assertEqual(self.fila(self.ejecuta("--defectos", ruta), "VIC-12")[-1], "1")

    def test_misma_ronda_desde_otro_worktree(self):
        # El repo es el nombre de la carpeta: en otro worktree cambia, la ronda es la misma.
        self.guarda("s4", {"inicio": "2026-11-03T10:00", "repo": "calc-otro", "issues": ["VIC-12"],
                           "g4": ronda(21, 1, 5, 2, 4, "2026-11-03T10:00")})
        self.assertEqual(self.fila(self.ejecuta(), "VIC-12")[5:9], ["2", "7", "3", "6"])

    def test_intervenciones_copiadas_al_reanudar(self):
        self.guarda("s5", {"inicio": "2026-11-04T10:00", "issues": ["VIC-20"], "intervenciones": 3,
                           "intervenciones_ids": ["a", "b", "c"]})
        # La sesión reanudada copia a y b y añade d, más una intervención sin uuid.
        self.guarda("s6", {"inicio": "2026-11-04T12:00", "issues": ["VIC-20"], "intervenciones": 4,
                           "intervenciones_ids": ["a", "b", "d"]})
        salida = self.ejecuta()
        self.assertEqual(self.fila(salida, "VIC-20")[4], "5")

    def test_aviso_si_la_skill_no_anoto_la_linea(self):
        # VIC-50 usó sdd-review y sdd-implement sin ninguna línea; VIC-12 usó sdd-review
        # con rondas; VIC-51, sdd-implement en otra rama de la sesión de VIC-50.
        self.guarda("s9", {"inicio": "2026-11-05T10:00", "issues": ["VIC-50"],
                           "skills": {"sdd-review": ["VIC-50"], "sdd-implement": ["VIC-50", "VIC-51"]}})
        self.guarda("s10", {"inicio": "2026-11-05T11:00", "issues": ["VIC-12"],
                            "skills": {"sdd-review": ["VIC-12"]}})
        salida = self.ejecuta()
        self.assertEqual(self.fila(salida, "VIC-50")[5:10], ["⚠ sin línea", "—", "—", "—", "⚠ sin línea"])
        self.assertEqual(self.fila(salida, "VIC-51")[5:10], ["0", "0", "0", "0", "⚠ sin línea"])
        # Con rondas o mutación anotadas, no hay aviso.
        self.assertEqual(self.fila(salida, "VIC-12")[5:10], ["2", "7", "3", "6", "5 de 5"])
        self.assertIn("⚠ sin línea: se usó sdd-review", salida)

    def test_sin_skills_no_hay_aviso(self):
        salida = self.ejecuta()
        self.assertNotIn("⚠", salida)
        self.assertEqual(self.fila(salida, "main")[5:10], ["0", "0", "0", "0", "—"])

    def test_skill_sin_issue_va_a_la_clave_de_la_sesion(self):
        self.guarda("s11", {"inicio": "2026-11-05T12:00", "ramas": ["main"], "skills": {"sdd-review": [None]}})
        self.assertEqual(self.fila(self.ejecuta(), "main")[5], "⚠ sin línea")

    def test_sin_mutaciones_quita_el_aviso(self):
        self.guarda("s12", {"inicio": "2026-11-05T13:00", "issues": ["VIC-60"],
                            "skills": {"sdd-implement": ["VIC-60"]},
                            "mutacion": {"sin_mutaciones": True, "fecha": "x", "issue": "VIC-60"}})
        salida = self.ejecuta()
        self.assertEqual(self.fila(salida, "VIC-60")[9], "sin mutaciones")
        self.assertNotIn("⚠", salida)

    def test_csv_con_columnas_de_mas(self):
        # Una coma sin comillas en una fila deja una lista en la clave None de DictReader.
        ruta = self.csv("issue,origen\nVIC-30,VIC-12,sobra\n")
        self.assertEqual(self.fila(self.ejecuta("--defectos", ruta), "VIC-12")[-1], "1")
        ruta = self.csv("ID,Labels,origen\nVIC-31,defecto-escapado,VIC-12,sobra\n")
        self.assertEqual(self.fila(self.ejecuta("--defectos", ruta), "VIC-12")[-1], "1")

    def test_repo_y_modelos_escapados(self):
        self.guarda("s13", {"inicio": "2026-11-05T14:00", "repo": "a|b", "modelos": ["m|1"], "ramas": ["r"]})
        fila = [l for l in self.ejecuta().splitlines() if "2026-11-05 14:00" in l][0]
        self.assertIn("a\\|b", fila)
        self.assertIn("m\\|1", fila)
        self.assertEqual(fila.count(" | "), 8)  # nueve columnas

    def test_csv_de_linear_con_columna_id(self):
        ruta = self.csv('﻿ID,Title,Origen\nVIC-30,"Redondeo, mal",VIC-12\n')
        self.assertEqual(self.fila(self.ejecuta("--defectos", ruta), "VIC-12")[-1], "1")

    def test_csv_sin_columna_origen(self):
        ruta = self.csv("ID,Title\nVIC-30,x\n")
        with self.assertRaises(SystemExit) as e:
            self.ejecuta("--defectos", ruta)
        self.assertIn("origen", str(e.exception.code))

    def test_desde(self):
        salida = self.ejecuta("2026-11-02")
        self.assertEqual(self.fila(salida, "VIC-12")[1], "1")
        self.assertNotIn("| main |", salida)

    def test_fichero_del_repo(self):
        # Hoy solo tiene la cabecera: se lee sin error y no añade defectos.
        ruta = pathlib.Path(__file__).resolve().parent.parent / "historial" / "defectos-escapados.csv"
        salida = self.ejecuta("--defectos", str(ruta))
        self.assertIn("Total: 3 sesiones", salida)
        self.assertNotIn("Defectos sin issue de origen", salida)
        for clave in ("VIC-12", "main"):
            self.assertEqual(self.fila(salida, clave)[-1], "0")

    def test_csv_con_punto_y_coma(self):
        ruta = self.csv("issue;origen\nVIC-30;VIC-12\n")
        self.assertEqual(self.fila(self.ejecuta("--defectos", ruta), "VIC-12")[-1], "1")

    def test_etiqueta_exacta(self):
        ruta = self.csv('ID,Labels,origen\nVIC-30,no-defecto-escapado,VIC-12\nVIC-31,"Bug,defecto-escapado",VIC-12\n')
        self.assertEqual(self.fila(self.ejecuta("--defectos", ruta), "VIC-12")[-1], "1")

    def test_rama_con_barra_vertical(self):
        self.guarda("s7", {"inicio": "2026-11-05T10:00", "ramas": ["x|y"]})
        self.assertIn("| x\\|y |", self.ejecuta())

    def test_rondas_y_mutacion_por_la_issue_de_su_rama(self):
        # Una sesión que pasó por dos issues: cada ronda va a la suya, no a "VIC-40, VIC-41".
        self.guarda("s8", {"inicio": "2026-11-05T10:00", "issues": ["VIC-40", "VIC-41"],
                           "g4": {"50/1": {"pr": 50, "ronda": 1, "confirmados": 3, "descartados": 0,
                                           "corregidos": 3, "fecha": "2026-11-05T10:00", "issue": "VIC-40"},
                                  "51/1": {"pr": 51, "ronda": 1, "confirmados": 1, "descartados": 1,
                                           "corregidos": 0, "fecha": "2026-11-05T11:00", "issue": "VIC-41"}},
                           "mutacion": {"detectados": 2, "total": 3, "fecha": "x", "issue": "VIC-41"}})
        salida = self.ejecuta()
        self.assertEqual(self.fila(salida, "VIC-40")[5:10], ["1", "3", "0", "3", "—"])
        self.assertEqual(self.fila(salida, "VIC-41")[5:10], ["1", "1", "1", "0", "2 de 3"])
        self.assertEqual(self.fila(salida, "VIC-40, VIC-41")[5:10], ["0", "0", "0", "0", "—"])


class DeLaSesionAlResumen(unittest.TestCase):
    """La cadena completa: transcript → sdd-metricas.py → JSON → resumen-metricas.py."""

    def test_skill_sin_linea_y_con_linea(self):
        ruta_m = pathlib.Path(__file__).resolve().parent.parent / "entorno" / "sdd-metricas.py"
        spec = importlib.util.spec_from_file_location("sdd_metricas_e2e", ruta_m)
        sdd_metricas = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sdd_metricas)
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            carpeta = os.path.join(d, "sdd-metricas")
            transcript = os.path.join(d, "t.jsonl")
            skill = lambda rama: {"type": "assistant", "gitBranch": rama, "message": {"content": [
                {"type": "tool_use", "id": "s", "name": "Skill", "input": {"skill": "sdd:sdd-review"}}]}}
            linea = "Métricas G4: PR #9 · ronda 1 · confirmados 2 · descartados 1 · corregidos 2"
            entradas = [
                skill("feat/vic-70-a"),  # VIC-70: sdd-review sin línea
                skill("feat/vic-71-b"),  # VIC-71: sdd-review con línea publicada
                {"type": "assistant", "gitBranch": "feat/vic-71-b", "timestamp": "t", "message": {"content": [
                    {"type": "tool_use", "id": "g", "name": "Bash", "input": {"command":
                        "{ cat r.md; cat <<'METRICAS_SDD'\n" + linea + "\nMETRICAS_SDD\n} | gh pr comment 9 -F -"}}]}},
                {"type": "user", "toolUseResult": {}, "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "g", "is_error": False, "content": "ok"}]}},
            ]
            with open(transcript, "w", encoding="utf-8") as f:
                f.writelines(json.dumps(e, ensure_ascii=False) + "\n" for e in entradas)
            entrada = {"session_id": "e2e", "transcript_path": transcript, "workspace": {"project_dir": d}}
            with mock.patch.object(sdd_metricas, "CARPETA", carpeta), \
                    mock.patch("sys.stdin", io.StringIO(json.dumps(entrada))), redirect_stdout(io.StringIO()):
                sdd_metricas.main()
            with redirect_stdout(io.StringIO()) as salida:
                resumen.main([carpeta])
            filas = {l.split("|")[1].strip(): [c.strip() for c in l.strip("|").split("|")]
                     for l in salida.getvalue().split("| Issue / rama | Sesiones", 1)[1].splitlines()
                     if l.startswith("| VIC-")}
            self.assertEqual(filas["VIC-70"][5:9], ["⚠ sin línea", "—", "—", "—"])
            self.assertEqual(filas["VIC-71"][5:9], ["1", "2", "1", "2"])


class Revisores(unittest.TestCase):
    """Tablas por revisor (VIC-48), con el formato de historial/coste-revision-bloque-4.md, §2."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(self.dir.name, "sesiones"))

    def tearDown(self):
        self.dir.cleanup()

    def guarda(self, nombre, revisores):
        with open(os.path.join(self.dir.name, "sesiones", nombre + ".json"), "w", encoding="utf-8") as f:
            json.dump({"inicio": "2026-11-22T10:00", "issues": ["VIC-48"], "revisores": revisores}, f)

    def ejecuta(self):
        with redirect_stdout(io.StringIO()) as salida:
            resumen.main([self.dir.name])
        return salida.getvalue()

    def filas(self, salida, cabecera):
        tabla = salida.split(cabecera, 1)[1].split("\n\n", 1)[0]
        return [[c.strip() for c in l.strip("|").split("|")] for l in tabla.splitlines()[2:]]

    def test_una_fila_por_pr_ronda_y_revisor_con_total(self):
        opus = {"claude-opus-5-5": {"entrada": 10, "cache_escritura": 50000, "cache_lectura": 900000,
                                    "salida": 20000}}
        self.guarda("s1", {**revisor(52, 1, "A", "2026-11-22T10:00"),
                           **revisor(52, 1, "B", "2026-11-22T10:00", conf=(1, 2, 0), desc=(0, 1, 0),
                                     tokens=opus, minutos=2.35)})
        # Sesión reanudada que repite la ronda 1 de A con otros números: cuenta la última.
        self.guarda("s2", revisor(52, 1, "A", "2026-11-22T11:00", conf=(0, 0, 1)))
        filas = self.filas(self.ejecuta(), "| Issue | PR | Ronda | Revisor")
        # Sonnet: 20×2 + 8100×10 + 170000×0,10 + 20000×2×1,25 = 148 040 µ$ → 0,15 $.
        self.assertEqual(filas[0], ["VIC-48", "#52", "1", "A", "claude-sonnet-5-5", "198 k", "8,1 k", "1,0",
                                    "0,15 $", "0 / 0 / 1", "1"])
        # Opus: 10×4 + 20000×20 + 900000×0,20 + 50000×4×1,25 = 830 040 µ$ → 0,83 $.
        self.assertEqual(filas[1], ["VIC-48", "#52", "1", "B", "claude-opus-5-5", "970 k", "20,0 k", "2,4",
                                    "0,83 $", "1 / 2 / 0", "1"])
        self.assertEqual(filas[2], ["**Total (2 rondas)**", "", "", "", "", "**1,2 M**", "", "**3,4**",
                                    "**0,98 $**", "**1 / 2 / 1**", "**2**"])

    def test_por_issue_y_revisor(self):
        self.guarda("s1", {**revisor(52, 1, "A", "2026-11-22T10:00"), **revisor(52, 2, "A", "2026-11-22T12:00"),
                           **revisor(9, 1, "A", "2026-11-22T10:00", issue="VIC-7")})
        filas = self.filas(self.ejecuta(), "| Issue | Revisor | Modelo | Rondas")
        self.assertEqual(filas, [["VIC-48", "A", "claude-sonnet-5-5", "2", "396 k", "2,0", "0,30 $", "0 / 2 / 4", "2"],
                                 ["VIC-7", "A", "claude-sonnet-5-5", "1", "198 k", "1,0", "0,15 $", "0 / 1 / 2", "1"]])

    def test_millones(self):
        # G4-1-A-03: 999 600 redondea a 1,0 M, no a «1000 k».
        self.assertEqual([resumen.miles(n) for n in (196400, 999400, 999600, 1500000)],
                         ["196 k", "999 k", "1,0 M", "1,5 M"])
        self.assertEqual(resumen.miles(8149, 1), "8,1 k")

    def test_modelo_del_transcript_y_alias_no_se_mezclan(self):
        # G4-1-A-02: una ronda con transcript y otra sin él: un solo modelo en la tabla por issue.
        self.guarda("s1", {**revisor(52, 1, "A", "2026-11-22T10:00"),
                           **revisor(52, 2, "A", "2026-11-22T12:00", tokens=False)})
        filas = self.filas(self.ejecuta(), "| Issue | Revisor | Modelo | Rondas")
        self.assertEqual(filas[0][2], "claude-sonnet-5-5")
        self.guarda("s1", revisor(52, 2, "A", "2026-11-22T12:00", tokens=False))
        self.assertEqual(self.filas(self.ejecuta(), "| Issue | Revisor | Modelo | Rondas")[0][2], "sonnet")

    def test_sin_transcript_ni_precio(self):
        self.guarda("s1", {**revisor(52, 1, "A", "2026-11-22T10:00", tokens=False),
                           **revisor(52, 1, "B", "2026-11-22T10:00",
                                     tokens={"claude-nuevo|x": {"entrada": 1000, "salida": 0}})})
        salida = self.ejecuta()
        filas = self.filas(salida, "| Issue | PR | Ronda | Revisor")
        self.assertEqual(filas[0][4:9], ["sonnet", "—", "—", "—", "—"])
        self.assertEqual(filas[2][0], "**Total (2 rondas)**")
        self.guarda("s1", revisor(52, 1, "A", "2026-11-22T10:00"))
        self.assertEqual(self.filas(self.ejecuta(), "| Issue | PR | Ronda | Revisor")[1][0], "**Total (1 ronda)**")
        # El | del modelo va escapado: aquí parte la celda en dos.
        self.assertEqual(filas[1][4:10], ["claude-nuevo\\", "x", "1 k", "0,0 k", "1,0", "?"])
        self.assertIn("?: sin precio para claude-nuevo|x", salida)
        self.assertIn("—: 1 sin el transcript del subagente", salida)

    def test_sin_revisores_no_hay_tablas(self):
        self.guarda("s1", {})
        self.assertNotIn("| Revisor |", self.ejecuta())


if __name__ == "__main__":
    unittest.main()

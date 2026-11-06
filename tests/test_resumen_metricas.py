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


if __name__ == "__main__":
    unittest.main()

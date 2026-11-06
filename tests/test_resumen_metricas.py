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
        ruta = pathlib.Path(__file__).resolve().parent.parent / "historial" / "defectos-escapados.csv"
        self.assertIn("Total: 3 sesiones", self.ejecuta("--defectos", str(ruta)))


if __name__ == "__main__":
    unittest.main()

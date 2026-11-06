"""Tests de entorno/sdd-metricas.py (VIC-16).

Los casos de issue_de() son los que se probaron a mano en el PR #3: ramas
<tipo>/vic-N-… de docs/convenciones.md, el formato anterior vic-N-… y
nombres que no son de una issue.
"""
import importlib.util
import pathlib
import unittest

RUTA = pathlib.Path(__file__).resolve().parent.parent / "entorno" / "sdd-metricas.py"
# El nombre lleva guion, así que no se puede importar con import.
_spec = importlib.util.spec_from_file_location("sdd_metricas", RUTA)
sdd_metricas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sdd_metricas)


class IssueDe(unittest.TestCase):
    def test_rama_con_tipo(self):
        casos = {
            "chore/vic-16-convenciones": "VIC-16",
            "feat/vic-12-logica": "VIC-12",
            "adr/vic-19-0009-modelos": "VIC-19",
        }
        for rama, issue in casos.items():
            with self.subTest(rama=rama):
                self.assertEqual(sdd_metricas.issue_de(rama), issue)

    def test_formato_anterior_sin_tipo(self):
        self.assertEqual(sdd_metricas.issue_de("vic-10-calculo"), "VIC-10")

    def test_ramas_sin_issue(self):
        for rama in ("spec-calc-003-x", "main", "feat/abc-3-x", "", None):
            with self.subTest(rama=rama):
                self.assertIsNone(sdd_metricas.issue_de(rama))


if __name__ == "__main__":
    unittest.main()

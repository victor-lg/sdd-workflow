"""El ejemplo de E2E con regresión visual y axe (M27, VIC-22, PR 3), en docs/ejemplos/e2e/.

Los navegadores no están en la CI de este repo: aquí se comprueba el texto (lo que exige sdd-implement),
que el lockfile pasa el job `versiones` del ejemplo de workflow con su misma imagen, y que las capturas de
referencia están. Las capturas se generan y se comprueban en el contenedor (README.md del ejemplo)."""
import json
import os
import pathlib
import re
import struct
import subprocess
import tempfile
import unittest

import yaml

RAIZ = pathlib.Path(__file__).resolve().parent.parent
EJEMPLO = RAIZ / "docs" / "ejemplos" / "e2e"
SPEC = (EJEMPLO / "ejemplo.spec.mjs").read_text(encoding="utf-8")
CONFIG = (EJEMPLO / "playwright.config.mjs").read_text(encoding="utf-8")
WORKFLOW = yaml.safe_load((RAIZ / "docs" / "ejemplos" / "workflows" / "tests-node-playwright.yml").read_text(encoding="utf-8"))
VERSIONES = next(p for p in WORKFLOW["jobs"]["versiones"]["steps"] if p.get("id") == "comprobar")
REGISTRO = (RAIZ / "docs" / "herramientas.md").read_text(encoding="utf-8")
CAPTURAS = ["panel-resumen", "formulario-con-aviso"]


class TextoDelEjemplo(unittest.TestCase):
    def test_axe_tal_cual_al_llegar_y_en_el_estado_nuevo(self):
        self.assertIn("const { violations } = await new AxeBuilder({ page }).analyze();\n  expect(violations).toEqual([]);", SPEC)
        for prohibido in ("disableRules", "exclude", "include", "withTags", "withRules", "options(", "configure",
                          "violations.filter"):
            with self.subTest(prohibido=prohibido):
                self.assertNotIn(prohibido, SPEC)
        for test in re.split(r"\ntest\(", SPEC)[1:]:
            with self.subTest(test=test.split("\n")[0]):
                self.assertEqual(test.count("sinViolaciones(page)"), 1)
                # Al llegar (antes de rellenar nada) o en el estado nuevo (tras el aviso).
                self.assertLess(test.index("page.goto"), test.index("sinViolaciones(page)"))
                if ".click()" in test:
                    self.assertLess(test.index('toHaveText("El grosor tiene que ser positivo")'),
                                    test.index("sinViolaciones(page)"))
                else:
                    self.assertNotIn(".fill(", test[:test.index("sinViolaciones(page)")])

    def test_capturas_sin_tolerancias_ni_mascaras(self):
        for prohibido in ("maxDiffPixels", "maxDiffPixelRatio", "threshold", "mask", "stylePath", "test.skip",
                          "test.fixme", "test.fail", "ignoreSnapshots"):
            with self.subTest(prohibido=prohibido):
                self.assertNotIn(prohibido, SPEC + CONFIG)
        self.assertIn('updateSnapshots: "none"', CONFIG)
        for captura in CAPTURAS:
            self.assertIn(f'toHaveScreenshot("{captura}.png")', SPEC)

    def test_navegadores_de_la_ci(self):
        self.assertEqual(re.findall(r'name: "(\w+)"', CONFIG), ["chromium", "webkit"])


class Capturas(unittest.TestCase):
    def test_estan_las_de_referencia_en_linux(self):
        """Una por captura y navegador, generadas en la imagen de la CI (README.md del ejemplo). Sin navegador en
        la CI, solo se comprueba que están y que son PNG: que sean correctas lo aprueba la persona al generarlas."""
        carpeta = EJEMPLO / "ejemplo.spec.mjs-snapshots"
        esperadas = {f"{c}-{n}-linux.png" for c in CAPTURAS for n in ("chromium", "webkit")}
        presentes = {f.name for f in carpeta.glob("*.png")} if carpeta.is_dir() else set()
        self.assertEqual(presentes, esperadas)
        contenidos = {}
        for nombre in esperadas:
            with self.subTest(captura=nombre):
                datos = (carpeta / nombre).read_bytes()
                self.assertEqual(datos[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(datos[12:16], b"IHDR")
                ancho, alto = struct.unpack(">II", datos[16:24])
                self.assertGreater(ancho * alto, 0)
                self.assertTrue(datos.endswith(b"IEND\xaeB`\x82"), "PNG truncado")
                contenidos[nombre] = datos
        # Chromium y WebKit no dan los mismos píxeles: dos ficheros iguales serían una copia.
        for captura in CAPTURAS:
            self.assertNotEqual(contenidos[f"{captura}-chromium-linux.png"], contenidos[f"{captura}-webkit-linux.png"])


class Dependencias(unittest.TestCase):
    def test_el_lockfile_pasa_versiones_con_la_imagen_del_workflow(self):
        """Sin el override de playwright-core, @axe-core/playwright metía la 1.65.1 y no coincidía con la imagen."""
        with tempfile.TemporaryDirectory() as temporal:
            salida = pathlib.Path(temporal) / "salida"
            salida.write_text("")
            r = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", VERSIONES["run"]],
                               cwd=EJEMPLO, capture_output=True, text=True, timeout=60,
                               env=dict(os.environ, GITHUB_OUTPUT=str(salida), IMAGEN=VERSIONES["env"]["IMAGEN"]))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("si=true", salida.read_text())

    def test_versiones_exactas_y_registradas(self):
        paquete = json.loads((EJEMPLO / "package.json").read_text(encoding="utf-8"))
        paquetes = json.loads((EJEMPLO / "package-lock.json").read_text(encoding="utf-8"))["packages"]
        for nombre, version in {**paquete["devDependencies"], **paquete["overrides"]}.items():
            with self.subTest(paquete=nombre):
                self.assertRegex(version, r"^\d+\.\d+\.\d+$")
                self.assertEqual(paquetes[f"node_modules/{nombre}"]["version"], version)
        for nombre in ("@axe-core/playwright", "axe-core"):
            with self.subTest(registro=nombre):
                datos = paquetes[f"node_modules/{nombre}"]
                self.assertTrue(datos["version"] in REGISTRO and datos["integrity"] in REGISTRO,
                                f"{nombre} {datos['version']} no está en docs/herramientas.md con su integridad")


if __name__ == "__main__":
    unittest.main()

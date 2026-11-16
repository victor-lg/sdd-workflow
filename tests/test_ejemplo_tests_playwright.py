"""El ejemplo de workflow de tests con el contenedor de Playwright por digest y los trozos (M6, VIC-22).

El job `versiones` falla con un mensaje claro si el package-lock.json y la imagen no tienen la misma versión de
Playwright (calculadora-discos#42: Dependabot subió el paquete y no la imagen). Sus pasos se ejecutan aquí con
bash sobre carpetas de prueba; en GitHub Actions no corre nunca en este repo, solo en los proyectos que lo copian."""
import json
import os
import pathlib
import re
import subprocess
import tempfile
import textwrap
import unittest

import yaml

RAIZ = pathlib.Path(__file__).resolve().parent.parent
TEXTO = (RAIZ / "docs" / "ejemplos" / "workflows" / "tests-node-playwright.yml").read_text(encoding="utf-8")
WORKFLOW = yaml.safe_load(TEXTO)
JOBS = WORKFLOW["jobs"]
REGISTRO = (RAIZ / "docs" / "herramientas.md").read_text(encoding="utf-8")
IMAGEN = re.compile(r"mcr\.microsoft\.com/playwright:v(\d+\.\d+\.\d+)-noble@sha256:[0-9a-f]{64}")


def paso(job, nombre):
    return next(p for p in JOBS[job]["steps"] if p.get("name") == nombre)


def lockfile(**versiones):
    """Un package-lock.json v3 con esas versiones; las claves son las rutas de `packages`."""
    paquetes = {"": {"name": "p", "devDependencies": {"@playwright/test": "*"}}}
    for ruta, version in versiones.items():
        paquetes[ruta] = {"version": version, "dev": True}
    return {"name": "p", "lockfileVersion": 3, "requires": True, "packages": paquetes}


def con(version):
    return lockfile(**{"node_modules/@playwright/test": version, "node_modules/playwright": version,
                       "node_modules/playwright-core": version})


class RepoDePrueba(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.carpeta = pathlib.Path(self.temporal.name) / "repo"
        self.carpeta.mkdir()

    def escribir(self, nombre, contenido):
        (self.carpeta / nombre).write_text(json.dumps(contenido) if not isinstance(contenido, str) else contenido)

    def ejecutar(self, job, nombre, env):
        definicion = paso(job, nombre)
        salida = pathlib.Path(self.temporal.name) / "salida"
        salida.write_text("")
        entorno = dict(os.environ, GITHUB_OUTPUT=str(salida), **env)
        # Como GitHub Actions con `shell: bash` por defecto: bash -e.
        r = subprocess.run(["bash", "-e", "-c", definicion["run"]], cwd=self.carpeta, env=entorno,
                           capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout + r.stderr, dict(l.split("=", 1) for l in salida.read_text().splitlines() if l)


class TextoDelEjemplo(unittest.TestCase):
    def test_solo_pull_request_y_lectura(self):
        self.assertEqual(list(WORKFLOW[True]), ["pull_request"])
        self.assertEqual(WORKFLOW["permissions"], {"contents": "read"})

    def test_la_imagen_se_escribe_una_vez_y_por_digest(self):
        """Una sola imagen en el fichero, la del job `versiones`, fijada por el digest de su índice."""
        self.assertEqual(len(re.findall(r"playwright:v[\d.]+-noble@sha256:", TEXTO)), 1)
        imagen = paso("versiones", "¿Coinciden Playwright y su imagen?")["env"]["IMAGEN"]
        self.assertRegex(imagen, f"^{IMAGEN.pattern}$")

    def test_la_imagen_esta_en_el_registro(self):
        imagen = paso("versiones", "¿Coinciden Playwright y su imagen?")["env"]["IMAGEN"]
        for parte in imagen.split("@"):
            self.assertTrue(parte in REGISTRO, f"{parte} no está en docs/herramientas.md")

    def test_los_trozos_usan_la_imagen_de_versiones(self):
        e2e = JOBS["e2e"]
        self.assertEqual(e2e["needs"], "versiones")
        self.assertEqual(e2e["if"], "needs.versiones.outputs.si == 'true'")
        self.assertEqual(e2e["container"], {"image": "${{ needs.versiones.outputs.imagen }}"})
        self.assertEqual(e2e["strategy"]["matrix"]["trozo"], [1, 2, 3])
        self.assertFalse(e2e["strategy"]["fail-fast"])
        self.assertIn("--shard=${{ matrix.trozo }}/3", TEXTO)

    def test_no_instala_navegadores(self):
        """Los trae la imagen: `playwright install` volvería a descargarlos (y con --with-deps, a esperar a apt)."""
        self.assertNotIn("playwright install", TEXTO)

    def test_check_final_tests(self):
        tests = JOBS["tests"]
        self.assertEqual(tests["needs"], ["versiones", "e2e"])
        self.assertEqual(tests["if"], "always()")

    def test_tiempo_maximo_en_cada_job(self):
        for nombre, job in JOBS.items():
            with self.subTest(job=nombre):
                self.assertIn("timeout-minutes", job)

    def test_acciones_fijadas_por_sha_y_registradas(self):
        usos = re.findall(r"uses: (\S+)@(\S+)", TEXTO)
        self.assertTrue(usos)
        for accion, ref in usos:
            with self.subTest(accion=accion):
                self.assertRegex(ref, r"^[0-9a-f]{40}$")
                if accion != "actions/checkout":
                    self.assertTrue(ref in REGISTRO, f"{accion}@{ref} no está en docs/herramientas.md")

    def test_sin_credenciales_en_el_checkout(self):
        for job in ("versiones", "e2e"):
            checkout = next(p for p in JOBS[job]["steps"] if p.get("uses", "").startswith("actions/checkout@"))
            self.assertIs(checkout["with"]["persist-credentials"], False)


class Versiones(RepoDePrueba):
    """El paso que compara el package-lock.json con la imagen."""
    PASO = "¿Coinciden Playwright y su imagen?"
    BUENA = "mcr.microsoft.com/playwright:v1.65.0-noble@sha256:" + "a" * 64

    def comprobar(self, imagen=BUENA):
        return self.ejecutar("versiones", self.PASO, {"IMAGEN": imagen})

    def test_sin_package_json_pasa_sin_e2e(self):
        codigo, texto, salida = self.comprobar()
        self.assertEqual(codigo, 0, texto)
        self.assertEqual(salida, {"si": "false"})

    def test_misma_version_pasa_y_da_la_imagen(self):
        self.escribir("package.json", {"name": "p"})
        self.escribir("package-lock.json", con("1.65.0"))
        codigo, texto, salida = self.comprobar()
        self.assertEqual(codigo, 0, texto)
        self.assertEqual(salida, {"si": "true", "imagen": self.BUENA})

    def test_dependabot_sube_el_paquete_y_no_la_imagen(self):
        """calculadora-discos#42: el lockfile en 1.65.0 y la imagen en 1.64.1."""
        self.escribir("package.json", {"name": "p"})
        self.escribir("package-lock.json", con("1.65.0"))
        codigo, texto, salida = self.comprobar(self.BUENA.replace("1.65.0", "1.64.1"))
        self.assertNotEqual(codigo, 0)
        self.assertIn("::error::@playwright/test está en 1.65.0 (package-lock.json) y la imagen de este workflow es la "
                      "v1.64.1. Sube la imagen a mcr.microsoft.com/playwright:v1.65.0-noble con su digest", texto)
        self.assertNotIn("si", salida)

    def test_playwright_core_distinto_falla(self):
        self.escribir("package.json", {"name": "p"})
        self.escribir("package-lock.json", lockfile(**{"node_modules/@playwright/test": "1.65.0",
                                                      "node_modules/playwright-core": "1.64.1"}))
        codigo, texto, _ = self.comprobar()
        self.assertNotEqual(codigo, 0)
        self.assertIn("::error::playwright-core está en 1.64.1", texto)

    def test_copia_anidada_distinta_falla(self):
        self.escribir("package.json", {"name": "p"})
        bloqueo = con("1.65.0")
        bloqueo["packages"]["node_modules/otro/node_modules/playwright-core"] = {"version": "1.60.0"}
        self.escribir("package-lock.json", bloqueo)
        codigo, texto, _ = self.comprobar()
        self.assertNotEqual(codigo, 0)
        self.assertIn("::error::playwright-core está en 1.60.0", texto)

    def test_la_version_del_lockfile_no_abre_ordenes(self):
        """La versión sale del lockfile de la rama: un salto de línea no puede empezar otra orden de workflow."""
        self.escribir("package.json", {"name": "p"})
        self.escribir("package-lock.json", con("1.65.0\n::warning::inyectada%"))
        codigo, texto, _ = self.comprobar()
        self.assertNotEqual(codigo, 0)
        self.assertIn("1.65.0%0A::warning::inyectada%25", texto)
        self.assertNotRegex(texto, r"(?m)^::warning::")

    def test_sin_digest_falla(self):
        self.escribir("package.json", {"name": "p"})
        self.escribir("package-lock.json", con("1.65.0"))
        for imagen in ("mcr.microsoft.com/playwright:v1.65.0-noble", "mcr.microsoft.com/playwright:v1.65.0-noble@sha256:abc",
                       "otro.registro/playwright:v1.65.0-noble@sha256:" + "a" * 64,
                       "mcr.microsoft.com/playwright:v1.65.0-noble@sha256:" + "a" * 64 + "\nmas"):
            with self.subTest(imagen=imagen):
                codigo, texto, salida = self.comprobar(imagen)
                self.assertNotEqual(codigo, 0)
                self.assertIn("::error::La imagen de Playwright tiene que ser", texto)
                self.assertNotIn("si", salida)

    def test_sin_lockfile_falla(self):
        self.escribir("package.json", {"name": "p"})
        codigo, texto, _ = self.comprobar()
        self.assertNotEqual(codigo, 0)
        self.assertIn("::error::Falta package-lock.json", texto)

    def test_lockfile_v1_falla(self):
        self.escribir("package.json", {"name": "p"})
        self.escribir("package-lock.json", {"name": "p", "lockfileVersion": 1, "dependencies": {}})
        codigo, texto, _ = self.comprobar()
        self.assertNotEqual(codigo, 0)
        self.assertIn('::error::package-lock.json no tiene "packages"', texto)

    def test_sin_playwright_en_el_lockfile_falla(self):
        self.escribir("package.json", {"name": "p"})
        self.escribir("package-lock.json", lockfile(**{"node_modules/otro": "1.0.0"}))
        codigo, texto, _ = self.comprobar()
        self.assertNotEqual(codigo, 0)
        self.assertIn("::error::package-lock.json no tiene @playwright/test", texto)


class CheckFinal(RepoDePrueba):
    """El job `tests`, que mantiene el nombre del check obligatorio."""
    PASO = "¿Han pasado las versiones y los 3 trozos?"

    def final(self, versiones, hay, e2e):
        return self.ejecutar("tests", self.PASO, {"VERSIONES": versiones, "HAY": hay, "E2E": e2e})[0]

    def test_resultados(self):
        for versiones, hay, e2e, espera in [
            ("success", "true", "success", 0),
            ("success", "false", "skipped", 0),     # sin package.json
            ("success", "true", "failure", 1),
            ("success", "true", "cancelled", 1),
            ("success", "true", "skipped", 1),
            ("failure", "", "skipped", 1),          # versiones distintas
            ("cancelled", "", "skipped", 1),
        ]:
            with self.subTest(versiones=versiones, hay=hay, e2e=e2e):
                self.assertEqual(self.final(versiones, hay, e2e) != 0, bool(espera))


if __name__ == "__main__":
    unittest.main()

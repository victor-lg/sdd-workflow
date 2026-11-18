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


def nombre_del_job(expresion, draft):
    """El nombre que da GitHub a un job con `name: ${{ github.event.pull_request.draft && 'A' || 'B' }}`.
    Falla si la expresión depende de otra cosa que el evento: un run relanzado conserva el evento de
    cuando se lanzó, así que un run de borrador relanzado sigue llamándose A (VIC-33, G4 de #49)."""
    m = re.fullmatch(r"\$\{\{ github\.event\.pull_request\.draft && '([^']+)' \|\| '([^']+)' \}\}", expresion)
    assert m, f"el nombre no sale solo del evento: {expresion}"
    return m.group(1) if draft else m.group(2)


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
        entorno = dict(os.environ, GITHUB_OUTPUT=str(salida))
        entorno.update(env)
        # Como GitHub Actions con `shell: bash` por defecto.
        r = subprocess.run(["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", definicion["run"]], cwd=self.carpeta, env=entorno,
                           capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout + r.stderr, dict(l.split("=", 1) for l in salida.read_text().splitlines() if l)


class TextoDelEjemplo(unittest.TestCase):
    def test_solo_pull_request_y_lectura(self):
        self.assertEqual(list(WORKFLOW[True]), ["pull_request"])
        self.assertEqual(WORKFLOW["permissions"], {"contents": "read"})

    def test_corre_al_marcar_el_pr_listo(self):
        """VIC-33: sin `ready_for_review`, los E2E no correrían hasta el siguiente push tras salir del borrador."""
        self.assertEqual(WORKFLOW[True]["pull_request"]["types"], ["opened", "synchronize", "reopened", "ready_for_review"])

    def test_ningun_job_pide_mas_permisos(self):
        for nombre, job in JOBS.items():
            with self.subTest(job=nombre):
                self.assertNotIn("permissions", job)

    def test_el_check_requerido_no_existe_en_borrador(self):
        """En borrador el job final se llama `tests (borrador)`: su verde barato nunca cuenta como el check
        requerido `tests`, ni en el hueco hasta que GitHub crea el job del run de `ready_for_review`, ni
        al relanzar un run de borrador con el PR ya listo (G4 de #49)."""
        expresion = JOBS["tests"]["name"]
        self.assertEqual(nombre_del_job(expresion, draft=True), "tests (borrador)")
        self.assertEqual(nombre_del_job(expresion, draft=False), "tests")

    def test_el_borrador_sale_siempre_del_evento(self):
        """El nombre, los trozos y el aviso miran lo mismo: si uno mirara la API y otro el evento, un PR que
        vuelve a borrador a mitad de un run podría dar el verde barato con el nombre del check requerido."""
        self.assertIn("!github.event.pull_request.draft", JOBS["e2e"]["if"])
        self.assertEqual(paso("tests", CheckFinal.PASO)["env"]["BORRADOR"], "${{ github.event.pull_request.draft }}")
        self.assertNotIn("gh api", TEXTO)
        self.assertNotIn("steps.borrador", TEXTO)

    def test_la_imagen_se_escribe_una_vez_y_por_digest(self):
        """Una sola imagen en el fichero, la del job `versiones`, fijada por el digest de su índice."""
        # Cualquier clave YAML con una imagen de Playwright, con digest o sin él (no los mensajes del script).
        self.assertEqual(len(re.findall(r"(?m)^\s*[\w-]+:\s*\S*mcr\.microsoft\.com/playwright", TEXTO)), 1)
        imagen = paso("versiones", "¿Coinciden Playwright y su imagen?")["env"]["IMAGEN"]
        self.assertRegex(imagen, f"^{IMAGEN.pattern}$")

    def test_la_imagen_esta_en_el_registro(self):
        imagen = paso("versiones", "¿Coinciden Playwright y su imagen?")["env"]["IMAGEN"]
        for parte in imagen.split("@"):
            self.assertTrue(parte in REGISTRO, f"{parte} no está en docs/herramientas.md")

    def test_los_trozos_usan_la_imagen_de_versiones(self):
        e2e = JOBS["e2e"]
        self.assertEqual(e2e["needs"], "versiones")
        self.assertEqual(e2e["if"], "needs.versiones.outputs.si == 'true' && !github.event.pull_request.draft")
        self.assertEqual(e2e["container"], {"image": "${{ needs.versiones.outputs.imagen }}"})
        self.assertEqual(e2e["strategy"]["matrix"]["trozo"], [1, 2, 3])
        self.assertFalse(e2e["strategy"]["fail-fast"])

    def test_pasos_de_los_trozos(self):
        """En orden: checkout, Node, npm ci y su trozo de E2E. Los unitarios tienen su job (VIC-33)."""
        pasos = JOBS["e2e"]["steps"]
        self.assertEqual([p.get("uses", "").split("@")[0] for p in pasos[:2]], ["actions/checkout", "actions/setup-node"])
        self.assertEqual([p.get("run") for p in pasos[2:]], ["npm ci --ignore-scripts", "npx playwright test --shard=${{ matrix.trozo }}/3"])

    def test_unitarios_tambien_en_borrador(self):
        """VIC-33: los unitarios son baratos y corren en borrador, sin la imagen de Playwright."""
        unitarios = JOBS["unitarios"]
        self.assertEqual(unitarios["needs"], "versiones")
        self.assertEqual(unitarios["if"], "needs.versiones.outputs.si == 'true'")
        self.assertNotIn("container", unitarios)
        pasos = unitarios["steps"]
        self.assertEqual([p.get("uses", "").split("@")[0] for p in pasos[:2]], ["actions/checkout", "actions/setup-node"])
        self.assertEqual([p.get("run") for p in pasos[2:]], ["npm ci --ignore-scripts", 'node --test "tests/unit/**/*.test.js"'])

    def test_no_instala_navegadores(self):
        """Los trae la imagen: `playwright install` volvería a descargarlos (y con --with-deps, a esperar a apt)."""
        for job in JOBS.values():
            for p in job["steps"]:
                self.assertNotIn("playwright install", p.get("run", ""))

    def test_cableado_entre_jobs(self):
        """Una errata en una salida o un resultado dejaría el check `tests` en verde sin E2E (G4 de #47)."""
        self.assertEqual(paso("versiones", "¿Coinciden Playwright y su imagen?")["id"], "comprobar")
        self.assertEqual(JOBS["versiones"]["outputs"], {"si": "${{ steps.comprobar.outputs.si }}",
                                                         "imagen": "${{ steps.comprobar.outputs.imagen }}"})
        self.assertEqual(paso("tests", CheckFinal.PASO)["env"], {
            "VERSIONES": "${{ needs.versiones.result }}",
            "HAY": "${{ needs.versiones.outputs.si }}",
            "UNITARIOS": "${{ needs.unitarios.result }}",
            "E2E": "${{ needs.e2e.result }}",
            "BORRADOR": "${{ github.event.pull_request.draft }}",
        })

    def test_check_final_tests(self):
        """No se salta nunca: un job requerido saltado cuenta como superado (VIC-33)."""
        tests = JOBS["tests"]
        self.assertEqual(tests["needs"], ["versiones", "unitarios", "e2e"])
        self.assertEqual(tests["if"], "always()")
        self.assertEqual([p["name"] for p in tests["steps"]], [CheckFinal.PASO])
        self.assertTrue(all("if" not in p for p in tests["steps"]))

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
                # La de checkout es la de los otros workflows (sdd.yml); el registro anota las nuevas.
                if accion != "actions/checkout":
                    self.assertTrue(ref in REGISTRO, f"{accion}@{ref} no está en docs/herramientas.md")

    def test_sin_credenciales_en_el_checkout(self):
        for job in ("versiones", "unitarios", "e2e"):
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
        self.assertIn("::error::playwright-core está en 1.60.0 en node_modules/otro/node_modules/playwright-core", texto)
        self.assertIn("alinea esa copia en el lockfile", texto)
        self.assertNotIn("Sube la imagen", texto)

    def test_la_raiz_que_se_llama_como_playwright_no_cuenta(self):
        self.escribir("package.json", {"name": "playwright"})
        bloqueo = con("1.65.0")
        bloqueo["packages"][""].update({"name": "playwright", "version": "0.1.0"})
        self.escribir("package-lock.json", bloqueo)
        codigo, texto, _ = self.comprobar()
        self.assertEqual(codigo, 0, texto)

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

    def test_alias_de_npm_distinto_falla(self):
        self.escribir("package.json", {"name": "p"})
        bloqueo = con("1.65.0")
        bloqueo["packages"]["node_modules/pwc"] = {"name": "playwright-core", "version": "1.60.0"}
        self.escribir("package-lock.json", bloqueo)
        codigo, texto, _ = self.comprobar()
        self.assertNotEqual(codigo, 0)
        self.assertIn("::error::playwright-core está en 1.60.0", texto)

    def test_entrada_sin_version_falla_con_su_mensaje(self):
        self.escribir("package.json", {"name": "p"})
        bloqueo = con("1.65.0")
        bloqueo["packages"]["node_modules/playwright"] = {"link": True, "resolved": "../pw"}
        self.escribir("package-lock.json", bloqueo)
        codigo, texto, _ = self.comprobar()
        self.assertNotEqual(codigo, 0)
        self.assertIn("::error::playwright no tiene versión en package-lock.json", texto)
        self.assertNotIn("None", texto)

    def test_lockfile_con_otra_forma_falla_con_mensaje(self):
        self.escribir("package.json", {"name": "p"})
        for contenido, mensaje in [
            ("{no es json", "::error::package-lock.json no es JSON válido"),
            ("[]", '::error::package-lock.json no tiene "packages"'),
            (json.dumps({"lockfileVersion": 3, "packages": {"node_modules/@playwright/test": {"version": "1.65.0"},
                                                            "node_modules/playwright": "x"}}),
             '::error::package-lock.json tiene una entrada de "packages" que no es un objeto'),
        ]:
            with self.subTest(contenido=contenido):
                self.escribir("package-lock.json", contenido)
                codigo, texto, _ = self.comprobar()
                self.assertNotEqual(codigo, 0)
                self.assertIn(mensaje, texto)
                self.assertNotIn("Traceback", texto)

    def test_sin_playwright_en_el_lockfile_falla(self):
        self.escribir("package.json", {"name": "p"})
        self.escribir("package-lock.json", lockfile(**{"node_modules/otro": "1.0.0"}))
        codigo, texto, _ = self.comprobar()
        self.assertNotEqual(codigo, 0)
        self.assertIn("::error::package-lock.json no tiene @playwright/test", texto)


class CheckFinal(RepoDePrueba):
    """El job `tests`, que mantiene el nombre del check obligatorio, en los dos estados del PR (VIC-33)."""
    PASO = "¿Han pasado las versiones, los unitarios y los 3 trozos?"

    def final(self, versiones, hay, unitarios, e2e, borrador):
        return self.ejecutar("tests", self.PASO, {"VERSIONES": versiones, "HAY": hay, "UNITARIOS": unitarios,
                                                  "E2E": e2e, "BORRADOR": borrador})

    def test_listo_exige_los_trozos(self):
        for versiones, hay, unitarios, e2e, espera in [
            ("success", "true", "success", "success", 0),
            ("success", "false", "skipped", "skipped", 0),     # sin package.json
            ("success", "true", "success", "failure", 1),
            ("success", "true", "success", "cancelled", 1),
            ("success", "true", "success", "skipped", 1),      # relanzado con el evento del borrador
            ("success", "true", "failure", "success", 1),
            ("success", "true", "skipped", "success", 1),
            ("success", "", "skipped", "skipped", 1),          # salida `si` vacía: falla cerrado
            ("success", "verdadero", "success", "success", 1),
            ("failure", "", "skipped", "skipped", 1),          # versiones distintas
            ("cancelled", "", "skipped", "skipped", 1),
            ("cancelled", "true", "success", "success", 1),    # versiones no terminó bien, aunque llegara a escribir `si`
        ]:
            with self.subTest(versiones=versiones, hay=hay, unitarios=unitarios, e2e=e2e):
                codigo, texto, _ = self.final(versiones, hay, unitarios, e2e, "false")
                self.assertEqual(codigo != 0, bool(espera), texto)
                self.assertNotIn("::warning::", texto)

    def test_borrador_verde_con_aviso_sin_e2e(self):
        codigo, texto, _ = self.final("success", "true", "success", "skipped", "true")
        self.assertEqual(codigo, 0, texto)
        self.assertIn("::warning::PR en borrador: los E2E no han corrido.", texto)

    def test_borrador_exige_lo_barato(self):
        for versiones, hay, unitarios, e2e, espera in [
            ("success", "false", "skipped", "skipped", 0),     # sin package.json, sin aviso
            ("success", "true", "success", "success", 0),      # pasó a borrador con los E2E ya corridos
            ("success", "true", "failure", "skipped", 1),
            ("success", "true", "cancelled", "skipped", 1),
            ("success", "true", "skipped", "skipped", 1),
            ("success", "true", "success", "failure", 1),      # si corrieron, cuentan
            ("success", "true", "success", "cancelled", 1),
            ("failure", "", "skipped", "skipped", 1),
            ("success", "", "skipped", "skipped", 1),
        ]:
            with self.subTest(versiones=versiones, hay=hay, unitarios=unitarios, e2e=e2e):
                codigo, texto, _ = self.final(versiones, hay, unitarios, e2e, "true")
                self.assertEqual(codigo != 0, bool(espera), texto)
                self.assertNotIn("::warning::", texto)

    def test_sin_saber_si_hay_borrador_falla(self):
        for borrador in ("", "null", "verdadero"):
            with self.subTest(borrador=borrador):
                codigo, texto, _ = self.final("success", "true", "success", "skipped", borrador)
                self.assertNotEqual(codigo, 0, texto)
                self.assertIn("::error::No se sabe si el PR está en borrador", texto)
                codigo, texto, _ = self.final("success", "true", "success", "success", borrador)
                self.assertNotEqual(codigo, 0, texto)


if __name__ == "__main__":
    unittest.main()

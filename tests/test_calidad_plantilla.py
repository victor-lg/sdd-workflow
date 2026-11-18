"""calidad.yml de la plantilla (VIC-21): mutaciones con Stryker (PR 2), código que sobra con knip y
duplicación nueva con jscpd (PR 3). El workflow no corre en este repo, así que los tests ejecutan
con bash los scripts de sus pasos, como en la CI, sobre repos de prueba: la configuración sale de
`main`, el umbral tiene que ser mayor que 0 y un test debilitado hace fallar el job. Los de Stryker
necesitan node y npm (y red para `npm ci`). Los que ejecutan knip y jscpd de verdad corren en la CI
(`validar`); en local se saltan si no encuentran el binario."""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

import yaml

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CALIDAD = (RAIZ / "plantilla-proyecto" / ".github" / "workflows" / "calidad.yml").read_text(encoding="utf-8")
REGISTRO = (RAIZ / "docs" / "herramientas.md").read_text(encoding="utf-8")
FIXTURE = RAIZ / "tests" / "fixtures" / "stryker"
FIXTURE_KNIP = RAIZ / "tests" / "fixtures" / "knip"
FIXTURE_JSCPD = RAIZ / "tests" / "fixtures" / "jscpd"
PLANTILLA = RAIZ / "plantilla-proyecto"
EN_LA_CI = os.environ.get("GITHUB_ACTIONS") == "true"
PAQUETE = {"name": "p", "private": True, "devDependencies": {"@stryker-mutator/core": "10.1.1"}}
CONFIG = {"mutate": ["src/**/*.js"], "testRunner": "command", "thresholds": {"break": 80}}


def script(paso):
    """El `run: |` del paso con ese nombre, sin la sangría del YAML."""
    bloque = re.search(rf"- name: {re.escape(paso)}\n(?:        .*\n)*?        run: \|\n((?:          .*\n|\n)+)",
                       CALIDAD).group(1)
    return textwrap.dedent(bloque)


def ejecutar(paso, carpeta, temporal, base="refs/remotes/origin/main", **extra):
    salida = pathlib.Path(temporal) / "salida"
    salida.write_text("")
    entorno = dict(os.environ, BASE=base, RUNNER_TEMP=str(temporal), GITHUB_OUTPUT=str(salida),
                   GIT_NO_REPLACE_OBJECTS="1", npm_config_cache=str(pathlib.Path(temporal) / "npm"))
    entorno.update(extra)
    r = subprocess.run(["bash", "-e", "-c", script(paso)], cwd=carpeta, env=entorno,
                       capture_output=True, text=True, timeout=600)
    return r.returncode, r.stdout + r.stderr, salida.read_text()


def git(carpeta, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                   cwd=carpeta, check=True, capture_output=True)


class TextoDeCalidad(unittest.TestCase):
    def test_solo_pull_request(self):
        bloque = re.search(r"^on:\n((?:[ #].*\n|\n)*)", CALIDAD, re.M).group(1)
        self.assertEqual(set(re.findall(r"^  ([a-z_]+):", bloque, re.M)), {"pull_request"})
        codigo = re.sub(r"^\s*#.*\n", "", CALIDAD, flags=re.M)
        self.assertNotIn("pull_request_target", codigo)
        self.assertNotIn("secrets.", codigo)
        self.assertNotIn("workflow_dispatch", codigo)

    def test_tres_jobs_con_tiempo_maximo(self):
        jobs = CALIDAD.split("\njobs:\n", 1)[1]
        nombres = re.findall(r"^  ([a-z0-9-]+):", jobs, re.M)
        self.assertEqual(nombres, ["mutaciones", "codigo-sobrante", "duplicados"])
        for nombre, bloque in zip(nombres, re.split(r"^  [a-z0-9-]+:\n", jobs, flags=re.M)[1:]):
            with self.subTest(job=nombre):
                self.assertRegex(bloque, r"\n    timeout-minutes: \d+\n")

    def test_stryker_de_node_modules_con_la_configuracion_de_main(self):
        """Nada de npx: descargaría una versión que no fija el lockfile."""
        self.assertNotIn("npx", CALIDAD)
        self.assertIn("npm ci --ignore-scripts", CALIDAD)
        self.assertIn('node_modules/.bin/stryker run "$RUNNER_TEMP/stryker.config.json" --force', CALIDAD)
        self.assertIn('git show "$BASE:stryker.config.json" > "$RUNNER_TEMP/stryker.config.json"', CALIDAD)

    def test_node_sin_cache(self):
        self.assertEqual(CALIDAD.count("package-manager-cache: false"), CALIDAD.count("actions/setup-node@"))
        self.assertNotIn("cache: npm", CALIDAD)

    def test_acciones_del_registro(self):
        """La de checkout es la de los otros workflows; la de Node es nueva en este PR."""
        for sha in re.findall(r"uses: (?!actions/checkout@)\S+@([0-9a-f]{40})", CALIDAD):
            with self.subTest(sha=sha):
                self.assertIn(sha, REGISTRO)



class Borrador(unittest.TestCase):
    """VIC-33: en borrador, `mutaciones` valida la configuración y avisa, pero no lanza Stryker. El job no se
    salta nunca (un check requerido saltado cuenta como superado) y el borrador sale de la API."""
    WORKFLOW = yaml.safe_load(CALIDAD)
    JOBS = WORKFLOW["jobs"]
    PASOS = JOBS["mutaciones"]["steps"]

    def paso(self, nombre):
        return next(p for p in self.PASOS if p.get("name") == nombre)

    def test_corre_al_marcar_el_pr_listo(self):
        self.assertEqual(self.WORKFLOW[True]["pull_request"]["types"], ["opened", "synchronize", "reopened", "ready_for_review"])

    def test_ningun_job_se_salta(self):
        for nombre, job in self.JOBS.items():
            with self.subTest(job=nombre):
                self.assertNotIn("if", list(job))

    def test_solo_mutaciones_lee_los_pr(self):
        self.assertEqual(self.JOBS["mutaciones"]["permissions"], {"contents": "read", "pull-requests": "read"})
        for nombre in ("codigo-sobrante", "duplicados"):
            with self.subTest(job=nombre):
                self.assertNotIn("permissions", self.JOBS[nombre])

    def test_la_consulta_es_la_del_ejemplo(self):
        """La misma que la del job `tests` del ejemplo, cuyos tests la ejecutan con un `gh` falso
        (tests/test_ejemplo_tests_playwright.py, clase Borrador)."""
        ejemplo = yaml.safe_load((RAIZ / "docs" / "ejemplos" / "workflows" / "tests-node-playwright.yml").read_text(encoding="utf-8"))
        consulta = self.PASOS[0]
        self.assertEqual(consulta["name"], "¿Está el PR en borrador?")
        self.assertEqual(consulta["id"], "borrador")
        self.assertNotIn("if", consulta)
        self.assertEqual(consulta, next(p for p in ejemplo["jobs"]["tests"]["steps"] if p.get("id") == "borrador"))

    def test_stryker_solo_fuera_del_borrador(self):
        fuera = "steps.preparar.outputs.stryker == 'si' && steps.borrador.outputs.borrador == 'false'"
        nodo = next(p for p in self.PASOS if p.get("uses", "").startswith("actions/setup-node@"))
        self.assertEqual(nodo["if"], fuera)
        self.assertEqual(self.paso("Stryker")["if"], fuera)
        # La configuración se valida también en borrador: es barato y avisa antes.
        self.assertNotIn("if", self.paso("Configuración de Stryker de main"))

    def test_en_borrador_lo_dice(self):
        aviso = self.paso("Aviso de borrador")
        self.assertEqual(aviso["if"], "steps.preparar.outputs.stryker == 'si' && steps.borrador.outputs.borrador == 'true'")
        r = subprocess.run(["bash", "-e", "-c", aviso["run"]], capture_output=True, text=True, timeout=10)
        self.assertEqual(r.returncode, 0)
        self.assertIn("::warning::PR en borrador: Stryker no ha corrido.", r.stdout)

class RepoDePrueba(unittest.TestCase):
    """Un repo con `main` y una rama, para ejecutar el paso PASO. CONFIG_PASO es el fichero de
    configuración que el paso copia de `main`."""
    PASO = CONFIG_PASO = None

    def setUp(self):
        self.temporal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temporal)
        self.repo = self.temporal / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")

    def escribir(self, nombre, contenido):
        (self.repo / nombre).parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contenido, bytes):
            (self.repo / nombre).write_bytes(contenido)
        else:
            (self.repo / nombre).write_text(contenido if isinstance(contenido, str) else json.dumps(contenido))
        git(self.repo, "add", nombre)

    def main(self, config=None):
        """Commit en `main` (con o sin la configuración) y su ref origin/main."""
        if config is not None:
            self.escribir(self.CONFIG_PASO, config)
        self.escribir("LEEME", "x")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")
        git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    def preparar(self, paso=None, **extra):
        """En la CI, HEAD es el merge con todo lo de la rama commiteado: aquí, un commit de la rama."""
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "rama")
        return ejecutar(paso or self.PASO, self.repo, self.temporal, **extra)

    def config_usada(self):
        return json.loads((self.temporal / self.CONFIG_PASO).read_text())


class Preparar(RepoDePrueba):
    """El paso "Configuración de Stryker de main", sobre un repo con `main` y una rama."""
    PASO = "Configuración de Stryker de main"
    CONFIG_PASO = "stryker.config.json"

    def test_sin_package_json_pasa_con_aviso(self):
        self.main()
        estado, texto, salida = self.preparar()
        self.assertEqual(estado, 0, texto)
        self.assertIn("::warning::Sin package.json", texto)
        self.assertEqual(salida, "stryker=no\n")

    def test_sin_package_json_en_la_rama_si_main_lo_tiene_falla(self):
        """G4, ronda 1: borrar o mover el package.json de main no puede dejar el check en verde."""
        self.escribir("package.json", PAQUETE)
        self.main(CONFIG)
        git(self.repo, "rm", "-q", "package.json")
        estado, texto, salida = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::main tiene package.json y la rama no", texto)
        self.assertNotIn("stryker=", salida)

    def test_sin_stryker_en_dev_dependencies_falla(self):
        self.main(CONFIG)
        for paquete in ({"name": "p"}, {"devDependencies": None},
                        {"dependencies": {"@stryker-mutator/core": "10.1.1"}}):
            with self.subTest(paquete=paquete):
                self.escribir("package.json", paquete)
                estado, texto, salida = self.preparar()
                self.assertEqual(estado, 1, texto)
                self.assertIn("::error::package.json no tiene @stryker-mutator/core", texto)
                self.assertNotIn("stryker=si", salida)

    def test_usa_la_configuracion_de_main_y_no_la_de_la_rama(self):
        self.main(CONFIG)
        self.escribir("package.json", PAQUETE)
        self.escribir("stryker.config.json", {"mutate": ["nada.js"], "thresholds": {"break": 1}})
        estado, texto, salida = self.preparar()
        self.assertEqual(estado, 0, texto)
        self.assertEqual(salida, "stryker=si\n")
        self.assertEqual(self.config_usada(), CONFIG)

    def test_sin_configuracion_en_main_usa_la_de_la_rama_con_aviso(self):
        self.main()
        self.escribir("package.json", PAQUETE)
        self.escribir("stryker.config.json", CONFIG)
        estado, texto, salida = self.preparar()
        self.assertEqual(estado, 0, texto)
        self.assertIn("::warning::main no tiene stryker.config.json", texto)
        self.assertEqual(self.config_usada(), CONFIG)

    def test_sin_configuracion_en_ninguna_falla(self):
        """Otro nombre en la rama (.mjs) no cuenta: la CI solo pasa stryker.config.json."""
        self.main()
        self.escribir("package.json", PAQUETE)
        self.escribir("stryker.config.mjs", "export default {thresholds: {break: 80}}")
        estado, texto, salida = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::Falta stryker.config.json", texto)

    def test_otra_configuracion_en_main_falla(self):
        """G4, ronda 3: si main usa .mjs (o .js…), la CI no la lee, y un .json de la rama no puede ocupar su sitio."""
        for nombre in ("stryker.config.mjs", ".stryker.conf.js", "stryker.conf.cjs"):
            with self.subTest(nombre=nombre):
                self.setUp()
                self.escribir(nombre, "export default {thresholds: {break: 80}}")
                self.main()
                self.escribir("package.json", PAQUETE)
                self.escribir("stryker.config.json", {"thresholds": {"break": 1}})
                estado, texto, salida = self.preparar()
                self.assertEqual(estado, 1, texto)
                self.assertIn("::error::main tiene una configuración de Stryker que no es stryker.config.json", texto)
                self.assertNotIn("stryker=si", salida)

    def test_umbral_mayor_que_cero(self):
        """Sin `break`, o con 0, Stryker nunca falla (Víctor, 2026-11-15)."""
        for umbral in ("falta", None, 0, 0.0, -5, "80", True, [80]):
            with self.subTest(umbral=umbral):
                umbrales = {} if umbral == "falta" else {"break": umbral}
                self.setUp()
                self.main({"thresholds": umbrales})
                self.escribir("package.json", PAQUETE)
                estado, texto, salida = self.preparar()
                self.assertEqual(estado, 1, texto)
                self.assertIn("thresholds.break mayor que 0", texto)
                self.assertNotIn("stryker=si", salida)
        for umbral in (1, 0.5, 80, 100):
            with self.subTest(umbral=umbral):
                self.setUp()
                self.main({"thresholds": {"break": umbral}})
                self.escribir("package.json", PAQUETE)
                self.assertEqual(self.preparar()[0], 0)

    def test_sin_thresholds_falla(self):
        self.main({"mutate": ["src/**/*.js"]})
        self.escribir("package.json", PAQUETE)
        self.assertEqual(self.preparar()[0], 1)

    def test_sin_la_rama_base_falla(self):
        self.escribir("package.json", PAQUETE)
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::Git no encuentra refs/remotes/origin/main", texto)


@unittest.skipUnless(shutil.which("node") and shutil.which("npm"), "sin node o npm en el PATH")
class StrykerEnLaCi(unittest.TestCase):
    """Hecho cuando (VIC-21): un cambio que rompe el código hace fallar una mutación. El paso
    "Stryker" sobre tests/fixtures/stryker, con la configuración fuera del proyecto, como en la CI."""
    PASO = "Stryker"

    def setUp(self):
        self.temporal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temporal)
        self.proyecto = self.temporal / "proyecto"
        shutil.copytree(FIXTURE, self.proyecto)
        (self.proyecto / "stryker.config.json").rename(self.temporal / "stryker.config.json")

    def stryker(self):
        return ejecutar(self.PASO, self.proyecto, self.temporal)

    def test_los_tests_del_ac_matan_los_mutantes(self):
        estado, texto, _ = self.stryker()
        self.assertEqual(estado, 0, texto)
        self.assertIn("Final mutation score of 100.00 is greater than or equal to break threshold 80", texto)

    def test_un_test_debilitado_hace_fallar_el_job(self):
        (self.proyecto / "test" / "unidades.test.js").write_text(
            'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
            'import { tbAGb } from "../src/unidades.js";\n\n'
            'test("devuelve un número", () => assert.equal(typeof tbAGb(1), "number"));\n')
        estado, texto, _ = self.stryker()
        self.assertEqual(estado, 1, texto)
        self.assertIn("under breaking threshold 80", texto)
        self.assertRegex(texto, r"unidades\.js \|\s+[\d.]+ \|\s+[\d.]+ \|\s+\d+ \|\s+\d+ \|\s+[1-9]")

    def test_sin_mutantes_falla(self):
        """Con cero mutantes la puntuación es NaN y Stryker sale con 0: el job no."""
        config = json.loads((self.temporal / "stryker.config.json").read_text())
        config["mutate"] = ["no-existe/**/*.js"]
        (self.temporal / "stryker.config.json").write_text(json.dumps(config))
        estado, texto, _ = self.stryker()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::Stryker no ha probado ningún mutante", texto)

    def debilitar_y_tapar(self, codigo):
        """El test debilitado de arriba (sobreviven 4 de 7) y `src/unidades.js` con comentarios de Stryker."""
        (self.proyecto / "test" / "unidades.test.js").write_text(
            'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
            'import { tbAGb } from "../src/unidades.js";\n\n'
            'test("devuelve un número", () => assert.equal(typeof tbAGb(1), "number"));\n')
        (self.proyecto / "src" / "unidades.js").write_bytes(codigo.encode("utf-8", "surrogateescape"))
        return self.stryker()

    def test_un_comentario_stryker_disable_hace_fallar_el_job(self):
        """G4, rondas 1 a 3: sin este control, con el test debilitado y los mutantes tapados por
        comentarios, Stryker 10.1.1 da 100,00 y sale con 0 (medido). Cada forma esconde el comentario
        a un `grep` del diff: `++` al principio, un NUL antes, un byte UTF-8 inválido en el motivo."""
        formas = {
            "next-line": "// Stryker disable next-line all\n  if (tb < 0) throw new RangeError();\n"
                         "  // Stryker disable next-line all\n  return tb * 1024;\n",
            "++ delante": "  if (tb < 0) throw new RangeError();\n  return tb * 1024;\n",
            "byte inválido": "  // Stryker disable all: \udcff\n  if (tb < 0) throw new RangeError();\n  return tb * 1024;\n",
        }
        for forma, cuerpo in formas.items():
            with self.subTest(forma=forma):
                self.setUp()
                if forma == "++ delante":
                    codigo = "let n = 0;\n++n; // Stryker disable all\nexport function tbAGb(tb) {\n" + cuerpo + "}\n"
                else:
                    codigo = "export function tbAGb(tb) {\n" + cuerpo + "}\n"
                estado, texto, _ = self.debilitar_y_tapar(codigo)
                self.assertEqual(estado, 1, texto)
                self.assertIn("::error::Hay mutantes Ignored", texto)
                self.assertRegex(texto, r"::error file=src/unidades\.js,line=\d+::Mutante ignorado")

    def test_con_los_tests_buenos_un_ignorado_tambien_falla(self):
        """Aunque la puntuación pase el umbral: lo que no se deba mutar sale de `mutate`, en main."""
        (self.proyecto / "src" / "unidades.js").write_text(
            "export function tbAGb(tb) {\n  if (tb < 0) throw new RangeError();\n"
            "  // Stryker disable next-line all: motivo\n  return tb * 1024;\n}\n")
        estado, texto, _ = self.stryker()
        self.assertEqual(estado, 1, texto)
        self.assertIn("greater than or equal to break threshold 80", texto)
        self.assertIn("Mutante ignorado (motivo)", texto)

    def test_un_informe_json_de_la_rama_no_cuenta(self):
        """El informe se borra antes de ejecutar: uno commiteado en la rama no sustituye al de Stryker."""
        informe = self.proyecto / "reports" / "mutation" / "mutation.json"
        informe.parent.mkdir(parents=True)
        informe.write_text('{"files": {}}')
        self.assertEqual(self.stryker()[0], 0)
        self.assertIn("unidades.js", informe.read_text())

    def test_sin_informe_falla(self):
        """Con `dryRunOnly`, Stryker sale con 0 sin mutar nada ni dejar informe (medido). Tampoco vale
        un informe que traiga la rama: se borra antes."""
        config = json.loads((self.temporal / "stryker.config.json").read_text())
        config["dryRunOnly"] = True
        (self.temporal / "stryker.config.json").write_text(json.dumps(config))
        for con_informe_de_la_rama in (False, True):
            with self.subTest(con_informe_de_la_rama=con_informe_de_la_rama):
                if con_informe_de_la_rama:
                    informe = self.proyecto / "reports" / "mutation" / "mutation.json"
                    informe.parent.mkdir(parents=True, exist_ok=True)
                    informe.write_text('{"files": {}}')
                estado, texto, _ = self.stryker()
                self.assertEqual(estado, 1, texto)
                self.assertIn("::error::Stryker no ha dejado el informe JSON", texto)

    def test_un_fichero_incremental_de_la_rama_no_cuenta(self):
        """--force: sin él, Stryker reutiliza un informe incremental que la rama marque como "Killed"
        (medido: 7 de 7 reutilizados y 100,00 con el test debilitado)."""
        config = json.loads((self.temporal / "stryker.config.json").read_text())
        config["incremental"] = True
        (self.temporal / "stryker.config.json").write_text(json.dumps(config))
        self.test_un_test_debilitado_hace_fallar_el_job()
        incremental = self.proyecto / "reports" / "stryker-incremental.json"
        informe = json.loads(incremental.read_text())
        for fichero in informe["files"].values():
            for mutante in fichero["mutants"]:
                mutante["status"] = "Killed"
        incremental.write_text(json.dumps(informe))
        estado, texto, _ = self.stryker()
        self.assertEqual(estado, 1, texto)
        self.assertIn("Force mode is activated", texto)


class BaseSinAmbiguedad(unittest.TestCase):
    """G4, ronda 1: con `origin/main`, Git resuelve antes una etiqueta llamada así (medido: avisa de
    la ambigüedad y devuelve la etiqueta). La ref completa no depende de eso."""

    def test_la_base_es_la_ref_completa(self):
        self.assertIn("  BASE: refs/remotes/origin/${{ github.base_ref }}\n", CALIDAD)



PAQUETE_KNIP = {"name": "p", "private": True, "devDependencies": {"knip": "6.45.1"}}
CONFIG_KNIP = {"entry": ["src/index.js"], "project": ["src/**/*.js"], "rules": {"exports": "error"}}
JSCPD_URL = re.search(r"\n      JSCPD_URL: (\S+)\n", CALIDAD).group(1)
JSCPD_SHA256 = re.search(r"\n      JSCPD_SHA256: ([0-9a-f]{64})\n", CALIDAD).group(1)
# Los tipos de hallazgo de knip 6.45.1 (ISSUE_TYPES, en dist/constants.js).
TIPOS_KNIP = {"files", "subpaths", "dependencies", "devDependencies", "optionalPeerDependencies", "unlisted",
              "binaries", "unresolved", "exports", "nsExports", "types", "nsTypes", "enumMembers",
              "namespaceMembers", "duplicates", "catalog", "catalogReferences", "cycles"}


def medida(texto):
    """Tiempos y hallazgos de knip y jscpd en la CI de este repo (VIC-21, PR 3): salen en el log de `validar`
    y, en la CI, como anotación del check, que se lee con la API sin descargar el log."""
    print(f"\nMEDIDA {texto}", file=sys.stderr)
    if EN_LA_CI:
        print(f"::notice title=MEDIDA::{texto}", flush=True)


def sonda(nombre, estado, texto, esperado=1):
    """Qué hace la herramienta en un caso que puede esconderle código (G4 del PR 3), si no es lo
    esperado: en la CI, como anotación, porque el log de `validar` no se puede descargar desde el
    sandbox. Solo si falla, porque GitHub guarda 10 avisos por paso."""
    if EN_LA_CI and estado != esperado:
        resumen = texto[-600:].replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::notice title=SONDA {nombre}::salida {estado}%0A{resumen}", flush=True)


class SinOrdenesDeLaHerramienta(unittest.TestCase):
    """Víctor, 2026-11-16 (G4 del PR 3): la salida de Stryker, knip y jscpd lleva nombres de fichero
    de la rama, que podrían inyectar anotaciones; cada paso la encierra en ::stop-commands::."""
    PASOS = ("Stryker", "knip", "jscpd", "Informe de salud de jscpd")

    def test_cada_herramienta_entre_stop_commands_y_su_token(self):
        for paso in self.PASOS:
            with self.subTest(paso=paso):
                lineas = script(paso).splitlines()
                self.assertIn("token=$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \\n')", lineas)
                parar = lineas.index('echo "::stop-commands::$token"')
                seguir = lineas.index('echo "::$token::"')
                herramienta = next(i for i, l in enumerate(lineas)
                                   if re.match(r'(node_modules/\.bin/(stryker|knip) |"\$RUNNER_TEMP/jscpd/jscpd" )', l))
                self.assertLess(parar, herramienta)
                self.assertLess(herramienta, seguir)
                self.assertFalse([l for l in lineas[parar + 1:seguir] if "::" in l and "$token" not in l])

    def falsa(self, temporal, estado):
        (temporal / "jscpd").mkdir()
        falso = temporal / "jscpd" / "jscpd"
        falso.write_text(f"#!/bin/sh\nprintf 'src/a.js\\n::error::inyectada\\n::stop-commands::otro\\n'\nexit {estado}\n")
        falso.chmod(0o755)

    def ejecutar_falsa(self, paso, estado):
        temporal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporal)
        self.falsa(temporal, estado)
        _, texto, _ = r = ejecutar(paso, temporal, temporal)
        lineas = texto.splitlines()
        parar = [l for l in lineas if l.startswith("::stop-commands::")]
        self.assertEqual(len(parar), 2, texto)  # el del paso y el que intenta la herramienta
        token = parar[0].removeprefix("::stop-commands::")
        self.assertRegex(token, r"^[0-9a-f]{32}$")
        self.assertLess(lineas.index(parar[0]), lineas.index("::error::inyectada"))
        self.assertLess(lineas.index("::error::inyectada"), lineas.index(f"::{token}::"))
        return r, lineas, token

    def test_jscpd_sale_con_lo_que_sale_la_herramienta(self):
        for estado in (0, 1, 2):
            with self.subTest(estado=estado):
                (salida, _, _), _, _ = self.ejecutar_falsa("jscpd", estado)
                self.assertEqual(salida, estado)

    def test_el_aviso_del_informe_de_salud_va_despues_del_token(self):
        (salida, texto, _), lineas, token = self.ejecutar_falsa("Informe de salud de jscpd", 2)
        self.assertEqual(salida, 0, texto)
        aviso = "::warning::El informe de salud de jscpd ha salido con error; no bloquea."
        self.assertLess(lineas.index(f"::{token}::"), lineas.index(aviso))


class TextoDeKnipYJscpd(unittest.TestCase):
    def codigo(self):
        return re.sub(r"^\s*#.*\n", "", CALIDAD, flags=re.M)

    def test_knip_de_node_modules_con_la_configuracion_de_main(self):
        self.assertIn('node_modules/.bin/knip --config "$RUNNER_TEMP/knip.json" --no-gitignore\n', CALIDAD)
        self.assertIn('git show "$BASE:knip.json" > "$RUNNER_TEMP/knip.json"', CALIDAD)
        self.assertNotIn("--fix", self.codigo())

    def test_jscpd_solo_con_la_duplicacion_nueva_y_sin_semantic(self):
        codigo = " ".join(self.codigo().replace("\\\n", " ").split())
        self.assertIn('"$RUNNER_TEMP/jscpd/jscpd" . --config "$RUNNER_TEMP/.jscpd.json" --no-gitignore '
                      '--baseline-from-ref "$BASE" --fail-on-new-clones', codigo)
        self.assertIn('git show "$BASE:.jscpd.json" > "$RUNNER_TEMP/.jscpd.json"', codigo)
        self.assertNotIn("--semantic", codigo)
        self.assertNotIn("npx", codigo)
        # Sin --max-size, jscpd salta sin avisar los ficheros de más de 1 MB (medido en el PR 3).
        self.assertEqual(codigo.count("--max-size 200mb"), 2)
        # Sin --cross-formats, una copia de un .js en un .ts no cuenta como clon (medido en el PR 3).
        self.assertEqual(codigo.count("--cross-formats js-ts"), 2)

    def test_jscpd_de_la_release_con_la_suma_del_registro(self):
        self.assertEqual(JSCPD_URL, "https://github.com/kucherenko/jscpd/releases/download/v5.4.3/"
                                    "jscpd-linux-x64-gnu.tar.gz")
        self.assertIn(JSCPD_SHA256, REGISTRO)
        self.assertIn('sha256sum --check --strict', CALIDAD)

    def test_knip_del_lockfile_con_la_version_y_la_integrity_del_registro(self):
        version = json.loads((FIXTURE_KNIP / "package.json").read_text())["devDependencies"]["knip"]
        knip = json.loads((FIXTURE_KNIP / "package-lock.json").read_text())["packages"]["node_modules/knip"]
        self.assertEqual(knip["version"], version)
        self.assertIn(f"`knip` {version}", REGISTRO)
        self.assertIn(knip["integrity"], REGISTRO)

    def test_la_plantilla_arranca_knip_en_warn(self):
        """Víctor, 2026-11-15: pasar a "error" es un cambio de la configuración de main (R2)."""
        config = json.loads((PLANTILLA / "knip.json").read_text(encoding="utf-8"))
        self.assertEqual(config["rules"], {tipo: "warn" for tipo in TIPOS_KNIP})


class PrepararKnip(RepoDePrueba):
    PASO = "Configuración de knip de main"
    CONFIG_PASO = "knip.json"

    def test_sin_package_json_pasa_con_aviso(self):
        self.main(CONFIG_KNIP)
        estado, texto, salida = self.preparar()
        self.assertEqual(estado, 0, texto)
        self.assertIn("::warning::Sin package.json", texto)
        self.assertEqual(salida, "knip=no\n")

    def test_sin_package_json_en_la_rama_si_main_lo_tiene_falla(self):
        self.escribir("package.json", PAQUETE_KNIP)
        self.main(CONFIG_KNIP)
        git(self.repo, "rm", "-q", "package.json")
        estado, texto, salida = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::main tiene package.json y la rama no", texto)
        self.assertNotIn("knip=", salida)

    def test_sin_knip_en_dev_dependencies_falla(self):
        self.main(CONFIG_KNIP)
        for paquete in ({"name": "p"}, {"devDependencies": None}, {"dependencies": {"knip": "6.45.1"}}):
            with self.subTest(paquete=paquete):
                self.escribir("package.json", paquete)
                estado, texto, salida = self.preparar()
                self.assertEqual(estado, 1, texto)
                self.assertIn("::error::package.json no tiene knip en devDependencies", texto)
                self.assertNotIn("knip=si", salida)

    def test_la_clave_knip_de_package_json_falla(self):
        """knip la mezcla con el fichero de --config: sus `ignore` saldrían de la rama."""
        self.main(CONFIG_KNIP)
        self.escribir("package.json", dict(PAQUETE_KNIP, knip={"ignore": ["src/**"]}))
        estado, texto, salida = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::package.json tiene la clave knip", texto)
        self.assertNotIn("knip=si", salida)

    def test_usa_la_configuracion_de_main_y_no_la_de_la_rama(self):
        self.main(CONFIG_KNIP)
        self.escribir("package.json", PAQUETE_KNIP)
        self.escribir("knip.json", {"rules": {"exports": "off"}})
        estado, texto, salida = self.preparar()
        self.assertEqual(estado, 0, texto)
        self.assertEqual(salida, "knip=si\n")
        self.assertEqual(self.config_usada(), CONFIG_KNIP)

    def test_sin_configuracion_en_main_usa_la_de_la_rama_con_aviso(self):
        self.main()
        self.escribir("package.json", PAQUETE_KNIP)
        self.escribir("knip.json", CONFIG_KNIP)
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 0, texto)
        self.assertIn("::warning::main no tiene knip.json", texto)
        self.assertEqual(self.config_usada(), CONFIG_KNIP)

    def test_sin_configuracion_en_ninguna_falla(self):
        self.main()
        self.escribir("package.json", PAQUETE_KNIP)
        self.escribir("knip.ts", "export default {}")
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::Falta knip.json", texto)

    def test_otra_configuracion_en_main_falla(self):
        for nombre in ("knip.jsonc", ".knip.json", ".knip.jsonc", "knip.ts", "knip.js", "knip.config.ts",
                       "knip.config.js"):
            with self.subTest(nombre=nombre):
                self.setUp()
                self.escribir(nombre, "{}")
                self.main()
                self.escribir("package.json", PAQUETE_KNIP)
                self.escribir("knip.json", {"rules": {"exports": "off"}})
                estado, texto, salida = self.preparar()
                self.assertEqual(estado, 1, texto)
                self.assertIn("::error::main tiene una configuración de knip que no es knip.json", texto)
                self.assertNotIn("knip=si", salida)

    def test_la_configuracion_tiene_que_ser_un_objeto(self):
        self.main([])
        self.escribir("package.json", PAQUETE_KNIP)
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::knip.json tiene que ser un objeto JSON", texto)

    def test_sin_la_rama_base_falla(self):
        self.escribir("package.json", PAQUETE_KNIP)
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::Git no encuentra refs/remotes/origin/main", texto)


class PrepararJscpd(RepoDePrueba):
    PASO = "Configuración de jscpd de main"
    CONFIG_PASO = ".jscpd.json"
    CONFIG = {"ignore": ["**/docs/**"]}

    def test_usa_la_configuracion_de_main_y_no_la_de_la_rama(self):
        self.main(self.CONFIG)
        self.escribir(".jscpd.json", {"ignore": ["**"]})
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 0, texto)
        self.assertEqual(self.config_usada(), self.CONFIG)

    def test_la_de_la_plantilla_vale(self):
        self.main(json.loads((PLANTILLA / ".jscpd.json").read_text(encoding="utf-8")))
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 0, texto)

    def test_sin_configuracion_en_main_usa_la_de_la_rama_con_aviso(self):
        self.main()
        self.escribir(".jscpd.json", self.CONFIG)
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 0, texto)
        self.assertIn("::warning::main no tiene .jscpd.json", texto)
        self.assertEqual(self.config_usada(), self.CONFIG)

    def test_sin_configuracion_en_ninguna_falla(self):
        self.main()
        self.escribir(".config/jscpd.json", self.CONFIG)
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::Falta .jscpd.json", texto)

    def test_otra_configuracion_en_main_falla(self):
        for nombre in (".config/jscpd.json", ".config/.jscpd.json"):
            with self.subTest(nombre=nombre):
                self.setUp()
                self.escribir(nombre, self.CONFIG)
                self.main()
                self.escribir(".jscpd.json", {"ignore": ["**"]})
                estado, texto, _ = self.preparar()
                self.assertEqual(estado, 1, texto)
                self.assertIn("::error::main tiene una configuración de jscpd que no es .jscpd.json", texto)

    def test_claves_que_fija_la_ci_fallan(self):
        """--semantic enviaría el código fuera; la base y el umbral de clones nuevos los pone la CI."""
        for clave, valor in (("semantic", True), ("semanticUrl", "http://x"), ("SemanticProvider", "http"),
                             ("baseline", "b.json"), ("baselineFromRef", "HEAD"), ("failOnNewClones", 9),
                             ("maxLines", 10), ("maxSize", "1kb"), ("ignoreAnnotations", True), ("exitCode", 0),
                             ("path", ["docs"]), ("pattern", "*.md"), ("changedOnly", True), ("skipLocal", True),
                             ("min_tokens", 50), ("Ignore", ["**"])):
            with self.subTest(clave=clave):
                self.setUp()
                self.main(dict(self.CONFIG, **{clave: valor}))
                estado, texto, _ = self.preparar()
                self.assertEqual(estado, 1, texto)
                self.assertIn(f"::error::.jscpd.json no puede llevar {clave}", texto)

    def test_las_claves_admitidas_pasan(self):
        self.main(dict(self.CONFIG, **{"$schema": "x", "format": ["javascript"], "minTokens": 50, "minLines": 5}))
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 0, texto)

    def test_la_configuracion_tiene_que_ser_un_objeto(self):
        self.main(["**"])
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::.jscpd.json tiene que ser un objeto JSON", texto)

    def test_la_clave_jscpd_de_package_json_falla(self):
        self.main(self.CONFIG)
        self.escribir("package.json", {"name": "p", "jscpd": {"ignore": ["src/**"]}})
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::package.json tiene la clave jscpd", texto)
        self.escribir("package.json", {"name": "p"})
        self.assertEqual(self.preparar()[0], 0)

    def test_un_comentario_que_excluye_una_region_falla(self):
        """Víctor, 2026-11-15: con uno solo. Es un control sobre texto: se busca en el árbol de la
        rama con git grep --text, sin distinguir mayúsculas, aunque .gitattributes marque el fichero
        como binario o tenga un NUL delante."""
        formas = {
            "src/a.js": b"// jscpd:ignore-start\nconst a = 1;\n// jscpd:ignore-end\n",
            "src/b.py": b"x = 1\n# JSCPD:IGNORE-START\n",
            "src/c.js": b"\0\n/* Jscpd:Ignore-End */\n",
            "src/d.bin": b"// jscpd:ignore-start\n",
            "src/e.js": b"// jscpd:ignore\n",
            "src/f.js": b"/* jscpd:ignore-file */\n",
        }
        for nombre, contenido in formas.items():
            with self.subTest(nombre=nombre):
                self.setUp()
                self.main(self.CONFIG)
                self.escribir(".gitattributes", "*.bin binary\n*.js -diff -text\n")
                self.escribir(nombre, contenido)
                estado, texto, _ = self.preparar()
                self.assertEqual(estado, 1, texto)
                self.assertIn(f"::error file={nombre}::Comentario de jscpd que excluye una región", texto)
                self.assertIn("::error::Hay comentarios que esconden código a jscpd", texto)

    def test_un_fichero_ignore_falla(self):
        for nombre in (".ignore", "src/.ignore"):
            with self.subTest(nombre=nombre):
                self.setUp()
                self.main(self.CONFIG)
                self.escribir(nombre, "src/a.js\n")
                estado, texto, _ = self.preparar()
                self.assertEqual(estado, 1, texto)
                self.assertIn(f"::error file={nombre}::jscpd no analiza lo que lista un .ignore", texto)
                self.assertIn("::error::Hay ficheros .ignore", texto)

    def test_otros_ficheros_parecidos_a_ignore_pasan(self):
        self.main(self.CONFIG)
        for nombre in ("a.ignore", ".ignorar", ".rgignore", "src/.gitignore"):
            self.escribir(nombre, "x\n")
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 0, texto)

    def test_la_plantilla_entera_pasa(self):
        """El propio calidad.yml, AGENTS.md y el resto de la plantilla van en el árbol del proyecto."""
        shutil.copytree(PLANTILLA, self.repo, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git"))
        self.main()
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 0, texto)

    def test_codigo_que_no_es_utf8_falla(self):
        """jscpd salta sin avisar un fichero que no es UTF-8 (medido en el PR 3). El NUL y el nombre que
        no es UTF-8 no se han medido: la CI falla igual, por si acaso (G4, ronda 3)."""
        casos = {
            "src/a.js": b"// \xff\nconst a = 1;\n",
            "src/b.PY": b"# \xff\na = 1\n",
            "src/c.tsx": b"// \xff\nconst a = 1;\n",
            "lib/d.ex": "# año\n".encode("latin-1"),
            "src/e.js": b"// \0\nconst a = 1;\n",
            os.fsdecode(b"src/f\xffg.js"): b"const a = 1;\n",
            os.fsdecode(b"datos/h\xff.txt"): b"x\n",
        }
        for nombre, contenido in casos.items():
            with self.subTest(nombre=nombre):
                self.setUp()
                self.main(self.CONFIG)
                self.escribir(nombre, contenido)
                estado, texto, _ = self.preparar()
                self.assertEqual(estado, 1, texto)
                visible = nombre.encode("utf-8", "surrogateescape").decode("utf-8", "replace")
                self.assertIn(f"::error file={visible}::El nombre o el contenido no es UTF-8, o lleva NUL", texto)
                self.assertIn("::error::Hay código que no es UTF-8 o lleva NUL", texto)

    def test_otros_ficheros_que_no_son_utf8_pasan(self):
        self.main(self.CONFIG)
        self.escribir("docs/manual.pdf", b"%PDF-1.4\n\xff\xfe\n")
        self.escribir("datos.csv", "año;número\n".encode("latin-1"))
        self.escribir("src/a.js", "// ñandú, en UTF-8\n".encode())
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 0, texto)

    def test_sin_comentarios_pasa(self):
        self.main(self.CONFIG)
        self.escribir("src/a.js", "// jscpd ignora esto solo si lo dice la configuración\n")
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 0, texto)

    def test_sin_la_rama_base_falla(self):
        estado, texto, _ = self.preparar()
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::Git no encuentra refs/remotes/origin/main", texto)


@unittest.skipUnless(shutil.which("node") and shutil.which("npm") and (EN_LA_CI or shutil.which("knip")),
                     "knip solo corre en la CI (validar) o con knip en el PATH")
class KnipEnLaCi(unittest.TestCase):
    """El paso "knip" sobre tests/fixtures/knip, con la configuración fuera del proyecto, como en la CI."""
    PASO = "knip"

    @classmethod
    def setUpClass(cls):
        cls.cache = pathlib.Path(tempfile.mkdtemp())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.cache)

    def setUp(self):
        self.temporal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temporal)
        self.proyecto = self.temporal / "proyecto"
        shutil.copytree(FIXTURE_KNIP, self.proyecto)
        self.config = json.loads((self.proyecto / "knip.json").read_text())
        (self.proyecto / "knip.json").unlink()

    def knip(self, reglas, config=None):
        (self.temporal / "knip.json").write_text(json.dumps(dict(config or self.config, rules=reglas)))
        inicio = time.monotonic()
        estado, texto, salida = ejecutar(self.PASO, self.proyecto, self.temporal, npm_config_cache=str(self.cache))
        return estado, texto, time.monotonic() - inicio

    def sobra(self):
        (self.proyecto / "src" / "suma.js").write_text(
            "export function suma(a, b) {\n  return a + b;\n}\n\nexport function resta(a, b) {\n  return a - b;\n}\n")
        (self.proyecto / "src" / "sobra.js").write_text("export const nada = 0;\n")

    def test_sin_codigo_que_sobre_pasa(self):
        estado, texto, segundos = self.knip({"files": "error", "exports": "error"})
        self.assertEqual(estado, 0, texto)
        medida(f"knip, proyecto de prueba limpio: {segundos:.1f} s con npm ci")

    def test_con_las_reglas_en_error_falla(self):
        self.sobra()
        estado, texto, segundos = self.knip({"files": "error", "exports": "error"})
        self.assertEqual(estado, 1, texto)
        self.assertIn("src/sobra.js", texto)
        self.assertIn("resta", texto)
        medida(f"knip, una exportación y un fichero que sobran: salida {estado}, {segundos:.1f} s")

    def test_con_las_reglas_en_warn_avisa_y_pasa(self):
        self.sobra()
        estado, texto, _ = self.knip({"files": "warn", "exports": "warn"})
        self.assertEqual(estado, 0, texto)
        self.assertIn("src/sobra.js", texto)
        self.assertIn("resta", texto)

    def test_la_configuracion_de_la_plantilla_avisa_y_pasa(self):
        self.sobra()
        reglas = json.loads((PLANTILLA / "knip.json").read_text(encoding="utf-8"))["rules"]
        estado, texto, segundos = self.knip(reglas)
        self.assertEqual(estado, 0, texto)
        self.assertIn("resta", texto)
        self.assertNotIn("Ignored unknown issue type", texto)
        medida(f"knip, con el knip.json de la plantilla: salida {estado}, {segundos:.1f} s")

    def test_la_configuracion_de_la_rama_no_cuenta(self):
        """Con --config, knip no busca otra: un knip.json de la rama con las reglas apagadas no vale."""
        self.sobra()
        (self.proyecto / "knip.json").write_text(json.dumps({"rules": {"files": "off", "exports": "off"}}))
        estado, texto, _ = self.knip({"files": "error", "exports": "error"})
        self.assertEqual(estado, 1, texto)

    def test_el_gitignore_de_la_rama_no_esconde_ficheros(self):
        self.sobra()
        (self.proyecto / ".gitignore").write_text("src/sobra.js\n")
        estado, texto, _ = self.knip({"files": "error"})
        self.assertEqual(estado, 1, texto)
        self.assertIn("src/sobra.js", texto)

    def test_una_carpeta_oculta_no_esconde_un_fichero(self):
        """Con el `project` por defecto de knip, como en la plantilla."""
        self.sobra()
        (self.proyecto / ".util").mkdir()
        (self.proyecto / ".util" / "oculto.js").write_text("export const oculto = 0;\n")
        estado, texto, _ = self.knip({"files": "error"}, config={"entry": ["src/index.js"]})
        self.assertEqual(estado, 1, texto)
        self.assertIn(".util/oculto.js", texto)

    def test_una_configuracion_que_no_carga_falla(self):
        estado, texto, _ = self.knip({"exports": "error"}, config={"entry": 5})
        self.assertNotEqual(estado, 0, texto)


@unittest.skipUnless(EN_LA_CI or shutil.which("jscpd"), "jscpd solo corre en la CI (validar) o con jscpd en el PATH")
class JscpdEnLaCi(RepoDePrueba):
    """Los pasos "Instalar jscpd", "jscpd" e "Informe de salud de jscpd" sobre un repo con
    tests/fixtures/jscpd en `main`, con el .jscpd.json de la plantilla. En la CI, el binario sale
    del paso de instalación; en local, del PATH."""
    PASO = "jscpd"
    CONFIG_PASO = ".jscpd.json"
    COPIA = (FIXTURE_JSCPD / "src" / "precios.js").read_text().replace("precioConImpuestos", "totalFactura")

    @classmethod
    def setUpClass(cls):
        cls.instalacion = pathlib.Path(tempfile.mkdtemp())
        if EN_LA_CI:
            inicio = time.monotonic()
            estado, texto, _ = ejecutar("Instalar jscpd", cls.instalacion, cls.instalacion,
                                        JSCPD_URL=JSCPD_URL, JSCPD_SHA256=JSCPD_SHA256)
            assert estado == 0, texto
            medida(f"jscpd, descarga y comprobación de la suma: {time.monotonic() - inicio:.1f} s")
            cls.binario = cls.instalacion / "jscpd" / "jscpd"
        else:
            cls.binario = pathlib.Path(shutil.which("jscpd"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.instalacion)

    def setUp(self):
        super().setUp()
        shutil.copytree(FIXTURE_JSCPD, self.repo, dirs_exist_ok=True)
        (self.temporal / "jscpd").mkdir()
        (self.temporal / "jscpd" / "jscpd").symlink_to(self.binario)

    def main(self, config=None):
        super().main(json.loads((PLANTILLA / ".jscpd.json").read_text(encoding="utf-8")) if config is None else config)

    def jscpd(self):
        estado, texto, _ = self.preparar("Configuración de jscpd de main")
        self.assertEqual(estado, 0, texto)
        inicio = time.monotonic()
        estado, texto, _ = ejecutar(self.PASO, self.repo, self.temporal)
        return estado, texto, time.monotonic() - inicio

    def informe(self):
        return json.loads((self.temporal / "jscpd-informe" / "jscpd-report.json").read_text())

    def test_sin_duplicacion_nueva_pasa(self):
        self.main()
        estado, texto, segundos = self.jscpd()
        self.assertEqual(estado, 0, texto)
        medida(f"jscpd, proyecto de prueba sin clones: {segundos:.1f} s")

    def test_un_clon_nuevo_falla(self):
        self.main()
        self.escribir("src/factura.js", self.COPIA)
        estado, texto, segundos = self.jscpd()
        self.assertEqual(estado, 1, texto)
        self.assertIn("factura.js", texto)
        medida(f"jscpd, un clon nuevo: salida {estado}, {segundos:.1f} s")

    def test_un_clon_heredado_de_main_no_cuenta(self):
        self.escribir("src/factura.js", self.COPIA)
        self.main()
        self.escribir("src/otro.js", "export const otro = 1;\n")
        estado, texto, _ = self.jscpd()
        self.assertEqual(estado, 0, texto)
        self.assertGreaterEqual(len(self.informe().get("duplicates", [])), 1)

    def test_lo_que_ignora_la_configuracion_de_main_no_cuenta(self):
        self.main({"ignore": ["**/copias/**"]})
        self.escribir("src/copias/factura.js", self.COPIA)
        estado, texto, _ = self.jscpd()
        self.assertEqual(estado, 0, texto)

    def test_el_gitignore_de_la_rama_no_esconde_ficheros(self):
        self.main()
        self.escribir(".gitignore", "src/factura.js\n")
        (self.repo / "src" / "factura.js").write_text(self.COPIA)
        git(self.repo, "add", "-f", "src/factura.js")
        estado, texto, _ = self.jscpd()
        self.assertEqual(estado, 1, texto)

    def test_la_configuracion_de_la_rama_no_cuenta(self):
        self.main()
        self.escribir(".jscpd.json", {"ignore": ["**/src/**"]})
        self.escribir("package.json", {"name": "p"})
        self.escribir("src/factura.js", self.COPIA)
        estado, texto, _ = self.jscpd()
        self.assertEqual(estado, 1, texto)

    def test_otra_configuracion_de_la_rama_no_cuenta(self):
        self.main()
        self.escribir(".config/jscpd.json", {"ignore": ["**/src/**"]})
        self.escribir(".config/.jscpd.json", {"ignore": ["**/src/**"]})
        self.escribir("src/factura.js", self.COPIA)
        estado, texto, _ = self.jscpd()
        self.assertEqual(estado, 1, texto)

    def test_un_fichero_grande_no_esconde_un_clon(self):
        """jscpd 3 y 4 se saltaban los ficheros de más de 1000 líneas o 100 kB."""
        self.main()
        relleno = "".join(f"// {i:04d} " + "x" * 100 + "\n" for i in range(1200))
        self.escribir("src/factura.js", self.COPIA + relleno)
        estado, texto, _ = self.jscpd()
        self.assertEqual(estado, 1, texto)

    def test_un_rgignore_no_esconde_ficheros(self):
        self.main()
        self.escribir(".rgignore", "src/factura.js\n")
        self.escribir("src/factura.js", self.COPIA)
        estado, texto, _ = self.jscpd()
        self.assertEqual(estado, 1, texto)

    def test_un_ignore_esconde_ficheros_a_jscpd(self):
        """Por eso falla la preparación con un .ignore (PrepararJscpd): jscpd recorre el árbol con el
        crate `ignore`, que lo lee aunque se pase --no-gitignore. Si deja de leerlo, sobra ese control."""
        self.main()
        self.escribir(".ignore", "src/factura.js\n")
        self.escribir("src/factura.js", self.COPIA)
        git(self.repo, "commit", "-q", "-m", "rama")
        shutil.copy(PLANTILLA / ".jscpd.json", self.temporal / ".jscpd.json")
        estado, texto, _ = ejecutar(self.PASO, self.repo, self.temporal)
        self.assertEqual(estado, 0, texto)

    def test_una_carpeta_oculta_no_esconde_un_clon(self):
        self.main()
        self.escribir(".util/factura.js", self.COPIA)
        estado, texto, _ = self.jscpd()
        self.assertEqual(estado, 1, texto)

    def test_una_carpeta_con_nombre_de_salida_cuenta(self):
        """jscpd aplica los `ignore` a cualquier profundidad (medido en el PR 3): la plantilla solo
        ignora Markdown y lockfiles, para que una carpeta build/ o node_modules/ no esconda código."""
        for nombre in ("src/build/factura.js", "src/reports/factura.js", "src/docs/factura.js", "src/factura.min.js",
                       "src/node_modules/factura.js", "src/.github/factura.js", "dist/factura.js", "docs/factura.js"):
            with self.subTest(nombre=nombre):
                self.setUp()
                self.main()
                self.escribir(nombre, self.COPIA)
                estado, texto, _ = self.jscpd()
                sonda(f"jscpd {nombre}", estado, texto)
                self.assertEqual(estado, 1, texto)

    def test_ficheros_raros_no_esconden_un_clon(self):
        grande = "".join(f"// {i:05d} " + "x" * 100 + "\n" for i in range(10000))
        casos = {
            "src/grande.js": (self.COPIA + grande).encode(),
            "src/factura.cjs": self.COPIA.encode(),
            "src/factura.mjs": self.COPIA.encode(),
        }
        for nombre, contenido in casos.items():
            with self.subTest(nombre=nombre):
                self.setUp()
                self.main()
                self.escribir(nombre, contenido)
                estado, texto, _ = self.jscpd()
                sonda(f"jscpd {nombre}", estado, texto)
                self.assertEqual(estado, 1, texto)

    def test_una_copia_en_otro_formato_de_js_cuenta(self):
        for ext in ("ts", "tsx", "jsx", "mts", "cts"):
            with self.subTest(ext=ext):
                self.setUp()
                self.main()
                self.escribir(f"src/factura.{ext}", self.COPIA)
                estado, texto, _ = self.jscpd()
                sonda(f"jscpd .{ext}", estado, texto)
                self.assertEqual(estado, 1, texto)

    def test_un_baseline_de_la_rama_no_cuenta(self):
        """La rama genera su .jscpd-baseline.json con el clon nuevo dentro: la base es la de main."""
        self.main()
        self.escribir("src/factura.js", self.COPIA)
        git(self.repo, "commit", "-q", "-m", "rama")
        subprocess.run([str(self.binario), ".", "--update-baseline", "--no-gitignore"], cwd=self.repo,
                       capture_output=True, text=True, timeout=120)
        hecho = [p.name for p in self.repo.rglob("*baseline*") if ".git" not in p.parts]
        estado, texto, _ = self.jscpd()
        sonda(f"jscpd baseline {hecho}", estado, texto)
        self.assertEqual(estado, 1, texto)

    def test_el_primer_pr_sin_nada_en_main(self):
        """Al adoptar la plantilla, main no tiene ni el código ni .jscpd.json: se analiza con el de la rama."""
        self.escribir("LEEME", "x")
        git(self.repo, "commit", "-q", "-m", "base")
        git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        shutil.copy(PLANTILLA / ".jscpd.json", self.repo / ".jscpd.json")
        estado, texto, _ = self.jscpd()
        sonda("jscpd primer PR sin clones", estado, texto, esperado=0)
        self.assertEqual(estado, 0, texto)
        self.escribir("src/factura.js", self.COPIA)
        estado, texto, _ = self.jscpd()
        sonda("jscpd primer PR con un clon", estado, texto)
        self.assertEqual(estado, 1, texto)

    def test_una_tercera_copia_de_un_clon_heredado_falla(self):
        self.escribir("src/factura.js", self.COPIA)
        self.main()
        self.escribir("src/albaran.js", self.COPIA.replace("totalFactura", "totalAlbaran"))
        estado, texto, _ = self.jscpd()
        self.assertEqual(estado, 1, texto)
        self.assertIn("albaran.js", texto)

    def test_el_informe_de_salud_no_bloquea(self):
        self.main()
        self.escribir("src/factura.js", self.COPIA)
        self.jscpd()
        estado, texto, _ = ejecutar("Informe de salud de jscpd", self.repo, self.temporal)
        self.assertEqual(estado, 0, texto)
        self.assertNotIn("::warning::El informe de salud", texto)

    def test_mide_este_repo(self):
        """El tiempo y los hallazgos de jscpd sobre este repo, con el .jscpd.json de la plantilla y sin
        clones nuevos (la base es el propio HEAD). No es un proyecto de producto: sirve de tamaño real."""
        temporal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporal)
        shutil.copy(PLANTILLA / ".jscpd.json", temporal / ".jscpd.json")
        (temporal / "jscpd").mkdir()
        (temporal / "jscpd" / "jscpd").symlink_to(self.binario)
        inicio = time.monotonic()
        estado, texto, _ = ejecutar(self.PASO, RAIZ, temporal, base="HEAD")
        segundos = time.monotonic() - inicio
        self.assertEqual(estado, 0, texto)
        informe = json.loads((temporal / "jscpd-informe" / "jscpd-report.json").read_text())
        total = (informe.get("statistics") or {}).get("total") or {}
        medida(f"jscpd, este repo: {segundos:.1f} s, {len(informe.get('duplicates', []))} clones heredados, "
               f"{total.get('sources')} ficheros, {total.get('lines')} líneas, {total.get('percentage')} %")


@unittest.skipUnless(EN_LA_CI, "descarga la release de GitHub: solo en la CI (validar)")
class InstalarJscpd(unittest.TestCase):
    def test_una_suma_que_no_coincide_falla(self):
        temporal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temporal)
        estado, texto, _ = ejecutar("Instalar jscpd", temporal, temporal, JSCPD_URL=JSCPD_URL, JSCPD_SHA256="0" * 64)
        self.assertEqual(estado, 1, texto)
        self.assertIn("::error::La suma de jscpd no coincide con la fijada", texto)
        self.assertFalse((temporal / "jscpd" / "jscpd").exists())


if __name__ == "__main__":
    unittest.main()

"""calidad.yml de la plantilla (VIC-21, PR 2): mutaciones con Stryker. El workflow no corre en
este repo, así que los tests ejecutan con bash los scripts de sus pasos, como en la CI, sobre
repos de prueba: la configuración sale de `main`, el umbral tiene que ser mayor que 0 y un test
debilitado hace fallar el job. Los de Stryker necesitan node y npm (y red para `npm ci`)."""
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CALIDAD = (RAIZ / "plantilla-proyecto" / ".github" / "workflows" / "calidad.yml").read_text(encoding="utf-8")
REGISTRO = (RAIZ / "docs" / "herramientas.md").read_text(encoding="utf-8")
FIXTURE = RAIZ / "tests" / "fixtures" / "stryker"
PAQUETE = {"name": "p", "private": True, "devDependencies": {"@stryker-mutator/core": "10.1.1"}}
CONFIG = {"mutate": ["src/**/*.js"], "testRunner": "command", "thresholds": {"break": 80}}


def script(paso):
    """El `run: |` del paso con ese nombre, sin la sangría del YAML."""
    bloque = re.search(rf"- name: {re.escape(paso)}\n(?:        .*\n)*?        run: \|\n((?:          .*\n|\n)+)",
                       CALIDAD).group(1)
    return textwrap.dedent(bloque)


def ejecutar(paso, carpeta, temporal, base="refs/remotes/origin/main"):
    salida = pathlib.Path(temporal) / "salida"
    salida.write_text("")
    entorno = dict(os.environ, BASE=base, RUNNER_TEMP=str(temporal), GITHUB_OUTPUT=str(salida),
                   GIT_NO_REPLACE_OBJECTS="1", npm_config_cache=str(pathlib.Path(temporal) / "npm"))
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

    def test_un_job_con_tiempo_maximo(self):
        jobs = CALIDAD.split("\njobs:\n", 1)[1]
        self.assertEqual(re.findall(r"^  ([a-z0-9-]+):", jobs, re.M), ["mutaciones"])
        self.assertRegex(jobs, r"\n    timeout-minutes: \d+\n")

    def test_stryker_de_node_modules_con_la_configuracion_de_main(self):
        """Nada de npx: descargaría una versión que no fija el lockfile."""
        self.assertNotIn("npx", CALIDAD)
        self.assertIn("npm ci --ignore-scripts", CALIDAD)
        self.assertIn('node_modules/.bin/stryker run "$RUNNER_TEMP/stryker.config.json" --force', CALIDAD)
        self.assertIn('git show "$BASE:stryker.config.json" > "$RUNNER_TEMP/stryker.config.json"', CALIDAD)

    def test_node_sin_cache(self):
        self.assertIn("package-manager-cache: false", CALIDAD)
        self.assertNotIn("cache: npm", CALIDAD)

    def test_acciones_del_registro(self):
        """La de checkout es la de los otros workflows; la de Node es nueva en este PR."""
        for sha in re.findall(r"uses: (?!actions/checkout@)\S+@([0-9a-f]{40})", CALIDAD):
            with self.subTest(sha=sha):
                self.assertIn(sha, REGISTRO)


class Preparar(unittest.TestCase):
    """El paso "Configuración de Stryker de main", sobre un repo con `main` y una rama."""
    PASO = "Configuración de Stryker de main"

    def setUp(self):
        self.temporal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temporal)
        self.repo = self.temporal / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")

    def escribir(self, nombre, contenido):
        (self.repo / nombre).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / nombre).write_text(contenido if isinstance(contenido, str) else json.dumps(contenido))
        git(self.repo, "add", nombre)

    def main(self, config=None):
        """Commit en `main` (con o sin stryker.config.json) y su ref origin/main."""
        if config is not None:
            self.escribir("stryker.config.json", config)
        self.escribir("LEEME", "x")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")
        git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    def preparar(self):
        """En la CI, HEAD es el merge con todo lo de la rama commiteado: aquí, un commit de la rama."""
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "rama")
        return ejecutar(self.PASO, self.repo, self.temporal)

    def config_usada(self):
        return json.loads((self.temporal / "stryker.config.json").read_text())

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


if __name__ == "__main__":
    unittest.main()

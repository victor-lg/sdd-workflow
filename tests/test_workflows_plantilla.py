"""Los workflows de la plantilla (VIC-18, PR 3) no corren en este repo: estos tests comprueban
su texto. Que seguridad.yml solo se lance en un PR (con `workflow_dispatch`, el agente podría
dejar sus checks en verde desde su rama; G4 del PR 3, ronda 2), que los jobs se llamen como los
checks requeridos y que versiones, sumas y digest sean los de docs/herramientas.md. Y que la base
sea la ref completa (VIC-26): los pasos que la leen se ejecutan con bash sobre un repo de prueba."""
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "plantilla-proyecto" / ".github"
WORKFLOWS = PLANTILLA / "workflows"
REGISTRO = (RAIZ / "docs" / "herramientas.md").read_text(encoding="utf-8")
REQUERIDOS = {"checks-sdd", "gitleaks", "osv-scanner", "semgrep", "mutaciones", "codigo-sobrante", "duplicados"}


def leer(nombre):
    return (WORKFLOWS / nombre).read_text(encoding="utf-8")


def disparadores(texto):
    bloque = re.search(r"^on:\n((?:[ #].*\n|\n)*)", texto, re.M).group(1)
    return set(re.findall(r"^  ([a-z_]+):", bloque, re.M))


def jobs(texto):
    bloque = texto.split("\njobs:\n", 1)[1]
    return set(re.findall(r"^  ([a-z0-9-]+):", bloque, re.M))


class WorkflowsDeLaPlantilla(unittest.TestCase):
    def test_seguridad_solo_en_un_pr(self):
        self.assertEqual(disparadores(leer("seguridad.yml")), {"pull_request"})
        self.assertNotIn("if:", leer("seguridad.yml"))

    def test_los_jobs_son_los_checks_requeridos(self):
        self.assertEqual(jobs(leer("seguridad.yml")), {"gitleaks", "osv-scanner", "semgrep"})
        self.assertEqual(jobs(leer("sdd.yml")), {"checks-sdd"})
        self.assertEqual(jobs(leer("calidad.yml")), {"mutaciones", "codigo-sobrante", "duplicados"})

    def test_sdd_solo_en_un_pr(self):
        """Fuera de un PR, github.base_ref está vacío: el paso que toma checks.py falla (BaseConEtiqueta)."""
        self.assertEqual(disparadores(leer("sdd.yml")), {"pull_request"})

    def test_la_tarea_mensual_no_se_llama_como_un_check_requerido(self):
        texto = leer("osv-mensual.yml")
        self.assertEqual(disparadores(texto), {"schedule", "workflow_dispatch"})
        self.assertFalse(jobs(texto) & REQUERIDOS)
        self.assertIn("if: github.ref == 'refs/heads/main'", texto)

    def test_osv_scanner_con_las_mismas_opciones(self):
        opciones = "scan source -r --no-ignore --allow-no-lockfiles --no-call-analysis=all --config"
        for nombre in ("seguridad.yml", "osv-mensual.yml"):
            with self.subTest(nombre=nombre):
                self.assertIn(opciones, " ".join(leer(nombre).replace("\\\n", " ").split()))

    def test_sumas_versiones_y_digest_del_registro(self):
        for nombre in ("seguridad.yml", "osv-mensual.yml"):
            texto = leer(nombre)
            sumas = re.findall(r'echo "([0-9a-f]{64})  ', texto)
            versiones = re.findall(r"/releases/download/(v[\d.]+)/", texto)
            digest = re.findall(r"@(sha256:[0-9a-f]{64})", texto)
            self.assertTrue(sumas and versiones)
            for valor in sumas + versiones + digest:
                with self.subTest(nombre=nombre, valor=valor):
                    self.assertIn(valor, REGISTRO)

    def test_semgrep_sin_la_lista_por_defecto(self):
        """Sin .semgrepignore, Semgrep excluiría tests/, vendor/… y los ficheros de más de 1 MB."""
        texto = leer("seguridad.yml")
        self.assertIn("else : > .semgrepignore; fi", texto)
        self.assertIn("\\( -name .semgrepignore -o -name .gitignore \\) ! -type d -exec rm -f {} +", texto)
        self.assertIn("semgrep scan --config p/default --metrics=off --error --disable-nosem --max-target-bytes=0", texto)

    def test_semgrep_confia_solo_en_el_workspace(self):
        """En el contenedor, Git rechazaba el checkout por ser de otro usuario (calculadora-discos#40)."""
        texto = leer("seguridad.yml")
        self.assertIn('git config --global --add safe.directory "$GITHUB_WORKSPACE"\n', texto)
        self.assertNotIn("safe.directory '*'", texto)
        self.assertNotIn('safe.directory "*"', texto)
        self.assertNotIn("safe.directory *", texto)

    def test_acciones_fijadas_por_sha(self):
        for fichero in WORKFLOWS.glob("*.yml"):
            for uso in re.findall(r"uses: (\S+)", fichero.read_text(encoding="utf-8")):
                with self.subTest(fichero=fichero.name, uso=uso):
                    self.assertRegex(uso, r"@[0-9a-f]{40}$")

    def test_sin_credenciales_ni_mas_permisos(self):
        for fichero in WORKFLOWS.glob("*.yml"):
            texto = fichero.read_text(encoding="utf-8")
            with self.subTest(fichero=fichero.name):
                self.assertIn("permissions:\n  contents: read\n", texto)
                self.assertEqual(texto.count("persist-credentials: false"), texto.count("actions/checkout@"))


def paso(texto, nombre, base_ref):
    """El script del paso con ese nombre y su entorno (el `env:` del workflow y el del paso), con
    `${{ github.base_ref }}` sustituido por base_ref. El resto de expresiones `${{ }}` se quedan fuera."""
    bloque = re.search(rf"\n      - name: {re.escape(nombre)}\n((?:        .*\n|\n)*)", texto).group(1)
    varios = re.search(r"^        run: \|\n((?:          .*\n|\n)+)", bloque, re.M)
    script = textwrap.dedent(varios.group(1)) if varios else re.search(r"^        run: (.+)$", bloque, re.M).group(1)
    lineas = ""
    for patron, origen in ((r"^env:\n((?:  .*\n)+)", texto), (r"^        env:\n((?:          .*\n)+)", bloque)):
        m = re.search(patron, origen, re.M)
        lineas += m.group(1) if m else ""
    entorno = {}
    for clave, valor in re.findall(r"^ +([A-Z_]+): (.+)$", lineas, re.M):
        valor = valor.replace("${{ github.base_ref }}", base_ref).strip('"')
        if "${{" not in valor:
            entorno[clave] = valor
    return script, entorno


CONFIGURACION = [".gitleaks.toml", ".gitleaksignore", "osv-scanner.toml", ".semgrepignore", ".github/sdd/checks.py"]


class BaseConEtiqueta(unittest.TestCase):
    """VIC-26 (G4 del PR #41, ronda 1): con `origin/main`, Git resuelve antes una etiqueta llamada así,
    que la rama puede empujar, y la configuración de main saldría de donde ella eligiera. Aquí la
    rama remota tiene la configuración "main" y la etiqueta `origin/main`, en la cabeza de la rama,
    la configuración "etiqueta"."""

    def setUp(self):
        self.temporal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temporal)
        self.repo = self.temporal / "repo"
        self.repo.mkdir()
        self.global_ = self.temporal / "gitconfig"
        self.global_.write_text("")
        self.entorno = dict(os.environ, GIT_CONFIG_GLOBAL=str(self.global_), GIT_CONFIG_NOSYSTEM="1",
                            RUNNER_TEMP=str(self.temporal), GITHUB_WORKSPACE=str(self.repo))
        self.git("init", "-q", "-b", "main")
        for contenido in ("main", "etiqueta"):
            for nombre in CONFIGURACION:
                (self.repo / nombre).parent.mkdir(parents=True, exist_ok=True)
                (self.repo / nombre).write_text(f"# {contenido}\n")
            self.git("add", "-A")
            self.git("commit", "-q", "-m", contenido)
            if contenido == "main":
                self.git("update-ref", "refs/remotes/origin/main", "HEAD")
                self.main = self.git("rev-parse", "HEAD")
        self.git("tag", "origin/main")

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                               "-c", "tag.gpgsign=false", *args], cwd=self.repo, env=self.entorno,
                              check=True, capture_output=True, text=True).stdout.strip()

    def ejecutar(self, workflow, nombre, base_ref="main"):
        script, entorno = paso(leer(workflow), nombre, base_ref)
        r = subprocess.run(["bash", "-e", "-c", script], cwd=self.repo, env={**self.entorno, **entorno},
                           capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout + r.stderr

    def resuelve_a_main(self, ref):
        self.assertEqual(self.git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"), self.main, ref)

    def test_la_etiqueta_existe_y_gana_a_la_rama_remota(self):
        """El repo de prueba reproduce el problema: sin esto, los demás tests no probarían nada."""
        self.assertNotEqual(self.git("rev-parse", "origin/main^{commit}"), self.main)

    def test_seguridad_toma_la_configuracion_de_la_rama_remota(self):
        for nombre, copias in (("Configuración de gitleaks de main", [self.repo / ".gitleaks.toml",
                                                                        self.repo / ".gitleaksignore"]),
                               ("Configuración de osv-scanner de main", [self.temporal / "osv-scanner.toml"]),
                               ("Configuración de Semgrep de main", [self.repo / ".semgrepignore"])):
            with self.subTest(paso=nombre):
                codigo, salida = self.ejecutar("seguridad.yml", nombre)
                self.assertEqual(codigo, 0, salida)
                for copia in copias:
                    self.assertEqual(copia.read_text(), "# main\n", copia.name)

    def test_sdd_toma_checks_py_de_la_rama_remota(self):
        codigo, salida = self.ejecutar("sdd.yml", "Tomar los checks de la rama base")
        self.assertEqual(codigo, 0, salida)
        self.assertEqual((self.temporal / "sdd" / "checks.py").read_text(), "# main\n")

    def test_sdd_pasa_a_checks_py_la_rama_remota(self):
        """En lugar de checks.py, uno que escribe sus argumentos: así se ve qué base le llega."""
        (self.temporal / "sdd").mkdir()
        (self.temporal / "sdd" / "checks.py").write_text("import sys\nprint(sys.argv[sys.argv.index('--base') + 1])\n")
        codigo, salida = self.ejecutar("sdd.yml", "Specs, mezcla, trazabilidad (G3), riesgo, convenciones y commits")
        self.assertEqual(codigo, 0, salida)
        self.resuelve_a_main(salida.strip())

    def test_checks_py_por_defecto_lee_la_rama_remota(self):
        texto = (PLANTILLA / "sdd" / "checks.py").read_text(encoding="utf-8")
        self.resuelve_a_main(re.search(r'add_argument\("--base", default="([^"]+)"', texto).group(1))

    def test_sdd_sin_rama_base_falla_con_un_error_claro(self):
        """Fuera de pull_request no hay github.base_ref: nunca se toma checks.py de otro sitio."""
        codigo, salida = self.ejecutar("sdd.yml", "Tomar los checks de la rama base", base_ref="")
        self.assertNotEqual(codigo, 0, salida)
        self.assertIn("::error::Sin rama base: sdd.yml solo corre en pull_request", salida)
        self.assertFalse((self.temporal / "sdd" / "checks.py").exists())


class SinOrigenAbreviado(unittest.TestCase):
    def test_ningun_workflow_ni_script_usa_origin_sin_la_ref_completa(self):
        """Los comentarios pueden nombrarlo; el código, no."""
        for fichero in [*WORKFLOWS.glob("*.yml"), *(PLANTILLA / "sdd").glob("*.py")]:
            for numero, linea in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
                if not linea.lstrip().startswith("#"):
                    with self.subTest(fichero=fichero.name, linea=numero):
                        self.assertNotRegex(linea, r"(?<!refs/remotes/)origin/")


if __name__ == "__main__":
    unittest.main()

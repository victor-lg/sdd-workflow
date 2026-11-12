"""La configuración de lefthook de la plantilla bloquea en local un commit con un secreto
(ADR-0008, §5; VIC-18) o con un mensaje fuera de formato (PR 3). Instala los hooks en un repo
de usar y tirar y hace commits de verdad con lefthook y gitleaks. Además, la orden de gitleaks
de la CI de la plantilla (`seguridad.yml`) ve lo que esconden un atributo, otra rama o un merge.

Necesita lefthook y gitleaks en el PATH, en las versiones de docs/herramientas.md; si no
están (la CI de este repo no los tiene), se salta. En local:
    PATH=<carpeta con los binarios>:$PATH python3 -m unittest tests.test_lefthook_gitleaks -v
El secreto señuelo se genera al ejecutar, para que ningún escáner lo encuentre en el repo."""
import os
import pathlib
import re
import secrets
import shutil
import string
import subprocess
import tempfile
import time
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "plantilla-proyecto" / "lefthook.json"
CHECKS = RAIZ / "plantilla-proyecto" / ".github" / "sdd" / "checks.py"
SEGURIDAD = RAIZ / "plantilla-proyecto" / ".github" / "workflows" / "seguridad.yml"
MENSAJE = "feat(config): lee el token del entorno\n\nRefs: VIC-1"
VERSIONES = {"lefthook": "2.2.2", "gitleaks": "8.30.1"}
# Sin la configuración global ni la del sistema de quien lo ejecute.
ENTORNO = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t"}
# Ni las variables que desvían los hooks ni las que llevarían git a otro repo (si se lanza
# desde un hook de Git, que las exporta).
for _variable in ("LEFTHOOK", "LEFTHOOK_EXCLUDE", "LEFTHOOK_CONFIG", "LEFTHOOK_BIN", "GITLEAKS_CONFIG",
                  "GITLEAKS_CONFIG_TOML", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
                  "GIT_OBJECT_DIRECTORY"):
    ENTORNO.pop(_variable, None)


def senuelo():
    """Un token con la forma de un token clásico de GitHub (ghp_ y 36 caracteres)."""
    return "ghp_" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(36))


def version(binario):
    r = subprocess.run([binario, "version"], capture_output=True, text=True)
    return r.stdout.strip().lstrip("v")


@unittest.skipUnless(shutil.which("lefthook") and shutil.which("gitleaks"), "sin lefthook o gitleaks en el PATH")
class CommitConSecreto(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        shutil.copy(CONFIG, self.repo / "lefthook.json")
        (self.repo / ".github" / "sdd").mkdir(parents=True)
        shutil.copy(CHECKS, self.repo / ".github" / "sdd" / "checks.py")
        r = subprocess.run(["lefthook", "install"], cwd=self.repo, capture_output=True, text=True, env=ENTORNO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.git("add", "lefthook.json", ".github/sdd/checks.py")
        r = self.commit("chore: inicio\n\nRefs: VIC-1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True, env=ENTORNO)

    def commit(self, mensaje, **entorno):
        return subprocess.run(["git", "commit", "-m", mensaje], cwd=self.repo, capture_output=True, text=True,
                              env={**ENTORNO, **entorno})

    def preparar(self, nombre, texto):
        (self.repo / nombre).write_text(texto, encoding="utf-8")
        self.git("add", nombre)

    def test_versiones_del_registro(self):
        for binario, esperada in VERSIONES.items():
            with self.subTest(binario=binario):
                self.assertEqual(version(binario), esperada)

    def test_el_secreto_bloquea_el_commit_sin_salir_en_el_registro(self):
        token = senuelo()
        self.preparar("config.py", f'TOKEN = "{token}"\n')
        inicio = time.monotonic()
        r = self.commit("feat(config): añade el token")
        print(f"\n  commit con secreto: {time.monotonic() - inicio:.2f} s", end=" ")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        # gitleaks escribe «leaks found: N» (y «no leaks found» si no hay): hace falta el número.
        self.assertRegex(r.stdout + r.stderr, re.compile(r"leaks found: [1-9]"))
        self.assertNotIn(token, r.stdout + r.stderr)
        self.assertNotIn("feat(config)", subprocess.run(["git", "log", "--format=%s"], cwd=self.repo,
                                                        capture_output=True, text=True, env=ENTORNO).stdout)

    def test_el_comentario_gitleaks_allow_no_lo_salta(self):
        """G4 del PR #30, ronda 3: sin --ignore-gitleaks-allow, el comentario dejaba pasar el commit."""
        self.preparar("config.py", f'TOKEN = "{senuelo()}"  # gitleaks:allow\n')
        r = self.commit("feat(config): añade el token")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_sin_secreto_pasa(self):
        self.preparar("config.py", 'TOKEN = os.environ["TOKEN"]\n')
        inicio = time.monotonic()
        r = self.commit(MENSAJE)
        print(f"\n  commit sin secreto: {time.monotonic() - inicio:.2f} s", end=" ")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_los_saltos_funcionan_y_por_eso_los_bloquea_el_plugin(self):
        """Lo que guarda-saltos.py bloquea en las órdenes del agente salta de verdad el hook
        (LEFTHOOK_EXCLUDE excluye por etiqueta y también por nombre)."""
        for entorno, opcion in (({"LEFTHOOK": "0"}, None), ({"LEFTHOOK_EXCLUDE": "gitleaks"}, None),
                                ({}, "--no-verify")):
            with self.subTest(entorno=entorno, opcion=opcion):
                self.preparar("config.py", f'TOKEN = "{senuelo()}"\n')
                orden = ["git", "commit", "-m", MENSAJE] + ([opcion] if opcion else [])
                r = subprocess.run(orden, cwd=self.repo, capture_output=True, text=True, env={**ENTORNO, **entorno})
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.git("reset", "-q", "--hard", "HEAD~1")

    def test_mensaje_fuera_de_formato_bloquea_el_commit(self):
        self.preparar("config.py", 'TOKEN = os.environ["TOKEN"]\n')
        inicio = time.monotonic()
        r = self.commit("lee el token del entorno")
        print(f"\n  commit con mensaje fuera de formato: {time.monotonic() - inicio:.2f} s", end=" ")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Error: el título", r.stdout + r.stderr)
        self.assertIn("AGENTS.md", r.stdout + r.stderr)
        r = self.commit("feat(config): lee el token del entorno")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Refs: VIC-N", r.stdout + r.stderr)
        self.assertEqual(self.commit(MENSAJE).returncode, 0)


ORDEN_CI = ["git", "--redact", "--no-banner", "--ignore-gitleaks-allow", "--log-opts=--diff-merges=remerge HEAD", "."]


@unittest.skipUnless(shutil.which("gitleaks"), "sin gitleaks en el PATH")
class GitleaksEnLaCi(unittest.TestCase):
    """Lo comprobado al escribir seguridad.yml: sin sus opciones, gitleaks no ve el secreto."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.escribir("README.md", "x\n")
        self.git("commit", "-q", "-m", "chore: inicio")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True, env=ENTORNO)

    def escribir(self, nombre, texto):
        (self.repo / nombre).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / nombre).write_text(texto, encoding="utf-8")
        self.git("add", nombre)

    def gitleaks(self, *opciones):
        r = subprocess.run(["gitleaks", *opciones], cwd=self.repo, capture_output=True, text=True, env=ENTORNO)
        self.assertNotIn("ghp_", r.stdout + r.stderr)
        return r.returncode

    def test_el_workflow_lanza_esta_orden(self):
        texto = " ".join(SEGURIDAD.read_text(encoding="utf-8").split())
        self.assertIn('"$RUNNER_TEMP/gitleaks" git --redact --no-banner --ignore-gitleaks-allow '
                      '--log-opts="--diff-merges=remerge HEAD" .', texto)
        self.assertIn("echo '* diff' >> .git/info/attributes", texto)

    def test_un_atributo_anidado_lo_esconde_y_info_attributes_lo_devuelve(self):
        for atributo in ("* -diff", "* binary", "config.py -diff"):
            with self.subTest(atributo=atributo):
                self.escribir("src/.gitattributes", atributo + "\n")
                self.escribir("src/config.py", f'TOKEN = "{senuelo()}"\n')
                self.git("commit", "-q", "-m", "feat: x")
                self.assertEqual(self.gitleaks(*ORDEN_CI), 0)
                (self.repo / ".git" / "info" / "attributes").write_text("* diff\n", encoding="utf-8")
                self.assertEqual(self.gitleaks(*ORDEN_CI), 1)
                (self.repo / ".git" / "info" / "attributes").unlink()
                self.git("reset", "-q", "--hard", "HEAD~1")

    def test_no_mira_otras_ramas(self):
        """Por defecto, gitleaks recorre todas las ramas: un secreto en otra pararía cualquier PR."""
        self.git("switch", "-q", "-c", "otra")
        self.escribir("config.py", f'TOKEN = "{senuelo()}"\n')
        self.git("commit", "-q", "-m", "feat: x")
        self.git("switch", "-q", "main")
        self.assertEqual(self.gitleaks("git", "--redact", "--no-banner", "."), 1)
        self.assertEqual(self.gitleaks(*ORDEN_CI), 0)
        self.git("switch", "-q", "otra")
        self.assertEqual(self.gitleaks(*ORDEN_CI), 1)

    def test_ve_lo_que_anade_un_merge(self):
        """`git log -p` no enseña el diff de un merge: un secreto añadido al resolverlo pasaría."""
        self.git("switch", "-q", "-c", "lado")
        self.escribir("a.py", "a = 1\n")
        self.git("commit", "-q", "-m", "feat: a")
        self.git("switch", "-q", "main")
        self.escribir("b.py", "b = 1\n")
        self.git("commit", "-q", "-m", "feat: b")
        self.git("merge", "-q", "--no-commit", "--no-ff", "lado")
        self.escribir("c.py", f'TOKEN = "{senuelo()}"\n')
        self.git("commit", "-q", "-m", "chore: merge")
        self.assertEqual(self.gitleaks("git", "--redact", "--no-banner", "--log-opts=HEAD", "."), 0)
        self.assertEqual(self.gitleaks(*ORDEN_CI), 1)


if __name__ == "__main__":
    unittest.main()

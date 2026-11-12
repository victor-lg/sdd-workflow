"""La configuración de lefthook de la plantilla bloquea en local un commit con un secreto
(ADR-0008, §5; VIC-18). Instala los hooks en un repo de usar y tirar y hace commits de
verdad con lefthook y gitleaks.

Necesita lefthook y gitleaks en el PATH, en las versiones de docs/herramientas.md; si no
están (la CI de este repo no los tiene), se salta. En local:
    PATH=<carpeta con los binarios>:$PATH python3 -m unittest tests.test_lefthook_gitleaks -v
El secreto señuelo se genera al ejecutar, para que ningún escáner lo encuentre en el repo."""
import os
import pathlib
import secrets
import shutil
import string
import subprocess
import tempfile
import time
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "plantilla-proyecto" / "lefthook.json"
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
        r = subprocess.run(["lefthook", "install"], cwd=self.repo, capture_output=True, text=True, env=ENTORNO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.git("add", "lefthook.json")
        self.assertEqual(self.commit("chore: inicio").returncode, 0)

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
        self.assertIn("gitleaks", r.stdout + r.stderr)
        self.assertNotIn(token, r.stdout + r.stderr)
        self.assertNotIn("feat(config)", subprocess.run(["git", "log", "--format=%s"], cwd=self.repo,
                                                        capture_output=True, text=True, env=ENTORNO).stdout)

    def test_sin_secreto_pasa(self):
        self.preparar("config.py", 'TOKEN = os.environ["TOKEN"]\n')
        inicio = time.monotonic()
        r = self.commit("feat(config): lee el token del entorno")
        print(f"\n  commit sin secreto: {time.monotonic() - inicio:.2f} s", end=" ")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_los_saltos_funcionan_y_por_eso_los_bloquea_el_plugin(self):
        """Lo que guarda-saltos.py bloquea en las órdenes del agente salta de verdad el hook
        (LEFTHOOK_EXCLUDE excluye por etiqueta y también por nombre)."""
        for entorno, opcion in (({"LEFTHOOK": "0"}, None), ({"LEFTHOOK_EXCLUDE": "gitleaks"}, None),
                                ({}, "--no-verify")):
            with self.subTest(entorno=entorno, opcion=opcion):
                self.preparar("config.py", f'TOKEN = "{senuelo()}"\n')
                orden = ["git", "commit", "-m", "x"] + ([opcion] if opcion else [])
                r = subprocess.run(orden, cwd=self.repo, capture_output=True, text=True, env={**ENTORNO, **entorno})
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.git("reset", "-q", "--hard", "HEAD~1")


if __name__ == "__main__":
    unittest.main()

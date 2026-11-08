"""Tests de plugin-sdd/hooks/sesion-unica.py (VIC-17, REG-49): una sesión por copia del repo."""
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HOOKS = pathlib.Path(__file__).resolve().parent.parent / "plugin-sdd" / "hooks"
RUTA = HOOKS / "sesion-unica.py"
_spec = importlib.util.spec_from_file_location("sesion_unica", RUTA)
sesion = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sesion)


class Sesion(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.copia = os.path.join(self.dir.name, "copia")
        subprocess.run(["git", "init", "-q", "-b", "main", self.copia], check=True)
        self.git_dir = sesion.directorio_de_git(self.copia)
        self.otra = subprocess.Popen(["sleep", "60"])
        self.addCleanup(self.terminar_otra)

    def terminar_otra(self):
        self.otra.kill()
        self.otra.wait()

    def ejecuta(self, cwd):
        entrada = json.dumps({"session_id": "s", "cwd": cwd, "source": "startup"})
        return subprocess.run([sys.executable, str(RUTA)], input=entrada, capture_output=True, text=True)

    def test_primera_sesion_no_avisa_y_deja_marca(self):
        self.assertEqual(sesion.registrar(self.git_dir, os.getpid(), "s1"), [])
        marcas = os.listdir(os.path.join(self.git_dir, "sdd-sesiones"))
        self.assertEqual(marcas, [f"{os.getpid()}.json"])

    def test_otra_sesion_viva_se_detecta(self):
        sesion.registrar(self.git_dir, self.otra.pid, "s1")
        self.assertEqual(sesion.registrar(self.git_dir, os.getpid(), "s2"), [self.otra.pid])

    def test_la_misma_sesion_tras_clear_no_se_avisa_a_si_misma(self):
        sesion.registrar(self.git_dir, os.getpid(), "s1")
        self.assertEqual(sesion.registrar(self.git_dir, os.getpid(), "s2"), [])

    def test_sesion_muerta_no_avisa_y_se_limpia(self):
        sesion.registrar(self.git_dir, self.otra.pid, "s1")
        self.terminar_otra()
        self.assertEqual(sesion.registrar(self.git_dir, os.getpid(), "s2"), [])
        self.assertEqual(os.listdir(os.path.join(self.git_dir, "sdd-sesiones")), [f"{os.getpid()}.json"])

    def test_pid_reutilizado_no_cuenta_como_viva(self):
        directorio = os.path.join(self.git_dir, "sdd-sesiones")
        os.makedirs(directorio)
        with open(os.path.join(directorio, f"{self.otra.pid}.json"), "w", encoding="utf-8") as f:
            json.dump({"pid": self.otra.pid, "arranque": "Thu Jan  1 00:00:00 1970"}, f)
        self.assertEqual(sesion.registrar(self.git_dir, os.getpid(), "s2"), [])

    def test_marca_rota_se_limpia(self):
        directorio = os.path.join(self.git_dir, "sdd-sesiones")
        os.makedirs(directorio)
        with open(os.path.join(directorio, "1234.json"), "w", encoding="utf-8") as f:
            f.write("{rota")
        self.assertEqual(sesion.registrar(self.git_dir, os.getpid(), "s2"), [])
        self.assertNotIn("1234.json", os.listdir(directorio))

    def test_un_worktree_es_otra_copia(self):
        subprocess.run(["git", "-C", self.copia, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                        "--allow-empty", "-m", "x"], check=True)
        arbol = os.path.join(self.dir.name, "arbol")
        subprocess.run(["git", "-C", self.copia, "worktree", "add", "-q", "-b", "w", arbol], check=True)
        sesion.registrar(self.git_dir, self.otra.pid, "s1")
        self.assertEqual(sesion.registrar(sesion.directorio_de_git(arbol), os.getpid(), "s2"), [])

    def test_una_subcarpeta_es_la_misma_copia(self):
        sub = os.path.join(self.copia, "sub")
        os.makedirs(sub)
        self.assertEqual(sesion.directorio_de_git(sub), self.git_dir)

    def test_fuera_de_un_repo_no_dice_nada(self):
        r = self.ejecuta(self.dir.name)
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_avisa_a_la_persona_y_al_agente_y_sugiere_worktree(self):
        sesion.registrar(self.git_dir, self.otra.pid, "s1")
        r = self.ejecuta(self.copia)
        salida = json.loads(r.stdout)
        self.assertEqual(salida["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("worktree", salida["systemMessage"])
        self.assertEqual(salida["systemMessage"], salida["hookSpecificOutput"]["additionalContext"])

    def test_si_no_puede_mirar_avisa(self):
        with mock.patch.object(sesion, "registrar", side_effect=PermissionError), \
                mock.patch.object(sys, "stdin", new=io.StringIO(json.dumps({"cwd": self.copia}))), \
                mock.patch.object(sys, "stdout", new=io.StringIO()) as salida:
            sesion.main()
        self.assertIn("no he podido comprobar", json.loads(salida.getvalue())["systemMessage"])

    def test_proceso_de_sesion_salta_los_interpretes(self):
        procesos = {10: "9 sh", 9: "8 bash", 8: "1 claude"}
        with mock.patch.object(sesion.os, "getppid", return_value=10), \
                mock.patch.object(sesion, "_ps", side_effect=lambda pid, *c: procesos.get(pid)):
            self.assertEqual(sesion.proceso_de_sesion(), 8)


if __name__ == "__main__":
    unittest.main()

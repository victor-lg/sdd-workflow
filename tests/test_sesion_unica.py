"""Tests de plugin-sdd/hooks/sesion-unica.py (VIC-17, REG-49): una sesión por copia del repo."""
import errno
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
        with open(os.path.join(directorio, "900007.json"), "w", encoding="utf-8") as f:
            f.write("{rota")
        self.assertEqual(sesion.registrar(self.git_dir, os.getpid(), "s2"), [])
        self.assertNotIn("900007.json", os.listdir(directorio))

    def crea_directorio(self):
        directorio = os.path.join(self.git_dir, "sdd-sesiones")
        os.makedirs(directorio)
        return directorio

    def test_no_toca_lo_que_apunta_un_enlace(self):
        victima = os.path.join(self.dir.name, "victima")
        os.makedirs(victima)
        for nombre in ("settings.json", "900007.json"):
            with open(os.path.join(victima, nombre), "w", encoding="utf-8") as f:
                f.write("{}")
        os.symlink(victima, os.path.join(self.git_dir, "sdd-sesiones"))
        with self.assertRaises(NotADirectoryError):
            sesion.registrar(self.git_dir, os.getpid(), "s")
        self.assertEqual(sorted(os.listdir(victima)), ["900007.json", "settings.json"])

    def test_solo_borra_nombres_de_marca(self):
        directorio = self.crea_directorio()
        for nombre in ("settings.json", "nota.txt"):
            with open(os.path.join(directorio, nombre), "w", encoding="utf-8") as f:
                f.write("{}")
        sesion.registrar(self.git_dir, os.getpid(), "s")
        self.assertTrue({"settings.json", "nota.txt"} <= set(os.listdir(directorio)))

    def test_marcas_hostiles_no_cuelgan_ni_cuentan(self):
        directorio = self.crea_directorio()
        fuera = os.path.join(self.dir.name, "fuera.json")
        with open(fuera, "w", encoding="utf-8") as f:
            json.dump({"pid": self.otra.pid, "arranque": sesion._ps(self.otra.pid, "lstart")}, f)
        os.mkfifo(os.path.join(directorio, "900001.json"))
        os.symlink("/dev/zero", os.path.join(directorio, "900002.json"))
        os.symlink(fuera, os.path.join(directorio, "900003.json"))
        with open(os.path.join(directorio, "900004.json"), "w", encoding="utf-8") as f:
            f.write("[]")
        with open(os.path.join(directorio, "900005.json"), "w", encoding="utf-8") as f:
            f.write("[" * 3000)
        os.mkdir(os.path.join(directorio, "900006.json"))
        self.assertEqual(sesion.registrar(self.git_dir, os.getpid(), "s"), [])
        self.assertTrue(os.path.exists(fuera))
        self.assertEqual(sorted(os.listdir(directorio)), [f"{os.getpid()}.json", "900006.json"])

    def test_error_de_git_no_es_estar_fuera_de_un_repo(self):
        with open(os.path.join(self.git_dir, "config"), "w", encoding="utf-8") as f:
            f.write("[rota")
        r = self.ejecuta(self.copia)
        self.assertIn("no he podido comprobar", json.loads(r.stdout)["systemMessage"])

    def test_sin_reglas_avisa_con_el_respaldo(self):
        with tempfile.TemporaryDirectory() as d:
            copia = pathlib.Path(d) / "sesion-unica.py"
            copia.write_text(RUTA.read_text(encoding="utf-8"), encoding="utf-8")
            r = subprocess.run([sys.executable, str(copia)], input="{}", capture_output=True, text=True)
        self.assertIn("no he podido comprobar", json.loads(r.stdout)["systemMessage"])

    def test_sin_ps_avisa(self):
        with mock.patch.object(sesion, "_ps", return_value=None):
            with self.assertRaises(RuntimeError):
                sesion.proceso_de_sesion()

    def test_si_ps_falla_no_borra_la_marca_de_otra_sesion(self):
        sesion.registrar(self.git_dir, self.otra.pid, "s1")
        directorio = os.path.join(self.git_dir, "sdd-sesiones")
        real = subprocess.run
        def falla_ps(orden, **k):
            if orden[0] == "ps":
                raise subprocess.TimeoutExpired(orden, 5)
            return real(orden, **k)
        with mock.patch.object(sesion.subprocess, "run", side_effect=falla_ps):
            with self.assertRaises(subprocess.TimeoutExpired):
                sesion.otras_vivas(directorio, os.getpid())
        self.assertIn(f"{self.otra.pid}.json", os.listdir(directorio))

    def test_error_al_leer_una_marca_no_la_da_por_muerta(self):
        with mock.patch.object(sesion.os, "open", side_effect=OSError(errno.EMFILE, "x")):
            with self.assertRaises(OSError):
                sesion.leer_marca("/x")

    def test_marca_con_pid_que_no_es_entero_no_cuenta(self):
        directorio = self.crea_directorio()
        for i, pid in enumerate(("1", True, -1, None)):
            with open(os.path.join(directorio, f"90001{i}.json"), "w", encoding="utf-8") as f:
                json.dump({"pid": pid, "arranque": "x"}, f)
        self.assertEqual(sesion.registrar(self.git_dir, os.getpid(), "s"), [])

    def test_intermedios_con_version(self):
        procesos = {10: "9 python3.12", 9: "8 sh", 8: "1 claude"}
        with mock.patch.object(sesion.os, "getppid", return_value=10), \
                mock.patch.object(sesion, "_ps", side_effect=lambda pid, *c: procesos.get(pid)):
            self.assertEqual(sesion.proceso_de_sesion(), 8)

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

"""Qué puede escribir el agente en el directorio de Git de su copia con el sandbox actual
(ADR-0008, §4 y §5; VIC-18). El diseño de lefthook se apoya en que .git/hooks y
.git/config quedan en solo lectura; si eso cambia, este test falla.

SandboxGit solo tiene sentido dentro del sandbox de Claude Code, que marca SANDBOX_RUNTIME.
Fuera (la CI, la persona en su terminal) se salta. Lo lanza el agente:
    python3 -m unittest tests.test_sandbox_git -v
o, para la tabla que va al PR:
    python3 tests/test_sandbox_git.py

Prueba escribiendo de verdad, sin cambiar nada: en las carpetas, crea y borra un fichero
con un nombre propio; en los ficheros, los abre para añadir y los cierra sin escribir.
No usa `test -w`, que en un montaje de solo lectura puede no coincidir con lo que pasa al
escribir.

MarcadoresDelSandbox (VIC-19) corre en todas partes: explica por qué no se deniegan
.git/commondir, .git/modules ni .git/worktrees. El sandbox deniega una ruta que no existe
poniendo ahí un marcador vacío: dentro, un dispositivo de 0 bytes que no se puede leer;
fuera queda un fichero vacío (M17). Aquí se simulan los dos en un repo desechable dentro
de .tareas/ y se prueban commit, switch y push contra un remoto local. Si Git cambia y el
commondir vacío deja de romperlo, falla. Que el sandbox siga marcando así lo mira
SandboxGit con las rutas que ya deniega él. También mide qué hace Git con un commondir que
apunta a otro directorio de Git con su propio config y hooks (docs/herramientas.md)."""
import errno
import os
import pathlib
import shlex
import stat
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DENTRO = bool(os.environ.get("SANDBOX_RUNTIME"))
NOMBRE_PRUEBA = f".sdd-prueba-escritura-{os.getpid()}"

# (ruta en el directorio de Git, si es carpeta, lo que el ADR-0008 necesita: False = solo lectura, None = se anota)
RUTAS = [
    ("hooks", True, False),
    ("config", False, False),
    ("info", True, None),
    ("info/exclude", False, None),
    ("HEAD", False, None),
    ("index", False, None),
    ("refs/heads", True, None),
    ("objects", True, None),
    ("modules", True, None),
    ("worktrees", True, None),
    # G4 del PR #30: si se puede crear, desvía config y hooks a otro directorio (ADR-0008, §6).
    # No se deniega: el sandbox pondría un commondir vacío y Git no arranca (VIC-19).
    ("commondir", False, None),
    ("", True, None),
]


def directorio_git(raiz=RAIZ):
    """El directorio de Git común: en un worktree, hooks y config están en el del repo principal."""
    r = subprocess.run(["git", "-C", str(raiz), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, text=True, check=True)
    return pathlib.Path(r.stdout.strip())


def se_puede_escribir(ruta, carpeta):
    """True, False, o "crear" / None si no existe y se puede crear o no. Lanza si falla
    por otra causa que el permiso."""
    if not ruta.exists():
        return "crear" if se_puede_escribir(ruta.parent, True) is True else None
    try:
        if carpeta:
            prueba = ruta / NOMBRE_PRUEBA
            prueba.touch(exist_ok=False)
            prueba.unlink()
        else:
            with open(ruta, "ab"):
                pass
        return True
    except OSError as e:
        if e.errno in (errno.EROFS, errno.EACCES, errno.EPERM):
            return False
        raise


def informe(raiz=RAIZ):
    git = directorio_git(raiz)
    return [(f".git/{nombre}" if nombre else ".git/", se_puede_escribir(git / nombre, carpeta), necesita)
            for nombre, carpeta, necesita in RUTAS]


# Rutas que el sandbox ya deniega sin que existan: dentro, aparecen como marcador vacío.
RUTAS_MARCADAS = [".gitmodules", ".git/config.lock"]

# (caso, ficheros que se ponen en el directorio de Git, paso en el que falla o None).
# Contenido None: fichero vacío que no se puede leer, como el marcador dentro del sandbox.
MARCADORES = [
    ("sin marcador", {}, None),
    ("commondir vacío", {"commondir": ""}, "status"),
    ("commondir sin lectura", {"commondir": None}, "status"),
    # La alternativa descartada: un commondir real que apunta al propio .git (docs/herramientas.md).
    ("commondir = .", {"commondir": ".\n"}, None),
    ("modules vacío", {"modules": ""}, None),
    ("worktrees vacío", {"worktrees": ""}, None),
]
PASOS = [
    ("status", ["status", "--short"]),
    ("switch", ["switch", "-c", "sdd-prueba"]),
    ("commit", ["commit", "--allow-empty", "-m", "prueba"]),
    ("push", ["push", "--quiet", "../remoto.git", "sdd-prueba"]),
    ("switch de vuelta", ["switch", "main"]),
]
WORKTREE = [("worktree add", ["worktree", "add", "--quiet", "../otra", "-b", "otra"])]


def _git(cwd, *args, check=False):
    # Sin las variables GIT_* heredadas (un hook exporta GIT_INDEX_FILE, por ejemplo) ni la
    # configuración de la persona o del sistema, y sin subir hasta el repo real.
    entorno = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    entorno.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                   GIT_CEILING_DIRECTORIES=str(RAIZ / ".tareas"))
    return subprocess.run(["git", "-c", "user.name=prueba", "-c", "user.email=prueba@ejemplo.invalid",
                           "-c", "init.defaultBranch=main", *args],
                          cwd=cwd, env=entorno, capture_output=True, text=True, check=check)


def simular(ficheros, pasos=PASOS):
    """Crea un repo con un commit y un remoto local en .tareas/, pone `ficheros` en su
    directorio de Git y prueba los pasos. Devuelve (paso que falla o None, error)."""
    base = RAIZ / ".tareas"
    base.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sdd-prueba-git-", dir=base) as tmp:
        tmp = pathlib.Path(tmp)
        _git(tmp, "init", "--quiet", "--bare", "remoto.git", check=True)
        _git(tmp, "init", "--quiet", "repo", check=True)
        repo = tmp / "repo"
        _git(repo, "commit", "--allow-empty", "--quiet", "-m", "inicio", check=True)
        for nombre, contenido in ficheros.items():
            ruta = repo / ".git" / nombre
            ruta.write_text(contenido or "")
            if contenido is None:
                ruta.chmod(0)
        for paso, args in pasos:
            r = _git(repo, *args)
            if r.returncode:
                return paso, r.stderr.strip()
    return None, ""


def tabla(filas):
    texto = {True: "sí", False: "no", "crear": "no existe; se puede crear", None: "no existe"}
    lineas = ["| Ruta | ¿Se puede escribir? | ADR-0008 |", "| --- | --- | --- |"]
    for ruta, escribe, necesita in filas:
        lineas.append(f"| `{ruta}` | {texto[escribe]} | {'solo lectura' if necesita is False else '—'} |")
    return "\n".join(lineas)


@unittest.skipUnless(DENTRO, "solo dentro del sandbox de Claude Code (SANDBOX_RUNTIME)")
class SandboxGit(unittest.TestCase):
    def test_hooks_y_config_en_solo_lectura(self):
        filas = informe()
        print("\n" + tabla(filas), end=" ")
        for ruta, escribe, necesita in filas:
            if necesita is False:
                with self.subTest(ruta=ruta):
                    self.assertIs(escribe, False, f"{ruta} se puede escribir desde el sandbox (ADR-0008, §4)")

    def test_no_deja_rastro(self):
        git = directorio_git()
        self.assertEqual([p for p in git.rglob(".sdd-prueba-escritura-*")], [])

    def test_marca_las_rutas_denegadas_que_no_existen(self):
        # La premisa de MarcadoresDelSandbox (docs/herramientas.md): si el sandbox deja de poner un
        # marcador vacío, la razón para no denegar commondir puede haber cambiado.
        # Un dispositivo, no un fichero vacío que haya quedado de otra sesión (M17).
        if not (RAIZ / ".git").is_dir():
            self.skipTest("en un worktree no se sabe qué rutas marca el sandbox")
        for nombre in RUTAS_MARCADAS:
            with self.subTest(ruta=nombre):
                ruta = RAIZ / nombre
                self.assertTrue(ruta.exists(), f"el sandbox ya no marca {nombre}: revisa la decisión de VIC-19 en docs/herramientas.md")
                info = ruta.stat()
                self.assertTrue(stat.S_ISCHR(info.st_mode), f"{nombre} no es el marcador del sandbox")
                self.assertEqual(info.st_size, 0)
                with self.assertRaises(PermissionError):
                    ruta.read_bytes()
                self.assertIs(se_puede_escribir(ruta, False), False)

    def test_git_es_punto_de_montaje(self):
        # Mover .git y dejar un fichero .git en su sitio desviaría config y hooks como
        # commondir; rename(2) no mueve un punto de montaje (EBUSY).
        with open("/proc/self/mountinfo") as f:
            montajes = {linea.split()[4] for linea in f}
        self.assertIn(str(directorio_git()), montajes)


class MarcadoresDelSandbox(unittest.TestCase):
    def test_commit_switch_y_push_con_cada_marcador(self):
        for caso, ficheros, falla_en in MARCADORES:
            with self.subTest(caso=caso):
                if any(c is None for c in ficheros.values()) and os.geteuid() == 0:
                    self.skipTest("root lee aunque falte el permiso")
                paso, error = simular(ficheros)
                self.assertEqual(paso, falla_en, error)
                if falla_en:
                    self.assertIn("commondir", error)

    def test_commondir_a_otro_directorio_toma_su_config_y_sus_hooks(self):
        # Lo que el agente podría hacer si escribe commondir: Git no avisa, toma config, hooks,
        # refs y objetos del otro directorio y ejecuta su pre-commit.
        base = RAIZ / ".tareas"
        base.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="sdd-prueba-git-", dir=base) as tmp:
            tmp = pathlib.Path(tmp)
            _git(tmp, "init", "--quiet", "ajeno", check=True)
            _git(tmp, "init", "--quiet", "repo", check=True)
            repo, ajeno = tmp / "repo", tmp / "ajeno" / ".git"
            _git(repo, "commit", "--allow-empty", "--quiet", "-m", "inicio", check=True)
            with open(ajeno / "config", "a") as f:
                f.write("[sdd]\n\tprueba = ajeno\n")
            marca = tmp / "hook-ajeno-ejecutado"
            hook = ajeno / "hooks" / "pre-commit"
            hook.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(marca))}\n")
            hook.chmod(0o755)
            (repo / ".git" / "commondir").write_text(f"{ajeno}\n")

            self.assertEqual(_git(repo, "config", "--get", "sdd.prueba").stdout.strip(), "ajeno")
            r = _git(repo, "commit", "--allow-empty", "--quiet", "-m", "prueba")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stderr, "", "Git avisó de algo")
            self.assertTrue(marca.exists(), "el pre-commit del otro directorio no se ejecutó")
            # La ref y el objeto del commit quedan en el otro directorio.
            otro = _git(ajeno.parent, "rev-parse", "--verify", "--quiet", "refs/heads/main^{commit}")
            self.assertEqual(otro.returncode, 0, "el commit no fue al otro directorio")

    def test_worktrees_vacio_rompe_git_worktree(self):
        # La plantilla usa git worktree para el trabajo en paralelo (AGENTS.md).
        self.assertEqual(simular({}, PASOS + WORKTREE)[0], None)
        paso, error = simular({"worktrees": ""}, PASOS + WORKTREE)
        self.assertEqual(paso, "worktree add", error)
        self.assertIn("worktrees", error)


if __name__ == "__main__":
    if not DENTRO:
        sys.exit("Fuera del sandbox de Claude Code (sin SANDBOX_RUNTIME): no mide lo que importa.")
    print(tabla(informe()))

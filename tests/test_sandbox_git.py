"""Qué puede escribir el agente en el directorio de Git de su copia con el sandbox actual
(ADR-0008, §4 y §5; VIC-18). El diseño de lefthook se apoya en que .git/hooks y
.git/config quedan en solo lectura; si eso cambia, este test falla.

Solo tiene sentido dentro del sandbox de Claude Code, que marca SANDBOX_RUNTIME. Fuera
(la CI, la persona en su terminal) se salta. Lo lanza el agente:
    python3 -m unittest tests.test_sandbox_git -v
o, para la tabla que va al PR:
    python3 tests/test_sandbox_git.py

Prueba escribiendo de verdad, sin cambiar nada: en las carpetas, crea y borra un fichero
con un nombre propio; en los ficheros, los abre para añadir y los cierra sin escribir.
No usa `test -w`, que en un montaje de solo lectura puede no coincidir con lo que pasa al
escribir.

MarcadoresDelSandbox (VIC-19) corre en todas partes: explica por qué no se deniegan
.git/commondir, .git/modules ni .git/worktrees. En Linux, el sandbox deniega una ruta que
no existe con un fichero vacío de solo lectura mientras corre cada orden; aquí se simula
ese fichero en un repo desechable dentro de .tareas/ y se prueban commit, switch y push
contra un remoto local. Si Git cambia y el commondir vacío deja de romperlo, falla y toca
revisar la decisión (ADR-0008, §6)."""
import errno
import os
import pathlib
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


# (caso, ficheros que se ponen en el directorio de Git, paso en el que falla o None)
MARCADORES = [
    ("sin marcador", {}, None),
    ("commondir vacío", {"commondir": ""}, "status"),
    # La alternativa descartada: un commondir real que apunta al propio .git (ADR-0008, §6).
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


def _git(cwd, *args):
    # Sin la configuración de la persona ni la del sistema, para que solo cuente el repo.
    entorno = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run(["git", "-c", "user.name=prueba", "-c", "user.email=prueba@ejemplo.invalid",
                           "-c", "init.defaultBranch=main", *args],
                          cwd=cwd, env=entorno, capture_output=True, text=True)


def simular(ficheros, pasos=PASOS):
    """Crea un repo con un commit y un remoto local en .tareas/, pone `ficheros` en su
    directorio de Git y prueba los pasos. Devuelve (paso que falla o None, error)."""
    base = RAIZ / ".tareas"
    base.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sdd-prueba-git-", dir=base) as tmp:
        tmp = pathlib.Path(tmp)
        _git(tmp, "init", "--quiet", "--bare", "remoto.git")
        _git(tmp, "init", "--quiet", "repo")
        repo = tmp / "repo"
        _git(repo, "commit", "--allow-empty", "--quiet", "-m", "inicio")
        for nombre, contenido in ficheros.items():
            (repo / ".git" / nombre).write_text(contenido)
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


class MarcadoresDelSandbox(unittest.TestCase):
    def test_commit_switch_y_push_con_cada_marcador(self):
        for caso, ficheros, falla_en in MARCADORES:
            with self.subTest(caso=caso):
                paso, error = simular(ficheros)
                self.assertEqual(paso, falla_en, error)
                if falla_en:
                    self.assertIn("commondir", error)

    def test_worktrees_vacio_rompe_git_worktree(self):
        # La plantilla usa git worktree para el trabajo en paralelo (AGENTS.md).
        self.assertEqual(simular({}, PASOS + WORKTREE)[0], None)
        self.assertEqual(simular({"worktrees": ""}, PASOS + WORKTREE)[0], "worktree add")


if __name__ == "__main__":
    if not DENTRO:
        sys.exit("Fuera del sandbox de Claude Code (sin SANDBOX_RUNTIME): no mide lo que importa.")
    print(tabla(informe()))

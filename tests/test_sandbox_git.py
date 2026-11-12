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
escribir."""
import errno
import os
import pathlib
import subprocess
import sys
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


if __name__ == "__main__":
    if not DENTRO:
        sys.exit("Fuera del sandbox de Claude Code (sin SANDBOX_RUNTIME): no mide lo que importa.")
    print(tabla(informe()))

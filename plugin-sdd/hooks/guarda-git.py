#!/usr/bin/env python3
"""Guarda de órdenes de Git para PreToolUse sobre Bash (M16, X-03, REG-83, X-04; VIC-17).

Es una segunda capa contra errores del agente, no un control de seguridad: lee el
texto de la orden, así que bash -c, eval, variables, alias o scripts la esquivan.
Lo que protege de verdad es el sandbox, que imponen los ajustes gestionados, y la CI.
Las reglas Bash(...) de esos ajustes no se pueden anular, pero también leen el texto
de la orden: un script las esquiva igual.

X-04 mira, sin red, lo que llevaría cada git commit contra .gitignore y contra la
lista "fugas" de reglas-git.json. No mira git merge, cherry-pick, revert, am ni
rebase, que crean commits con contenido que ya estaba en otro commit.

Las reglas, sus niveles y sus mensajes están en reglas-git.json. Si no puede mirar,
falla cerrado.
"""
import fnmatch
import json
import os
import posixpath
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from lector_bash import NoAnalizable, analizar, juntar, opciones, orden_efectiva
    from lector_bash import nombres as _nombres
    ERROR_DE_CARGA = None
except Exception as e:  # Sin el lector, main() falla cerrado.
    ERROR_DE_CARGA = e

RUTA_REGLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglas-git.json")

OPCIONES_GLOBALES_CON_VALOR = {
    "-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env", "--attr-source",
}

LARGAS_PUSH = dict.fromkeys(
    ("all", "branches", "mirror", "delete", "tags", "follow-tags", "no-follow-tags", "signed", "no-signed",
     "atomic", "no-atomic", "dry-run", "porcelain", "force", "no-force", "force-with-lease",
     "no-force-with-lease", "force-if-includes", "no-force-if-includes", "prune", "no-prune", "verbose", "quiet",
     "progress", "no-progress", "recurse-submodules", "no-recurse-submodules", "verify", "no-verify",
     "thin", "no-thin", "ipv4", "ipv6", "set-upstream", "no-set-upstream"), False)
LARGAS_PUSH.update(dict.fromkeys(("repo", "receive-pack", "exec", "push-option"), True))

LARGAS_BRANCH = dict.fromkeys(
    ("delete", "create-reflog", "force", "move", "copy", "color", "no-color", "column", "no-column", "remotes",
     "all", "list", "show-current", "verbose", "quiet", "abbrev", "no-abbrev", "track", "no-track",
     "unset-upstream", "edit-description", "ignore-case", "omit-empty", "recurse-submodules"), False)
LARGAS_BRANCH.update(dict.fromkeys(
    ("set-upstream-to", "contains", "no-contains", "merged", "no-merged", "sort", "points-at", "format"), True))

LARGAS_CONFIG = dict.fromkeys(
    ("global", "system", "local", "worktree", "get", "get-all", "get-regexp", "get-urlmatch", "replace-all",
     "add", "unset", "unset-all", "rename-section", "remove-section", "list", "fixed-value", "edit", "bool",
     "int", "bool-or-int", "bool-or-str", "path", "expiry-date", "no-type", "null", "name-only", "includes",
     "no-includes", "show-origin", "show-scope", "show-names", "no-show-names", "all", "regexp"), False)
LARGAS_CONFIG.update(dict.fromkeys(
    ("file", "blob", "type", "default", "comment", "value", "url", "get-color", "get-colorbool"), True))
CONFIG_SUBORDENES_ESCRITURA = {"set", "unset", "rename-section", "remove-section", "edit"}
CONFIG_SUBORDENES_LECTURA = {"get", "list"}
CONFIG_OPCIONES_ESCRITURA = {
    "add", "replace-all", "unset", "unset-all", "rename-section", "remove-section", "edit", "e",
}
CONFIG_OPCIONES_LECTURA = {
    "get", "get-all", "get-regexp", "get-urlmatch", "get-color", "get-colorbool", "list", "l",
}

LARGAS_ADD = dict.fromkeys(
    ("dry-run", "verbose", "force", "interactive", "patch", "edit", "update", "all", "no-all", "ignore-removal",
     "no-ignore-removal", "intent-to-add", "refresh", "ignore-errors", "ignore-missing", "sparse",
     "no-warn-embedded-repo", "renormalize", "pathspec-file-nul", "no-dry-run"), False)
LARGAS_ADD.update(dict.fromkeys(("chmod", "pathspec-from-file"), True))

# El hook corre fuera del sandbox y el agente puede preparar el repo que mira (un .git
# que apunta a otro gitdir): git no debe ejecutar nada de su configuración ni escribir
# el índice (G4 del PR #26). Ninguna llamada pide al árbol de trabajo que pase filtros.
GIT_SEGURO = ("-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", "--no-optional-locks")
# Variables y opciones que hacen que git mire otro repo u otro índice que el de la carpeta.
OTRO_REPO = re.compile(r"(GIT_(DIR|WORK_TREE|INDEX_FILE|COMMON_DIR|OBJECT_DIRECTORY|CEILING_DIRECTORIES)(=|$)|--(git-dir|work-tree)(=|$))")
# Plazo de toda la orden: también acota cada llamada a git (G4 del PR #26).
_LIMITE = [float("inf")]


def _plazo():
    queda = _LIMITE[0] - time.monotonic()
    if queda < 0.2:
        raise NoPuedoMirar("sin tiempo")
    return min(3, queda)

LARGAS_COMMIT = dict.fromkeys(
    ("all", "patch", "reset-author", "short", "branch", "porcelain", "long", "null", "signoff", "no-signoff",
     "no-verify", "verify", "allow-empty", "allow-empty-message", "edit", "no-edit", "amend", "no-post-rewrite",
     "include", "only", "pathspec-file-nul", "untracked-files", "verbose", "quiet", "dry-run", "status",
     "no-status", "no-gpg-sign", "interactive", "gpg-sign"), False)
LARGAS_COMMIT.update(dict.fromkeys(
    ("reuse-message", "reedit-message", "fixup", "squash", "file", "author", "date", "message", "template",
     "trailer", "cleanup", "pathspec-from-file"), True))
# Con estas opciones, o con rutas, el commit lleva también cambios sin preparar.
COMMIT_CON_TRABAJO = {"a", "all", "i", "include", "o", "only", "p", "patch", "interactive", "pathspec-from-file"}

_LARGAS_CAMBIO_RAMA = dict.fromkeys(
    ("track", "no-track", "guess", "no-guess", "detach", "force", "merge", "quiet", "progress", "no-progress",
     "conflict", "recurse-submodules", "no-recurse-submodules", "ignore-other-worktrees", "overwrite-ignore",
     "no-overwrite-ignore"), False)
_LARGAS_CAMBIO_RAMA["orphan"] = True
LARGAS_SWITCH = {**_LARGAS_CAMBIO_RAMA, "create": True, "force-create": True, "discard-changes": False}
LARGAS_CHECKOUT = {**_LARGAS_CAMBIO_RAMA, "ours": False, "theirs": False, "patch": False, "overlay": False,
                   "no-overlay": False, "pathspec-from-file": True, "pathspec-file-nul": False}


class NoPuedoMirar(Exception):
    """Git no ha podido decir cómo está el repo."""


def separar_git(palabras):
    """Devuelve (subcomando, argumentos, directorios de -C, ajustes de -c) o None si no es git."""
    if not palabras or posixpath.basename(palabras[0]) not in ("git", "git.exe"):
        return None
    i, directorios, ajustes = 1, [], []
    while i < len(palabras) and palabras[i].startswith("-"):
        if palabras[i] in ("-C", "-c") and i + 1 < len(palabras):
            (directorios if palabras[i] == "-C" else ajustes).append(palabras[i + 1])
        i += 2 if palabras[i] in OPCIONES_GLOBALES_CON_VALOR else 1
    if i >= len(palabras):
        return None
    return palabras[i], palabras[i + 1:], directorios, ajustes


def _configura_seguimiento(ajuste):
    clave, _, valor = ajuste.partition("=")
    return clave.lower() == "push.autosetupremote" and valor.lower() not in ("false", "no", "off", "0")


def regla_push(args, ajustes):
    encontradas, _ = opciones(args, "o", LARGAS_PUSH)
    if _nombres(encontradas) & {"u", "set-upstream"} or any(map(_configura_seguimiento, ajustes)):
        return "push-seguimiento"
    return None


def regla_traer(args):
    """git fetch y git pull: solo la forma larga, porque -u no significa lo mismo."""
    for a in args:
        if a == "--":
            break
        if len(a) >= 5 and "--set-upstream".startswith(a):
            return "branch-seguimiento"
    return None


def regla_branch(args):
    encontradas, _ = opciones(args, "u", LARGAS_BRANCH)
    return "branch-seguimiento" if _nombres(encontradas) & {"u", "set-upstream-to"} else None


def regla_config(args):
    encontradas, posicionales = opciones(args, "f", LARGAS_CONFIG)
    nombres = _nombres(encontradas)
    if posicionales and posicionales[0] in CONFIG_SUBORDENES_LECTURA:
        return None
    if posicionales and posicionales[0] in CONFIG_SUBORDENES_ESCRITURA:
        return "config-escribe"
    if nombres & CONFIG_OPCIONES_ESCRITURA:
        return "config-escribe"
    if nombres & CONFIG_OPCIONES_LECTURA:
        return None
    return "config-escribe" if len(posicionales) >= 2 else None


def regla_add(args, conf):
    encontradas, posicionales = opciones(args, "", LARGAS_ADD)
    nombres = _nombres(encontradas)
    vista_previa = False
    for nombre, _ in encontradas:
        if nombre in ("n", "dry-run", "no-dry-run"):
            vista_previa = nombre != "no-dry-run"
    if vista_previa:
        return None
    if nombres & {"A", "all", "no-ignore-removal", "u", "update"}:
        return "add-sin-nombre"
    excluye = re.compile(conf["patron_pathspec_exclusion"])
    if posicionales and all(excluye.match(ruta) for ruta in posicionales):
        return "add-sin-nombre"
    for ruta in posicionales:
        partes = posixpath.normpath(ruta).split("/")
        if ruta and (set(partes) <= {".", ".."} or ruta in conf["rutas_que_abarcan_todo"]):
            return "add-sin-nombre"
    return None


def _git(cwd, *args, codigos_validos=(0,)):
    try:
        r = subprocess.run(["git", *GIT_SEGURO, "-C", cwd, *args], capture_output=True, text=True, timeout=_plazo())
    except (OSError, subprocess.SubprocessError) as e:
        raise NoPuedoMirar(str(e))
    if r.returncode not in codigos_validos:
        raise NoPuedoMirar(r.stderr.strip())
    return r.stdout.strip()


def _fetch_reciente(cwd, conf):
    ruta = _git(cwd, "rev-parse", "--git-path", "FETCH_HEAD")
    try:
        edad = time.time() - os.path.getmtime(os.path.join(cwd, ruta))
    except FileNotFoundError:
        return False
    return edad <= conf["max_minutos_desde_fetch"] * 60


def comprobar_base(inicio, cwd, previas, conf):
    """REG-83. inicio es el punto de partida escrito en la orden, o None. previas son
    los pares (subcomando, carpeta) de los fetch y pull anteriores que traen main."""
    if "$" in cwd:
        raise NoPuedoMirar("ruta dinámica")
    principal, remota = conf["rama_principal"], f'{conf["remoto"]}/{conf["rama_principal"]}'
    if inicio in (remota, f"remotes/{remota}", f"refs/remotes/{remota}"):
        local = None
    elif inicio in (principal, f"refs/heads/{principal}"):
        local = inicio
    elif inicio in (None, "HEAD", "@"):
        if _git(cwd, "symbolic-ref", "--short", "-q", "HEAD", codigos_validos=(0, 1)) != principal:
            return "base-no-main"
        local = principal
    else:
        return "base-no-main"
    con_fetch, con_pull = ("fetch", cwd) in previas, ("pull", cwd) in previas
    if local and con_pull and _git(cwd, "symbolic-ref", "--short", "-q", "HEAD", codigos_validos=(0, 1)) == principal:
        return None
    if not (con_fetch or con_pull or _fetch_reciente(cwd, conf)):
        return "base-desactualizada"
    if local and _git(cwd, "rev-parse", local) != _git(cwd, "rev-parse", f"refs/remotes/{remota}"):
        return "base-desactualizada"
    return None


def regla_crear_rama(sub, args, cwd, previas, conf):
    if sub == "switch":
        encontradas, posicionales = opciones(args, "cC", LARGAS_SWITCH)
        crea = _nombres(encontradas) & {"c", "C", "create", "force-create"}
    else:
        encontradas, posicionales = opciones(args, "bB", LARGAS_CHECKOUT)
        crea = _nombres(encontradas) & {"b", "B"}
    con_seguimiento = sin_seguimiento = False
    for nombre, _ in encontradas:
        if nombre in ("t", "track"):
            con_seguimiento, sin_seguimiento = True, False
        elif nombre == "no-track":
            con_seguimiento, sin_seguimiento = False, True
    inicio = posicionales[0] if posicionales else None
    desde_remota = inicio is not None and inicio.startswith(tuple(conf["prefijos_ramas_remotas"]))
    if con_seguimiento or (crea and desde_remota and not sin_seguimiento):
        return "crear-sin-no-track"
    return comprobar_base(inicio, cwd, previas, conf) if crea else None


def _trae_main(args, conf):
    """Si un git fetch o git pull con estos argumentos trae la rama principal del remoto."""
    encontradas, posicionales = opciones(args)
    if "dry-run" in _nombres(encontradas):  # En fetch y pull, -n no es --dry-run.
        return False
    if not posicionales:
        return True
    return posicionales[0] == conf["remoto"] and (len(posicionales) == 1 or conf["rama_principal"] in posicionales[1:])


def _git_entrada(cwd, entrada, *args, codigos_validos=(0,)):
    try:
        r = subprocess.run(["git", *GIT_SEGURO, "-C", cwd, *args], input=entrada, capture_output=True, text=True,
                           timeout=_plazo())
    except (OSError, subprocess.SubprocessError) as e:
        raise NoPuedoMirar(str(e))
    if r.returncode not in codigos_validos:
        raise NoPuedoMirar(r.stderr.strip())
    return r.stdout


def _rutas(salida):
    return [r for r in salida.split("\0") if r]


def _nunca_se_sube(ruta, fugas):
    nombre = posixpath.basename(ruta)
    if re.search(fugas["excepciones"], nombre):
        return False
    return any(fnmatch.fnmatchcase(ruta if "/" in patron else nombre, patron) for patron in fugas["nunca"])


def _dentro(ruta, carpeta):
    if "$" in carpeta:
        return False
    ruta, carpeta = os.path.realpath(ruta), os.path.realpath(carpeta)
    return ruta == carpeta or ruta.startswith(carpeta.rstrip("/") + "/")


def anadidos_por_add(args, cwd):
    """(ruta absoluta, forzado) de lo que un git add o git stage con estos argumentos va
    a preparar. Las rutas pueden ser carpetas o patrones: regla_commit las expande."""
    encontradas, posicionales = opciones(args, "", LARGAS_ADD)
    if _nombres(encontradas) & {"n", "dry-run"}:
        return []
    forzado = bool(_nombres(encontradas) & {"f", "force"})
    return [(juntar(cwd, ruta), forzado) for ruta in posicionales]


def regla_commit(args, cwd, anadidos, conf):
    """X-04. Devuelve ("commit-fuga", rutas) si el commit llevaría algo que .gitignore
    excluye o que nunca debe subirse. anadidos son las rutas absolutas de los git add
    anteriores de la misma orden, que aún no están preparadas cuando corre el hook."""
    if "$" in cwd:
        raise NoPuedoMirar("ruta dinámica")
    encontradas, posicionales = opciones(args, "mFCct", LARGAS_COMMIT)
    raiz = _git(cwd, "rev-parse", "--show-toplevel")
    rutas = _rutas(_git_entrada(cwd, None, "diff", "--cached", "--no-relative", "--no-ext-diff", "--no-textconv",
                                "--name-only", "-z", "--diff-filter=d"))
    preparadas = set(rutas)
    if posicionales or _nombres(encontradas) & COMMIT_CON_TRABAJO:
        # Con rutas, los ficheros del índice que casan con ellas; con -a, -p o
        # --pathspec-from-file, todos. Se miran también los no modificados: comparar con
        # el árbol de trabajo pasaría los filtros del repo.
        rutas += _rutas(_git_entrada(raiz, None, "ls-files", "-z", "--full-name", "--",
                                     *[os.path.relpath(juntar(cwd, r), raiz) for r in posicionales]))
    # Lo que añadirían esos git add, en una llamada con -f y otra sin él (sin -f, git se
    # salta lo ignorado).
    for forzado in (False, True):
        # Rutas reales en los dos lados: si cwd pasa por un enlace, relpath daría "..".
        relativas = [os.path.relpath(os.path.realpath(ruta), os.path.realpath(raiz))
                     for ruta, f in anadidos if f == forzado]
        relativas = [r for r in relativas if r != ".." and not r.startswith(".." + os.sep)]
        if relativas:
            excluir = () if forzado else ("--exclude-standard",)
            anadidas = _rutas(_git_entrada(raiz, None, "ls-files", "-z", "--full-name", "--cached", "--others",
                                           *excluir, "--", *relativas))
            rutas += anadidas
            preparadas.update(anadidas)
    rutas = list(dict.fromkeys(rutas))
    if not rutas:
        return None
    ignoradas = set(_rutas(_git_entrada(cwd, "\0".join(rutas) + "\0", "-C", raiz, "check-ignore", "--no-index",
                                        "-z", "--stdin", codigos_validos=(0, 1))))
    if ignoradas:  # Lo que ya está en HEAD se versionó a propósito: solo cuenta la lista "fugas".
        ignoradas -= set(_rutas(_git_entrada(raiz, None, "ls-tree", "-r", "-z", "--name-only", "--full-tree", "HEAD",
                                             "--", *ignoradas, codigos_validos=(0, 128))))
    fugas = [r for r in rutas if r in ignoradas or _nunca_se_sube(r, conf["fugas"])]
    if not fugas:
        return None
    # Si solo salen de -a o de las rutas del commit, el remedio es otro: preparar por nombre.
    return ("commit-fuga" if set(fugas) & preparadas else "commit-fuga-todo", fugas)


def _regla_de(sub, args, ajustes, cwd, previas, conf, anadidos=(), otro_repo=False):
    if sub == "push":
        return regla_push(args, ajustes)
    if sub in ("fetch", "pull"):
        return regla_traer(args)
    if sub == "branch":
        return regla_branch(args)
    if sub == "config":
        return regla_config(args)
    if sub in ("add", "stage"):
        return regla_add(args, conf)
    if sub in ("switch", "checkout"):
        return regla_crear_rama(sub, args, cwd, previas, conf)
    if sub == "commit":
        try:
            if otro_repo:
                raise NoPuedoMirar("otro repo u otro índice")
            return regla_commit(args, cwd, anadidos, conf)
        except NoPuedoMirar:
            return "commit-sin-mirar"
    return None


def decidir(comando, cwd, conf):
    """Devuelve el id de la regla más grave que incumple la orden, o None."""
    return decidir_con_detalle(comando, cwd, conf)[0]


def decidir_con_detalle(comando, cwd, conf):
    """Como decidir, pero devuelve (regla, detalle); el detalle son las rutas de X-04."""
    if len(comando) > conf["max_caracteres_orden"] and "git" in comando:
        return "sin-analizar", None
    limite = time.monotonic() + conf["max_segundos_analisis"]
    _LIMITE[0] = limite
    sesion = cwd
    try:
        ordenes = analizar(comando)
    except NoAnalizable:
        return ("sin-analizar" if "git" in comando else None), None
    candidata, previas, anadidos = None, set(), []
    otro_repo = any(OTRO_REPO.match(p) for palabras in ordenes for p in palabras)
    for palabras in ordenes:
        if time.monotonic() > limite:  # Antes de que el timeout del hook deje pasar la orden.
            return "sin-analizar", None
        efectiva = orden_efectiva(palabras)
        if efectiva[:1] in (["pushd"], ["popd"]):  # No se sigue: REG-83 falla cerrado.
            cwd = "$"
            continue
        if efectiva[:1] == ["cd"]:
            destinos = [a for a in efectiva[1:] if not a.startswith("-")]
            # cd solo, cd - o varios destinos: no se sabe a dónde va.
            cwd = juntar(cwd, destinos[0]) if len(destinos) == 1 and destinos[0] != "-" else "$"
            continue
        separado = separar_git(efectiva)
        if separado is None:
            continue
        sub, args, directorios, ajustes = separado
        cwd_git = cwd
        for directorio in directorios:
            cwd_git = juntar(cwd_git, directorio)
        try:
            regla = _regla_de(sub, args, ajustes, cwd_git, previas, conf, anadidos, otro_repo)
        except NoPuedoMirar:
            regla = "sin-mirar"
        regla, detalle = regla if isinstance(regla, tuple) else (regla, None)
        if regla and conf["reglas"][regla]["nivel"] != "preguntar":
            return regla, detalle
        candidata = candidata or regla
        if sub in ("fetch", "pull") and _trae_main(args, conf):
            previas.add((sub, cwd_git))
        if sub in ("add", "stage"):
            # Solo dentro de la carpeta de la sesión: fuera, el hook listaría nombres de ficheros ajenos.
            anadidos += [a for a in anadidos_por_add(args, cwd_git) if _dentro(a[0], sesion)]
    return candidata, None


def lista_corta(rutas, maximo=5):
    nombres = ", ".join(rutas[:maximo])
    return nombres + (f" y {len(rutas) - maximo} más" if len(rutas) > maximo else "")


def respuesta(decision, motivo):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": motivo}}


def main():
    try:
        if ERROR_DE_CARGA:
            raise ERROR_DE_CARGA
        with open(RUTA_REGLAS, encoding="utf-8") as f:
            conf = json.load(f)
        datos = json.load(sys.stdin)
        comando = datos["tool_input"]["command"]
        regla, detalle = decidir_con_detalle(comando, datos.get("cwd") or os.getcwd(), conf)
        if regla is None:
            return
        info = conf["reglas"][regla]
        mensaje = info["mensaje"].replace("{ficheros}", lista_corta(detalle or []))
        if info["nivel"] == "preguntar":
            salida = respuesta("ask", mensaje)
        else:
            salida = respuesta("deny", f'{mensaje} {conf["cierre"]}')
    except Exception as e:  # Si no puede mirar, falla cerrado (criterio 5 del inventario).
        salida = respuesta("deny", f"La guarda de Git no ha podido comprobar esta orden ({type(e).__name__}). "
                                   "Avisa a la persona; no la esquives.")
    json.dump(salida, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

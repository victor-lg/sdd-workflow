#!/usr/bin/env python3
"""Guarda de órdenes de Git para PreToolUse sobre Bash (M16, X-03, REG-83; VIC-17).

Es una segunda capa contra errores del agente, no un control de seguridad: lee el
texto de la orden, así que bash -c, eval, variables, alias o scripts la esquivan.
Lo que protege de verdad es el sandbox, los ajustes gestionados y la CI.

Las reglas, sus niveles y sus mensajes están en reglas-git.json. Si no puede mirar,
falla cerrado.
"""
import json
import os
import posixpath
import re
import subprocess
import sys
import time

RUTA_REGLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglas-git.json")

ASIGNACION = re.compile(r"[A-Za-z_]\w*\+?=")
RESERVADAS = {"if", "then", "elif", "else", "while", "until", "do", "!", "{"}
# Envolturas: opciones que llevan valor aparte y argumentos antes de la orden real.
ENVOLTURAS = {
    "env": ({"-u", "--unset", "-C", "--chdir"}, 0),
    "command": (set(), 0),
    "time": (set(), 0),
    "builtin": (set(), 0),
    "exec": ({"-a"}, 0),
    "nohup": (set(), 0),
    "nice": ({"-n", "--adjustment"}, 0),
    "timeout": ({"-s", "--signal", "-k", "--kill-after"}, 1),
    "sudo": ({"-u", "--user", "-g", "--group", "-h", "--host", "-p", "--prompt", "-C", "-D", "-R", "-T", "-U"}, 0),
}
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

_LARGAS_CAMBIO_RAMA = dict.fromkeys(
    ("track", "no-track", "guess", "no-guess", "detach", "force", "merge", "quiet", "progress", "no-progress",
     "conflict", "recurse-submodules", "no-recurse-submodules", "ignore-other-worktrees", "overwrite-ignore",
     "no-overwrite-ignore"), False)
_LARGAS_CAMBIO_RAMA["orphan"] = True
LARGAS_SWITCH = {**_LARGAS_CAMBIO_RAMA, "create": True, "force-create": True, "discard-changes": False}
LARGAS_CHECKOUT = {**_LARGAS_CAMBIO_RAMA, "ours": False, "theirs": False, "patch": False, "overlay": False,
                   "no-overlay": False, "pathspec-from-file": True, "pathspec-file-nul": False}


class NoAnalizable(Exception):
    """La orden tiene comillas, sustituciones o similares sin cerrar."""


class NoPuedoMirar(Exception):
    """Git no ha podido decir cómo está el repo."""


class _Lector:
    """Divide un texto de bash en órdenes simples. Las palabras salen sin comillas;
    lo que hay dentro de $(...) y de las comillas invertidas se lee como orden, salvo
    si va dentro de ${...} o de $((...)). El cuerpo de los heredocs y los comentarios
    no cuentan."""

    def __init__(self, texto, ordenes=None):
        self.t, self.i = texto, 0
        self.ordenes = [] if ordenes is None else ordenes

    def leer(self, anidado=False):
        palabras, heredocs, profundidad = [], [], 0

        def cerrar():
            if palabras:
                self.ordenes.append(palabras.copy())
                palabras.clear()

        while self.i < len(self.t):
            c = self.t[self.i]
            if c == "\n":
                self.i += 1
                cerrar()
                self._cuerpos(heredocs)
                heredocs.clear()
            elif c in " \t":
                self.i += 1
            elif c == "\\" and self.t[self.i + 1:self.i + 2] == "\n":
                self.i += 2
            elif c == "#":
                fin = self.t.find("\n", self.i)
                self.i = len(self.t) if fin < 0 else fin
            elif self.t.startswith("&>", self.i):
                self._redireccion(palabras, heredocs)
            elif c in ";&|":
                self.i += 1
                cerrar()
            elif c == "(":
                self.i += 1
                profundidad += 1
                cerrar()
            elif c == ")":
                self.i += 1
                cerrar()
                if anidado and profundidad == 0:
                    return
                profundidad = max(0, profundidad - 1)
            elif c in "<>":
                self._redireccion(palabras, heredocs)
            else:
                palabras.append(self._palabra())
        cerrar()
        self._cuerpos(heredocs)
        if anidado:
            raise NoAnalizable

    def _espacios(self):
        while self.t[self.i:self.i + 1] in (" ", "\t"):
            self.i += 1

    def _redireccion(self, palabras, heredocs):
        t, i = self.t, self.i
        if i > 0 and t[i - 1].isdigit() and palabras and palabras[-1].isdigit():
            palabras.pop()
        if t[i + 1:i + 2] == "(":  # <(orden) o >(orden): el paréntesis se lee como subshell.
            self.i += 1
        elif t.startswith("<<<", i):
            self.i += 3
            self._espacios()
            self._palabra()
        elif t.startswith("<<", i):
            self.i += 2
            quitar_tabs = t[self.i:self.i + 1] == "-"
            self.i += quitar_tabs
            self._espacios()
            desde = self.i
            delimitador = self._palabra()
            literal = any(q in t[desde:self.i] for q in "'\"\\")
            if not delimitador.isdigit():  # (( x << 2 )): un desplazamiento, no un heredoc.
                heredocs.append((delimitador, quitar_tabs, literal))
        else:
            self.i += 1
            while t[self.i:self.i + 1] in (">", "<", "&", "|"):
                self.i += 1
            self._espacios()
            self._palabra()

    def _cuerpos(self, heredocs):
        for delimitador, quitar_tabs, literal in heredocs:
            lineas = []
            while self.i < len(self.t):
                fin = self.t.find("\n", self.i)
                fin = len(self.t) if fin < 0 else fin
                linea = self.t[self.i:fin]
                self.i = min(fin + 1, len(self.t))
                if (linea.lstrip("\t") if quitar_tabs else linea) == delimitador:
                    break
                lineas.append(linea)
            if not literal:
                _Lector("\n".join(lineas), self.ordenes)._dobles(cierre=None)

    def _palabra(self):
        t, salida = self.t, []
        while self.i < len(t):
            c = t[self.i]
            if c in " \t\n;&|()<>":
                break
            if c == "\\":
                if t[self.i + 1:self.i + 2] != "\n":
                    salida.append(t[self.i + 1:self.i + 2])
                self.i += 2
            elif c == "'":
                fin = t.find("'", self.i + 1)
                if fin < 0:
                    raise NoAnalizable
                salida.append(t[self.i + 1:fin])
                self.i = fin + 1
            elif c == '"':
                self.i += 1
                salida.append(self._dobles())
            elif c == "`":
                salida.append(self._invertidas())
            elif c == "$":
                salida.append(self._dolar())
            else:
                salida.append(c)
                self.i += 1
        return "".join(salida)

    def _dobles(self, cierre='"'):
        t, salida = self.t, []
        while self.i < len(t):
            c = t[self.i]
            if c == cierre:
                self.i += 1
                return "".join(salida)
            if c == "\\":
                siguiente = t[self.i + 1:self.i + 2]
                if siguiente != "\n":
                    salida.append(siguiente if siguiente in ('$', '`', '"', "\\") else c + siguiente)
                self.i += 2
            elif c == "`":
                salida.append(self._invertidas())
            elif c == "$":
                salida.append(self._dolar(en_dobles=True))
            else:
                salida.append(c)
                self.i += 1
        if cierre is not None:
            raise NoAnalizable
        return "".join(salida)

    def _dolar(self, en_dobles=False):
        t, i = self.t, self.i
        if t.startswith("$((", i):
            return self._equilibrado("(", ")", i + 1)
        if t.startswith("$(", i):
            self.i += 2
            self.leer(anidado=True)
            return "$()"
        if t.startswith("${", i):
            return self._equilibrado("{", "}", i + 1)
        if t.startswith("$'", i) and not en_dobles:
            j = i + 2
            while j < len(t) and t[j] != "'":
                j += 2 if t[j] == "\\" else 1
            if j >= len(t):
                raise NoAnalizable
            self.i = j + 1
            return t[i + 2:j]
        if t.startswith('$"', i) and not en_dobles:
            self.i += 2
            return self._dobles()
        self.i += 1
        return "$"

    def _equilibrado(self, abre, cierra, desde):
        t, j, nivel = self.t, desde, 0
        while j < len(t):
            if t[j] == "\\":
                j += 2
                continue
            nivel += (t[j] == abre) - (t[j] == cierra)
            j += 1
            if nivel == 0:
                texto = t[self.i:j]
                self.i = j
                return texto
        raise NoAnalizable

    def _invertidas(self):
        t, j = self.t, self.i + 1
        interior = []
        while j < len(t) and t[j] != "`":
            if t[j] == "\\" and t[j + 1:j + 2] in ("`", "\\", "$"):
                j += 1
            interior.append(t[j:j + 1])
            j += 1
        if j >= len(t):
            raise NoAnalizable
        self.i = j + 1
        _Lector("".join(interior), self.ordenes).leer()
        return "$()"


def analizar(texto):
    lector = _Lector(texto)
    lector.leer()
    return lector.ordenes


def orden_efectiva(palabras):
    """Quita asignaciones, palabras reservadas y envolturas como env o timeout."""
    i = 0
    while i < len(palabras):
        palabra = palabras[i]
        if palabra in RESERVADAS or ASIGNACION.match(palabra):
            i += 1
        elif posixpath.basename(palabra) in ENVOLTURAS:
            con_valor, posicionales = ENVOLTURAS[posixpath.basename(palabra)]
            i += 1
            while i < len(palabras) and palabras[i].startswith("-") and palabras[i] != "-":
                i += 2 if palabras[i] in con_valor else 1
            i += posicionales
        else:
            break
    return palabras[i:]


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


def _resolver(nombre, largas):
    if nombre in largas:
        return nombre
    candidatas = [l for l in largas if l.startswith(nombre)]
    return candidatas[0] if len(candidatas) == 1 else nombre


def opciones(args, cortas_con_valor="", largas=None):
    """Separa opciones y posicionales como parse-options de Git: cortas juntas
    (-fu), largas abreviadas (--set-up) y valores con = o en la palabra siguiente."""
    largas = largas or {}
    encontradas, posicionales, i = [], [], 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            posicionales.extend(args[i:])
            break
        if a.startswith("--"):
            nombre, igual, valor = a[2:].partition("=")
            nombre = _resolver(nombre, largas)
            if not igual and largas.get(nombre) and i < len(args):
                valor = args[i]
                i += 1
            encontradas.append((nombre, valor))
        elif a.startswith("-") and len(a) > 1:
            j = 1
            while j < len(a):
                corta = a[j]
                j += 1
                if corta in cortas_con_valor:
                    valor = a[j:]
                    if not valor and i < len(args):
                        valor = args[i]
                        i += 1
                    encontradas.append((corta, valor))
                    break
                encontradas.append((corta, ""))
        else:
            posicionales.append(a)
    return encontradas, posicionales


def _nombres(encontradas):
    return {nombre for nombre, _ in encontradas}


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
        r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=3)
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


def _juntar(cwd, ruta):
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(ruta)))


def _trae_main(args, conf):
    """Si un git fetch o git pull con estos argumentos trae la rama principal del remoto."""
    encontradas, posicionales = opciones(args)
    if "dry-run" in _nombres(encontradas):  # En fetch y pull, -n no es --dry-run.
        return False
    if not posicionales:
        return True
    return posicionales[0] == conf["remoto"] and (len(posicionales) == 1 or conf["rama_principal"] in posicionales[1:])


def _regla_de(sub, args, ajustes, cwd, previas, conf):
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
    return None


def decidir(comando, cwd, conf):
    """Devuelve el id de la regla más grave que incumple la orden, o None."""
    if len(comando) > conf["max_caracteres_orden"] and "git" in comando:
        return "sin-analizar"
    limite = time.monotonic() + conf["max_segundos_analisis"]
    try:
        ordenes = analizar(comando)
    except NoAnalizable:
        return "sin-analizar" if "git" in comando else None
    candidata, previas = None, set()
    for palabras in ordenes:
        if time.monotonic() > limite:  # Antes de que el timeout del hook deje pasar la orden.
            return "sin-analizar"
        efectiva = orden_efectiva(palabras)
        if efectiva[:1] in (["pushd"], ["popd"]):  # No se sigue: REG-83 falla cerrado.
            cwd = "$"
            continue
        if efectiva[:1] == ["cd"]:
            destinos = [a for a in efectiva[1:] if not a.startswith("-")]
            if len(destinos) == 1:
                cwd = _juntar(cwd, destinos[0])
            continue
        separado = separar_git(efectiva)
        if separado is None:
            continue
        sub, args, directorios, ajustes = separado
        cwd_git = cwd
        for directorio in directorios:
            cwd_git = _juntar(cwd_git, directorio)
        try:
            regla = _regla_de(sub, args, ajustes, cwd_git, previas, conf)
        except NoPuedoMirar:
            regla = "sin-mirar"
        if regla and conf["reglas"][regla]["nivel"] != "preguntar":
            return regla
        candidata = candidata or regla
        if sub in ("fetch", "pull") and _trae_main(args, conf):
            previas.add((sub, cwd_git))
    return candidata


def respuesta(decision, motivo):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": motivo}}


def main():
    try:
        with open(RUTA_REGLAS, encoding="utf-8") as f:
            conf = json.load(f)
        datos = json.load(sys.stdin)
        comando = datos["tool_input"]["command"]
        regla = decidir(comando, datos.get("cwd") or os.getcwd(), conf)
        if regla is None:
            return
        info = conf["reglas"][regla]
        if info["nivel"] == "preguntar":
            salida = respuesta("ask", info["mensaje"])
        else:
            salida = respuesta("deny", f'{info["mensaje"]} {conf["cierre"]}')
    except Exception as e:  # Si no puede mirar, falla cerrado (criterio 5 del inventario).
        salida = respuesta("deny", f"La guarda de Git no ha podido comprobar esta orden ({type(e).__name__}). "
                                   "Avisa a la persona; no la esquives.")
    json.dump(salida, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

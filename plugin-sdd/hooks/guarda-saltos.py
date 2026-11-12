#!/usr/bin/env python3
"""Guarda contra los saltos de los hooks de Git para PreToolUse (ADR-0008; VIC-18).

Bloquea, en las órdenes del agente, las formas conocidas de saltar o desviar los hooks
de Git que instala lefthook (docs/herramientas.md, "Formas de saltarlo"):

- --no-verify (y sus abreviaturas) en commit y merge; -n en commit;
- las variables que apagan o desvían lefthook o gitleaks;
- core.hooksPath, include o alias con git -c, --config-env o GIT_CONFIG_*, y PATH, HOME,
  XDG_CONFIG_HOME, GIT_CONFIG_GLOBAL o GIT_CONFIG_SYSTEM en una orden con git;
- escribir configuración de lefthook fuera de lefthook.json, .git/hooks, .git/config,
  .git/commondir, un fichero .git, la configuración global de Git o los ajustes de
  Claude Code, también con Write, Edit o NotebookEdit; y preguntar antes de cambiar
  lefthook.json, .gitleaks.toml o .gitleaksignore en el árbol de trabajo, porque lefthook
  y gitleaks los leen de ahí aunque el cambio no llegue a un commit;
- ocultar cambios con update-index o .git/info/exclude;
- escribir .git/info/attributes, perfiles de shell o ficheros llamados lefthook, gitleaks o python3
  (un atributo binary deja ciego a gitleaks; un perfil o un binario antes en el PATH
  sustituyen a los de verdad); y preguntar antes de cambiar .gitattributes;
- crear commits sin pasar por pre-commit: am, commit-tree, fast-import, un clon local,
  otro directorio de Git o gh api.

No bloquea merge, cherry-pick, revert ni rebase, que tampoco pasan por pre-commit: crean
commits con contenido que ya estaba en otro commit, y la CI repite los controles.

Es una segunda capa contra errores del agente, no un control de seguridad: lee el
texto de la orden, así que bash -c, eval, variables o scripts la esquivan. La autoridad
es la CI, que repite los controles. Las variables solo cuentan en la misma llamada:
el estado del shell no pasa de una llamada de Bash a la siguiente.

Las reglas, sus niveles y sus mensajes están en reglas-saltos.json. Si no puede mirar,
falla cerrado.
"""
import json
import os
import posixpath
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from lector_bash import (ASIGNACION, ENVOLTURAS, RESERVADAS, NoAnalizable, analizar_todo, juntar, opciones,
                             orden_efectiva)
    from lector_bash import nombres as _nombres
    ERROR_DE_CARGA = None
except Exception as e:  # Sin el lector, main() falla cerrado.
    ERROR_DE_CARGA = e

RUTA_REGLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglas-saltos.json")
ESCRITURA = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
DECLARAN = {"export", "declare", "typeset", "readonly", "local"}
OPCIONES_GLOBALES_CON_VALOR = {
    "-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env", "--attr-source",
}
OTRO_REPO = re.compile(r"(GIT_(DIR|WORK_TREE|INDEX_FILE|COMMON_DIR|OBJECT_DIRECTORY)=|--(git-dir|work-tree)(=|$))")
# Opciones de commit que se escriben con su valor pegado o aparte: -m "-n" no es -n.
CORTAS_CON_VALOR_COMMIT = "mFCct"
LARGAS_COMMIT_CON_VALOR = dict.fromkeys(
    ("reuse-message", "reedit-message", "fixup", "squash", "file", "author", "date", "message", "template",
     "trailer", "cleanup", "pathspec-from-file"), True)
LARGAS_CLONE_CON_VALOR = dict.fromkeys(
    ("template", "reference", "reference-if-able", "origin", "branch", "revision", "upload-pack", "depth",
     "shallow-since", "shallow-exclude", "separate-git-dir", "jobs", "server-option", "filter", "config",
     "bundle-uri"), True)
URL_REMOTA = re.compile(r"^([a-z][a-z0-9+.-]*://(?!/)|[\w.-]+@[^:/]+:|[\w.-]+\.[\w.-]+:(?!/))", re.I)
# git am crea commits sin pasar por pre-commit; estas formas no crean ninguno.
AM_SIN_COMMIT = {"--abort", "--quit", "--skip", "--show-current-patch"}
GH_API_CON_VALOR = dict.fromkeys(
    ("method", "field", "raw-field", "input", "header", "hostname", "jq", "template", "cache", "preview"), True)


def asignaciones(palabras):
    """Las asignaciones de variables de una orden simple: las de delante (A=1 orden),
    las de env y las de export, declare, typeset, readonly y local."""
    encontradas, i = [], 0
    while i < len(palabras):
        palabra = palabras[i]
        if ASIGNACION.match(palabra):
            encontradas.append(palabra)
            i += 1
        elif palabra in RESERVADAS:
            i += 1
        elif posixpath.basename(palabra) in ENVOLTURAS:
            con_valor, posicionales = ENVOLTURAS[posixpath.basename(palabra)]
            i += 1
            while i < len(palabras) and palabras[i].startswith("-") and palabras[i] != "-":
                i += 2 if palabras[i] in con_valor else 1
            i += posicionales
        else:
            break
    if i < len(palabras) and palabras[i] in DECLARAN:
        encontradas += [p for p in palabras[i + 1:] if ASIGNACION.match(p)]
    return [a.split("=", 1)[0].rstrip("+") for a in encontradas]


def separar_git(palabras):
    """(subcomando, argumentos, opciones globales) o None si no es git. También la forma
    con guion (/usr/lib/git-core/git-commit), que Git despacha por el nombre."""
    if not palabras:
        return None
    nombre = posixpath.basename(palabras[0])
    if nombre.startswith("git-") and len(nombre) > 4:
        return nombre[4:], palabras[1:], []
    if nombre not in ("git", "git.exe"):
        return None
    i, globales = 1, []
    while i < len(palabras) and palabras[i].startswith("-"):
        if palabras[i] in OPCIONES_GLOBALES_CON_VALOR and i + 1 < len(palabras):
            globales.append((palabras[i], palabras[i + 1]))
            i += 2
        else:
            globales.append((palabras[i], ""))
            i += 1
    if i >= len(palabras):
        return None
    return palabras[i], palabras[i + 1:], globales


def _ajustes(globales):
    """Las claves de configuración de git -c y --config-env, en minúsculas."""
    claves = []
    for opcion, valor in globales:
        if opcion == "-c" or opcion == "--config-env":
            claves.append(valor.split("=", 1)[0].lower())
        elif opcion.startswith("--config-env="):
            claves.append(opcion[len("--config-env="):].split("=", 1)[0].lower())
    return claves


def _no_verify(args, cortas_con_valor, largas_con_valor, con_n):
    """La forma que salta los hooks en estos argumentos, o None. Git acepta prefijos
    de las opciones largas: --no-veri es --no-verify."""
    encontradas, _ = opciones(args, cortas_con_valor, largas_con_valor, abreviadas=False)
    for nombre, _ in encontradas:
        if len(nombre) >= len("no-v") and "no-verify".startswith(nombre):
            return f"--{nombre}"
        if con_n and nombre == "n":
            return "-n"
    return None


def _clon_local(args):
    _, posicionales = opciones(args, "obucj", LARGAS_CLONE_CON_VALOR, abreviadas=False)
    if posicionales and not URL_REMOTA.match(posicionales[0]):
        return f"git clone {posicionales[0]}"
    return None


def _gh_api_crea_commit(args):
    encontradas, posicionales = opciones(args, "XfFHpqt", GH_API_CON_VALOR, abreviadas=False)
    texto = " ".join(posicionales + [v for _, v in encontradas])
    if re.search(r"/git/commits\b", texto) or "createCommitOnBranch" in texto:
        return "gh api (commit)"
    metodo = next((v.upper() for n, v in encontradas if n in ("X", "method")), None)
    escribe = metodo not in (None, "GET", "HEAD") or (metodo is None and _nombres(encontradas) & {
        "f", "F", "field", "raw-field", "input"})
    if escribe and any(re.search(r"/contents/", p) for p in posicionales):
        return "gh api (contents)"
    return None


def _regla_git(sub, args, globales, palabras, conf):
    for clave in _ajustes(globales):
        if re.match(conf["claves_de_hooks"], clave):
            return "config-de-hooks", f"git -c {clave}"
    if sub == "commit":
        forma = _no_verify(args, CORTAS_CON_VALOR_COMMIT, LARGAS_COMMIT_CON_VALOR, con_n=True)
        if forma:
            return "sin-verificar", f"git commit {forma}"
    if sub in ("merge", "pull"):
        # -S lleva su valor pegado (-S<clave>): no se come la palabra siguiente.
        forma = _no_verify(args, "msXF", {"strategy": True, "strategy-option": True, "message": True,
                                           "file": True, "gpg-sign": False}, con_n=False)
        if forma:
            return "sin-verificar", f"git {sub} {forma}"
    if sub == "am" and not set(args) & AM_SIN_COMMIT:
        return "commit-sin-hooks", "git am"
    if sub in ("commit", "merge") and (any(OTRO_REPO.match(p) for p in palabras)
                                            or any(o.startswith(("--git-dir", "--work-tree")) for o, _ in globales)):
        return "commit-sin-hooks", f"git {sub} en otro directorio de Git"
    if sub in ("commit-tree", "fast-import"):
        return "commit-sin-hooks", f"git {sub}"
    if sub == "clone":
        forma = _clon_local(args)
        if forma:
            return "commit-sin-hooks", forma
    if sub == "update-index":
        for a in args:
            for opcion in ("--skip-worktree", "--assume-unchanged"):
                if len(a) >= 4 and opcion.startswith(a):
                    return "ocultar-cambios", f"git update-index {opcion}"
    return None


def _casa(clave, ruta, conf):
    return bool(re.search(conf[clave], posixpath.normpath(ruta), re.I))


def _escribe_en(nombre, efectiva, conf):
    """Si una orden que nombra el fichero puede escribirlo: todas salvo las que solo leen,
    y de git, checkout, restore y mv."""
    if nombre in ("git", "git.exe"):
        separado = separar_git(efectiva)
        if not separado:
            return False
        sub, args, _ = separado
        return sub in conf["git_escritores"] or (sub == "rm" and "--cached" not in args)
    if nombre in ("sed", "perl"):
        args = efectiva[1:]
        return any(a.startswith("--in-place") or (a[:1] == "-" and a[1:2] != "-" and "i" in a[1:]) for a in args)
    return nombre not in conf["solo_leen"]


def _candidatas(palabra):
    candidatas = [palabra]
    _, igual, valor = palabra.partition("=")
    if igual and valor:
        candidatas.append(valor)
    return candidatas


def _fichero_protegido(ruta, conf):
    if _casa("config_local_lefthook", ruta, conf) or _casa("otra_config_lefthook", ruta, conf):
        return "config-local-lefthook"
    if _casa("exclude_de_git", ruta, conf) or _casa("ocultar_a_gitleaks", ruta, conf):
        return "ocultar-cambios"
    if _casa("hooks_y_config_de_git", ruta, conf):
        return "config-de-hooks"
    if _casa("ajustes_del_agente", ruta, conf) or _casa("entorno_del_agente", ruta, conf):
        return "ajustes-del-agente"
    if _casa("config_de_controles", ruta, conf):
        return "config-de-controles"
    return None


def _mas_grave(actual, nueva, conf):
    """La que bloquea gana a la que pregunta; entre iguales, la primera."""
    if actual[0] is None or (conf["reglas"][actual[0]]["nivel"] == "preguntar"
                             and conf["reglas"][nueva[0]]["nivel"] != "preguntar"):
        return nueva
    return actual


def _protegido_en(ruta, cwd, conf):
    """Como _fichero_protegido, también con la ruta resuelta contra la carpeta de la orden:
    tras cd .git, «commondir» es .git/commondir."""
    regla = _fichero_protegido(ruta, conf)
    if regla or cwd is None or "$" in ruta:
        return regla
    return _fichero_protegido(juntar(cwd, ruta), conf)


def decidir_bash(comando, conf, cwd=None):
    """Devuelve (regla, forma) o (None, None). cwd es la carpeta de la sesión; los cd de
    la orden la cambian."""
    relevante = re.search(r"\b(git|gh|lefthook|gitleaks)|LEFTHOOK|GITLEAKS|GIT_|\.git\b|commondir|\.claude/|"
                          r"attributes|\.bashrc|\.profile|\.zshrc", comando)
    if len(comando) > conf["max_caracteres_orden"]:
        return ("sin-analizar", "la orden") if relevante else (None, None)
    try:
        analisis = analizar_todo(comando)
    except NoAnalizable:
        return ("sin-analizar", "la orden") if relevante else (None, None)
    ordenes = analisis.ordenes
    con_git = any(separar_git(orden_efectiva(p)) for p in ordenes)
    variables_de_config = re.compile(conf["variables_de_config_git"])
    for palabras in ordenes:
        for variable in asignaciones(palabras):
            if variable in conf["variables_de_hooks"]:
                return "variables-de-hooks", variable
            if variables_de_config.match(variable):
                return "config-de-hooks", variable
            if con_git and variable in conf["variables_con_git"]:
                return "config-de-hooks", f"{variable} en una orden con git"
    candidata = (None, None)
    carpetas = []  # La carpeta en la que corre cada orden, siguiendo los cd.
    for palabras in ordenes:
        carpetas.append(cwd)
        efectiva = orden_efectiva(palabras)
        if efectiva[:1] == ["cd"]:
            destinos = [a for a in efectiva[1:] if not a.startswith("-")]
            sigue = cwd is not None and len(destinos) == 1 and "$" not in destinos[0] and destinos[0] != "-"
            cwd = juntar(cwd, destinos[0]) if sigue else None
    for indice, operador, destino in analisis.redirecciones:
        if ">" in operador:
            regla = _protegido_en(destino, carpetas[indice] if indice < len(carpetas) else cwd, conf)
            if regla:
                candidata = _mas_grave(candidata, (regla, destino), conf)
    for palabras, carpeta in zip(ordenes, carpetas):
        efectiva = orden_efectiva(palabras)
        if not efectiva:
            continue
        nombre = posixpath.basename(efectiva[0])
        separado = separar_git(efectiva)
        if separado:
            resultado = _regla_git(*separado, palabras, conf)
            if resultado:
                return resultado
        if nombre == "gh" and efectiva[1:2] == ["api"]:
            forma = _gh_api_crea_commit(efectiva[2:])
            if forma:
                return "commit-sin-hooks", forma
        if _escribe_en(nombre, efectiva, conf):
            for palabra in efectiva[1:]:
                for ruta in _candidatas(palabra):
                    regla = _protegido_en(ruta, carpeta, conf)
                    # Borrar una configuración de lefthook que sobra está bien.
                    if regla and not (nombre == "rm" and regla == "config-local-lefthook"):
                        candidata = _mas_grave(candidata, (regla, ruta), conf)
    return candidata



def decidir_fichero(herramienta, entrada, cwd, conf):
    if herramienta not in ESCRITURA:
        return None, None
    ruta = entrada.get("notebook_path") if herramienta == "NotebookEdit" else entrada.get("file_path")
    if not isinstance(ruta, str) or not ruta:
        raise ValueError("sin ruta")
    # Con la ruta resuelta también: un enlace a la configuración local no la esquiva.
    for candidata in (ruta, os.path.realpath(juntar(cwd, ruta))):
        regla = _fichero_protegido(candidata, conf)
        if regla:
            return regla, ruta
    return None, None


def decidir(datos, conf):
    herramienta, entrada = datos["tool_name"], datos["tool_input"]
    if herramienta == "Bash":
        return decidir_bash(entrada["command"], conf, os.path.normpath(datos.get("cwd") or os.getcwd()))
    return decidir_fichero(herramienta, entrada, os.path.normpath(datos.get("cwd") or os.getcwd()), conf)


def respuesta(decision, motivo):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": motivo}}


def main():
    try:
        if ERROR_DE_CARGA:
            raise ERROR_DE_CARGA
        with open(RUTA_REGLAS, encoding="utf-8") as f:
            conf = json.load(f)
        regla, forma = decidir(json.load(sys.stdin), conf)
        if regla is None:
            return
        info = conf["reglas"][regla]
        mensaje = info["mensaje"].replace("{forma}", forma)
        if info["nivel"] == "preguntar":
            salida = respuesta("ask", mensaje)
        else:
            salida = respuesta("deny", f'{mensaje} {conf["cierre"]}')
    except Exception as e:  # Si no puede mirar, falla cerrado (criterio 5 del inventario).
        salida = respuesta("deny", f"La guarda de saltos de hooks no ha podido comprobar esta llamada "
                                   f"({type(e).__name__}). Avisa a la persona; no la esquives.")
    json.dump(salida, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

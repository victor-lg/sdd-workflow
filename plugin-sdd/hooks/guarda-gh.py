#!/usr/bin/env python3
"""Guarda de órdenes de gh para PreToolUse sobre Bash (REG-43, REG-93, REG-102/M5; VIC-17).

- REG-43: gh pr create lleva --draft.
- REG-93: el cuerpo de PR, comentarios y revisiones va por --body-file, nunca en la
  orden (--body, -f body=, echo o un heredoc sin comillas delante de --body-file -).
- REG-102 y M5: gh pr ready solo con todos los checks del último commit en verde,
  ninguno cancelado ni pendiente, sin conflictos y con la rama local subida. Si no hay
  línea «Métricas G4» en el PR, pregunta. Es la única regla que usa la red: consulta
  el PR con gh, con las credenciales de gh de quien ejecuta Claude Code.

Es una segunda capa contra errores del agente, no un control de seguridad: lee el
texto de la orden, así que bash -c, eval, variables, gh api o scripts la esquivan.
Las reglas, sus niveles y sus mensajes están en reglas-gh.json. Si no puede mirar,
falla cerrado.
"""
import json
import os
import posixpath
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from lector_bash import NoAnalizable, analizar_todo, cambia_de_carpeta, juntar, nombres, opciones, orden_efectiva
    ERROR_DE_CARGA = None
except Exception as e:  # Sin el lector, main() falla cerrado.
    ERROR_DE_CARGA = e

RUTA_REGLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglas-gh.json")

# Opciones cortas que llevan valor en cada orden de gh que acepta un cuerpo.
CORTAS_CON_VALOR = {
    ("pr", "create"): "aBbFHlmprtTR", ("pr", "new"): "aBbFHlmprtTR",
    ("pr", "comment"): "bFR", ("pr", "edit"): "BbFtR", ("pr", "review"): "bFR", ("pr", "merge"): "bFtAR",
    ("issue", "create"): "abFlmptTR", ("issue", "new"): "abFlmptTR", ("issue", "comment"): "bFR",
    ("issue", "edit"): "bFtR", ("pr", "close"): "cR", ("issue", "close"): "cR",
}
# Opciones que llevan el cuerpo en la propia orden; en close, el comentario.
OPCIONES_CUERPO = {"b", "body"}
OPCIONES_CUERPO_CLOSE = {"c", "comment"}
VARIABLES_GH = re.compile(
    r"(GH_(REPO|HOST|CONFIG_DIR)|GITHUB_REPOSITORY|GIT_(DIR|WORK_TREE|COMMON_DIR|CEILING_DIRECTORIES|CONFIG\w*))(=|$)")
AYUDA = {"h", "help"}


def _falso(valor):
    return valor.lower() in ("false", "0", "f")
LARGAS_CON_VALOR = dict.fromkeys(
    ("assignee", "base", "body", "body-file", "head", "label", "milestone", "project", "reviewer", "title",
     "template", "repo", "recover", "add-assignee", "remove-assignee", "add-label", "remove-label",
     "add-project", "remove-project", "add-reviewer", "remove-reviewer", "subject", "author-email",
     "match-head-commit"), True)
CORTAS_API = "fFHXqtp"
LARGAS_API = dict.fromkeys(("field", "raw-field", "header", "method", "jq", "template", "input", "preview",
                            "hostname", "cache"), True)
MUTACION_READY = "markPullRequestReadyForReview"
# El hook corre fuera del sandbox y fuera de su lista de red: solo se pasa a gh un PR y
# un repo de github.com con forma conocida (G4 del PR #26).
SELECTOR = re.compile(r"^(\d+|https://github\.com/[\w.-]+/[\w.-]+/pull/\d+|[\w][\w./-]*)$")
REPO = re.compile(r"^((https://)?github\.com/)?[\w.-]+/[\w.-]+$")
GIT_SEGURO = ("-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", "--no-optional-locks")
NOMBRE_SEGURO = re.compile(r"[^\w .:/()-]")
# gh llama a git por su cuenta en la carpeta de la orden: con la misma protección.
ENTORNO_GH = {**os.environ, "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "core.fsmonitor",
              "GIT_CONFIG_VALUE_0": "false", "GIT_CONFIG_KEY_1": "core.untrackedCache",
              "GIT_CONFIG_VALUE_1": "false", "GIT_OPTIONAL_LOCKS": "0"}


class NoPuedoMirar(Exception):
    """gh no ha podido decir cómo está el PR."""


def _quedan(limite):
    return limite - time.monotonic()


def _gh(cwd, *args, conf, limite):
    if _quedan(limite) < 1:
        raise NoPuedoMirar("sin tiempo")
    try:
        r = subprocess.run(["gh", *args], cwd=cwd, capture_output=True, text=True, env=ENTORNO_GH,
                           timeout=min(conf["segundos_gh"], _quedan(limite)))
    except (OSError, subprocess.SubprocessError) as e:
        raise NoPuedoMirar(str(e))
    if r.returncode != 0:
        raise NoPuedoMirar(r.stderr.strip())
    return r.stdout


def _git(cwd, *args):
    """La salida de git, o None si no se puede saber (fuera de un repo, cabeza suelta…)."""
    try:
        r = subprocess.run(["git", *GIT_SEGURO, "-C", cwd, *args], capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def regla_create(grupo, accion, args):
    encontradas, _ = opciones(args, CORTAS_CON_VALOR[(grupo, accion)], LARGAS_CON_VALOR, abreviadas=False)
    if nombres(encontradas) & AYUDA:  # Como opción, no como valor de otra: la ayuda no crea nada.
        return None
    borrador = False
    for nombre, valor in encontradas:
        if nombre in ("d", "draft"):
            borrador = not _falso(valor)
    return None if borrador else "pr-sin-borrador"


def regla_cuerpo(grupo, accion, args, analisis, ordenes_previas):
    encontradas, _ = opciones(args, CORTAS_CON_VALOR[(grupo, accion)], LARGAS_CON_VALOR, abreviadas=False)
    if nombres(encontradas) & AYUDA:
        return None
    if nombres(encontradas) & (OPCIONES_CUERPO_CLOSE if accion == "close" else OPCIONES_CUERPO):
        return "cuerpo-en-la-orden"
    desde_entrada = any(n in ("F", "body-file") and v == "-" for n, v in encontradas)
    if desde_entrada and _cuerpo_por_la_entrada(analisis, ordenes_previas):
        return "cuerpo-en-la-orden"
    return None


def _cuerpo_por_la_entrada(analisis, ordenes_previas):
    return analisis.heredocs_expandidos or analisis.cadenas or ordenes_previas & {"echo", "printf"}


def regla_api(args, analisis, ordenes_previas):
    encontradas, _ = opciones(args, CORTAS_API, LARGAS_API, abreviadas=False)
    if any(MUTACION_READY in a for a in args):
        return "ready-por-api"
    if nombres(encontradas) & AYUDA:
        return None
    for nombre, valor in encontradas:
        clave, _, contenido = valor.partition("=")
        if nombre in ("f", "F", "field", "raw-field") and clave == "body":
            if not (nombre in ("F", "field") and contenido.startswith("@")):
                return "cuerpo-en-la-orden"
            if contenido == "@-" and _cuerpo_por_la_entrada(analisis, ordenes_previas):
                return "cuerpo-en-la-orden"
    return None


def _nombre_check(check):
    """El nombre llega al modelo en el mensaje: corto y sin caracteres raros."""
    return NOMBRE_SEGURO.sub("", str(check.get("name") or check.get("context") or "?"))[:60] or "?"


def _ultimos(checks):
    """La ejecución más reciente de cada check, que es la que mira GitHub."""
    ultimos = {}
    for check in checks:
        clave = (check.get("workflowName"), _nombre_check(check))
        fecha = check.get("startedAt") or ""
        if (not fecha or fecha.startswith("0001")) and check.get("status") not in (None, "COMPLETED"):
            fecha = "9999"  # En cola, sin fecha: es la más reciente.
        if clave not in ultimos or fecha >= ultimos[clave][0]:
            ultimos[clave] = (fecha, check)
    return [check for _, check in ultimos.values()]


def regla_ready(args, cwd, conf, limite, entorno_gh=False):
    """Devuelve (regla, checks implicados) o (None, None)."""
    encontradas, posicionales = opciones(args, "R", {"repo": True, "undo": False}, abreviadas=False)
    if nombres(encontradas) & AYUDA or any(n == "undo" and not _falso(v) for n, v in encontradas):
        return None, None
    encontradas = [(n, v) for n, v in encontradas if n != "undo"]  # --undo=false es quitar el borrador.
    repos = [v for n, v in encontradas if n in ("R", "repo")]
    if entorno_gh or "$" in cwd or len(posicionales) > 1 or not all(map(SELECTOR.match, posicionales)) or \
            len(repos) > 1 or not all(map(REPO.match, repos)) or nombres(encontradas) - {"R", "repo"}:
        return "ready-sin-mirar", None
    repo = ["--repo", repos[0]] if repos else []
    campos = "isDraft,headRefName,headRefOid,mergeable,statusCheckRollup,comments"
    try:
        pr = json.loads(_gh(cwd, "pr", "view", *repo, "--json", campos, "--", *posicionales,
                            conf=conf, limite=limite))
    except (NoPuedoMirar, ValueError):
        return "ready-sin-mirar", None
    if not pr.get("isDraft"):
        return None, None
    checks = pr.get("statusCheckRollup") or []
    if not checks:
        return "ready-sin-checks", None
    cancelados, rojos, pendientes = [], [], []
    for check in _ultimos(checks):
        if check.get("__typename") == "StatusContext" or "context" in check:
            estado = check.get("state")
            if estado in ("PENDING", "EXPECTED"):
                pendientes.append(_nombre_check(check))
            elif estado != "SUCCESS":
                rojos.append(_nombre_check(check))
        elif check.get("status") != "COMPLETED":
            pendientes.append(_nombre_check(check))
        elif check.get("conclusion") == "CANCELLED":
            ejecucion = re.search(r"/runs/(\d+)", check.get("detailsUrl") or "")
            cancelados.append(_nombre_check(check) + (f" (gh run rerun {ejecucion.group(1)})" if ejecucion else ""))
        elif check.get("conclusion") not in conf["conclusiones_buenas"]:
            rojos.append(_nombre_check(check))
    for regla, lista in (("ready-check-cancelado", cancelados), ("ready-ci-roja", rojos),
                         ("ready-ci-pendiente", pendientes)):
        if lista:
            return regla, sorted(set(lista))
    if pr.get("mergeable") == "CONFLICTING":
        return "ready-conflictos", None
    if not repo:  # Si el PR es el de la rama actual, la rama local tiene que estar subida.
        if _git(cwd, "symbolic-ref", "--short", "-q", "HEAD") == pr.get("headRefName") and \
                _git(cwd, "rev-parse", "HEAD") != pr.get("headRefOid"):
            return "ready-sin-push", None
    linea_g4 = re.compile(conf["linea_g4"], re.M)
    if not any(linea_g4.search(c.get("body") or "") for c in pr.get("comments") or []):
        return "ready-sin-g4", None
    return None, None


def decidir(comando, cwd, conf):
    """Devuelve (regla, checks) de la regla más grave, o (None, None)."""
    if len(comando) > conf["max_caracteres_orden"] and "gh" in comando:
        return "sin-analizar", None
    try:
        analisis = analizar_todo(comando)
    except NoAnalizable:
        return ("sin-analizar" if "gh" in comando else None), None
    candidata, previas = (None, None), set()
    limite = time.monotonic() + conf["max_segundos_analisis"]
    for palabras in analisis.ordenes:
        if _quedan(limite) < 0:  # Antes de que el timeout del hook deje pasar la orden.
            return "sin-analizar", None
        efectiva = orden_efectiva(palabras)
        primera = posixpath.basename(efectiva[0]) if efectiva else ""
        if primera in ("pushd", "popd"):
            cwd = "$"
        elif primera == "cd":
            destinos = [a for a in efectiva[1:] if not a.startswith("-")]
            cwd = juntar(cwd, destinos[0]) if len(destinos) == 1 and destinos[0] != "-" else "$"
        elif primera in ("gh", "gh.exe") and len(efectiva) >= 2:
            grupo, i, previas_accion = efectiva[1], 2, []
            # Opciones entre el grupo y la acción (gh pr -R o/r ready 54): cobra las admite.
            while grupo in ("pr", "issue") and i < len(efectiva) and efectiva[i].startswith("-"):
                salto = 2 if efectiva[i] in ("-R", "--repo") else 1
                previas_accion += efectiva[i:i + salto]
                i += salto
            accion, args = (efectiva[i:i + 1] or [""])[0], efectiva[i + 1:] + previas_accion
            resultado = (None, None)
            orden_cwd = "$" if cambia_de_carpeta(palabras) else cwd
            # GH_REPO y compañía, en cualquier parte de la orden (también con export), cambian
            # a qué repo o host pregunta gh: la consulta no sería la del PR.
            entorno_gh = any(VARIABLES_GH.match(p) for orden in analisis.ordenes for p in orden)
            if grupo == "api":
                resultado = (regla_api(efectiva[2:], analisis, previas), None)
            elif grupo == "pr" and accion == "ready":
                resultado = regla_ready(args, orden_cwd, conf, limite, entorno_gh)
            elif (grupo, accion) in CORTAS_CON_VALOR:
                regla = regla_cuerpo(grupo, accion, args, analisis, previas)
                if not regla and grupo == "pr" and accion in ("create", "new"):
                    regla = regla_create(grupo, accion, args)
                resultado = (regla, None)
            if resultado[0] and conf["reglas"][resultado[0]]["nivel"] != "preguntar":
                return resultado
            candidata = candidata if candidata[0] else resultado
        previas.add(primera)
    return candidata


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
        regla, checks = decidir(datos["tool_input"]["command"], datos.get("cwd") or os.getcwd(), conf)
        if regla is None:
            return
        info = conf["reglas"][regla]
        mensaje = info["mensaje"].replace("{checks}", ", ".join(checks or []))
        if info["nivel"] == "preguntar":
            salida = respuesta("ask", mensaje)
        else:
            salida = respuesta("deny", f'{mensaje} {conf["cierre"]}')
    except Exception as e:  # Si no puede mirar, falla cerrado (criterio 5 del inventario).
        salida = respuesta("deny", f"La guarda de gh no ha podido comprobar esta orden ({type(e).__name__}). "
                                   "Avisa a la persona; no la esquives.")
    json.dump(salida, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

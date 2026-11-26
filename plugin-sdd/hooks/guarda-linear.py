#!/usr/bin/env python3
"""Guarda del MCP de Linear para PreToolUse (REG-04; VIC-17, y ADR-0009 §3.6 y M4, VIC-58).

El agente lee issues, las comenta, las crea y las empieza; nunca las cierra, cancela,
borra ni archiva. El visto bueno de la persona es la sección «Entregas» de una spec en
main, a la que se llega por un merge que ella aprueba (CODEOWNERS de docs/specs/). De ahí
salen dos reglas:

- empezar una issue (moverla a Ready, In Progress o In Review) solo si su ID abre una línea
  de lista de esa sección en alguna spec de main;
- editar el título, la descripción o las etiquetas de una issue solo si su ID no está en
  ninguna: lo aprobado no lo cambia el agente.

Qué es «main» no lo decide el repo local, que el agente puede preparar (una referencia
origin/main movida, una rama o una etiqueta con ese nombre, otro repo con `cd`): el remoto
origin tiene que ser uno de los repos de `repos` en reglas-linear.json, y el commit de main
se pide con `git ls-remote` a la URL que fija ese fichero, no a la del repo. Las specs se
leen de ese commit, que tiene que estar ya en el repo local (si no, git fetch origin). Es la
única llamada con red; a git se le pasan las mismas opciones que en guarda-git.py para que
no ejecute nada de la configuración del repo.

Es una lista de permitidas: una herramienta, un campo o un estado que no conoce se bloquea,
también si el servidor añade uno nuevo. La issue se nombra por su identificador (VIC-12), no
por su UUID, que la guarda no puede buscar en las specs.

Se registra con un matcher sobre los nombres mcp__<servidor>__<herramienta> que contienen
"linear" (el MCP propio, el conector de claude.ai o el de un plugin). La API de Linear por
Bash no la mira: el sandbox no deja salir a linear.app.

Las reglas, los estados, los repos y los mensajes están en reglas-linear.json. Si no puede
mirar, falla cerrado.
"""
import json
import os
import re
import subprocess
import sys
import time

RUTA_REGLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglas-linear.json")
IDENTIFICADOR = re.compile(r"([A-Za-z][A-Za-z0-9]*)-(\d+)")
GIT_SEGURO = ("-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", "--no-optional-locks")
ORIGEN = re.compile(r"(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)([\w.-]+/[\w.-]+?)(?:\.git)?/?")
PLAZO = 15  # segundos para todas las llamadas a git; el hook tiene 20 en hooks.json


def clave(ident):
    """VIC-041 y vic-41 son la misma issue: ('VIC', 41). None si no es un identificador."""
    m = IDENTIFICADOR.fullmatch(str(ident).strip())
    return (m.group(1).upper(), int(m.group(2))) if m else None


def ids_de_entregas(texto):
    """Las claves de los IDs que abren una línea de lista (`- VIC-12: …`) en las secciones
    tituladas exactamente «Entregas» (con o sin número delante), hasta el siguiente título del
    mismo nivel o mayor. Lo que hay dentro de bloques de código no cuenta."""
    dentro, nivel, cerca, ids = False, 0, None, []
    for linea in texto.splitlines():
        bloque = re.match(r"\s{0,3}(`{3,}|~{3,})", linea)
        if bloque and (cerca is None or bloque.group(1)[0] == cerca[0] and len(bloque.group(1)) >= len(cerca)):
            cerca = None if cerca else bloque.group(1)
            continue
        if cerca:
            continue
        titulo = re.match(r"(#{1,6})\s+(.*?)\s*#*\s*$", linea)
        if titulo:
            n = len(titulo.group(1))
            if dentro and n <= nivel:
                dentro = False
            if re.fullmatch(r"(?:\d+(?:\.\d+)*\.?\s+)?Entregas", titulo.group(2), re.IGNORECASE):
                dentro, nivel = True, n
            continue
        item = re.match(r"\s*(?:[-*+]|\d+[.)])\s+(?:\*\*|`)?([A-Za-z][A-Za-z0-9]*-\d+)(?![\w-])", linea)
        if dentro and item:
            ids.append(clave(item.group(1)))
    return ids


class Git:
    def __init__(self):
        self.limite = time.monotonic() + PLAZO

    def __call__(self, *args, cwd=None, repo=None):
        restante = self.limite - time.monotonic()
        if restante <= 0:
            raise TimeoutError("git")
        orden = ["git", *GIT_SEGURO, *(["-C", repo] if repo else []), *args]
        r = subprocess.run(orden, capture_output=True, text=True, timeout=restante, cwd=cwd,
                           stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            raise RuntimeError(f"git {args[0]}: {r.stderr.strip()[:200]}")
        return r.stdout


def aprobadas_en_main(cwd, conf):
    """{clave: ruta de la spec} de las secciones «Entregas» de las specs del main de GitHub
    (sin las que empiezan por "_", que son plantillas y ejemplos)."""
    git = Git()
    raiz = git("rev-parse", "--show-toplevel", repo=cwd).strip()
    origen = ORIGEN.fullmatch(git("config", "--get", "remote.origin.url", repo=raiz).strip())
    url = origen and conf["repos"].get(origen.group(1).lower())
    if not url:
        raise LookupError("el remoto origin del clon no es uno de los repos de reglas-linear.json")
    # Desde la raíz del sistema y sin -C: la URL no pasa por insteadOf ni por la configuración de ningún repo.
    remoto = git("ls-remote", "--", url, "refs/heads/main", cwd=os.path.abspath(os.sep)).split()
    if len(remoto) != 2 or not re.fullmatch(r"[0-9a-f]{40,64}", remoto[0]):
        raise LookupError("main no está en el remoto")
    main = remoto[0]
    try:
        git("cat-file", "-e", f"{main}^{{commit}}", repo=raiz)
    except RuntimeError:
        raise LookupError(f"el main de GitHub ({main[:8]}) no está en el clon: haz git fetch origin") from None
    ids = {}
    for ruta in git("ls-tree", "-r", "-z", "--full-tree", "--name-only", main, "--", "docs/specs/",
                    repo=raiz).split("\0"):
        if not ruta.endswith(".md") or os.path.basename(ruta).startswith("_"):
            continue
        for k in ids_de_entregas(git("show", f"{main}:{ruta}", repo=raiz)):
            ids.setdefault(k, ruta)
    return ids


def clase_estado(estado, conf):
    """'libre', 'empezar', 'cerrar' o None si el estado no lo conoce (nombre, tipo o id)."""
    valor = str(estado).strip().lower()
    for clase, valores in conf["estados"].items():
        if valor in (v.lower() for v in valores):
            return clase
    return None


def decidir(nombre, entrada, conf, aprobadas):
    """Devuelve (id de la regla, contexto para el mensaje) o None. `aprobadas` es una
    función sin argumentos que devuelve las IDs de la lista aprobada; solo se llama si hace
    falta. Un comentario con id ya existe y puede ser de la persona: editarlo no es comentar."""
    partes = nombre.split("__")
    if len(partes) < 3 or partes[0] != "mcp" or conf["servidor"] not in partes[1].lower():
        return None
    herramienta = partes[-1]
    if re.search(conf["cerrar"], herramienta):
        return "cerrar", {}
    if re.match(r"(create|save)_comment$", herramienta):
        return ("herramienta", {}) if entrada.get("id") else None
    if not re.fullmatch(conf["issues"], herramienta):
        return None if re.search(conf["lecturas"], herramienta) else ("herramienta", {})

    issue = entrada.get("id")
    campos = set(entrada) - {"id"}
    permitidos = conf["campos_crear"] if issue is None else conf["campos_editar"] + ["state"]
    if campos - set(permitidos):
        return "desconocido", {"detalle": "el campo " + ", ".join(sorted(campos - set(permitidos)))}
    clase = None
    if "state" in entrada:
        clase = clase_estado(entrada["state"], conf)
        if clase is None:
            return "desconocido", {"detalle": f"el estado «{entrada['state']}»"}
        if clase == "cerrar":
            return "cerrar", {}
    if issue is None:
        return ("fuera-de-lista", {"issue": "nueva"}) if clase == "empezar" else None
    if not isinstance(issue, str) or clave(issue) is None:
        return "desconocido", {"detalle": f"la issue «{issue}» (usa su identificador, como VIC-12, no el UUID)"}
    if clase != "empezar" and not (campos & set(conf["campos_editar"])):
        return None
    spec = aprobadas().get(clave(issue))
    if clase == "empezar" and spec is None:
        return "fuera-de-lista", {"issue": issue}
    if campos & set(conf["campos_editar"]) and spec is not None:
        return "lista-aprobada", {"issue": issue, "spec": spec}
    return None


def respuesta(decision, motivo):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": motivo}}


def main():
    try:
        with open(RUTA_REGLAS, encoding="utf-8") as f:
            conf = json.load(f)
        datos = json.load(sys.stdin)
        nombre = datos["tool_name"]
        entrada = datos.get("tool_input") or {}
        if not isinstance(entrada, dict):
            raise TypeError("tool_input")
        cwd = datos.get("cwd") or os.getcwd()
        resultado = decidir(nombre, entrada, conf, lambda: aprobadas_en_main(cwd, conf))
        if resultado is None:
            return
        regla, contexto = resultado
        info = conf["reglas"][regla]
        decision = "ask" if info["nivel"] == "preguntar" else "deny"
        mensaje = info["mensaje"].replace("{herramienta}", nombre)
        for clave in ("issue", "spec", "detalle"):
            mensaje = mensaje.replace("{" + clave + "}", str(contexto.get(clave, "")))
        salida = respuesta(decision, mensaje)
    except Exception as e:  # Si no puede mirar, falla cerrado (criterio 5 del inventario).
        causa = str(e) if isinstance(e, LookupError) else type(e).__name__
        salida = respuesta("deny", f"La guarda de Linear no ha podido comprobar esta llamada ({causa}). "
                                   "Si es la lista aprobada: comprueba que estás en el clon del proyecto, que su "
                                   "origin es uno de los repos de reglas-linear.json y que tienes main al día "
                                   "(git fetch origin). Si no, avisa a la persona; no la esquives.")
    json.dump(salida, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

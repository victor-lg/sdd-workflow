#!/usr/bin/env python3
"""Guarda del MCP de Linear para PreToolUse (REG-04; VIC-17, y ADR-0009 §3.6 y M4, VIC-58).

El agente lee issues, las comenta, las crea y las empieza; nunca las cierra, cancela,
borra ni archiva. El visto bueno de la persona es la sección «Entregas» de una spec en
origin/main, a la que se llega por un merge que ella aprueba (CODEOWNERS de docs/specs/).
De ahí salen dos reglas:

- empezar una issue (moverla a Ready, In Progress o In Review) solo si su ID está en esa
  sección de alguna spec de origin/main;
- editar el título, la descripción o las etiquetas de una issue solo si su ID no está en
  ninguna: lo aprobado no lo cambia el agente.

Es una lista de permitidas: una herramienta, un campo o un estado que no conoce se bloquea,
también si el servidor añade uno nuevo. La issue se nombra por su identificador (VIC-12), no
por su UUID, que la guarda no puede buscar en las specs.

Se registra con un matcher sobre los nombres mcp__<servidor>__<herramienta> que contienen
"linear" (el MCP propio, el conector de claude.ai o el de un plugin). La API de Linear por
Bash no la mira: el sandbox no deja salir a linear.app.

Las reglas, los estados y los mensajes están en reglas-linear.json. Si no puede mirar, falla
cerrado.
"""
import json
import os
import re
import subprocess
import sys

RUTA_REGLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglas-linear.json")
IDENTIFICADOR = re.compile(r"[A-Za-z][A-Za-z0-9]*-\d+")


def secciones_entregas(texto):
    """Las líneas de las secciones cuyo título es «Entregas» (con o sin número delante),
    hasta el siguiente título del mismo nivel o mayor."""
    dentro, nivel, lineas = False, 0, []
    for linea in texto.splitlines():
        titulo = re.match(r"(#{1,6})\s+(.*)", linea)
        if titulo:
            n = len(titulo.group(1))
            if dentro and n <= nivel:
                dentro = False
            if re.fullmatch(r"(?:\d+(?:\.\d+)*\.?\s+)?Entregas\b.*", titulo.group(2).strip(), re.IGNORECASE):
                dentro, nivel = True, n
                continue
        if dentro:
            lineas.append(linea)
    return "\n".join(lineas)


def git(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=8)
    if r.returncode != 0:
        raise RuntimeError(f"git {args[0]}: {r.stderr.strip()[:200]}")
    return r.stdout


def aprobadas_en_main(cwd):
    """{ID en mayúsculas: ruta de la spec} de las secciones «Entregas» de las specs de
    origin/main (sin las que empiezan por "_", que son plantillas y ejemplos)."""
    ids = {}
    git(cwd, "rev-parse", "--verify", "--quiet", "origin/main^{commit}")
    for ruta in git(cwd, "ls-tree", "-r", "--name-only", "origin/main", "--", "docs/specs/").splitlines():
        if not ruta.endswith(".md") or os.path.basename(ruta).startswith("_"):
            continue
        for ident in re.findall(r"(?<![\w-])([A-Za-z][A-Za-z0-9]*-\d+)(?![\w-])",
                                secciones_entregas(git(cwd, "show", f"origin/main:{ruta}"))):
            ids.setdefault(ident.upper(), ruta)
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
    if not isinstance(issue, str) or not IDENTIFICADOR.fullmatch(issue.strip()):
        return "desconocido", {"detalle": f"la issue «{issue}» (usa su identificador, como VIC-12, no el UUID)"}
    if clase != "empezar" and not (campos & set(conf["campos_editar"])):
        return None
    lista = aprobadas()
    spec = lista.get(issue.strip().upper())
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
        resultado = decidir(nombre, entrada, conf, lambda: aprobadas_en_main(cwd))
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
        salida = respuesta("deny", f"La guarda de Linear no ha podido comprobar esta llamada ({type(e).__name__}). "
                                   "Si es la lista aprobada, comprueba que estás en el clon del proyecto y que "
                                   "origin/main existe (git fetch origin). Si no, avisa a la persona; no la esquives.")
    json.dump(salida, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

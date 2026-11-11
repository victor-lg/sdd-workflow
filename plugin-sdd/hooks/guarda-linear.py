#!/usr/bin/env python3
"""Guarda del MCP de Linear para PreToolUse (REG-04, decisión 1 del inventario; VIC-17).

El agente lee las issues y las comenta; crearlas, moverlas, etiquetarlas o editarlas
es de la persona. Es una lista de permitidas: una herramienta de Linear que no lee ni
comenta se bloquea, también si el servidor añade una nueva.

Se registra con un matcher sobre los nombres mcp__<servidor>__<herramienta> que
contienen "linear" (el MCP propio, el conector de claude.ai o el de un plugin). La
API de Linear por Bash no la mira: el sandbox no deja salir a linear.app.

Las reglas y su mensaje están en reglas-linear.json. Si no puede mirar, falla cerrado.
"""
import json
import os
import re
import sys

RUTA_REGLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglas-linear.json")


def decidir(nombre, entrada, conf):
    """Devuelve el id de la regla que incumple la herramienta, o None. Un comentario
    con id ya existe y puede ser de la persona: editarlo no es comentar."""
    partes = nombre.split("__")
    if len(partes) < 3 or partes[0] != "mcp" or conf["servidor"] not in partes[1].lower():
        return None
    if not re.search(conf["permitidas"], partes[-1]) or (re.match(r"(create|save)_comment$", partes[-1]) and entrada.get("id")):
        return "solo-comentar"
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
        regla = decidir(nombre, datos.get("tool_input") or {}, conf)
        if regla is None:
            return
        info = conf["reglas"][regla]
        decision = "ask" if info["nivel"] == "preguntar" else "deny"
        salida = respuesta(decision, info["mensaje"].replace("{herramienta}", nombre))
    except Exception as e:  # Si no puede mirar, falla cerrado (criterio 5 del inventario).
        salida = respuesta("deny", f"La guarda de Linear no ha podido comprobar esta llamada ({type(e).__name__}). "
                                   "Avisa a la persona; no la esquives.")
    json.dump(salida, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

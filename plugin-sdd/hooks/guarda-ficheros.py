#!/usr/bin/env python3
"""Guarda de ficheros para PreToolUse (X-02, REG-40, X-06/M12; VIC-17).

- X-02: no escribir, copiar, mover ni borrar ficheros .env*, salvo plantillas
  (.env.example…), ni con Write, Edit o NotebookEdit ni por Bash.
- REG-40: leerlos con Read o mencionarlos en otra orden de Bash pregunta a la persona.
- X-06 (M12): capturas y ficheros de trabajo dentro del repo, nunca en /tmp ni en
  $TMPDIR. Write, Edit y NotebookEdit no escriben ahí, y Bash no los menciona.

Cada guarda de ficheros lleva su pareja en Bash (criterio 3 del inventario). La de
Bash lee el texto de la orden: no sabe qué argumento es un fichero, así que mira
todos, y bash -c, eval, variables o scripts la esquivan. Es una segunda capa contra
errores del agente, no un control de seguridad. Tampoco mira el contenido de lo que
se escribe: un test que guarda una captura en /tmp pasa.

Las reglas, sus niveles y sus mensajes están en reglas-ficheros.json. Si no puede
mirar, falla cerrado.
"""
import json
import os
import posixpath
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from lector_bash import NoAnalizable, analizar_todo, juntar, orden_efectiva
    ERROR_DE_CARGA = None
except Exception as e:  # Sin el lector, main() falla cerrado.
    ERROR_DE_CARGA = e

RUTA_REGLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglas-ficheros.json")
ESCRITURA = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def es_env(ruta, conf):
    nombre = posixpath.basename(ruta.rstrip("/"))
    return bool(re.match(conf["env"]["patron"], nombre)) and not re.search(conf["env"]["excepciones"], nombre)


def es_temporal(ruta, cwd, conf):
    """Si la ruta cae en una carpeta temporal fuera del proyecto. Las rutas con otra
    variable no se pueden resolver y no cuentan."""
    temporales = conf["temporales"]
    if re.match(temporales["variables"], ruta):
        return True
    if "$" in ruta:
        return False
    completa = juntar(cwd, ruta)
    if completa == cwd or completa.startswith(cwd.rstrip("/") + "/"):
        return False
    return any(completa == c or completa.startswith(c + "/") for c in temporales["carpetas"])


def _candidatas(palabra):
    """La palabra y, si lleva =, lo que va detrás (--path=/tmp/x, of=/tmp/x)."""
    _, igual, valor = palabra.partition("=")
    return [palabra, valor] if igual and valor else [palabra]


def decidir_bash(comando, cwd, conf):
    """Devuelve (regla, fichero) de la regla más grave, o (None, None)."""
    if len(comando) > conf["max_caracteres_orden"]:
        return "sin-analizar", "la orden"
    try:
        analisis = analizar_todo(comando)
    except NoAnalizable:
        menciona = ".env" in comando or "TMP" in comando or "TEMP" in comando or any(
            c in comando for c in conf["temporales"]["carpetas"])
        return ("sin-analizar", "la orden") if menciona else (None, None)
    candidata = (None, None)
    redirecciones = {}
    for indice, operador, destino in analisis.redirecciones:
        redirecciones.setdefault(indice, []).append((operador, destino))
    for indice in range(max([len(analisis.ordenes)] + [i + 1 for i in redirecciones])):
        efectiva = orden_efectiva(analisis.ordenes[indice]) if indice < len(analisis.ordenes) else []
        nombre = posixpath.basename(efectiva[0]) if efectiva else ""
        for operador, destino in redirecciones.get(indice, []):
            if es_temporal(destino, cwd, conf):
                return "temporal", destino
            if es_env(destino, conf):
                if ">" in operador:
                    return "env-escribe", destino
                candidata = candidata if candidata[0] else ("env-lee", destino)
        for palabra in efectiva[1:]:
            for ruta in _candidatas(palabra):
                if nombre not in conf["temporales"]["solo_citan"] and es_temporal(ruta, cwd, conf):
                    return "temporal", ruta
                if nombre not in conf["env"]["solo_citan"] and es_env(ruta, conf):
                    if nombre in conf["env"]["escritores"]:
                        return "env-escribe", ruta
                    candidata = candidata if candidata[0] else ("env-lee", ruta)
    return candidata


def decidir_fichero(herramienta, entrada, cwd, conf):
    ruta = entrada.get("notebook_path") if herramienta == "NotebookEdit" else entrada.get("file_path")
    if not isinstance(ruta, str) or not ruta:
        raise ValueError("sin ruta")
    if herramienta in ESCRITURA:
        if es_env(ruta, conf):
            return "env-escribe", ruta
        if es_temporal(ruta, cwd, conf):
            return "temporal", ruta
    elif herramienta == "Read" and es_env(ruta, conf):
        return "env-lee", ruta
    return None, None


def decidir(datos, conf):
    herramienta, entrada = datos["tool_name"], datos["tool_input"]
    cwd = os.path.normpath(datos.get("cwd") or os.getcwd())
    if herramienta == "Bash":
        return decidir_bash(entrada["command"], cwd, conf)
    return decidir_fichero(herramienta, entrada, cwd, conf)


def respuesta(decision, motivo):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": motivo}}


def main():
    try:
        if ERROR_DE_CARGA:
            raise ERROR_DE_CARGA
        with open(RUTA_REGLAS, encoding="utf-8") as f:
            conf = json.load(f)
        regla, fichero = decidir(json.load(sys.stdin), conf)
        if regla is None:
            return
        info = conf["reglas"][regla]
        mensaje = info["mensaje"].replace("{fichero}", fichero)
        if info["nivel"] == "preguntar":
            salida = respuesta("ask", mensaje)
        else:
            salida = respuesta("deny", f'{mensaje} {conf["cierre"]}')
    except Exception as e:  # Si no puede mirar, falla cerrado (criterio 5 del inventario).
        salida = respuesta("deny", f"La guarda de ficheros no ha podido comprobar esta llamada ({type(e).__name__}). "
                                   "Avisa a la persona; no la esquives.")
    json.dump(salida, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

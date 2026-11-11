#!/usr/bin/env python3
"""Guarda de ficheros para PreToolUse (X-02, REG-40, X-06/M12; VIC-17).

- X-02: no escribir, copiar, mover ni borrar ficheros .env*, salvo plantillas
  (.env.example…), ni con Write, Edit o NotebookEdit ni por Bash.
- REG-40: leerlos con Read o Grep o mencionarlos en otra orden de Bash pregunta a la persona.
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
    if cwd != "/" and (completa == cwd or completa.startswith(cwd + "/")):
        return False
    return any(completa == c or completa.startswith(c + "/") for c in temporales["carpetas"])


def _candidatas(palabra):
    """La palabra; si lleva =, lo que va detrás (--path=/tmp/x, of=/tmp/x); y si es una
    opción corta con el valor pegado, el valor (-o/tmp/x)."""
    candidatas = [palabra]
    _, igual, valor = palabra.partition("=")
    if igual and valor:
        candidatas.append(valor)
    if len(palabra) > 2 and palabra[0] == "-" and palabra[1] != "-":
        candidatas.append(palabra[2:])
    return candidatas


def _escribe(nombre, efectiva, conf):
    """Si la orden escribe en los ficheros que nombra: sed y perl solo con -i, y de git,
    rm, mv, restore y checkout salvo los que solo tocan el índice."""
    env, args = conf["env"], efectiva[1:]
    if nombre in env["escritores_con_i"]:
        return any(a.startswith("--in-place") or (a[:1] == "-" and a[1:2] != "-" and "i" in a[1:]) for a in args)
    if nombre in ("git", "git.exe"):
        i = 0
        while i < len(args) and args[i].startswith("-"):
            i += 2 if args[i] in ("-C", "-c") else 1
        sub = args[i] if i < len(args) else ""
        return sub in env["git_escritores"] and not set(args[i:]) & set(env["git_solo_indice"])
    return nombre in env["escritores"]


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
        escribe = bool(efectiva) and _escribe(nombre, efectiva, conf)
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
                if es_env(ruta, conf):
                    if escribe:
                        return "env-escribe", ruta
                    if nombre not in conf["env"]["solo_citan"]:
                        candidata = candidata if candidata[0] else ("env-lee", ruta)
    return candidata


def decidir_fichero(herramienta, entrada, cwd, conf):
    if herramienta == "Grep":  # Con output_mode content, Grep devuelve el contenido.
        for clave in ("path", "glob"):
            valor = entrada.get(clave)
            if isinstance(valor, str) and es_env(valor, conf):
                return "env-lee", valor
        return None, None
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

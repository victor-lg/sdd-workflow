#!/usr/bin/env python3
"""Línea de estado de Claude Code que, además, guarda las métricas de cada sesión.

Workflow SDD + IA, v0.23 (mejora M9 de historial/recorrido-2.md); v1.1 lee las ramas
<tipo>/vic-N-… de docs/convenciones.md (ADR-0007) y cuenta lo que pasa en la
conversación (medición del plan v1.1, VIC-16).

Claude Code ejecuta este script cada vez que actualiza la línea de estado y le pasa
por la entrada estándar un JSON con los datos de la sesión. El script:

1. guarda un resumen de la sesión en <carpeta>/sesiones/<session_id>.json; cada
   actualización sobrescribe la anterior, así que el último estado es el final;
2. imprime una línea corta: modelo, coste estimado, duración y rama.

Qué guarda: identificador, fechas, versión de Claude Code, modelos usados, coste
estimado (precio de API, no lo que descuenta la suscripción), duraciones, líneas
cambiadas, tokens, pico de uso del contexto, repo, rama e issue de Linear deducida
de la rama. Del transcript de la sesión guarda solo recuentos:

- intervenciones humanas: cada mensaje escrito por la persona, el primero incluido;
  no cuentan resultados de herramientas, mensajes internos, resúmenes de
  compactación, salida de comandos locales, avisos de tareas ni interrupciones;
- G4: las líneas "Métricas G4: PR #N · ronda R · confirmados X · descartados Y ·
  corregidos Z" que escribe sdd-review, una por PR y ronda (la última manda);
- mutación: la última línea "Métricas mutación: detectados X de Y" de sdd-implement.

Las dos líneas solo cuentan en el texto del asistente, solas en su línea. El
transcript se lee por partes: el JSON de la sesión guarda hasta qué byte se ha
leído. No guarda el contenido de la conversación ni rutas fuera del proyecto
(del transcript, solo el nombre del fichero).

No lee nada aparte de lo que le pasa Claude Code, el transcript que le indica y la
rama de Git del proyecto.
Corre fuera del sandbox porque lo lanza Claude Code, no el agente; por eso solo
escribe en su carpeta. Si algo falla, imprime la línea igualmente y no guarda nada.

Carpeta: la variable SDD_METRICAS_DIR o, si no está,
/mnt/c/Users/victor/Documents/sdd-metricas (C:\\Users\\victor\\Documents\\sdd-metricas).
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime

CARPETA = os.environ.get("SDD_METRICAS_DIR", "/mnt/c/Users/victor/Documents/sdd-metricas")
# Rama de convenciones.md (feat/vic-16-…) o del formato anterior (vic-10-…).
ISSUE = re.compile(r"^(?:[a-z]+/)?vic-(\d+)\b", re.I)
# Líneas de formato fijo de sdd-review y sdd-implement (docs en cada skill).
LINEA_G4 = re.compile(r"^[ \t]*Métricas G4: PR #(\d+) · ronda (\d+) · confirmados (\d+) · "
                      r"descartados (\d+) · corregidos (\d+)[ \t]*$", re.M)
LINEA_MUTACION = re.compile(r"^[ \t]*Métricas mutación: detectados (\d+) de (\d+)[ \t]*$", re.M)
# Mensajes de tipo "user" que no escribe la persona, en transcripts sin "origin".
NO_HUMANO = ("<local-command-", "<command-name>", "<task-notification>", "<system-reminder>",
             "This session is being continued")


def g(d, *claves, defecto=None):
    """Lee d[c1][c2]... sin fallar si falta algo."""
    for c in claves:
        if not isinstance(d, dict) or c not in d:
            return defecto
        d = d[c]
    return d if d is not None else defecto


def rama(directorio):
    if not directorio:
        return None
    try:
        # symbolic-ref funciona también en un repo sin commits; en HEAD suelto no hay rama.
        r = subprocess.run(["git", "-C", directorio, "symbolic-ref", "--short", "-q", "HEAD"],
                           capture_output=True, text=True, timeout=1)
        return r.stdout.strip() or None if r.returncode == 0 else None
    except Exception:
        return None


def issue_de(nombre):
    # Solo cuenta el ID del team de Linear: spec-calc-003-... no es una issue.
    m = ISSUE.match(nombre or "")
    return f"VIC-{m.group(1)}" if m else None


def texto_de(contenido):
    """Texto de un mensaje: una cadena o la lista de bloques de la API."""
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        return "\n".join(b.get("text") or "" for b in contenido
                         if isinstance(b, dict) and b.get("type") == "text")
    return ""


def es_intervencion(e):
    """True si la entrada del transcript es un mensaje escrito por la persona."""
    if e.get("type") != "user" or e.get("isSidechain") or e.get("isMeta") \
            or e.get("isCompactSummary") or "toolUseResult" in e:
        return False
    contenido = g(e, "message", "content")
    if isinstance(contenido, list) and any(isinstance(b, dict) and b.get("type") == "tool_result"
                                           for b in contenido):
        return False
    texto = texto_de(contenido).lstrip()
    if texto.startswith("[Request interrupted") or texto.startswith("<local-command-"):
        return False
    origen = e.get("origin")
    if isinstance(origen, dict):
        # Claude Code marca así lo que escribe la persona; "peer" y las tareas no cuentan.
        return origen.get("kind") == "human"
    if texto.startswith(NO_HUMANO):
        return False
    # Una imagen sin texto también es un mensaje de la persona.
    return bool(texto) or (isinstance(contenido, list) and bool(contenido))


def lee_transcript(ruta, antes):
    """Lee lo nuevo del transcript desde el byte guardado y devuelve los recuentos."""
    nombre = os.path.basename(ruta)
    desde = int(antes.get("transcript_leido") or 0)
    estado = {
        "intervenciones": int(antes.get("intervenciones") or 0),
        "g4": dict(antes.get("g4") or {}),
        "mutacion": antes.get("mutacion"),
    }
    if antes.get("transcript") != nombre or os.path.getsize(ruta) < desde:
        # Otro fichero o uno reescrito: se cuenta desde el principio.
        desde, estado = 0, {"intervenciones": 0, "g4": {}, "mutacion": None}
    with open(ruta, "rb") as f:
        f.seek(desde)
        bloque = f.read()
    # Una línea a medio escribir se deja para la próxima vez.
    bloque = bloque[:bloque.rfind(b"\n") + 1]
    for linea in bloque.decode("utf-8", errors="replace").splitlines():
        try:
            e = json.loads(linea)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        if es_intervencion(e):
            estado["intervenciones"] += 1
        elif e.get("type") == "assistant" and not e.get("isSidechain"):
            texto = texto_de(g(e, "message", "content"))
            fecha = e.get("timestamp")
            for m in LINEA_G4.finditer(texto):
                pr, ronda, conf, desc, corr = (int(x) for x in m.groups())
                estado["g4"][f"{pr}/{ronda}"] = {"pr": pr, "ronda": ronda, "confirmados": conf,
                                                 "descartados": desc, "corregidos": corr,
                                                 "fecha": fecha}
            for m in LINEA_MUTACION.finditer(texto):
                estado["mutacion"] = {"detectados": int(m.group(1)), "total": int(m.group(2)),
                                      "fecha": fecha}
    estado["transcript"] = nombre
    estado["transcript_leido"] = desde + len(bloque)
    return estado


def guarda(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(ruta), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ruta)


def main():
    try:
        e = json.load(sys.stdin)
    except Exception:
        print("sdd-metricas: sin datos")
        return

    sid = g(e, "session_id")
    proyecto = g(e, "workspace", "project_dir") or g(e, "cwd")
    r = rama(proyecto)
    modelo = g(e, "model", "display_name") or g(e, "model", "id") or "?"
    coste = float(g(e, "cost", "total_cost_usd", defecto=0) or 0)
    dur = int(g(e, "cost", "total_duration_ms", defecto=0) or 0)
    ahora = datetime.now().astimezone().isoformat(timespec="seconds")

    # Línea de estado: se imprime pase lo que pase con el guardado.
    minutos = dur // 60000
    print(f"{modelo} · ${coste:.2f} · {minutos} min" + (f" · {r}" if r else ""))

    if not sid or not os.path.isdir(os.path.dirname(CARPETA.rstrip("/")) or "/"):
        return  # la unidad o la carpeta padre no existe: no se crea nada fuera de lugar
    ruta = os.path.join(CARPETA, "sesiones", re.sub(r"[^A-Za-z0-9_-]", "_", sid) + ".json")
    try:
        with open(ruta, encoding="utf-8") as f:
            antes = json.load(f)
    except Exception:
        antes = {}

    cw = g(e, "context_window", defecto={}) or {}
    tam = g(cw, "context_window_size", defecto=0) or 0
    uso = g(cw, "current_usage", defecto={}) or {}
    en_contexto = sum(int(uso.get(k) or 0) for k in
                      ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    pico = max(float(antes.get("contexto_pico_pct") or 0), round(100 * en_contexto / tam, 1) if tam else 0)
    modelos = list(dict.fromkeys((antes.get("modelos") or []) + [modelo]))
    ramas = list(dict.fromkeys((antes.get("ramas") or []) + ([r] if r else [])))
    issues = list(dict.fromkeys((antes.get("issues") or []) + ([issue_de(r)] if issue_de(r) else [])))

    datos = {
        "session_id": sid,
        "inicio": antes.get("inicio") or ahora,
        "ultima_actualizacion": ahora,
        "claude_code": g(e, "version"),
        "repo": os.path.basename(proyecto.rstrip("/")) if proyecto else None,
        "ramas": ramas,
        "issues": issues,
        "modelos": modelos,
        "coste_estimado_usd": round(coste, 4),
        "duracion_min": round(dur / 60000, 1),
        "duracion_api_min": round(int(g(e, "cost", "total_api_duration_ms", defecto=0) or 0) / 60000, 1),
        "lineas_anadidas": g(e, "cost", "total_lines_added", defecto=0),
        "lineas_quitadas": g(e, "cost", "total_lines_removed", defecto=0),
        "tokens_entrada": g(cw, "total_input_tokens", defecto=0),
        "tokens_salida": g(cw, "total_output_tokens", defecto=0),
        "contexto_pico_pct": pico,
        "estilo_salida": g(e, "output_style", "name"),
    }
    # Recuentos de la conversación; si el transcript falla, se conservan los anteriores.
    conversacion = {k: antes[k] for k in ("transcript", "transcript_leido", "intervenciones",
                                          "g4", "mutacion") if k in antes}
    transcript = g(e, "transcript_path")
    if transcript:
        try:
            conversacion = lee_transcript(transcript, antes)
        except Exception:
            pass
    datos.update(conversacion)
    try:
        guarda(ruta, datos)
    except Exception:
        pass


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Línea de estado de Claude Code que, además, guarda las métricas de cada sesión.

Workflow SDD + IA, v0.23 (mejora M9 de historial/recorrido-2.md).

Claude Code ejecuta este script cada vez que actualiza la línea de estado y le pasa
por la entrada estándar un JSON con los datos de la sesión. El script:

1. guarda un resumen de la sesión en <carpeta>/sesiones/<session_id>.json; cada
   actualización sobrescribe la anterior, así que el último estado es el final;
2. imprime una línea corta: modelo, coste estimado, duración y rama.

Qué guarda: identificador, fechas, versión de Claude Code, modelos usados, coste
estimado (precio de API, no lo que descuenta la suscripción), duraciones, líneas
cambiadas, tokens, pico de uso del contexto, repo, rama e issue de Linear deducida
de la rama. No guarda el contenido de la conversación ni rutas fuera del proyecto.

No lee nada aparte de lo que le pasa Claude Code y de la rama de Git del proyecto.
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
ISSUE = re.compile(r"\b([a-z]{2,10})-(\d+)\b", re.I)


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
    # Ramas como vic-10-calculo o spec-calc-003-...: solo se toma el prefijo del team de Linear.
    m = ISSUE.match(nombre or "")
    return f"{m.group(1).upper()}-{m.group(2)}" if m and m.group(1).lower() == "vic" else None


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
    try:
        guarda(ruta, datos)
    except Exception:
        pass


if __name__ == "__main__":
    main()

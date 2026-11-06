#!/usr/bin/env python3
"""Resume en Markdown las sesiones guardadas por sdd-metricas.py.

Uso: python3 resumen-metricas.py <carpeta-sdd-metricas> [desde AAAA-MM-DD]
                                 [--defectos <fichero.csv>]

Saca dos tablas: una fila por sesión y los totales por issue de Linear (o por rama
si la sesión no tiene issue). El coste es una estimación a precio de API.

Por issue, además: rondas de G4, hallazgos confirmados, descartados y corregidos,
la última puntuación de mutación, intervenciones humanas y defectos escapados (M10).
Una misma ronda de un PR que aparezca en varias sesiones cuenta una vez (la última).

Los defectos escapados no salen de las sesiones, sino de Linear: las issues con la
etiqueta "defecto-escapado". --defectos recibe un CSV con las columnas issue y
origen (la issue del defecto y la issue cuya entrega lo dejó pasar), exportado de
Linear o mantenido en el repo, por ejemplo historial/defectos-escapados.csv. Cada
defecto se atribuye a su issue de origen; "ID" vale como nombre de la columna issue.
"""
import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

ID = re.compile(r"^vic-\d+$", re.I)


def lee_defectos(ruta):
    """Devuelve ({issue de origen: nº de defectos}, [defectos sin origen válido])."""
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = csv.DictReader(f)
        columnas = {(c or "").strip().lower(): c for c in filas.fieldnames or []}
        col_issue = columnas.get("issue") or columnas.get("id")
        col_origen = columnas.get("origen")
        if not col_issue or not col_origen:
            sys.exit(f"{ruta}: faltan las columnas issue (o ID) y origen")
        por_origen, sin_origen = Counter(), []
        for fila in filas:
            defecto = (fila.get(col_issue) or "").strip().upper()
            origen = (fila.get(col_origen) or "").strip().upper()
            if not defecto:
                continue
            if ID.match(origen):
                por_origen[origen] += 1
            else:
                sin_origen.append(defecto)
    return por_origen, sin_origen


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("carpeta")
    p.add_argument("desde", nargs="?", default="")
    p.add_argument("--defectos")
    a = p.parse_args(argv)

    sesiones = []
    for ruta in glob.glob(os.path.join(a.carpeta, "sesiones", "*.json")):
        try:
            with open(ruta, encoding="utf-8") as f:
                s = json.load(f)
        except Exception:
            continue
        if (s.get("inicio") or "") >= a.desde:
            sesiones.append(s)
    sesiones.sort(key=lambda s: s.get("inicio") or "")

    print("| Inicio | Repo | Issue / rama | Modelos | Coste est. | Min (API) | Líneas +/− | Contexto pico | Interv. |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    tot = defaultdict(lambda: {"n": 0, "coste": 0.0, "min": 0.0, "interv": 0, "mutacion": None})
    rondas = {}  # (repo, pr, ronda) -> (clave, ronda de G4); gana la de fecha más reciente
    for s in sesiones:
        clave = ", ".join(s.get("issues") or []) or ", ".join(s.get("ramas") or []) or "—"
        print(f"| {(s.get('inicio') or '')[:16].replace('T', ' ')} | {s.get('repo') or '—'} | {clave} | "
              f"{', '.join(s.get('modelos') or [])} | ${s.get('coste_estimado_usd', 0):.2f} | "
              f"{s.get('duracion_min', 0)} ({s.get('duracion_api_min', 0)}) | "
              f"+{s.get('lineas_anadidas', 0)}/−{s.get('lineas_quitadas', 0)} | {s.get('contexto_pico_pct', 0)} % | "
              f"{s.get('intervenciones', 0)} |")
        t = tot[clave]
        t["n"] += 1
        t["coste"] += s.get("coste_estimado_usd", 0) or 0
        t["min"] += s.get("duracion_min", 0) or 0
        t["interv"] += s.get("intervenciones", 0) or 0
        m = s.get("mutacion")
        if m and (not t["mutacion"] or (m.get("fecha") or "") >= (t["mutacion"].get("fecha") or "")):
            t["mutacion"] = m
        for r in (s.get("g4") or {}).values():
            k = (s.get("repo"), r.get("pr"), r.get("ronda"))
            if k not in rondas or (r.get("fecha") or "") >= (rondas[k][1].get("fecha") or ""):
                rondas[k] = (clave, r)

    g4 = defaultdict(lambda: [0, 0, 0, 0])  # rondas, confirmados, descartados, corregidos
    for clave, r in rondas.values():
        x = g4[clave]
        x[0] += 1
        x[1] += r.get("confirmados", 0) or 0
        x[2] += r.get("descartados", 0) or 0
        x[3] += r.get("corregidos", 0) or 0

    defectos, sin_origen = lee_defectos(a.defectos) if a.defectos else (Counter(), [])
    for origen in defectos:
        tot[origen]  # una issue con defectos aparece aunque no tenga sesiones en el periodo

    print("\n| Issue / rama | Sesiones | Coste est. | Minutos | Intervenciones | Rondas G4 | "
          "Confirmados | Descartados | Corregidos | Última mutación | Defectos escapados |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for clave, t in sorted(tot.items()):
        rd, conf, desc, corr = g4[clave] if clave in g4 else (0, 0, 0, 0)
        m = t["mutacion"]
        mut = f"{m.get('detectados')} de {m.get('total')}" if m else "—"
        esc = defectos.get(clave, 0) if a.defectos else "—"
        print(f"| {clave} | {t['n']} | ${t['coste']:.2f} | {t['min']:.0f} | {t['interv']} | {rd} | "
              f"{conf} | {desc} | {corr} | {mut} | {esc} |")
    print(f"\nTotal: {len(sesiones)} sesiones, ${sum(t['coste'] for t in tot.values()):.2f} estimados.")
    if sin_origen:
        print(f"Defectos sin issue de origen: {', '.join(sin_origen)}.")


if __name__ == "__main__":
    main()

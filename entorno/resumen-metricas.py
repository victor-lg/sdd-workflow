#!/usr/bin/env python3
"""Resume en Markdown las sesiones guardadas por sdd-metricas.py.

Uso: python3 resumen-metricas.py <carpeta-sdd-metricas> [desde AAAA-MM-DD]

Saca dos tablas: una fila por sesión y los totales por issue de Linear (o por rama
si la sesión no tiene issue). El coste es una estimación a precio de API.
"""
import glob
import json
import os
import sys
from collections import defaultdict


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    carpeta, desde = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "")
    sesiones = []
    for p in glob.glob(os.path.join(carpeta, "sesiones", "*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                s = json.load(f)
        except Exception:
            continue
        if (s.get("inicio") or "") >= desde:
            sesiones.append(s)
    sesiones.sort(key=lambda s: s.get("inicio") or "")

    print("| Inicio | Repo | Issue / rama | Modelos | Coste est. | Min (API) | Líneas +/− | Contexto pico |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    tot = defaultdict(lambda: [0, 0.0, 0.0])
    for s in sesiones:
        clave = ", ".join(s.get("issues") or []) or ", ".join(s.get("ramas") or []) or "—"
        print(f"| {(s.get('inicio') or '')[:16].replace('T', ' ')} | {s.get('repo') or '—'} | {clave} | "
              f"{', '.join(s.get('modelos') or [])} | ${s.get('coste_estimado_usd', 0):.2f} | "
              f"{s.get('duracion_min', 0)} ({s.get('duracion_api_min', 0)}) | "
              f"+{s.get('lineas_anadidas', 0)}/−{s.get('lineas_quitadas', 0)} | {s.get('contexto_pico_pct', 0)} % |")
        t = tot[clave]
        t[0] += 1; t[1] += s.get("coste_estimado_usd", 0) or 0; t[2] += s.get("duracion_min", 0) or 0

    print("\n| Issue / rama | Sesiones | Coste est. | Minutos |")
    print("| --- | --- | --- | --- |")
    for clave, (n, c, m) in sorted(tot.items()):
        print(f"| {clave} | {n} | ${c:.2f} | {m:.0f} |")
    print(f"\nTotal: {len(sesiones)} sesiones, ${sum(t[1] for t in tot.values()):.2f} estimados.")


if __name__ == "__main__":
    main()

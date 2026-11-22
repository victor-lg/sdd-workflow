#!/usr/bin/env python3
"""Resume en Markdown las sesiones guardadas por sdd-metricas.py.

Uso: python3 resumen-metricas.py <carpeta-sdd-metricas> [desde AAAA-MM-DD]
                                 [--defectos <fichero.csv>]

Saca dos tablas: una fila por sesión y los totales por issue de Linear (o por rama
si la sesión no tiene issue). El coste es una estimación a precio de API.

Por issue, además: rondas de G4, hallazgos confirmados, descartados y corregidos,
la última puntuación de mutación, intervenciones humanas y defectos escapados (M10).
Una misma ronda de un PR que aparezca en varias sesiones de la issue cuenta una vez
(la última), y un mensaje copiado al reanudar una sesión, también; por eso, en una
sesión reanudada, la suma de intervenciones de la primera tabla puede pasar de la
de la segunda. G4 y mutación se atribuyen a la issue de la rama en la que se
escribió su línea (o, en sesiones anteriores, a la de la sesión): una revisión
lanzada desde main sale en la fila de main.

Si una sesión usó sdd-review en una issue y esa issue no tiene ninguna ronda de G4,
la tabla marca "⚠ sin línea" en vez de 0; lo mismo con sdd-implement y la mutación
(una entrega sin mutaciones lo dice con "Métricas mutación: sin mutaciones").
Así se distingue "no hubo hallazgos" de "la skill no anotó la línea".

Revisores de G4 (VIC-48): de las líneas "Métricas revisor" de sdd-review, dos tablas
más. Una fila por PR, ronda y revisor, con el formato de la §2 de
historial/coste-revision-bloque-4.md: tokens (entrada, caché y salida), salida,
minutos, coste estimado y hallazgos confirmados por gravedad y descartados. Y los
totales por issue y revisor. Una misma ronda de un revisor cuenta una vez (la
última). El coste sale de PRECIOS, a precio de API; un modelo sin precio deja la
celda en "?" y no suma. Si sdd-metricas no encontró el transcript del subagente,
sus tokens, minutos y coste salen como "—".

Los defectos escapados no salen de las sesiones, sino de Linear: las issues con la
etiqueta "defecto-escapado". --defectos recibe un CSV con las columnas issue y
origen (la issue del defecto y la issue cuya entrega lo dejó pasar), exportado de
Linear o mantenido en el repo, por ejemplo historial/defectos-escapados.csv. Cada
defecto se atribuye a su issue de origen y cuenta una vez; "ID" vale como nombre de
la columna issue. La exportación de Linear no trae la columna origen: se añade a
mano. Si el CSV tiene una columna Labels, solo cuentan las filas con la etiqueta
defecto-escapado. Los defectos no se filtran por fecha. El separador puede ser coma
o punto y coma.
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
SIN_LINEA = "⚠ sin línea"
# Dólares por millón de tokens: entrada, salida y lectura de caché. La escritura de
# caché, a 1,25 veces la entrada. Los de historial/coste-revision-bloque-4.md, §1.
PRECIOS = {"claude-opus-5-5": (4, 20, 0.20), "claude-sonnet-5-5": (2, 10, 0.10)}
GRAVEDADES = ("debe", "importante", "menor")


def coste_de(tokens):
    """Coste estimado de {modelo: tokens}, o None si algún modelo no tiene precio."""
    total = 0.0
    for modelo, t in tokens.items():
        if modelo not in PRECIOS:
            return None
        entrada, salida, lectura = PRECIOS[modelo]
        total += (t.get("entrada", 0) * entrada + t.get("salida", 0) * salida + t.get("cache_lectura", 0) * lectura
                  + t.get("cache_escritura", 0) * entrada * 1.25) / 1e6
    return total


def miles(n, decimales=0):
    """196 k, 8,1 k o 1,5 M, como en las tablas del historial."""
    if round(n / 1000, decimales) >= 1000:  # 999 600 es 1,0 M, no 1000 k
        return f"{n / 1e6:.1f} M".replace(".", ",")
    return f"{n / 1000:.{decimales}f} k".replace(".", ",")


def coma(x, decimales):
    return f"{x:.{decimales}f}".replace(".", ",")


def tabla_revisores(revisores):
    """Las dos tablas de revisores: una fila por PR, ronda y revisor, y por issue y revisor."""
    print("\n| Issue | PR | Ronda | Revisor | Modelo | Tokens | Salida | Min | Coste est. | "
          "Confirmados (deb. / imp. / men.) | Descartados |")
    print("| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |")
    total = {"tokens": 0, "min": 0.0, "coste": 0.0, "conf": [0, 0, 0], "desc": 0}
    por_issue = defaultdict(lambda: {"rondas": 0, "modelos": [], "tokens": 0, "min": 0.0, "coste": 0.0,
                                     "conf": [0, 0, 0], "desc": 0})
    sin_precio, sin_transcript = set(), 0
    for (clave, pr, ronda, letra), r in sorted(revisores.items(), key=lambda x: tuple(map(str, x[0]))):
        consumo = r.get("consumo") if isinstance(r.get("consumo"), dict) else None
        tokens = consumo.get("tokens") or {} if consumo else {}
        # El modelo del transcript (claude-sonnet-5-5); el alias de la línea (sonnet), solo sin él.
        modelos = ", ".join(tokens) or r.get("modelo") or "—"
        conf = [int((r.get("confirmados") or {}).get(g) or 0) for g in GRAVEDADES]
        desc = sum(int((r.get("descartados") or {}).get(g) or 0) for g in GRAVEDADES)
        t = por_issue[(clave, letra)]
        t["rondas"] += 1
        t["modelos"] = list(dict.fromkeys(t["modelos"] + list(tokens)))
        t["alias"] = list(dict.fromkeys(t.get("alias", []) + [r.get("modelo") or "—"]))
        if consumo:
            n = sum(sum(x.values()) for x in tokens.values())
            salida = sum(x.get("salida", 0) for x in tokens.values())
            minutos = consumo.get("minutos") or 0
            coste = coste_de(tokens)
            celdas = [miles(n), miles(salida, 1), coma(minutos, 1), "?" if coste is None else f"{coma(coste, 2)} $"]
            for d in (t, total):
                d["tokens"] += n
                d["min"] += minutos
                d["coste"] += coste or 0
            if coste is None:
                sin_precio.update(m for m in tokens if m not in PRECIOS)
        else:
            celdas = ["—"] * 4
            sin_transcript += 1
        for d in (t, total):
            d["conf"] = [a + b for a, b in zip(d["conf"], conf)]
            d["desc"] += desc
        print(f"| {clave} | #{pr} | {ronda} | {celda(letra)} | {celda(modelos)} | {' | '.join(celdas)} | "
              f"{' / '.join(map(str, conf))} | {desc} |")
    print(f"| **Total ({len(revisores)} ronda{'' if len(revisores) == 1 else 's'})** | | | | | **{miles(total['tokens'])}** | | "
          f"**{coma(total['min'], 1)}** | **{coma(total['coste'], 2)} $** | **{' / '.join(map(str, total['conf']))}** | "
          f"**{total['desc']}** |")
    if sin_precio:
        print(f"\n?: sin precio para {', '.join(sorted(sin_precio))} en PRECIOS; no suma al total.")
    if sin_transcript:
        print(f"\n—: {sin_transcript} sin el transcript del subagente; no suman al total.")

    print("\n| Issue | Revisor | Modelo | Rondas | Tokens | Min | Coste est. | "
          "Confirmados (deb. / imp. / men.) | Descartados |")
    print("| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |")
    for (clave, letra), t in sorted(por_issue.items()):
        modelos = ", ".join(t["modelos"] or t["alias"])
        print(f"| {clave} | {celda(letra)} | {celda(modelos)} | {t['rondas']} | {miles(t['tokens'])} | "
              f"{coma(t['min'], 1)} | {coma(t['coste'], 2)} $ | {' / '.join(map(str, t['conf']))} | {t['desc']} |")


def lee_defectos(ruta):
    """Devuelve ({issue de origen: nº de defectos}, [defectos sin origen válido])."""
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        cabecera = f.readline()
        f.seek(0)
        # Excel con configuración regional española exporta con punto y coma.
        separador = ";" if cabecera.count(";") > cabecera.count(",") else ","
        filas = csv.DictReader(f, delimiter=separador)
        columnas = {(c or "").strip().lower(): c for c in filas.fieldnames or []}
        col_issue = columnas.get("issue") or columnas.get("id")
        col_origen = columnas.get("origen")
        col_etiquetas = columnas.get("labels") or columnas.get("etiquetas")
        if not col_issue or not col_origen:
            sys.exit(f"{ruta}: faltan las columnas issue (o ID) y origen")
        por_origen, sin_origen, vistos = Counter(), [], set()
        for fila in filas:
            defecto = (fila.get(col_issue) or "").strip().upper()
            origen = (fila.get(col_origen) or "").strip().upper()
            if not defecto or defecto in vistos:
                continue
            if col_etiquetas:
                # Una fila con campos de más deja una lista en la clave None: aquí no llega.
                etiquetas = str(fila.get(col_etiquetas) or "")
                if "defecto-escapado" not in {x.strip().lower() for x in etiquetas.split(",")}:
                    continue
            vistos.add(defecto)
            if ID.match(origen):
                por_origen[origen] += 1
            else:
                sin_origen.append(defecto)
    return por_origen, sin_origen


def celda(texto):
    # Ramas, repos y modelos los puede crear el agente: un | descuadraría la tabla.
    return str(texto).replace("|", "\\|")


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
    tot = defaultdict(lambda: {"n": 0, "coste": 0.0, "min": 0.0, "interv": 0, "ids": set(),
                               "mutacion": None})
    # (clave, pr, ronda) -> ronda de G4; gana la de fecha más reciente. La clave es la
    # issue y no el repo, que es el nombre de la carpeta y cambia en cada worktree.
    rondas = {}
    revisores = {}  # (clave, pr, ronda, letra) -> revisor; gana el de fecha más reciente
    usos = defaultdict(set)  # clave -> skills con métricas usadas en esa issue
    for s in sesiones:
        clave = celda(", ".join(s.get("issues") or []) or ", ".join(s.get("ramas") or []) or "—")
        print(f"| {(s.get('inicio') or '')[:16].replace('T', ' ')} | {celda(s.get('repo') or '—')} | {clave} | "
              f"{celda(', '.join(s.get('modelos') or []))} | ${s.get('coste_estimado_usd', 0):.2f} | "
              f"{s.get('duracion_min', 0)} ({s.get('duracion_api_min', 0)}) | "
              f"+{s.get('lineas_anadidas', 0)}/−{s.get('lineas_quitadas', 0)} | {s.get('contexto_pico_pct', 0)} % | "
              f"{s.get('intervenciones', 0)} |")
        t = tot[clave]
        t["n"] += 1
        t["coste"] += s.get("coste_estimado_usd", 0) or 0
        t["min"] += s.get("duracion_min", 0) or 0
        ids = s.get("intervenciones_ids") or []
        t["ids"].update(ids)
        # Las intervenciones sin uuid (o de sesiones anteriores a la v1.1) se suman tal cual.
        t["interv"] += max(0, (s.get("intervenciones", 0) or 0) - len(ids))
        m = s.get("mutacion")
        if m:
            tm = tot[m.get("issue") or clave]
            if not tm["mutacion"] or (m.get("fecha") or "") >= (tm["mutacion"].get("fecha") or ""):
                tm["mutacion"] = m
        for skill, issues in (s.get("skills") or {}).items():
            for iss in issues or [None]:
                usos[iss or clave].add(skill)
                tot[iss or clave]  # la fila existe aunque no haya otra cosa
        for r in (s.get("g4") or {}).values():
            k = (r.get("issue") or clave, r.get("pr"), r.get("ronda"))
            if k not in rondas or (r.get("fecha") or "") >= (rondas[k].get("fecha") or ""):
                rondas[k] = r
        for r in (s.get("revisores") or {}).values():
            if not isinstance(r, dict):
                continue
            k = (r.get("issue") or clave, r.get("pr"), r.get("ronda"), r.get("revisor"))
            if k not in revisores or (r.get("fecha") or "") >= (revisores[k].get("fecha") or ""):
                revisores[k] = r

    g4 = defaultdict(lambda: [0, 0, 0, 0])  # rondas, confirmados, descartados, corregidos
    for (clave, _, _), r in rondas.items():
        tot[clave]  # una issue con rondas aparece aunque sus sesiones sean de otra rama
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
    marcas = False
    for clave, t in sorted(tot.items()):
        rd, conf, desc, corr = g4[clave] if clave in g4 else (0, 0, 0, 0)
        if not rd and "sdd-review" in usos[clave]:
            rd, conf, desc, corr = SIN_LINEA, "—", "—", "—"
        m = t["mutacion"]
        mut = ("sin mutaciones" if m.get("sin_mutaciones") else f"{m.get('detectados')} de {m.get('total')}") if m else (
            SIN_LINEA if "sdd-implement" in usos[clave] else "—")
        esc = defectos.get(clave, 0) if a.defectos else "—"
        marcas = marcas or SIN_LINEA in (rd, mut)
        print(f"| {clave} | {t['n']} | ${t['coste']:.2f} | {t['min']:.0f} | {t['interv'] + len(t['ids'])} | {rd} | "
              f"{conf} | {desc} | {corr} | {mut} | {esc} |")
    if marcas:
        print(f"\n{SIN_LINEA}: se usó sdd-review (G4) o sdd-implement (mutación) en esa issue y no hay "
              "ninguna línea de métricas válida en un gh pr comment.")
    if revisores:
        tabla_revisores(revisores)
    print(f"\nTotal: {len(sesiones)} sesiones, ${sum(t['coste'] for t in tot.values()):.2f} estimados.")
    if sin_origen:
        print(f"Defectos sin issue de origen: {', '.join(sin_origen)}.")


if __name__ == "__main__":
    main()

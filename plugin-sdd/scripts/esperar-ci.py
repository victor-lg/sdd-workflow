#!/usr/bin/env python3
"""Espera a que termine la CI de un PR y dice cómo ha acabado (VIC-69).

Uso: python3 esperar-ci.py <PR> [--repo dueño/repo] [--intervalo S] [--max S]

Consulta con `gh api` los check runs y los estados del commit de la cabeza del PR, cada `--intervalo`
segundos (30 por defecto), hasta que todos terminan, y lo confirma con una consulta más, por si un
workflow arranca tarde. Un run con conclusión cuenta como terminado aunque GitHub lo siga dando
en curso, como pasa a veces. Si la cabeza cambia (otro push), sigue con la nueva. No usa `gh pr checks` ni
`--jq`, que cambian entre versiones de gh: solo la API REST.

Escribe todo en la salida estándar, también los errores de gh, y termina siempre con una línea que
empieza por «CI » y uno de estos códigos de salida:

  0  verde: todos los checks terminaron bien (success, neutral o skipped);
  1  rojo: alguno falló, se canceló o se agotó (M5: un cancelado no es verde);
  2  error: falló la consulta (gh, la red, la API) o los argumentos;
  3  tiempo agotado: pasó `--max` segundos (45 min por defecto) con checks sin terminar.

El agente lo lanza con Bash en segundo plano, para que el sistema lo despierte al terminar.
"""
import argparse
import json
import subprocess
import sys
import time

VERDE = {"success", "neutral", "skipped"}
TRANSITORIO = ("HTTP 5", "HTTP 429", "timeout", "timed out", "connection", "EOF", "TLS", "temporarily")
REINTENTOS = 3


class ErrorConsulta(Exception):
    def __init__(self, texto, transitorio):
        super().__init__(texto)
        self.transitorio = transitorio


def gh_api(ruta):
    """Devuelve la lista de documentos JSON de `gh api --paginate`, que los concatena sin separador."""
    orden = ["gh", "api", "-H", "Accept: application/vnd.github+json", "--paginate", ruta]
    try:
        r = subprocess.run(orden, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        raise ErrorConsulta("no encuentro gh en el PATH", False)
    except subprocess.TimeoutExpired:
        raise ErrorConsulta(f"gh api {ruta}: sin respuesta en 60 s (timeout)", True)
    if r.returncode != 0:
        texto = (r.stderr.strip() or r.stdout.strip() or f"código {r.returncode}")
        transitorio = any(t.lower() in texto.lower() for t in TRANSITORIO)
        raise ErrorConsulta(f"gh api {ruta}: {texto}", transitorio)
    docs, dec, i, s = [], json.JSONDecoder(), 0, r.stdout
    while True:
        while i < len(s) and s[i].isspace():
            i += 1
        if i >= len(s):
            return docs
        try:
            doc, i = dec.raw_decode(s, i)
        except ValueError:
            raise ErrorConsulta(f"gh api {ruta}: la respuesta no es JSON: {s[:200]!r}", False)
        docs.append(doc)


def consultar(repo, pr):
    """Lee la cabeza del PR y sus checks. Devuelve (sha, checks), con checks como [(nombre, estado, conclusión)]."""
    try:
        pull = gh_api(f"repos/{repo}/pulls/{pr}")[0]
        sha = pull["head"]["sha"]
        checks = []
        for doc in gh_api(f"repos/{repo}/commits/{sha}/check-runs?per_page=100"):
            for c in doc["check_runs"]:
                # GitHub deja a veces un run en «in_progress» con su conclusión y su hora de fin ya puestas
                # (osv-scanner en calculadora-discos#114): con conclusión, ha terminado.
                conclusion = c.get("conclusion")
                checks.append((c["name"], "completed" if conclusion else c["status"], conclusion))
        # Los estados de la API antigua (los que no son de Actions). Sin ninguno, `state` es «pending»: no cuenta.
        for doc in gh_api(f"repos/{repo}/commits/{sha}/status?per_page=100"):
            for e in doc["statuses"]:
                terminado = e["state"] != "pending"
                checks.append((e["context"], "completed" if terminado else "pending", e["state"] if terminado else None))
    except (KeyError, IndexError, TypeError) as e:
        raise ErrorConsulta(f"la respuesta de la API no tiene la forma esperada ({e!r})", False)
    return sha, checks


def resumen(checks):
    return ", ".join(f"{n} ({c or s})" for n, s, c in sorted(checks))


def esperar(repo, pr, intervalo, maximo, reloj=time.monotonic, dormir=time.sleep):
    inicio = reloj()
    sha_previo, terminados_previos, fallos, visto = None, None, 0, None
    while True:
        try:
            sha, checks = consultar(repo, pr)
            fallos = 0
        except ErrorConsulta as e:
            fallos += 1
            print(f"Error al consultar la CI: {e}", flush=True)
            if not e.transitorio or fallos >= REINTENTOS:
                motivo = "" if not e.transitorio else f" ({fallos} intentos)"
                print(f"CI error{motivo}: no sé cómo ha acabado; mira el PR #{pr} a mano.", flush=True)
                return 2
            dormir(intervalo)
            continue
        if sha != sha_previo:
            if sha_previo is not None:
                print(f"La cabeza cambió: {sha_previo[:12]} → {sha[:12]}. Espero a la CI del commit nuevo.", flush=True)
            else:
                print(f"PR #{pr}, cabeza {sha[:12]}.", flush=True)
            sha_previo, terminados_previos = sha, None
        pendientes = [c for c in checks if c[1] != "completed"]
        estado = (len(checks), len(pendientes))
        if estado != visto:
            if not checks:
                print("La CI aún no ha empezado en este commit.", flush=True)
            else:
                print(f"{len(checks) - len(pendientes)} de {len(checks)} checks terminados.", flush=True)
            visto = estado
        if checks and not pendientes:
            nombres = sorted(checks)
            if nombres == terminados_previos:
                malos = [c for c in checks if c[2] not in VERDE]
                if malos:
                    print(f"CI rojo en {sha[:12]}: {resumen(malos)}. Resto: {len(checks) - len(malos)} en verde.", flush=True)
                    return 1
                print(f"CI verde en {sha[:12]}: {len(checks)} checks ({resumen(checks)}).", flush=True)
                return 0
            terminados_previos = nombres
        else:
            terminados_previos = None
        if reloj() - inicio >= maximo:
            falta = resumen(pendientes) if checks else "ningún check ha empezado"
            print(f"CI tiempo agotado tras {int(reloj() - inicio)} s en {sha[:12]}: sin terminar {falta}.", flush=True)
            return 3
        dormir(intervalo)


def main(argv=None):
    p = argparse.ArgumentParser(description="Espera a que termine la CI de un PR (VIC-69).")
    p.add_argument("pr", help="número del PR")
    p.add_argument("--repo", default="{owner}/{repo}", help="dueño/repo; por defecto, el del directorio actual")
    p.add_argument("--intervalo", type=float, default=30, help="segundos entre consultas (30)")
    p.add_argument("--max", type=float, default=2700, help="segundos como máximo (2700, 45 min)")
    try:
        a = p.parse_args(argv)
    except SystemExit as e:
        if e.code:
            print("CI error: argumentos no válidos.", flush=True)
            return 2
        return 0
    pr = a.pr.lstrip("#")
    if not pr.isdigit() or a.intervalo < 0 or a.max < 0:
        print(f"CI error: argumentos no válidos (PR {a.pr!r}, intervalo {a.intervalo}, max {a.max}).", flush=True)
        return 2
    return esperar(a.repo, pr, a.intervalo, a.max)


if __name__ == "__main__":
    sys.exit(main())

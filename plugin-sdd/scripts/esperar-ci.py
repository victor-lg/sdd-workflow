#!/usr/bin/env python3
"""Espera a que termine la CI de un PR y dice cómo ha acabado (VIC-69).

Uso: python3 esperar-ci.py <PR> [--repo dueño/repo] [--intervalo S] [--max S]

Consulta con `gh api` los check runs y los estados del commit de la cabeza del PR, cada `--intervalo`
segundos (30 por defecto), hasta que todos terminan, y lo confirma con una consulta más, por si un
workflow arranca tarde. Si la cabeza cambia (otro push), sigue con la nueva. No usa `gh pr checks` ni
`--jq`, que cambian entre versiones de gh: solo la API REST.

- **Solo el último run de cada workflow** (y evento) en ese commit: los check runs de un run anterior
  (el del borrador, uno cancelado por `cancel-in-progress`) no cuentan. En calculadora-discos#114, el
  `checks-sdd` en rojo del run de borrador seguía en el commit junto al verde del run de `ready_for_review`.
- **Fuera de borrador, los checks requeridos de la rama base** (reglas `required_status_checks`) tienen
  que existir: tras `gh pr ready`, el commit ya tiene en verde los checks del borrador, y sin esto el
  script daría verde antes de que aparezca el run completo (el check `tests` de la calculadora solo
  existe en ese run).
- Un workflow cuyo último run no tiene check runs (falló antes de crear jobs) cuenta con su conclusión.
- Un run con conclusión cuenta como terminado aunque GitHub lo siga dando en curso, como pasa a veces.

Escribe todo en la salida estándar, también los errores de gh, y termina siempre con una línea que
empieza por «CI » y uno de estos códigos de salida:

  0  verde: todos los checks terminaron bien (success, neutral o skipped);
  1  rojo: alguno falló, se canceló o se agotó (M5: un cancelado no es verde);
  2  error: falló la consulta (gh, la red, la API) o los argumentos;
  3  tiempo agotado: pasó `--max` segundos (45 min por defecto) con checks sin terminar o sin aparecer.

El agente lo lanza con Bash en segundo plano, para que el sistema lo despierte al terminar.
"""
import argparse
import json
import math
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


def estado_de(estado, conclusion):
    # GitHub deja a veces un run en «in_progress» con su conclusión y su hora de fin ya puestas
    # (osv-scanner en calculadora-discos#114): con conclusión, ha terminado.
    return "completed" if conclusion else estado


def consultar(repo, pr):
    """Lee la cabeza del PR y sus checks. Devuelve (sha, nombre del repo, checks), con checks como
    [(nombre, estado, conclusión)]; un check requerido que aún no existe va con el estado «falta»."""
    try:
        pull = gh_api(f"repos/{repo}/pulls/{pr}")[0]
        sha, nombre = pull["head"]["sha"], pull["base"]["repo"]["full_name"]
        # El último run de cada workflow y evento; las suites de los anteriores no cuentan.
        ultimos, suites = {}, {}
        for doc in gh_api(f"repos/{repo}/actions/runs?head_sha={sha}&per_page=100"):
            for w in doc["workflow_runs"]:
                clave = (w["workflow_id"], w["event"])
                if clave not in ultimos or (w["created_at"], w["id"]) > (ultimos[clave]["created_at"], ultimos[clave]["id"]):
                    ultimos[clave] = w
                suites[w["check_suite_id"]] = False
        for w in ultimos.values():
            suites[w["check_suite_id"]] = True
        checks, con_runs = [], set()
        for doc in gh_api(f"repos/{repo}/commits/{sha}/check-runs?per_page=100"):
            for c in doc["check_runs"]:
                suite = (c.get("check_suite") or {}).get("id")
                if suites.get(suite) is False:
                    continue
                con_runs.add(suite)
                checks.append((c["name"], estado_de(c["status"], c.get("conclusion")), c.get("conclusion")))
        for w in ultimos.values():
            if w["check_suite_id"] not in con_runs:
                checks.append((f"workflow {w['name']}", estado_de(w["status"], w.get("conclusion")), w.get("conclusion")))
        # Los estados de la API antigua (los que no son de Actions). Sin ninguno, `state` es «pending»: no cuenta.
        for doc in gh_api(f"repos/{repo}/commits/{sha}/status?per_page=100"):
            for e in doc["statuses"]:
                terminado = e["state"] != "pending"
                checks.append((e["context"], "completed" if terminado else "pending", e["state"] if terminado else None))
        if not pull["draft"]:
            hay = {c[0] for c in checks}
            for doc in gh_api(f"repos/{repo}/rules/branches/{pull['base']['ref']}?per_page=100"):
                for regla in doc:
                    if regla["type"] == "required_status_checks":
                        for r in regla["parameters"]["required_status_checks"]:
                            if r["context"] not in hay:
                                checks.append((r["context"], "falta", None))
                                hay.add(r["context"])
    except (KeyError, IndexError, TypeError) as e:
        raise ErrorConsulta(f"la respuesta de la API no tiene la forma esperada ({e!r})", False)
    return sha, nombre, checks


def resumen(checks):
    return ", ".join(f"{n} ({c or s})" for n, s, c in sorted(checks))


def esperar(repo, pr, intervalo, maximo, reloj=time.monotonic, dormir=time.sleep):
    inicio = reloj()
    sha_previo, terminados_previos, fallos, visto = None, None, 0, None
    while True:
        try:
            sha, nombre, checks = consultar(repo, pr)
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
                print(f"PR #{pr} de {nombre}, cabeza {sha[:12]}.", flush=True)
            sha_previo, terminados_previos = sha, None
        pendientes = [c for c in checks if c[1] != "completed"]
        estado = (len(checks), len(pendientes))
        if estado != visto:
            if not checks:
                print("La CI aún no ha empezado en este commit.", flush=True)
            else:
                print(f"{len(checks) - len(pendientes)} de {len(checks)} checks terminados.", flush=True)
            visto = estado
        confirmando = bool(checks) and not pendientes
        if confirmando:
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
        # Con todo terminado, la consulta de confirmación se hace aunque se haya pasado el tope.
        if not confirmando and reloj() - inicio >= maximo:
            falta = resumen(pendientes) if checks else "ningún check ha empezado"
            print(f"CI tiempo agotado tras {int(reloj() - inicio)} s en {sha[:12]}: sin terminar o sin aparecer {falta}.", flush=True)
            return 3
        dormir(intervalo)


class Argumentos(argparse.ArgumentParser):
    def error(self, mensaje):
        # Por la salida estándar, como todo lo demás, y con la línea final.
        print(f"{self.prog}: {mensaje}\nCI error: argumentos no válidos.", flush=True)
        sys.exit(2)


def main(argv=None):
    p = Argumentos(description="Espera a que termine la CI de un PR (VIC-69).")
    p.add_argument("pr", help="número del PR")
    p.add_argument("--repo", default="{owner}/{repo}", help="dueño/repo; por defecto, el del directorio actual")
    p.add_argument("--intervalo", type=float, default=30, help="segundos entre consultas (30)")
    p.add_argument("--max", type=float, default=2700, help="segundos como máximo (2700, 45 min)")
    a = p.parse_args(argv)
    pr = a.pr.lstrip("#")
    if not pr.isdigit() or not (math.isfinite(a.intervalo) and math.isfinite(a.max)) or a.intervalo < 0 or a.max < 0:
        print(f"CI error: argumentos no válidos (PR {a.pr!r}, intervalo {a.intervalo}, max {a.max}).", flush=True)
        return 2
    return esperar(a.repo, pr, a.intervalo, a.max)


if __name__ == "__main__":
    sys.exit(main())

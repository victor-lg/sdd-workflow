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
  corregidos Z" que sdd-review escribe en el comentario de reconciliación, una por
  PR y ronda (la última manda);
- revisores de G4 (VIC-48): las líneas "Métricas revisor: PR #N · ronda R · revisor
  L · modelo M · agente ID · confirmados D/I/M · descartados D/I/M" del mismo
  comentario, una por revisor y ronda, con los hallazgos por gravedad (debe
  corregirse / importante / menor). Con el ID del agente, del transcript de ese
  subagente (<sesión>/subagents/agent-ID.jsonl) guarda sus tokens por modelo
  (entrada, escritura y lectura de caché y salida) y sus minutos, del primer al
  último mensaje; si no lo encuentra, sin ellos;
- mutación: la última línea "Métricas mutación: detectados X de Y" (o "sin
  mutaciones") de sdd-implement;
- qué sesiones usaron sdd-review o sdd-implement, para avisar si falta su línea.

Las líneas solo cuentan en la entrada de una llamada a Bash del agente principal
con gh pr comment al principio de una orden, y solo cuando llega su resultado sin
error (una orden fallida o rechazada no cuenta). Nunca se leen del resultado, del
texto suelto del asistente (Claude Code no siempre lo guarda literal) ni de gh pr
edit (reenvía la descripción entera, y con ella líneas viejas). Tienen que ir solas
en su línea y fuera de un bloque ``` o ~~~, y se atribuyen a la issue de la rama de
esa entrada del transcript (gitBranch), no a la de la sesión. Son autodeclaradas:
el agente las escribe y nada las comprueba (tampoco que el PR #N sea el de la orden),
así que un texto que lo engañe podría falsearlas. El transcript se lee por partes
(hasta 8 MB cada vez): el JSON de la sesión guarda hasta qué byte se ha leído. Una
línea de más de 8 MB se salta sin analizar; si era un mensaje de la persona, no
cuenta. Se supone que Claude Code solo añade al transcript: si se reescribe, se
detecta cuando queda más corto o el byte guardado ya no cierra una línea. No
guarda el contenido de la conversación ni rutas fuera del proyecto: del transcript,
solo el nombre del fichero y el principio del uuid de cada intervención.

No lee nada aparte de lo que le pasa Claude Code, el transcript que le indica, los
transcripts de los subagentes que citan las líneas de revisor (en la carpeta de esa
sesión o, si no está, en la de otra sesión del mismo proyecto) y la rama de Git del
proyecto.
Corre fuera del sandbox porque lo lanza Claude Code, no el agente; por eso solo
escribe en su carpeta. Si algo falla, imprime la línea igualmente y no guarda nada.

Carpeta: la variable SDD_METRICAS_DIR o, si no está,
/mnt/c/Users/victor/Documents/sdd-metricas (C:\\Users\\victor\\Documents\\sdd-metricas).
"""
import glob
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
# Líneas de formato fijo de sdd-review y sdd-implement (docs en cada skill). Los
# números van acotados: int() con miles de dígitos lanza ValueError.
N = r"(\d{1,6})"
LINEA_G4 = re.compile(rf"^[ \t]*Métricas G4: PR #{N} · ronda {N} · confirmados {N} · "
                      rf"descartados {N} · corregidos {N}[ \t\r]*$", re.M)
# Una línea por revisor: letra, modelo, ID del subagente y hallazgos por gravedad
# (debe corregirse / importante / menor). El ID solo lleva letras y cifras: con él se
# forma la ruta del transcript del subagente.
LINEA_REVISOR = re.compile(rf"^[ \t]*Métricas revisor: PR #{N} · ronda {N} · revisor ([A-Z]) · "
                           rf"modelo ([\w.:-]{{1,60}}) · agente ([A-Za-z0-9]{{1,64}}) · "
                           rf"confirmados {N}/{N}/{N} · descartados {N}/{N}/{N}[ \t\r]*$", re.M)
# Lo que se lee del transcript de un subagente, de una vez.
MAX_SUBAGENTE = 64 * 1024 * 1024
# "sin mutaciones" dice que la entrega no las tuvo, sin dar números.
LINEA_MUTACION = re.compile(rf"^[ \t]*Métricas mutación: (?:detectados {N} de {N}|(sin mutaciones))[ \t\r]*$",
                            re.M)
# Las líneas solo se leen de la entrada de gh pr comment al principio de una orden
# (no en un comentario de shell ni dentro de otro texto), y solo si su resultado no
# es un error: ni un fallo ni una orden rechazada. gh pr edit no vale porque reenvía
# la descripción entera y con ella líneas viejas.
GH_PR = re.compile(r"(?:^|[;&|({])[ \t]*gh[ \t]+pr[ \t]+comment\b", re.M)
GRAVEDADES = ("debe", "importante", "menor")
# Skills cuyo uso sin ninguna línea válida se avisa en el resumen.
SKILLS_CON_METRICAS = ("sdd-review", "sdd-implement")
SKILL_DE_BARRA = re.compile(r"\s*(?:<command-message>[^<]*</command-message>\s*)?"
                            r"<command-name>/(?:[\w-]+:)?(sdd-review|sdd-implement)</command-name>")
# Mensajes de tipo "user" que no escribe la persona, en transcripts sin "origin". Ahí
# no se distingue /clear de /sdd:sdd-plan, así que ningún comando de barra cuenta.
NO_HUMANO = ("<local-command-", "<command-", "<task-notification>", "<system-reminder>",
             "This session is being continued")
# Lo que se lee del transcript en cada ejecución, para no retrasar la línea de estado.
MAX_LECTURA = 8 * 1024 * 1024


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
        return "\n".join(b["text"] for b in contenido if isinstance(b, dict)
                         and b.get("type") == "text" and isinstance(b.get("text"), str))
    return ""


def fuera_de_bloques(texto):
    """Quita los bloques ``` y ~~~: una línea de métricas citada en uno no cuenta."""
    lineas, valla = [], None
    for linea in texto.split("\n"):
        inicio = linea.lstrip()[:3]
        if inicio in ("```", "~~~") and valla in (None, inicio):
            valla = None if valla else inicio
        elif not valla:
            lineas.append(linea)
    return "\n".join(lineas)


def entero(v):
    try:
        return max(0, int(v or 0))
    except (TypeError, ValueError):
        return 0


def lineas_de(orden, fecha, issue):
    """Las líneas de métricas de una orden con gh pr comment, o None si no hay."""
    texto = fuera_de_bloques(orden)
    g4 = {}
    for m in LINEA_G4.finditer(texto):
        pr, ronda, conf, desc, corr = (int(x) for x in m.groups())
        g4[f"{pr}/{ronda}"] = {"pr": pr, "ronda": ronda, "confirmados": conf, "descartados": desc,
                               "corregidos": corr, "fecha": fecha, "issue": issue}
    revisores = {}
    for m in LINEA_REVISOR.finditer(texto):
        pr, ronda, letra, modelo, agente = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4), m.group(5)
        conf, desc = (dict(zip(GRAVEDADES, (int(x) for x in m.groups()[i:i + 3]))) for i in (5, 8))
        revisores[f"{pr}/{ronda}/{letra}"] = {"pr": pr, "ronda": ronda, "revisor": letra, "modelo": modelo,
                                             "agente": agente, "confirmados": conf, "descartados": desc,
                                             "fecha": fecha, "issue": issue}
    mutacion = None
    for m in LINEA_MUTACION.finditer(texto):
        mutacion = ({"sin_mutaciones": True} if m.group(3) else
                    {"detectados": int(m.group(1)), "total": int(m.group(2))})
        mutacion.update(fecha=fecha, issue=issue)
    return {"g4": g4, "revisores": revisores, "mutacion": mutacion} if g4 or revisores or mutacion else None


def transcript_de_agente(ruta, agente):
    """El transcript del subagente: en la carpeta de la sesión o en la de otra del proyecto."""
    nombre = f"agent-{agente}.jsonl"
    propio = os.path.join(os.path.splitext(ruta)[0], "subagents", nombre)
    if os.path.isfile(propio):
        return propio
    otros = glob.glob(os.path.join(glob.escape(os.path.dirname(ruta)), "*", "subagents", nombre))
    return otros[0] if otros else None


def consumo_de(ruta):
    """Tokens por modelo y minutos de un subagente, o None si no se puede leer.

    Claude Code escribe una entrada por bloque de cada respuesta, todas con el mismo
    message.id y el mismo uso: cuenta una vez por id. El tiempo va del primer al
    último mensaje del transcript.
    """
    try:
        with open(ruta, "rb") as f:
            bloque = f.read(MAX_SUBAGENTE)
    except OSError:
        return None
    usos, fechas = {}, []
    for linea in bloque.split(b"\n"):
        try:
            e = json.loads(linea.decode("utf-8", errors="replace"))
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        if isinstance(e.get("timestamp"), str):
            fechas.append(e["timestamp"])
        m = dic(e.get("message"))
        modelo, uso = m.get("model"), dic(m.get("usage"))
        # "<synthetic>" son mensajes que Claude Code genera sin llamar a la API.
        if e.get("type") == "assistant" and uso and isinstance(modelo, str) and not modelo.startswith("<"):
            usos[m.get("id") or len(usos)] = (modelo[:60], uso)
    tokens = {}
    for modelo, uso in usos.values():
        t = tokens.setdefault(modelo, {"entrada": 0, "cache_escritura": 0, "cache_lectura": 0, "salida": 0})
        for clave, campo in (("entrada", "input_tokens"), ("cache_escritura", "cache_creation_input_tokens"),
                             ("cache_lectura", "cache_read_input_tokens"), ("salida", "output_tokens")):
            t[clave] += entero(uso.get(campo))
    try:
        inicio, fin = (datetime.fromisoformat(x.replace("Z", "+00:00")) for x in (min(fechas), max(fechas)))
        minutos = round((fin - inicio).total_seconds() / 60, 2)
    except ValueError:
        minutos = None
    return {"tokens": tokens, "minutos": minutos}


def dic(v):
    return v if isinstance(v, dict) else {}


def anota_skill(estado, nombre, issue):
    """Apunta que la sesión usó una skill de SKILLS_CON_METRICAS en esa issue."""
    if nombre in SKILLS_CON_METRICAS:
        issues = estado["skills"].setdefault(nombre, [])
        if issue not in issues:
            issues.append(issue)


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
    # Una imagen sin texto también es un mensaje de la persona; uno vacío, no.
    if not texto and not (isinstance(contenido, list) and any(
            isinstance(b, dict) and b.get("type") != "text" for b in contenido)):
        return False
    if texto.startswith("[Request interrupted") or texto.startswith("<local-command-"):
        return False
    origen = e.get("origin")
    if isinstance(origen, dict):
        # Claude Code marca así lo que escribe la persona; "peer" y las tareas no cuentan.
        return origen.get("kind") == "human"
    return not texto.startswith(NO_HUMANO)


def lee_transcript(ruta, antes):
    """Lee lo nuevo del transcript desde el byte guardado y devuelve los recuentos.

    Las intervenciones se guardan también como el principio de su uuid: al reanudar
    una sesión, Claude Code copia los mensajes anteriores al transcript nuevo con el
    mismo uuid, y así resumen-metricas.py no los cuenta dos veces.
    """
    nombre = os.path.basename(ruta)
    desde = entero(antes.get("transcript_leido"))
    # True si la lectura anterior acabó dentro de una línea mayor que MAX_LECTURA.
    a_media_linea = antes.get("transcript_a_media_linea") is True
    ids = list(antes.get("intervenciones_ids") or [])
    estado = {
        "intervenciones": entero(antes.get("intervenciones")),
        "g4": dict(dic(antes.get("g4"))),
        "revisores": dict(dic(antes.get("revisores"))),
        "mutacion": antes.get("mutacion") if isinstance(antes.get("mutacion"), dict) else None,
        "skills": {k: list(v) for k, v in dic(antes.get("skills")).items() if isinstance(v, list)},
        # Líneas de un gh pr comment cuyo resultado aún no ha llegado, por tool_use_id.
        "pendientes": dict(dic(antes.get("pendientes"))),
    }
    with open(ruta, "rb") as f:
        reescrito = os.fstat(f.fileno()).st_size < desde
        if desde and not reescrito and not a_media_linea:
            # Lo leído terminaba en un salto de línea; si ahí no lo hay, el fichero cambió.
            f.seek(desde - 1)
            reescrito = f.read(1) != b"\n"
        if antes.get("transcript") != nombre or reescrito:
            # Otro fichero o uno reescrito: se cuenta desde el principio.
            desde, ids, a_media_linea = 0, [], False
            estado = {"intervenciones": 0, "g4": {}, "revisores": {}, "mutacion": None, "skills": {},
                      "pendientes": {}}
        f.seek(desde)
        bloque = f.read(MAX_LECTURA)
    if a_media_linea:
        # Se termina de saltar la línea larga, sin analizarla.
        fin = bloque.find(b"\n")
        if fin < 0:
            desde, bloque = desde + len(bloque), b""
        else:
            desde, bloque, a_media_linea = desde + fin + 1, bloque[fin + 1:], False
    corte = bloque.rfind(b"\n") + 1
    if not corte and len(bloque) == MAX_LECTURA:
        # Una línea más larga que todo el bloque no se analiza: se salta por partes.
        # Si es un mensaje de la persona, no cuenta (límite conocido).
        desde, bloque, a_media_linea = desde + len(bloque), b"", True
    else:
        # Una línea a medio escribir se deja para la próxima vez.
        bloque = bloque[:corte]
    vistos = set(ids)
    # Se parte por bytes: splitlines() también corta en U+2028, que va sin escapar
    # dentro de las cadenas JSON.
    for linea in bloque.split(b"\n"):
        try:
            e = json.loads(linea.decode("utf-8", errors="replace"))
            if not isinstance(e, dict):
                continue
            if e.get("type") == "user" and not e.get("isSidechain"):
                for b in g(e, "message", "content", defecto=[]):
                    # El resultado de un gh pr comment: sus líneas cuentan si no es un error.
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        lineas = estado["pendientes"].pop(str(b.get("tool_use_id")), None)
                        if isinstance(lineas, dict) and b.get("is_error") is not True:
                            estado["g4"].update(dic(lineas.get("g4")))
                            for clave, r in dic(lineas.get("revisores")).items():
                                if isinstance(r, dict) and isinstance(r.get("agente"), str):
                                    sub = transcript_de_agente(ruta, r["agente"])
                                    estado["revisores"][clave] = {**r, "consumo": consumo_de(sub) if sub else None}
                            if isinstance(lineas.get("mutacion"), dict):
                                estado["mutacion"] = lineas["mutacion"]
            if e.get("type") == "user" and not e.get("isSidechain") and "toolUseResult" not in e:
                # La persona puede lanzar la skill con /sdd:sdd-review en vez de pedírsela al agente.
                m = SKILL_DE_BARRA.match(texto_de(g(e, "message", "content")))
                if m:
                    rama_e = e.get("gitBranch")
                    anota_skill(estado, m.group(1), issue_de(rama_e) if isinstance(rama_e, str) else None)
            if es_intervencion(e):
                uid = e.get("uuid")
                if isinstance(uid, str) and uid:
                    if uid[:12] in vistos:
                        continue
                    vistos.add(uid[:12])
                    ids.append(uid[:12])
                estado["intervenciones"] += 1
            elif e.get("type") == "assistant" and not e.get("isSidechain"):
                fecha = e.get("timestamp")
                fecha = fecha[:40] if isinstance(fecha, str) else None
                # La rama de la entrada, no la de la sesión: una sesión puede pasar por
                # varias issues.
                rama_e = e.get("gitBranch")
                issue = issue_de(rama_e) if isinstance(rama_e, str) else None
                for b in g(e, "message", "content", defecto=[]):
                    if not isinstance(b, dict) or b.get("type") != "tool_use":
                        continue
                    entrada = b.get("input") if isinstance(b.get("input"), dict) else {}
                    if b.get("name") == "Skill" and isinstance(entrada.get("skill"), str):
                        anota_skill(estado, entrada["skill"].split(":")[-1], issue)
                    orden = entrada.get("command")
                    if b.get("name") != "Bash" or not isinstance(orden, str) or not GH_PR.search(orden) \
                            or not isinstance(b.get("id"), str):
                        continue
                    lineas = lineas_de(orden, fecha, issue)
                    if lineas:
                        estado["pendientes"][b["id"]] = lineas
        except Exception:
            continue  # una entrada rara no debe congelar las métricas de la sesión
    estado["intervenciones_ids"] = ids
    estado["transcript"] = nombre
    estado["transcript_leido"] = desde + len(bloque)
    estado["transcript_a_media_linea"] = a_media_linea
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
    print(f"{modelo} · ${coste:.2f} · {minutos} min" + (f" · {r}" if r else ""), flush=True)

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
                                          "intervenciones_ids", "g4", "revisores", "mutacion",
                                          "skills", "pendientes", "transcript_a_media_linea") if k in antes}
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

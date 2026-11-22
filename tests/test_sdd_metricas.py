"""Tests de entorno/sdd-metricas.py (VIC-16).

Los casos de issue_de() son los que se probaron a mano en el PR #3: ramas
<tipo>/vic-N-… de docs/convenciones.md, el formato anterior vic-N-… y
nombres que no son de una issue.

Las entradas de transcript imitan las de Claude Code 2.1.31x: los mensajes de
la persona llevan origin.kind "human"; los transcripts anteriores, no.
"""
import importlib.util
import io
import json
import os
import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

RUTA = pathlib.Path(__file__).resolve().parent.parent / "entorno" / "sdd-metricas.py"
# El nombre lleva guion, así que no se puede importar con import.
_spec = importlib.util.spec_from_file_location("sdd_metricas", RUTA)
sdd_metricas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sdd_metricas)


class IssueDe(unittest.TestCase):
    def test_rama_con_tipo(self):
        casos = {
            "chore/vic-16-convenciones": "VIC-16",
            "feat/vic-12-logica": "VIC-12",
            "adr/vic-19-0009-modelos": "VIC-19",
        }
        for rama, issue in casos.items():
            with self.subTest(rama=rama):
                self.assertEqual(sdd_metricas.issue_de(rama), issue)

    def test_formato_anterior_sin_tipo(self):
        self.assertEqual(sdd_metricas.issue_de("vic-10-calculo"), "VIC-10")

    def test_mayusculas(self):
        self.assertEqual(sdd_metricas.issue_de("Feat/VIC-7-x"), "VIC-7")

    def test_ramas_sin_issue(self):
        # vic-16x no termina el número; a/b/ no es un tipo de convenciones.md.
        for rama in ("spec-calc-003-x", "main", "feat/abc-3-x", "feat/vic-16x",
                     "a/b/vic-1-x", "", None):
            with self.subTest(rama=rama):
                self.assertIsNone(sdd_metricas.issue_de(rama))


def humano(texto, **extra):
    return {"type": "user", "origin": {"kind": "human"}, "promptSource": "typed",
            "message": {"role": "user", "content": texto}, **extra}


def asistente(texto, fecha="2026-11-06T10:00:00Z", **extra):
    return {"type": "assistant", "timestamp": fecha,
            "message": {"role": "assistant", "content": [{"type": "text", "text": texto}]}, **extra}


# La forma que piden las skills: el cuerpo en un fichero y la línea en un heredoc entrecomillado.
SEGURA = "{{ cat \"$TMPDIR/r.md\"; cat <<'METRICAS_SDD'\n{}\nMETRICAS_SDD\n}} | gh pr comment 21 --body-file -"
_ids = iter(range(10 ** 6))


def gh(cuerpo, orden=SEGURA, fecha="2026-11-06T10:00:00Z", herramienta="Bash", resultado="ok", **extra):
    """El agente publica un comentario y llega su resultado: "ok", "error", "rechazada" o None."""
    tid = f"toolu_{next(_ids)}"
    llamada = {"type": "assistant", "timestamp": fecha, "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": tid, "name": herramienta, "input": {"command": orden.format(cuerpo)}}]},
        **extra}
    if resultado is None:
        return [llamada]
    error = resultado != "ok"
    salida = {"type": "user", "toolUseResult": "Error" if error else {"stdout": "https://…"},
              "message": {"role": "user", "content": [
                  {"type": "tool_result", "tool_use_id": tid, "is_error": error, "content": "…"}]}}
    if resultado == "rechazada":
        salida["toolDenialKind"] = "user"
    return [llamada, salida]


def skill(nombre, **extra):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": "s", "name": "Skill", "input": {"skill": nombre, "args": "PR #21"}}]},
        **extra}


G4 = "Métricas G4: PR #21 · ronda {r} · confirmados {c} · descartados 1 · corregidos 2"
REVISOR = ("Métricas revisor: PR #21 · ronda {r} · revisor {l} · modelo sonnet · agente {a} · "
           "confirmados 0/1/2 · descartados 0/0/1")


def respuesta(mid, modelo="claude-sonnet-5-5", fecha="2026-11-06T09:00:00Z", texto="SECRETO-REVISOR",
              entrada=2, escritura=1000, lectura=5000, salida=300):
    """Una entrada de respuesta del transcript de un subagente (VIC-48)."""
    return {"type": "assistant", "isSidechain": True, "timestamp": fecha, "message": {
        "id": mid, "model": modelo, "content": [{"type": "text", "text": texto}],
        "usage": {"input_tokens": entrada, "cache_creation_input_tokens": escritura,
                  "cache_read_input_tokens": lectura, "output_tokens": salida}}}


def subagente(carpeta, sesion, agente, *entradas):
    ruta = os.path.join(carpeta, sesion, "subagents", f"agent-{agente}.jsonl")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        for e in entradas:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


class Transcript(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.dir.name, "s1.jsonl")
        open(self.ruta, "w").close()

    def tearDown(self):
        self.dir.cleanup()

    def escribe(self, *entradas, cola=""):
        with open(self.ruta, "a", encoding="utf-8") as f:
            for e in entradas:
                for x in (e if isinstance(e, list) else [e]):
                    f.write(json.dumps(x, ensure_ascii=False) + "\n")
            f.write(cola)

    def test_cuentan_los_mensajes_de_la_persona(self):
        casos = {
            "escrito": humano("Primer mensaje"),
            "en cola": humano("Otro en cola", promptSource="queued"),
            "skill invocada": humano("<command-message>sdd:sdd-plan</command-message>"),
            "sin origin": {"type": "user", "message": {"content": "Transcript antiguo"}},
            "solo una imagen": {"type": "user", "message": {"content": [{"type": "image", "source": {}}]}},
            "texto e imagen": humano([{"type": "text", "text": "mira"}, {"type": "image", "source": {}}]),
        }
        for caso, e in casos.items():
            with self.subTest(caso=caso):
                self.assertTrue(sdd_metricas.es_intervencion(e))

    def test_no_cuentan(self):
        resultado = [{"type": "tool_result", "tool_use_id": "x", "content": "salida"}]
        casos = {
            "resultado de herramienta": {"type": "user", "toolUseResult": {}, "message": {"content": resultado}},
            "tool_result sin toolUseResult": {"type": "user", "message": {"content": resultado}},
            "tool_result con texto": humano(resultado + [{"type": "text", "text": "y esto"}]),
            "isMeta": {"type": "user", "isMeta": True, "message": {"content": "<system-reminder>x"}},
            "isMeta en lista": {"type": "user", "isMeta": True,
                                "message": {"content": [{"type": "text", "text": "skill"}]}},
            "resumen de compactación": {"type": "user", "isCompactSummary": True,
                                        "message": {"content": "This session is being continued"}},
            "resumen sin marca": {"type": "user", "message": {"content": "This session is being continued"}},
            "comando local, nombre primero": {"type": "user", "message": {"content": "<command-name>/clear</command-name>"}},
            "comando, mensaje primero": {"type": "user", "message": {
                "content": "<command-message>clear</command-message>\n<command-name>/clear</command-name>"}},
            "salida de comando local": {"type": "user", "message": {"content": "<local-command-stdout>ok</local-command-stdout>"}},
            "salida con origin humano": humano("<local-command-stdout>ok</local-command-stdout>"),
            "interrupción": {"type": "user", "message": {"content": [{"type": "text", "text": "[Request interrupted by user]"}]}},
            "interrupción con origin": humano("[Request interrupted by user for tool use]"),
            "otro agente": {"type": "user", "origin": {"kind": "peer", "from": "a1"}, "message": {"content": "hola"}},
            "aviso de tarea": {"type": "user", "origin": {"kind": "task-notification"},
                               "message": {"content": "<task-notification> <task-id>1</task-id>"}},
            "aviso de tarea sin origin": {"type": "user", "message": {"content": "<task-notification>x"}},
            "recordatorio sin origin": {"type": "user", "message": {"content": "<system-reminder>x"}},
            "subagente": {"type": "user", "isSidechain": True, "message": {"content": "encargo"}},
            "vacío": {"type": "user", "message": {"content": ""}},
            "vacío con origin": humano("   "),
            "texto que no es cadena": humano([{"type": "text", "text": 3}]),
            "del asistente": asistente("hola"),
        }
        for caso, e in casos.items():
            with self.subTest(caso=caso):
                self.assertFalse(sdd_metricas.es_intervencion(e))

    def test_lectura_incremental(self):
        self.escribe(humano("uno"), humano("dos"))
        e1 = sdd_metricas.lee_transcript(self.ruta, {})
        self.assertEqual(e1["intervenciones"], 2)
        self.assertEqual(e1["transcript_leido"], os.path.getsize(self.ruta))
        # La línea a medio escribir no se cuenta todavía ni se salta.
        linea = json.dumps(humano("tres"))
        self.escribe(cola=linea[:10])
        e2 = sdd_metricas.lee_transcript(self.ruta, e1)
        self.assertEqual(e2["intervenciones"], 2)
        self.assertEqual(e2["transcript_leido"], e1["transcript_leido"])
        self.escribe(cola=linea[10:] + "\n")
        e3 = sdd_metricas.lee_transcript(self.ruta, e2)
        self.assertEqual(e3["intervenciones"], 3)
        # Releer sin cambios no suma nada.
        self.assertEqual(sdd_metricas.lee_transcript(self.ruta, e3), e3)

    def test_fichero_reescrito_o_distinto_se_cuenta_de_cero(self):
        self.escribe(humano("uno"), humano("dos"), humano("tres"))
        e = sdd_metricas.lee_transcript(self.ruta, {})
        with open(self.ruta, "w", encoding="utf-8") as f:
            f.write(json.dumps(humano("solo uno")) + "\n")
        self.assertEqual(sdd_metricas.lee_transcript(self.ruta, e)["intervenciones"], 1)
        otro = dict(e, transcript="otra-sesion.jsonl")
        self.assertEqual(sdd_metricas.lee_transcript(self.ruta, otro)["intervenciones"], 1)

    def test_separador_de_linea_unicode_dentro_de_un_mensaje(self):
        # json.dumps(ensure_ascii=False) deja U+2028 y U+0085 sin escapar.
        self.escribe(humano("pegado\u2028de un PDF\u0085y más"), gh("a\u2029b\n" + G4.format(r=1, c=1)))
        e = sdd_metricas.lee_transcript(self.ruta, {})
        self.assertEqual(e["intervenciones"], 1)
        self.assertEqual(set(e["g4"]), {"21/1"})

    def test_reescrito_con_tamano_mayor(self):
        self.escribe(humano("uno"), humano("dos"))
        e = sdd_metricas.lee_transcript(self.ruta, {})
        with open(self.ruta, "w", encoding="utf-8") as f:
            f.write(json.dumps(humano("un mensaje bastante más largo que los dos de antes juntos " * 4)) + "\n")
        self.assertGreater(os.path.getsize(self.ruta), e["transcript_leido"])
        self.assertEqual(sdd_metricas.lee_transcript(self.ruta, e)["intervenciones"], 1)

    def test_mensajes_repetidos_por_uuid(self):
        self.escribe(humano("uno", uuid="aaaaaaaa-1111-0000"), humano("uno otra vez", uuid="aaaaaaaa-1111-0000"),
                     humano("dos", uuid="bbbbbbbb-2222-0000"), humano("sin uuid"))
        e = sdd_metricas.lee_transcript(self.ruta, {})
        self.assertEqual(e["intervenciones"], 3)
        self.assertEqual(e["intervenciones_ids"], ["aaaaaaaa-111", "bbbbbbbb-222"])
        # En lecturas posteriores tampoco se repite.
        self.escribe(humano("uno", uuid="aaaaaaaa-1111-0000"))
        self.assertEqual(sdd_metricas.lee_transcript(self.ruta, e)["intervenciones"], 3)

    def test_una_entrada_rara_no_congela_las_metricas(self):
        self.escribe(
            gh("Métricas G4: PR #" + "9" * 5000 + " · ronda 1 · confirmados 1 · descartados 0 · corregidos 0"),
            {"type": "assistant", "message": {"content": [{"type": "text", "text": {"no": "cadena"}}]}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": "raro"}]}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": 3}}]}},
            {"type": "assistant", "message": {"content": "no es una lista"}},
            {"type": "user", "origin": "raro", "message": {"content": None}},
            gh(G4.format(r=1, c=2), fecha={"no": "cadena"}),
            humano("sigue contando"),
        )
        e = sdd_metricas.lee_transcript(self.ruta, {"transcript_leido": "basura", "intervenciones": "x"})
        self.assertEqual(e["intervenciones"], 1)
        self.assertEqual(set(e["g4"]), {"21/1"})
        self.assertIsNone(e["g4"]["21/1"]["fecha"])
        self.assertEqual(e["transcript_leido"], os.path.getsize(self.ruta))

    def test_linea_larga_a_medio_escribir_se_lee_por_partes(self):
        with mock.patch.object(sdd_metricas, "MAX_LECTURA", 200):
            self.escribe(humano("antes"))
            larga = json.dumps(humano("y" * 900))
            self.escribe(cola=larga[:800])  # sin terminar
            e = {}
            for _ in range(8):
                previo = e.get("transcript_leido", 0)
                e = sdd_metricas.lee_transcript(self.ruta, e)
                # Cada ejecución avanza como mucho MAX_LECTURA y no vuelve atrás.
                self.assertLessEqual(e["transcript_leido"] - previo, 200)
                self.assertGreaterEqual(e["transcript_leido"], previo)
            self.assertEqual(e["transcript_leido"], os.path.getsize(self.ruta))
            self.assertTrue(e["transcript_a_media_linea"])
            self.assertEqual(e["intervenciones"], 1)
            # Termina la línea y llega otro mensaje: se retoma sin tomarlo por una reescritura.
            self.escribe(cola=larga[800:] + "\n")
            self.escribe(humano("después"))
            for _ in range(3):
                e = sdd_metricas.lee_transcript(self.ruta, e)
            self.assertEqual(e["intervenciones"], 2)
            self.assertFalse(e["transcript_a_media_linea"])
            self.assertEqual(e["transcript_leido"], os.path.getsize(self.ruta))

    def test_lectura_acotada(self):
        with mock.patch.object(sdd_metricas, "MAX_LECTURA", 200):
            self.escribe(*(humano(f"mensaje {i}") for i in range(10)))
            e = sdd_metricas.lee_transcript(self.ruta, {})
            self.assertLess(e["intervenciones"], 10)
            while e["transcript_leido"] < os.path.getsize(self.ruta):
                e = sdd_metricas.lee_transcript(self.ruta, e)
            self.assertEqual(e["intervenciones"], 10)
            # Una línea más larga que todo el bloque se salta en vez de atascarse.
            self.escribe(humano("x" * 500), humano("después"))
            for _ in range(10):
                e = sdd_metricas.lee_transcript(self.ruta, e)
            self.assertEqual(e["intervenciones"], 11)
            self.assertEqual(e["transcript_leido"], os.path.getsize(self.ruta))

    def test_lineas_g4_por_pr_y_ronda(self):
        self.escribe(
            gh("## Reconciliación\n" + G4.format(r=1, c=4) + "\nSigo.", fecha="2026-11-06T10:00:00Z",
               gitBranch="feat/vic-12-logica"),
            gh(G4.format(r=2, c=1)),
            # La misma ronda repetida: manda la última.
            gh("  " + G4.format(r=2, c=3) + "  ", fecha="2026-11-06T12:00:00Z"),
            gh("Métricas G4: PR #22 · ronda 1 · confirmados 0 · descartados 0 · corregidos 0"),
        )
        g4 = sdd_metricas.lee_transcript(self.ruta, {})["g4"]
        self.assertEqual(set(g4), {"21/1", "21/2", "22/1"})
        self.assertEqual(g4["21/1"], {"pr": 21, "ronda": 1, "confirmados": 4, "descartados": 1,
                                      "corregidos": 2, "fecha": "2026-11-06T10:00:00Z",
                                      "issue": "VIC-12"})
        self.assertIsNone(g4["22/1"]["issue"])  # sin gitBranch
        self.assertEqual(g4["21/2"]["confirmados"], 3)
        self.assertEqual(g4["21/2"]["fecha"], "2026-11-06T12:00:00Z")

    def test_ordenes_gh_que_cuentan(self):
        ordenes = {
            "la forma de las skills": SEGURA,
            "tras &&": "cd repo && " + SEGURA,
            "gh al principio con heredoc entrecomillado": "gh pr comment 21 --body-file - <<'METRICAS_SDD'\n{}\nMETRICAS_SDD",
            "con espacios de más": "{{ cat r.md; cat <<'X'\n{}\nX\n}} |  gh  pr   comment 21 -F -",
            "en una línea propia": "cat <<'X' > r.md\n{}\nX\ngh pr comment 21 --body-file r.md",
        }
        for caso, orden in ordenes.items():
            with self.subTest(caso=caso):
                open(self.ruta, "w").close()
                self.escribe(gh(G4.format(r=1, c=1), orden=orden))
                self.assertEqual(set(sdd_metricas.lee_transcript(self.ruta, {})["g4"]), {"21/1"})

    def test_lineas_que_no_cuentan(self):
        linea, mut = G4.format(r=1, c=9), "Métricas mutación: detectados 1 de 2"
        resultado = lambda t: {"type": "user", "toolUseResult": {}, "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t", "content": t}]}}
        casos = {
            "texto del asistente": asistente(linea + "\n" + mut),
            "la persona": humano(linea + "\n" + mut),
            "resultado de gh pr comment": resultado(linea + "\n" + mut),
            "resultado de gh pr view": resultado("gh pr view 21 --comments\n" + linea),
            "orden fallida": gh(linea + "\n" + mut, resultado="error"),
            "orden rechazada": gh(linea + "\n" + mut, resultado="rechazada"),
            "sin resultado todavía": gh(linea + "\n" + mut, resultado=None),
            "un subagente": gh(linea + "\n" + mut, isSidechain=True),
            "Bash sin gh pr": gh(linea + "\n" + mut, orden="cat > r.md <<'EOF'\n{}\nEOF"),
            "gh pr edit": gh(linea + "\n" + mut, orden="gh pr edit 21 --body-file - <<'EOF'\n{}\nEOF"),
            "gh pr create": gh(linea, orden="gh pr create --body-file - <<'EOF'\n{}\nEOF"),
            "gh pr view": gh(linea, orden="gh pr view 21 # {}"),
            "en un comentario de shell": gh(linea, orden="cat <<'X' > r.md\n{}\nX\n# luego gh pr comment 21"),
            "dentro de otro texto": gh(linea, orden="git commit -m 'gh pr comment 21'\ncat <<'X'\n{}\nX"),
            "otra palabra": gh(linea, orden="xgh pr comment 21 <<'EOF'\n{}\nEOF"),
            "Write del fichero": gh(linea, orden="gh pr comment 21\n{}", herramienta="Write"),
            "citada en una frase": gh("Escribe `" + linea + "` al final."),
            "con letras": gh("Métricas G4: PR #N · ronda R · confirmados X · descartados Y · corregidos Z\n"
                             "Métricas mutación: detectados X de Y"),
            "con viñeta": gh("- " + linea),
            "en un bloque ```": gh("Salida:\n```\n" + linea + "\n" + mut + "\n```"),
            "en un bloque ~~~": gh("~~~text\n" + linea + "\n```\n" + mut + "\n~~~"),
        }
        for caso, e in casos.items():
            with self.subTest(caso=caso):
                open(self.ruta, "w").close()
                self.escribe(e)
                r = sdd_metricas.lee_transcript(self.ruta, {})
                self.assertEqual(r["g4"], {})
                self.assertIsNone(r["mutacion"])

    def test_cuenta_al_llegar_el_resultado_en_otra_lectura(self):
        llamada, salida = gh(G4.format(r=1, c=1))
        self.escribe(llamada)
        e = sdd_metricas.lee_transcript(self.ruta, {})
        self.assertEqual(e["g4"], {})
        self.assertEqual(len(e["pendientes"]), 1)
        self.escribe(salida)
        e = sdd_metricas.lee_transcript(self.ruta, e)
        self.assertEqual(set(e["g4"]), {"21/1"})
        self.assertEqual(e["pendientes"], {})

    def test_mutacion_la_ultima(self):
        self.escribe(gh("Métricas mutación: detectados 3 de 5", fecha="2026-11-06T10:00:00Z"),
                     gh("## Validación\nMétricas mutación: detectados 5 de 5", fecha="2026-11-06T11:00:00Z",
                        gitBranch="fix/vic-13-redondeo"))
        self.assertEqual(sdd_metricas.lee_transcript(self.ruta, {})["mutacion"],
                         {"detectados": 5, "total": 5, "fecha": "2026-11-06T11:00:00Z", "issue": "VIC-13"})

    def test_sin_mutaciones(self):
        self.escribe(gh("Métricas mutación: sin mutaciones", gitBranch="fix/vic-13-redondeo"))
        self.assertEqual(sdd_metricas.lee_transcript(self.ruta, {})["mutacion"],
                         {"sin_mutaciones": True, "fecha": "2026-11-06T10:00:00Z", "issue": "VIC-13"})

    def test_json_anterior_con_tipos_raros(self):
        self.escribe(gh(G4.format(r=1, c=1)), skill("sdd:sdd-review"), humano("uno"))
        raro = {"g4": [1], "skills": "x", "mutacion": 3, "pendientes": [2], "intervenciones_ids": None}
        e = sdd_metricas.lee_transcript(self.ruta, raro)
        self.assertEqual(set(e["g4"]), {"21/1"})
        self.assertEqual(e["skills"], {"sdd-review": [None]})
        self.assertEqual(e["intervenciones"], 1)

    def test_issue_de_la_rama_de_cada_entrada(self):
        # Una sesión que pasa de VIC-12 a VIC-13: cada ronda va a la issue de su rama.
        self.escribe(gh(G4.format(r=1, c=1), gitBranch="feat/vic-12-x"),
                     gh("Métricas G4: PR #30 · ronda 1 · confirmados 2 · descartados 0 · corregidos 2",
                        gitBranch="feat/vic-13-y"),
                     gh(G4.format(r=2, c=1), gitBranch="main"),
                     gh(G4.format(r=3, c=1), gitBranch=["no", "cadena"]))
        g4 = sdd_metricas.lee_transcript(self.ruta, {})["g4"]
        self.assertEqual({k: v["issue"] for k, v in g4.items()},
                         {"21/1": "VIC-12", "30/1": "VIC-13", "21/2": None, "21/3": None})

    def test_retornos_de_carro(self):
        self.escribe(gh(G4.format(r=1, c=1) + "\r\nMétricas mutación: detectados 1 de 2\r\n"))
        e = sdd_metricas.lee_transcript(self.ruta, {})
        self.assertEqual(set(e["g4"]), {"21/1"})
        self.assertEqual(e["mutacion"]["total"], 2)

    def test_skills_usadas(self):
        self.escribe(
            skill("sdd:sdd-review", gitBranch="feat/vic-12-x"),
            skill("sdd-review", gitBranch="feat/vic-12-x"),                 # repetida en la issue
            skill("sdd:sdd-implement", gitBranch="main"),                   # sin issue
            humano("<command-message>sdd:sdd-review</command-message>\n"
                   "<command-name>/sdd:sdd-review</command-name>\n<command-args>21</command-args>",
                   gitBranch="feat/vic-13-y"),
            # No cuentan: otras skills, subagentes, resultados y la etiqueta citada en un mensaje.
            skill("sdd:sdd-plan", gitBranch="feat/vic-14-z"),
            skill("sdd:sdd-review", gitBranch="feat/vic-15-z", isSidechain=True),
            {"type": "user", "toolUseResult": {}, "gitBranch": "feat/vic-16-z", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "t",
                 "content": "<command-name>/sdd:sdd-review</command-name>"}]}},
            humano("¿Qué hace <command-name>/sdd:sdd-implement</command-name>?", gitBranch="feat/vic-17-z"),
        )
        e = sdd_metricas.lee_transcript(self.ruta, {})
        self.assertEqual(e["skills"], {"sdd-review": ["VIC-12", "VIC-13"], "sdd-implement": [None]})
        # El comando de barra también es una intervención.
        self.assertEqual(e["intervenciones"], 2)
        # Se conservan entre lecturas.
        self.escribe(skill("sdd:sdd-review", gitBranch="feat/vic-18-z"))
        e = sdd_metricas.lee_transcript(self.ruta, e)
        self.assertEqual(e["skills"]["sdd-review"], ["VIC-12", "VIC-13", "VIC-18"])

    def test_lineas_de_revisor_con_su_subagente(self):
        # Claude Code repite la misma respuesta (mismo id) en una entrada por bloque.
        subagente(self.dir.name, "s1", "a1b2", {"type": "user", "timestamp": "2026-11-06T09:00:00Z"},
                  respuesta("m1"), respuesta("m1"), respuesta("m2", fecha="2026-11-06T09:01:30Z"),
                  respuesta("m3", modelo="<synthetic>", salida=0),
                  {"type": "user", "timestamp": "2026-11-06T09:02:00Z"})
        subagente(self.dir.name, "s1", "c3d4", respuesta("m9", modelo="claude-opus-5-5", salida=50))
        self.escribe(gh("\n".join([G4.format(r=1, c=3), REVISOR.format(r=1, l="A", a="a1b2"),
                                   REVISOR.format(r=1, l="B", a="c3d4")]), gitBranch="feat/vic-48-x"))
        rev = sdd_metricas.lee_transcript(self.ruta, {})["revisores"]
        self.assertEqual(set(rev), {"21/1/A", "21/1/B"})
        a = rev["21/1/A"]
        self.assertEqual({k: a[k] for k in ("pr", "ronda", "revisor", "modelo", "agente", "issue")},
                         {"pr": 21, "ronda": 1, "revisor": "A", "modelo": "sonnet", "agente": "a1b2",
                          "issue": "VIC-48"})
        self.assertEqual(a["confirmados"], {"debe": 0, "importante": 1, "menor": 2})
        self.assertEqual(a["descartados"], {"debe": 0, "importante": 0, "menor": 1})
        self.assertEqual(a["consumo"], {"minutos": 2.0, "tokens": {"claude-sonnet-5-5": {
            "entrada": 4, "cache_escritura": 2000, "cache_lectura": 10000, "salida": 600}}})
        self.assertEqual(rev["21/1/B"]["consumo"]["tokens"]["claude-opus-5-5"]["salida"], 50)
        self.assertEqual(rev["21/1/B"]["consumo"]["minutos"], 0)

    def test_subagente_en_otra_sesion_o_sin_transcript(self):
        # Al reanudar, el revisor pudo lanzarse desde la sesión anterior.
        subagente(self.dir.name, "s0", "e5", respuesta("m1"))
        self.escribe(gh(REVISOR.format(r=1, l="A", a="e5") + "\n" + REVISOR.format(r=2, l="A", a="ff")))
        rev = sdd_metricas.lee_transcript(self.ruta, {})["revisores"]
        self.assertEqual(rev["21/1/A"]["consumo"]["tokens"]["claude-sonnet-5-5"]["salida"], 300)
        self.assertIsNone(rev["21/2/A"]["consumo"])  # la línea cuenta, sin tokens

    def test_lineas_de_revisor_que_no_cuentan(self):
        subagente(self.dir.name, "s1", "a1", respuesta("m1"))
        buena = REVISOR.format(r=1, l="A", a="a1")
        casos = {
            "texto del asistente": [asistente(buena)],
            "orden fallida": gh(buena, resultado="error"),
            "sin resultado aún": gh(buena, resultado=None),
            "en un bloque de código": gh("```\n" + buena + "\n```"),
            "agente con ruta": gh(REVISOR.format(r=1, l="A", a="../s1/subagents/agent-a1")),
            "letra minúscula": gh(REVISOR.format(r=1, l="a", a="a1")),
            "sin gravedades": gh(buena.replace("confirmados 0/1/2", "confirmados 3")),
        }
        for caso, entradas in casos.items():
            with self.subTest(caso=caso):
                open(self.ruta, "w").close()
                self.escribe(*entradas)
                self.assertEqual(sdd_metricas.lee_transcript(self.ruta, {})["revisores"], {})

    def test_revisor_repetido_manda_el_ultimo(self):
        self.escribe(gh(REVISOR.format(r=1, l="A", a="x1")),
                     gh(REVISOR.format(r=1, l="A", a="x1").replace("0/1/2", "1/1/2"),
                        fecha="2026-11-06T12:00:00Z"))
        rev = sdd_metricas.lee_transcript(self.ruta, {})["revisores"]
        self.assertEqual(rev["21/1/A"]["confirmados"]["debe"], 1)

    def test_lineas_basura(self):
        self.escribe(cola="no es json\n[1, 2]\n")
        self.escribe(humano("uno"))
        self.assertEqual(sdd_metricas.lee_transcript(self.ruta, {})["intervenciones"], 1)


class Main(unittest.TestCase):
    """De la entrada de la línea de estado al JSON de la sesión."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.carpeta = os.path.join(self.dir.name, "sdd-metricas")
        self.transcript = os.path.join(self.dir.name, "abc.jsonl")

    def tearDown(self):
        self.dir.cleanup()

    def ejecuta(self, entrada):
        with mock.patch.object(sdd_metricas, "CARPETA", self.carpeta), \
                mock.patch("sys.stdin", io.StringIO(json.dumps(entrada))), \
                redirect_stdout(io.StringIO()) as salida:
            sdd_metricas.main()
        return salida.getvalue()

    def sesion(self):
        with open(os.path.join(self.carpeta, "sesiones", "abc.json"), encoding="utf-8") as f:
            return f.read()

    def test_guarda_recuentos_y_nunca_contenido(self):
        with open(self.transcript, "w", encoding="utf-8") as f:
            for e in (humano("SECRETO-PERSONA"), asistente("SECRETO-ASISTENTE"),
                      *gh("SECRETO-COMENTARIO\n" + G4.format(r=1, c=2)), skill("sdd:sdd-review"),
                      *gh("Métricas mutación: detectados 4 de 6"),
                      *gh(REVISOR.format(r=1, l="A", a="a9"))):
                f.write(json.dumps(e) + "\n")
        subagente(self.dir.name, "abc", "a9", respuesta("m1"))
        entrada = {"session_id": "abc", "transcript_path": self.transcript,
                   "model": {"display_name": "Opus"}, "cost": {"total_cost_usd": 1.5}}
        self.assertIn("Opus · $1.50", self.ejecuta(entrada))
        texto = self.sesion()
        d = json.loads(texto)
        self.assertEqual(d["intervenciones"], 1)
        self.assertEqual(d["g4"]["21/1"]["confirmados"], 2)
        self.assertEqual(d["mutacion"]["detectados"], 4)
        self.assertEqual(d["revisores"]["21/1/A"]["consumo"]["tokens"]["claude-sonnet-5-5"]["salida"], 300)
        self.assertEqual(d["skills"], {"sdd-review": [None]})
        self.assertEqual(d["transcript"], "abc.jsonl")
        self.assertNotIn("SECRETO", texto)
        self.assertNotIn(self.dir.name, texto)  # ni rutas completas

        with open(self.transcript, "a", encoding="utf-8") as f:
            f.write(json.dumps(humano("otro")) + "\n")
        self.ejecuta(entrada)
        self.assertEqual(json.loads(self.sesion())["intervenciones"], 2)

    def test_si_el_transcript_falla_conserva_lo_anterior(self):
        with open(self.transcript, "w", encoding="utf-8") as f:
            f.write(json.dumps(humano("uno")) + "\n")
        entrada = {"session_id": "abc", "transcript_path": self.transcript}
        self.ejecuta(entrada)
        os.remove(self.transcript)
        self.assertTrue(self.ejecuta(entrada))  # la línea de estado sale igual
        self.assertEqual(json.loads(self.sesion())["intervenciones"], 1)


if __name__ == "__main__":
    unittest.main()

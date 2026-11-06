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


G4 = "Métricas G4: PR #21 · ronda {r} · confirmados {c} · descartados 1 · corregidos 2"


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
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
            f.write(cola)

    def test_solo_cuentan_los_mensajes_de_la_persona(self):
        self.escribe(
            humano("Primer mensaje"),                                       # cuenta
            humano("Otro en cola", promptSource="queued"),                  # cuenta
            humano("<command-message>sdd:sdd-plan</command-message>"),      # cuenta: lo escribió
            {"type": "user", "message": {"content": "Sin origin, transcript antiguo"}},  # cuenta
            {"type": "user", "message": {"content": [{"type": "image", "source": {}}]}},  # cuenta
            {"type": "user", "toolUseResult": {}, "message": {"content": [
                {"type": "tool_result", "tool_use_id": "x", "content": "salida"}]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "y", "content": "salida"}]}},
            {"type": "user", "isMeta": True, "message": {"content": "<system-reminder>x"}},
            {"type": "user", "isMeta": True, "message": {"content": [{"type": "text", "text": "skill"}]}},
            {"type": "user", "isCompactSummary": True, "isVisibleInTranscriptOnly": True,
             "message": {"content": "This session is being continued from a previous conversation"}},
            {"type": "user", "message": {"content": "This session is being continued from a previous"}},
            {"type": "user", "message": {"content": "<command-name>/clear</command-name>"}},
            {"type": "user", "message": {"content": "<local-command-stdout>ok</local-command-stdout>"}},
            humano("<local-command-stdout>ok</local-command-stdout>"),
            {"type": "user", "message": {"content": [{"type": "text", "text": "[Request interrupted by user]"}]}},
            humano("[Request interrupted by user for tool use]"),
            {"type": "user", "origin": {"kind": "peer", "from": "a1"}, "message": {"content": "hola"}},
            {"type": "user", "origin": {"kind": "task-notification"},
             "message": {"content": "<task-notification> <task-id>1</task-id>"}},
            {"type": "user", "isSidechain": True, "message": {"content": "encargo al subagente"}},
            {"type": "user", "message": {"content": ""}},
        )
        self.assertEqual(sdd_metricas.lee_transcript(self.ruta, {})["intervenciones"], 5)

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

    def test_lineas_g4_por_pr_y_ronda(self):
        self.escribe(
            asistente("Reconciliado.\n" + G4.format(r=1, c=4) + "\nSigo.", "2026-11-06T10:00:00Z"),
            asistente(G4.format(r=2, c=1)),
            # La misma ronda repetida: manda la última.
            asistente("  " + G4.format(r=2, c=3) + "  ", "2026-11-06T12:00:00Z"),
            asistente("Métricas G4: PR #22 · ronda 1 · confirmados 0 · descartados 0 · corregidos 0"),
        )
        g4 = sdd_metricas.lee_transcript(self.ruta, {})["g4"]
        self.assertEqual(set(g4), {"21/1", "21/2", "22/1"})
        self.assertEqual(g4["21/1"], {"pr": 21, "ronda": 1, "confirmados": 4, "descartados": 1,
                                      "corregidos": 2, "fecha": "2026-11-06T10:00:00Z"})
        self.assertEqual(g4["21/2"]["confirmados"], 3)
        self.assertEqual(g4["21/2"]["fecha"], "2026-11-06T12:00:00Z")

    def test_lineas_que_no_cuentan(self):
        self.escribe(
            humano(G4.format(r=1, c=9)),                                   # la persona
            {"type": "user", "toolUseResult": {}, "message": {"content": [
                {"type": "tool_result", "tool_use_id": "x", "content": G4.format(r=1, c=9)}]}},
            asistente(G4.format(r=1, c=9), isSidechain=True),              # un subagente
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Bash", "input": {"command": G4.format(r=1, c=9)}}]}},
            asistente("Escribe `" + G4.format(r=1, c=9) + "` al final."),  # citada, no sola
            asistente("Métricas G4: PR #N · ronda R · confirmados X · descartados Y · corregidos Z"),
            asistente("- " + G4.format(r=1, c=9)),
            asistente("Métricas mutación: detectados X de Y"),
            humano("Métricas mutación: detectados 1 de 2"),
        )
        e = sdd_metricas.lee_transcript(self.ruta, {})
        self.assertEqual(e["g4"], {})
        self.assertIsNone(e["mutacion"])

    def test_mutacion_la_ultima(self):
        self.escribe(asistente("Métricas mutación: detectados 3 de 5", "2026-11-06T10:00:00Z"),
                     asistente("Hecho.\nMétricas mutación: detectados 5 de 5", "2026-11-06T11:00:00Z"))
        self.assertEqual(sdd_metricas.lee_transcript(self.ruta, {})["mutacion"],
                         {"detectados": 5, "total": 5, "fecha": "2026-11-06T11:00:00Z"})

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
            for e in (humano("SECRETO-PERSONA"), asistente("SECRETO-ASISTENTE\n" + G4.format(r=1, c=2)),
                      asistente("Métricas mutación: detectados 4 de 6")):
                f.write(json.dumps(e) + "\n")
        entrada = {"session_id": "abc", "transcript_path": self.transcript,
                   "model": {"display_name": "Opus"}, "cost": {"total_cost_usd": 1.5}}
        self.assertIn("Opus · $1.50", self.ejecuta(entrada))
        texto = self.sesion()
        d = json.loads(texto)
        self.assertEqual(d["intervenciones"], 1)
        self.assertEqual(d["g4"]["21/1"]["confirmados"], 2)
        self.assertEqual(d["mutacion"]["detectados"], 4)
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

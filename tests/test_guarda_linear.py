"""Tests de plugin-sdd/hooks/guarda-linear.py (VIC-17): REG-04, decisión 1. El agente lee y
comenta; el resto de herramientas de Linear se bloquea, también las que aún no existen."""
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HOOKS = RAIZ / "plugin-sdd" / "hooks"
RUTA = HOOKS / "guarda-linear.py"
_spec = importlib.util.spec_from_file_location("guarda_linear", RUTA)
guarda = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guarda)
CONF = json.loads((HOOKS / "reglas-linear.json").read_text(encoding="utf-8"))
SERVIDORES = ("mcp__linear__", "mcp__claude_ai_Linear__", "mcp__plugin_linear_linear__", "mcp__LINEAR__")

BLOQUEADAS = [
    "save_issue", "create_issue", "update_issue", "delete_issue", "archive_issue", "create_issue_label",
    "save_project", "update_project", "create_attachment", "delete_attachment", "delete_comment",
    "save_document", "create_document", "update_document", "save_milestone", "create_issue_relation",
    "set_issue_status", "assign_issue", "herramienta_nueva", "getter_que_escribe",
]
PERMITIDAS = [
    "get_issue", "list_issues", "list_comments", "get_issue_status", "list_issue_statuses", "search_documentation",
    "extract_images", "get_attachment", "list_projects", "get_document", "list_cycles", "get_user",
    "create_comment", "save_comment",
]


class Guarda(unittest.TestCase):
    def test_bloquea_lo_que_no_es_leer_ni_comentar(self):
        for servidor in SERVIDORES:
            for herramienta in BLOQUEADAS:
                with self.subTest(nombre=servidor + herramienta):
                    self.assertEqual(guarda.decidir(servidor + herramienta, {}, CONF), "solo-comentar")

    def test_deja_leer_y_comentar(self):
        for servidor in SERVIDORES:
            for herramienta in PERMITIDAS:
                with self.subTest(nombre=servidor + herramienta):
                    self.assertIsNone(guarda.decidir(servidor + herramienta, {"issueId": "VIC-1", "body": "x"}, CONF))

    def test_editar_un_comentario_existente_no_es_comentar(self):
        self.assertEqual(guarda.decidir("mcp__linear__save_comment", {"id": "abc", "body": "x"}, CONF),
                         "solo-comentar")

    def test_otros_servidores_no_son_cosa_suya(self):
        for nombre in ("mcp__github__create_issue", "mcp__claude_ai_Claude_Docs__update", "Bash", "Write",
                       "mcp__notion__save_issue", "mcp_linear_save_issue", "linear__save_issue"):
            with self.subTest(nombre=nombre):
                self.assertIsNone(guarda.decidir(nombre, {}, CONF))

    def test_el_matcher_cubre_los_servidores(self):
        registro = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        grupo = next(g for g in registro if "guarda-linear.py" in g["hooks"][0]["command"])
        self.assertTrue(grupo["hooks"][0]["command"].endswith("|| exit 2"))
        for servidor in SERVIDORES:
            with self.subTest(servidor=servidor):
                self.assertTrue(re.fullmatch(grupo["matcher"], servidor + "save_issue"))
        self.assertFalse(re.fullmatch(grupo["matcher"], "Bash"))


class Principal(unittest.TestCase):
    def ejecuta(self, entrada, ruta=RUTA):
        r = subprocess.run([sys.executable, str(ruta)], input=entrada, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        return r.stdout

    def test_deja_pasar_en_silencio(self):
        self.assertEqual(self.ejecuta(json.dumps({"tool_name": "mcp__linear__get_issue", "tool_input": {}})), "")

    def test_bloquea_y_dice_que_hacer(self):
        salida = json.loads(self.ejecuta(json.dumps(
            {"tool_name": "mcp__linear__save_issue", "tool_input": {"id": "VIC-1", "state": "Done"}})))
        salida = salida["hookSpecificOutput"]
        self.assertEqual(salida["permissionDecision"], "deny")
        self.assertIn("En su lugar:", salida["permissionDecisionReason"])
        self.assertIn("(mcp__linear__save_issue)", salida["permissionDecisionReason"])

    def test_entrada_rota_o_sin_reglas_falla_cerrado(self):
        for entrada in ("", "{}", "[]"):
            with self.subTest(entrada=entrada):
                salida = json.loads(self.ejecuta(entrada))["hookSpecificOutput"]
                self.assertEqual(salida["permissionDecision"], "deny")
        with tempfile.TemporaryDirectory() as d:
            copia = pathlib.Path(d) / "guarda-linear.py"
            copia.write_text(RUTA.read_text(encoding="utf-8"), encoding="utf-8")
            salida = json.loads(self.ejecuta(json.dumps({"tool_name": "mcp__linear__get_issue"}), copia))
        self.assertEqual(salida["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()

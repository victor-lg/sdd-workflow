"""Tests de plugin-sdd/hooks/guarda-linear.py: REG-04 (VIC-17) y ADR-0009 §3.6 y M4 (VIC-58).
El agente lee, comenta, crea y empieza issues de la lista aprobada; edita solo las que no
están en ella; nunca cierra, cancela, borra ni archiva; lo que no conoce se bloquea."""
import importlib.util
import json
import os
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
LISTA = {("VIC", 41): "docs/specs/SPEC-DISCO-004.md"}


def aprobadas():
    return LISTA


def sin_lista():
    raise AssertionError("no debía mirar la lista aprobada")


def decide(herramienta, entrada, lista=aprobadas, servidor="mcp__linear__"):
    r = guarda.decidir(servidor + herramienta, entrada, CONF, lista)
    return r and r[0]


OTRAS = [
    "create_issue_label", "save_project", "update_project", "create_attachment", "save_document",
    "create_document", "update_document", "save_milestone", "create_issue_relation", "set_issue_status",
    "assign_issue", "herramienta_nueva", "getter_que_escribe", "get_or_create_issue", "list_and_update_issues",
    "get_issue_set_status", "save_issues", "save_issue_bulk",
]
CERRAR = ["delete_issue", "archive_issue", "unarchive_issue", "delete_comment", "delete_attachment",
          "delete_project", "archive_project", "close_issue", "cancel_issue", "issue_delete"]
LECTURAS = [
    "get_issue", "list_issues", "list_comments", "get_issue_status", "list_issue_statuses", "search_documentation",
    "extract_images", "get_attachment", "list_projects", "get_document", "list_cycles", "get_user",
]


class Herramientas(unittest.TestCase):
    def test_bloquea_lo_que_no_es_leer_comentar_crear_ni_empezar(self):
        for servidor in SERVIDORES:
            for herramienta in OTRAS:
                with self.subTest(nombre=servidor + herramienta):
                    self.assertEqual(decide(herramienta, {}, sin_lista, servidor), "herramienta")

    def test_cerrar_borrar_y_archivar_siempre(self):
        for servidor in SERVIDORES:
            for herramienta in CERRAR:
                with self.subTest(nombre=servidor + herramienta):
                    self.assertEqual(decide(herramienta, {"id": "VIC-99"}, sin_lista, servidor), "cerrar")

    def test_deja_leer_y_comentar(self):
        for servidor in SERVIDORES:
            for herramienta in LECTURAS + ["create_comment", "save_comment"]:
                with self.subTest(nombre=servidor + herramienta):
                    self.assertIsNone(decide(herramienta, {"issueId": "VIC-1", "body": "x"}, sin_lista, servidor))

    def test_las_lecturas_del_mcp_actual_pasan(self):
        """Las herramientas de lectura que expone hoy el MCP de Linear (2026-11-12)."""
        for herramienta in ("extract_images", "get_agent_skill", "get_attachment", "get_diff", "get_diff_threads",
                            "get_document", "get_issue", "get_issue_status", "get_milestone", "get_notifications",
                            "get_project", "get_release", "get_release_note", "get_status_updates", "get_team",
                            "get_template", "get_triage_responsibility", "get_user", "get_workspace",
                            "list_agent_skills", "list_comments", "list_custom_views", "list_cycles", "list_diffs",
                            "list_documents", "list_issue_labels", "list_issue_statuses", "list_issues",
                            "list_milestones", "list_project_labels", "list_projects", "list_release_notes",
                            "list_release_pipelines", "list_releases", "list_teams", "list_templates", "list_users",
                            "search_documentation"):
            with self.subTest(herramienta=herramienta):
                self.assertIsNone(decide(herramienta, {"id": "x"}, sin_lista))

    def test_editar_un_comentario_existente_no_es_comentar(self):
        self.assertEqual(decide("save_comment", {"id": "abc", "body": "x"}), "herramienta")
        self.assertEqual(decide("create_comment", {"id": "abc"}), "herramienta")
        self.assertIsNone(decide("get_comment", {"id": "abc"}))

    def test_otros_servidores_no_son_cosa_suya(self):
        for nombre in ("mcp__github__create_issue", "mcp__claude_ai_Claude_Docs__update", "Bash", "Write",
                       "mcp__notion__save_issue", "mcp_linear_save_issue", "linear__save_issue"):
            with self.subTest(nombre=nombre):
                self.assertIsNone(guarda.decidir(nombre, {"id": "VIC-1", "state": "Done"}, CONF, sin_lista))

    def test_el_matcher_cubre_los_servidores(self):
        registro = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        grupo = next(g for g in registro if "guarda-linear.py" in g["hooks"][0]["command"])
        self.assertTrue(grupo["hooks"][0]["command"].endswith("|| exit 2"))
        for servidor in SERVIDORES:
            with self.subTest(servidor=servidor):
                self.assertTrue(re.fullmatch(grupo["matcher"], servidor + "save_issue"))
        self.assertFalse(re.fullmatch(grupo["matcher"], "Bash"))


class Issues(unittest.TestCase):
    """save_issue sin id crea; con id edita. create_issue y update_issue, igual."""

    def test_crear_en_inbox_o_discovery(self):
        for herramienta in ("save_issue", "create_issue"):
            for entrada in ({"title": "t", "team": "Desarrollo"},
                            {"title": "t", "description": "d", "team": "Desarrollo", "labels": ["R1"], "state": "Inbox"},
                            {"title": "t", "team": "Desarrollo", "state": "discovery", "project": "p", "parentId": "VIC-3"}):
                with self.subTest(herramienta=herramienta, entrada=entrada):
                    self.assertIsNone(decide(herramienta, entrada, sin_lista))

    def test_crear_ya_empezada_o_cerrada_no(self):
        for estado in ("Ready", "In Progress", "started", "a2352fd0-dd43-4854-ad12-a9d5a77bced8"):
            with self.subTest(estado=estado):
                self.assertEqual(decide("save_issue", {"title": "t", "state": estado}, sin_lista), "fuera-de-lista")
        for estado in ("Done", "canceled", "Duplicate", "1eb64988-d3f3-4399-a9fb-9710f67406c6"):
            with self.subTest(estado=estado):
                self.assertEqual(decide("save_issue", {"title": "t", "state": estado}, sin_lista), "cerrar")

    def test_empezar_una_de_la_lista(self):
        for estado in ("Ready", "In Progress", "in review", "started", "unstarted"):
            for ident in ("VIC-41", "vic-41", " VIC-41 ", "VIC-041"):
                with self.subTest(estado=estado, ident=ident):
                    self.assertIsNone(decide("save_issue", {"id": ident, "state": estado}))

    def test_empezar_una_fuera_de_la_lista(self):
        for estado in ("Ready", "In Progress", "In Review", "3cdf9b6e-6713-45b8-b5a6-2681499dd37e"):
            with self.subTest(estado=estado):
                self.assertEqual(decide("save_issue", {"id": "VIC-43", "state": estado}), "fuera-de-lista")
        self.assertEqual(decide("update_issue", {"id": "VIC-43", "state": "In Progress"}), "fuera-de-lista")
        self.assertEqual(decide("save_issue", {"id": "VIC-410", "state": "In Progress"}), "fuera-de-lista")

    def test_cerrar_nunca_tampoco_las_de_la_lista(self):
        for ident in ("VIC-41", "VIC-43"):
            for estado in ("Done", "Canceled", "Duplicate", "completed", "duplicate"):
                with self.subTest(ident=ident, estado=estado):
                    self.assertEqual(decide("save_issue", {"id": ident, "state": estado}, sin_lista), "cerrar")

    def test_devolver_a_inbox_o_discovery(self):
        for ident in ("VIC-41", "VIC-43"):
            with self.subTest(ident=ident):
                self.assertIsNone(decide("save_issue", {"id": ident, "state": "Inbox"}, sin_lista))

    def test_editar_una_fuera_de_la_lista(self):
        for campos in ({"title": "t"}, {"description": "d"}, {"labels": ["R2"]},
                       {"title": "t", "description": "d", "labels": ["R1"], "state": "Discovery"}):
            with self.subTest(campos=campos):
                self.assertIsNone(decide("save_issue", {"id": "VIC-43", **campos}))

    def test_editar_una_de_la_lista_no(self):
        for campos in ({"title": "t"}, {"description": "d"}, {"labels": ["R2"]},
                       {"title": "t", "state": "In Progress"}, {"description": "d", "state": "Inbox"}):
            with self.subTest(campos=campos):
                self.assertEqual(decide("save_issue", {"id": "VIC-41", **campos}), "lista-aprobada")

    def test_empezar_y_editar_fuera_de_la_lista_no(self):
        self.assertEqual(decide("save_issue", {"id": "VIC-43", "title": "t", "state": "In Progress"}),
                         "fuera-de-lista")

    def test_por_uuid_no(self):
        """Por UUID la guarda no puede buscarla en la lista: se pide el identificador."""
        for ident in ("661e6c38-b16d-48a8-ae02-bb1407791586", "VIC 41", "41", "", 41, ["VIC-41"]):
            with self.subTest(ident=ident):
                self.assertEqual(decide("save_issue", {"id": ident, "title": "t"}, sin_lista), "desconocido")

    def test_campos_y_estados_que_no_conoce(self):
        casos = [{"id": "VIC-43", "assignee": "me"}, {"id": "VIC-43", "priority": 1}, {"id": "VIC-43", "team": "Otro"},
                 {"id": "VIC-43", "duplicateOf": "VIC-1"}, {"title": "t", "assignee": "me"},
                 {"title": "t", "duplicateOf": "VIC-1"}, {"id": "VIC-41", "state": "Archivada"},
                 {"title": "t", "state": "Triage"}]
        for entrada in casos:
            with self.subTest(entrada=entrada):
                self.assertEqual(decide("save_issue", entrada, sin_lista), "desconocido")

    def test_sin_cambios_no_mira_la_lista(self):
        self.assertIsNone(decide("save_issue", {"id": "VIC-41"}, sin_lista))

    def test_los_estados_no_se_solapan(self):
        clases = [{v.lower() for v in valores} for valores in CONF["estados"].values()]
        self.assertEqual(sum(map(len, clases)), len(set().union(*clases)))
        self.assertEqual(set(CONF["estados"]), {"libre", "empezar", "cerrar"})


class Entregas(unittest.TestCase):
    def test_solo_el_id_que_abre_cada_linea(self):
        texto = ("# SPEC\n\nVIC-1 en la intro\n\n## 13. Entregas\n\n- VIC-41: lógica (AC-01, AC-02; sustituye a VIC-30)\n"
                 "* **VIC-42**: interfaz\n1. vic-046 cosa\n  - VIC-47\nTexto que nombra VIC-48\n### Detalle\n- VIC-49\n"
                 "## 14. Otra\n- VIC-43\n# Fin\n- VIC-45\n")
        self.assertEqual(guarda.ids_de_entregas(texto),
                         [("VIC", 41), ("VIC", 42), ("VIC", 46), ("VIC", 47), ("VIC", 49)])

    def test_solo_el_titulo_exacto(self):
        for titulo in ("## Entregas", "## 13. Entregas", "### 2.1 entregas", "## Entregas ##"):
            with self.subTest(titulo=titulo):
                self.assertEqual(guarda.ids_de_entregas(f"{titulo}\n- VIC-41\n"), [("VIC", 41)])
        for titulo in ("## Entregas pendientes", "## Entregas fuera de alcance", "## Entregables", "## Otras entregas",
                       "Entregas", "##Entregas"):
            with self.subTest(titulo=titulo):
                self.assertEqual(guarda.ids_de_entregas(f"{titulo}\n- VIC-41\n"), [])

    def test_sin_bloques_de_codigo(self):
        texto = ("```markdown\n## Entregas\n- VIC-90\n```\n## Entregas\n- VIC-41\n~~~~\n- VIC-91\n```\n- VIC-92\n~~~~\n"
                 "- VIC-42\n")
        self.assertEqual(guarda.ids_de_entregas(texto), [("VIC", 41), ("VIC", 42)])

    def test_clave(self):
        self.assertEqual(guarda.clave(" vic-041 "), ("VIC", 41))
        for malo in ("VIC 41", "41", "", "661e6c38-b16d-48a8-ae02-bb1407791586", "VIC-4a"):
            with self.subTest(malo=malo):
                self.assertIsNone(guarda.clave(malo))


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t",
                           "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", *args],
                          check=True, capture_output=True, text=True).stdout


class ListaEnMain(unittest.TestCase):
    """Con repos de verdad: un bare hace de GitHub y su URL va en la configuración, como la de
    reglas-linear.json. Solo cuenta su main: ni la referencia local, ni la rama, ni el árbol."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.dir.name)
        self.remoto, self.repo = base / "remoto.git", base / "clon"
        git(base, "init", "-q", "--bare", "-b", "main", str(self.remoto))
        git(base, "init", "-q", "-b", "main", str(self.repo))
        specs = self.repo / "docs" / "specs"
        specs.mkdir(parents=True)
        (specs / "SPEC-DISCO-004.md").write_text(
            "# SPEC\nVIC-1\n## 13. Entregas\n- VIC-41: lógica (AC-01)\n- vic-042\n", encoding="utf-8")
        (specs / "_ejemplo-SPEC-AUTH-002.md").write_text("## Entregas\n- VIC-90\n", encoding="utf-8")
        (specs / "notas.txt").write_text("## Entregas\n- VIC-91\n", encoding="utf-8")
        (specs / "SPEC-ñ-005.md").write_text("## Entregas\n- VIC-50\n", encoding="utf-8")
        (self.repo / "web").mkdir()
        (self.repo / "web" / "x").write_text("x", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "x")
        git(self.repo, "remote", "add", "origin", "https://github.com/Prueba/Repo.git")
        git(self.repo, "push", "-q", str(self.remoto), "main")
        git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        (specs / "SPEC-DISCO-004.md").write_text("## Entregas\n- VIC-43\n", encoding="utf-8")
        git(self.repo, "commit", "-q", "-am", "en la rama")
        self.conf = {**CONF, "repos": {"prueba/repo": self.remoto.as_uri()}}
        self.esperado = {("VIC", 41): "docs/specs/SPEC-DISCO-004.md", ("VIC", 42): "docs/specs/SPEC-DISCO-004.md",
                         ("VIC", 50): "docs/specs/SPEC-ñ-005.md"}

    def tearDown(self):
        self.dir.cleanup()

    def test_lee_el_main_del_remoto(self):
        self.assertEqual(guarda.aprobadas_en_main(str(self.repo), self.conf), self.esperado)

    def test_desde_una_subcarpeta(self):
        for sub in ("web", "docs", "docs/specs"):
            with self.subTest(sub=sub):
                self.assertEqual(guarda.aprobadas_en_main(str(self.repo / sub), self.conf), self.esperado)

    def test_no_se_fia_de_las_referencias_locales(self):
        """Mover origin/main, o una rama o etiqueta llamada origin/main, no cambia la lista."""
        git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(self.repo, "branch", "origin/main", "HEAD")
        git(self.repo, "tag", "main", "HEAD")
        self.assertEqual(guarda.aprobadas_en_main(str(self.repo), self.conf), self.esperado)

    def test_main_nuevo_sin_fetch_falla(self):
        otro = pathlib.Path(self.dir.name) / "otro"
        git(self.dir.name, "clone", "-q", str(self.remoto), str(otro))
        (otro / "y").write_text("y", encoding="utf-8")
        git(otro, "add", "y")
        git(otro, "commit", "-q", "-m", "y")
        git(otro, "push", "-q", "origin", "main")
        with self.assertRaisesRegex(LookupError, "git fetch origin"):
            guarda.aprobadas_en_main(str(self.repo), self.conf)
        git(self.repo, "fetch", "-q", str(self.remoto), "main")
        self.assertEqual(guarda.aprobadas_en_main(str(self.repo), self.conf), self.esperado)

    def test_origen_que_no_esta_en_la_configuracion(self):
        for url in ("https://github.com/prueba/otro.git", "https://gitlab.com/prueba/repo.git",
                    self.remoto.as_uri(), "https://github.com/prueba/repo.git.evil.com/x"):
            with self.subTest(url=url):
                git(self.repo, "remote", "set-url", "origin", url)
                with self.assertRaises(LookupError):
                    guarda.aprobadas_en_main(str(self.repo), self.conf)

    def test_formas_del_origen(self):
        for url in ("https://github.com/prueba/repo", "git@github.com:Prueba/Repo.git",
                    "ssh://git@github.com/prueba/repo.git", "https://github.com/prueba/repo.git/"):
            with self.subTest(url=url):
                git(self.repo, "remote", "set-url", "origin", url)
                self.assertEqual(guarda.aprobadas_en_main(str(self.repo), self.conf), self.esperado)

    def test_insteadof_del_repo_no_cuenta(self):
        """El ls-remote va fuera del repo: un insteadOf en su configuración no desvía la URL."""
        falso = pathlib.Path(self.dir.name) / "falso.git"
        git(self.dir.name, "init", "-q", "--bare", "-b", "main", str(falso))
        git(self.repo, "push", "-q", str(falso), "HEAD:main")
        git(self.repo, "config", f"url.{falso.as_uri()}.insteadOf", self.remoto.as_uri())
        self.assertEqual(guarda.aprobadas_en_main(str(self.repo), self.conf), self.esperado)

    def test_fuera_de_un_repo_falla(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                guarda.aprobadas_en_main(d, self.conf)

    def test_principal_con_el_cwd(self):
        copia = pathlib.Path(self.dir.name) / "hook"
        copia.mkdir()
        (copia / "guarda-linear.py").write_text(RUTA.read_text(encoding="utf-8"), encoding="utf-8")
        (copia / "reglas-linear.json").write_text(json.dumps(self.conf), encoding="utf-8")

        def llama(entrada, cwd=self.repo):
            r = subprocess.run([sys.executable, str(copia / "guarda-linear.py")], capture_output=True, text=True,
                               input=json.dumps({"tool_name": "mcp__linear__save_issue", "tool_input": entrada,
                                                 "cwd": str(cwd)}))
            return json.loads(r.stdout)["hookSpecificOutput"] if r.stdout else None

        self.assertIsNone(llama({"id": "VIC-41", "state": "In Progress"}))
        self.assertIsNone(llama({"id": "VIC-41", "state": "In Progress"}, self.repo / "web"))
        self.assertIsNone(llama({"id": "VIC-43", "title": "t"}))
        fuera = llama({"id": "VIC-43", "state": "In Progress"})
        self.assertEqual(fuera["permissionDecision"], "deny")
        self.assertIn("VIC-43", fuera["permissionDecisionReason"])
        self.assertIn("En su lugar:", fuera["permissionDecisionReason"])
        for ident, cwd in (("VIC-42", self.repo), ("VIC-042", self.repo / "web")):
            with self.subTest(ident=ident):
                aprobada = llama({"id": ident, "description": "d"}, cwd)
                self.assertEqual(aprobada["permissionDecision"], "deny")
                self.assertIn("docs/specs/SPEC-DISCO-004.md", aprobada["permissionDecisionReason"])
                self.assertNotIn("{", aprobada["permissionDecisionReason"])
        git(self.repo, "remote", "set-url", "origin", "https://github.com/prueba/otro.git")
        for entrada in ({"id": "VIC-41", "state": "In Progress"}, {"id": "VIC-43", "title": "t"}):
            with self.subTest(entrada=entrada):
                salida = llama(entrada)
                self.assertEqual(salida["permissionDecision"], "deny")
                self.assertIn("reglas-linear.json", salida["permissionDecisionReason"])


class Principal(unittest.TestCase):
    def ejecuta(self, entrada, ruta=RUTA):
        r = subprocess.run([sys.executable, str(ruta)], input=entrada, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        return r.stdout

    def test_deja_pasar_en_silencio(self):
        self.assertEqual(self.ejecuta(json.dumps({"tool_name": "mcp__linear__get_issue", "tool_input": {}})), "")

    def test_bloquea_y_dice_que_hacer(self):
        for entrada, regla in (({"id": "VIC-1", "state": "Done"}, "M4"), ({"id": "x-y-z", "title": "t"}, "no reconoce")):
            with self.subTest(entrada=entrada):
                salida = json.loads(self.ejecuta(json.dumps(
                    {"tool_name": "mcp__linear__save_issue", "tool_input": entrada})))["hookSpecificOutput"]
                self.assertEqual(salida["permissionDecision"], "deny")
                self.assertIn(regla, salida["permissionDecisionReason"])
                self.assertIn("En su lugar:", salida["permissionDecisionReason"])
                self.assertIn("mcp__linear__save_issue", salida["permissionDecisionReason"])
                self.assertNotIn("{", salida["permissionDecisionReason"])

    def test_todos_los_mensajes_dicen_que_hacer(self):
        for regla, info in CONF["reglas"].items():
            with self.subTest(regla=regla):
                self.assertEqual(info["nivel"], "bloquear")
                self.assertIn("En su lugar:", info["mensaje"])
                self.assertIn("{herramienta}", info["mensaje"])

    def test_sin_repo_falla_cerrado(self):
        """Sin origin/main no hay lista: empezar o editar se bloquea; crear y comentar, no."""
        with tempfile.TemporaryDirectory() as d:
            for entrada in ({"id": "VIC-41", "state": "In Progress"}, {"id": "VIC-43", "title": "t"}):
                with self.subTest(entrada=entrada):
                    r = subprocess.run([sys.executable, str(RUTA)], capture_output=True, text=True, cwd=d,
                                       env={**os.environ, "GIT_CEILING_DIRECTORIES": d}, input=json.dumps(
                                           {"tool_name": "mcp__linear__save_issue", "tool_input": entrada, "cwd": d}))
                    salida = json.loads(r.stdout)["hookSpecificOutput"]
                    self.assertEqual(salida["permissionDecision"], "deny")
                    self.assertIn("git fetch origin", salida["permissionDecisionReason"])
            r = subprocess.run([sys.executable, str(RUTA)], capture_output=True, text=True, input=json.dumps(
                {"tool_name": "mcp__linear__save_issue", "tool_input": {"title": "t"}, "cwd": d}))
            self.assertEqual(r.stdout, "")

    def test_respeta_el_nivel(self):
        with tempfile.TemporaryDirectory() as d:
            copia = pathlib.Path(d) / "guarda-linear.py"
            copia.write_text(RUTA.read_text(encoding="utf-8"), encoding="utf-8")
            conf = json.loads(json.dumps(CONF))
            conf["reglas"]["cerrar"]["nivel"] = "preguntar"
            (pathlib.Path(d) / "reglas-linear.json").write_text(json.dumps(conf), encoding="utf-8")
            salida = json.loads(self.ejecuta(json.dumps(
                {"tool_name": "mcp__linear__delete_issue", "tool_input": {"id": "VIC-1"}}), copia))
        self.assertEqual(salida["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_entrada_rota_o_sin_reglas_falla_cerrado(self):
        for entrada in ("", "{}", "[]", json.dumps({"tool_name": "mcp__linear__save_issue", "tool_input": [1]})):
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

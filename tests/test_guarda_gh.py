"""Tests de plugin-sdd/hooks/guarda-gh.py (VIC-17): REG-43, REG-93 y REG-102/M5. gh pr ready
se prueba con la respuesta de gh simulada; nunca se llama a GitHub."""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HOOKS = RAIZ / "plugin-sdd" / "hooks"
RUTA = HOOKS / "guarda-gh.py"
_spec = importlib.util.spec_from_file_location("guarda_gh", RUTA)
guarda = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guarda)
CONF = json.loads((HOOKS / "reglas-gh.json").read_text(encoding="utf-8"))

BLOQUEADAS = {
    "pr-sin-borrador": [
        "gh pr create --title 'feat(x): y' --body-file .tareas/VIC-1/pr.md",
        "gh pr create -t x -F f.md",
        "gh pr create --fill",
        "gh pr new --fill",
        "gh pr create --draft=false --fill",
        "gh pr create -t -d -F f.md",
        "GH_REPO=a/b gh pr create --fill",
        "git push origin x && gh pr create --fill",
        "cd sub && gh pr create --fill",
        "echo $(gh pr create --fill)",
    ],
    "cuerpo-en-la-orden": [
        "gh pr create --draft --title x --body 'hola'",
        "gh pr create -d -t x -b hola",
        "gh pr create -d -t x -bhola",
        "gh pr create -d --body=hola",
        "gh pr comment 3 --body 'hola'",
        "gh pr comment 3 -b \"$(cat f.md)\"",
        "gh pr comment 3 --body \"`cat f.md`\"",
        "gh pr edit 3 --body x",
        "gh pr edit 3 -b x",
        "gh pr review 3 --comment -b x",
        "gh pr review 3 -r -b x",
        "gh pr merge 3 --squash -b x",
        "gh issue comment 3 --body x",
        "gh issue create -t x -b y",
        "gh issue edit 3 -b y",
        "echo hola | gh pr comment 3 --body-file -",
        "printf '%s' \"$X\" | gh pr comment 3 -F -",
        "gh pr comment 3 --body-file - <<EOF\nHola $(date)\nEOF",
        "gh pr comment 3 -F - <<FIN\ncuerpo\nFIN",
        "gh api repos/a/b/issues/3/comments -f body=hola",
        "gh api repos/a/b/issues/3/comments -F body=hola",
        "gh api repos/a/b/issues/3/comments --raw-field body=hola",
        "gh api repos/a/b/issues/3/comments --field=body=hola",
        "gh api -X PATCH repos/a/b/pulls/3 -f body=x",
    ],
    "ready-por-api": [
        "gh api graphql -f query='mutation { markPullRequestReadyForReview(input: {pullRequestId: \"X\"}) { clientMutationId } }'",
        "gh api graphql -F query=@x.graphql -f q=markPullRequestReadyForReview",
    ],
}

LEGITIMAS = [
    "gh pr create --draft --title 'feat(x): y' --body-file .tareas/VIC-1/pr.md",
    "gh pr create -d -t x -F f.md",
    "gh pr create --fill --draft",
    "gh pr create --draft=true --fill",
    "gh pr comment 3 --body-file .tareas/VIC-1/c.md",
    "gh pr comment 3 -F c.md",
    "{ cat .tareas/VIC-1/g4.md; cat <<'METRICAS_SDD'\nMétricas G4: PR #3 · ronda 1 · confirmados 0 · descartados 0 · corregidos 0\nMETRICAS_SDD\n} | gh pr comment 3 --body-file -",
    "cat c.md | gh pr comment 3 --body-file -",
    "gh pr comment 3 --body-file - < c.md",
    "gh pr edit 3 --title 'fix(x): y'",
    "gh pr edit 3 --body-file .tareas/VIC-1/pr.md",
    "gh pr edit 3 --add-label R2",
    "gh pr review 3 --approve",
    "gh pr view 3 --json body",
    "gh pr checks 3",
    "gh pr list --search 'is:draft --body x'",
    "gh pr ready 3 --undo",
    "gh issue view 3",
    "gh api repos/a/b/pulls/3",
    "gh api repos/a/b/issues/3/comments -F body=@c.md",
    "gh api graphql -f query='{ viewer { login } }'",
    "gh run rerun 123",
    "gh --version",
    "echo 'gh pr create --fill'",
    "git commit -m 'usa gh pr comment --body x'",
    "grep -rn 'gh pr create' docs",
    "cat <<'FIN'\ngh pr comment 3 --body x\nFIN",
]

SE_ESQUIVA = [
    "bash -c 'gh pr create --fill'",
    "eval 'gh pr comment 3 --body x'",
    "C=create; gh pr $C --fill",
    "gh api repos/a/b/pulls -f title=x -f head=y -f base=main",
    "gh api repos/a/b/pulls -F draft=false -f title=x -f head=y -f base=main",
    "./abrir-pr.sh",
]


def pr(checks, borrador=True, comentarios=("Métricas G4: PR #3 · ronda 1 · confirmados 1 · descartados 0 · corregidos 1",),
       mergeable="MERGEABLE", rama="feat/vic-1-x", oid="a" * 40):
    return {"isDraft": borrador, "headRefName": rama, "headRefOid": oid, "mergeable": mergeable,
            "statusCheckRollup": checks, "comments": [{"body": c} for c in comentarios]}


def run(nombre, conclusion="SUCCESS", status="COMPLETED", inicio="2026-11-11T10:00:00Z", flujo="sdd", ejecucion=7):
    return {"__typename": "CheckRun", "name": nombre, "status": status, "conclusion": conclusion,
            "startedAt": inicio, "completedAt": inicio if status == "COMPLETED" else None, "workflowName": flujo,
            "detailsUrl": f"https://github.com/a/b/actions/runs/{ejecucion}/job/1"}


VERDE = [run("checks-sdd"), run("tests", flujo="tests")]


class Guarda(unittest.TestCase):
    def decide(self, comando, respuesta=None):
        with mock.patch.object(guarda, "_gh", return_value=json.dumps(respuesta or pr(VERDE))) as gh, \
                mock.patch.object(guarda, "_git", return_value=None):
            self.gh = gh
            return guarda.decidir(comando, "/home/u/proyecto", CONF)

    def test_formas_bloqueadas(self):
        for regla, comandos in BLOQUEADAS.items():
            for comando in comandos:
                with self.subTest(comando=comando):
                    self.assertEqual(self.decide(comando)[0], regla)

    def test_formas_legitimas(self):
        for comando in LEGITIMAS:
            with self.subTest(comando=comando):
                self.assertEqual(self.decide(comando), (None, None))

    def test_limitacion_conocida_no_se_detecta(self):
        for comando in SE_ESQUIVA:
            with self.subTest(comando=comando):
                self.assertEqual(self.decide(comando), (None, None))

    def test_el_cuerpo_gana_a_borrador(self):
        self.assertEqual(self.decide("gh pr create --title x --body y")[0], "cuerpo-en-la-orden")

    def test_sin_cerrar_falla_cerrado_si_menciona_gh(self):
        self.assertEqual(self.decide("gh pr comment 3 --body 'sin cerrar")[0], "sin-analizar")
        self.assertEqual(self.decide("echo 'sin cerrar"), (None, None))


class Ready(unittest.TestCase):
    def decide(self, respuesta, comando="gh pr ready 3", git=None):
        with mock.patch.object(guarda, "_gh", return_value=json.dumps(respuesta)) as gh, \
                mock.patch.object(guarda, "_git", side_effect=lambda cwd, *a: (git or {}).get(a[0])):
            resultado = guarda.decidir(comando, "/home/u/proyecto", CONF)
        self.llamada = gh.call_args
        return resultado

    def test_todo_en_verde(self):
        self.assertEqual(self.decide(pr(VERDE)), (None, None))

    def test_pide_el_pr_que_toca(self):
        self.decide(pr(VERDE), "gh pr ready 3 -R a/b")
        self.assertEqual(self.llamada.args[1:5], ("pr", "view", "3", "--repo"))
        self.decide(pr(VERDE), "cd /otro && gh pr ready")
        self.assertEqual(self.llamada.args[0], "/otro")
        self.assertEqual(self.llamada.args[1:4], ("pr", "view", "--json"))

    def test_ya_no_es_borrador(self):
        self.assertEqual(self.decide(pr([], borrador=False)), (None, None))

    def test_check_cancelado_m5(self):
        regla, checks = self.decide(pr([run("checks-sdd", "CANCELLED", ejecucion=4321), run("tests", flujo="tests")]))
        self.assertEqual((regla, checks), ("ready-check-cancelado", ["checks-sdd (gh run rerun 4321)"]))

    def test_cuenta_la_ultima_ejecucion_de_cada_check(self):
        viejo = run("checks-sdd", "CANCELLED", inicio="2026-11-11T09:00:00Z")
        nuevo = run("checks-sdd", inicio="2026-11-11T09:05:00Z")
        self.assertEqual(self.decide(pr([viejo, nuevo])), (None, None))
        self.assertEqual(self.decide(pr([nuevo, run("checks-sdd", "CANCELLED", inicio="2026-11-11T09:06:00Z")]))[0],
                         "ready-check-cancelado")
        en_cola = run("checks-sdd", conclusion=None, status="QUEUED", inicio=None)
        self.assertEqual(self.decide(pr([nuevo, en_cola])), ("ready-ci-pendiente", ["checks-sdd"]))
        cero = run("checks-sdd", conclusion=None, status="QUEUED", inicio="0001-01-01T00:00:00Z")
        self.assertEqual(self.decide(pr([nuevo, cero]))[0], "ready-ci-pendiente")

    def test_ci_roja(self):
        for conclusion in ("FAILURE", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE", "STALE", None):
            with self.subTest(conclusion=conclusion):
                self.assertEqual(self.decide(pr([run("tests", conclusion)])), ("ready-ci-roja", ["tests"]))

    def test_neutros_y_saltados_cuentan_como_verde(self):
        self.assertEqual(self.decide(pr([run("a", "SKIPPED"), run("b", "NEUTRAL", flujo="b")])), (None, None))

    def test_ci_pendiente(self):
        for status in ("IN_PROGRESS", "QUEUED", "PENDING", "WAITING"):
            with self.subTest(status=status):
                self.assertEqual(self.decide(pr([run("tests", None, status)]))[0], "ready-ci-pendiente")

    def test_estados_de_commit(self):
        contexto = {"__typename": "StatusContext", "context": "ci/externa", "state": "PENDING",
                    "startedAt": "2026-11-11T10:00:00Z"}
        self.assertEqual(self.decide(pr([contexto]))[0], "ready-ci-pendiente")
        self.assertEqual(self.decide(pr([{**contexto, "state": "FAILURE"}]))[0], "ready-ci-roja")
        self.assertEqual(self.decide(pr([{**contexto, "state": "ERROR"}]))[0], "ready-ci-roja")
        self.assertEqual(self.decide(pr([{**contexto, "state": "SUCCESS"}])), (None, None))

    def test_cancelado_gana_a_rojo_y_pendiente(self):
        checks = [run("a", "FAILURE"), run("b", None, "IN_PROGRESS", flujo="b"), run("c", "CANCELLED", flujo="c")]
        self.assertEqual(self.decide(pr(checks))[0], "ready-check-cancelado")

    def test_sin_checks(self):
        self.assertEqual(self.decide(pr([])), ("ready-sin-checks", None))

    def test_conflictos(self):
        self.assertEqual(self.decide(pr(VERDE, mergeable="CONFLICTING"))[0], "ready-conflictos")
        self.assertEqual(self.decide(pr(VERDE, mergeable="UNKNOWN")), (None, None))

    def test_rama_local_sin_subir(self):
        git = {"symbolic-ref": "feat/vic-1-x", "rev-parse": "b" * 40}
        self.assertEqual(self.decide(pr(VERDE), "gh pr ready", git)[0], "ready-sin-push")
        self.assertEqual(self.decide(pr(VERDE), "gh pr ready", {**git, "rev-parse": "a" * 40}), (None, None))
        self.assertEqual(self.decide(pr(VERDE), "gh pr ready", {**git, "symbolic-ref": "otra"}), (None, None))
        self.assertEqual(self.decide(pr(VERDE), "gh pr ready 3", git), (None, None))

    def test_sin_g4_pregunta(self):
        for comentarios in ((), ("Métricas mutación: sin mutaciones",), ("```\nMétricas G4: PR #3 · ronda\n```",)):
            with self.subTest(comentarios=comentarios):
                self.assertEqual(self.decide(pr(VERDE, comentarios=comentarios))[0], "ready-sin-g4")
        self.assertEqual(CONF["reglas"]["ready-sin-g4"]["nivel"], "preguntar")

    def test_gh_falla_cerrado(self):
        for efecto in (guarda.NoPuedoMirar("sin red"), ["no es json"]):
            with self.subTest(efecto=efecto), mock.patch.object(guarda, "_gh", side_effect=efecto):
                self.assertEqual(guarda.decidir("gh pr ready 3", "/home/u/proyecto", CONF)[0], "ready-sin-mirar")
        self.assertEqual(guarda.decidir("pushd x && gh pr ready", "/home/u/proyecto", CONF)[0], "ready-sin-mirar")

    def test_gh_real_sin_red_falla_cerrado(self):
        with mock.patch.object(guarda.subprocess, "run", side_effect=OSError("sin gh")):
            self.assertEqual(guarda.decidir("gh pr ready 3", "/home/u/proyecto", CONF)[0], "ready-sin-mirar")
        error = subprocess.CompletedProcess([], 1, "", "HTTP 401")
        with mock.patch.object(guarda.subprocess, "run", return_value=error):
            self.assertEqual(guarda.decidir("gh pr ready 3", "/home/u/proyecto", CONF)[0], "ready-sin-mirar")


class GitReal(unittest.TestCase):
    def test_git_lee_la_rama_y_falla_en_silencio(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "init", "-q", "-b", "feat/x", d], check=True)
            self.assertEqual(guarda._git(d, "symbolic-ref", "--short", "-q", "HEAD"), "feat/x")
            self.assertIsNone(guarda._git(d, "rev-parse", "HEAD"))
            self.assertIsNone(guarda._git(os.path.join(d, "no-existe"), "rev-parse", "HEAD"))


class Principal(unittest.TestCase):
    def ejecuta(self, comando, ruta=RUTA):
        entrada = json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(RAIZ)})
        r = subprocess.run([sys.executable, str(ruta)], input=entrada, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        return r.stdout

    def test_deja_pasar_en_silencio(self):
        self.assertEqual(self.ejecuta("gh pr create --draft --fill"), "")

    def test_bloquea_con_alternativa(self):
        salida = json.loads(self.ejecuta("gh pr create --fill"))["hookSpecificOutput"]
        self.assertEqual(salida["permissionDecision"], "deny")
        self.assertIn("--draft", salida["permissionDecisionReason"])
        self.assertIn("no la esquives", salida["permissionDecisionReason"])

    def test_el_mensaje_nombra_los_checks(self):
        with mock.patch.object(guarda, "_gh", return_value=json.dumps(pr([run("checks-sdd", "CANCELLED")]))), \
                mock.patch.object(sys, "stdin", new=__import__("io").StringIO(json.dumps(
                    {"tool_name": "Bash", "tool_input": {"command": "gh pr ready 3"}, "cwd": "/x"}))), \
                mock.patch.object(sys, "stdout", new=__import__("io").StringIO()) as salida:
            guarda.main()
        motivo = json.loads(salida.getvalue())["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("checks cancelados (checks-sdd (gh run rerun 7))", motivo)

    def test_entrada_rota_falla_cerrado(self):
        for entrada in ("", "{}", '{"tool_input": {}}'):
            with self.subTest(entrada=entrada):
                r = subprocess.run([sys.executable, str(RUTA)], input=entrada, capture_output=True, text=True)
                self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_sin_reglas_o_sin_lector_falla_cerrado(self):
        for ficheros in (("guarda-gh.py",), ("guarda-gh.py", "reglas-gh.json")):
            with self.subTest(ficheros=ficheros), tempfile.TemporaryDirectory() as d:
                for nombre in ficheros:
                    (pathlib.Path(d) / nombre).write_text((HOOKS / nombre).read_text(encoding="utf-8"),
                                                          encoding="utf-8")
                salida = json.loads(self.ejecuta("gh pr list", pathlib.Path(d) / "guarda-gh.py"))
                self.assertEqual(salida["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_mensajes_dicen_que_hacer(self):
        for regla, info in CONF["reglas"].items():
            with self.subTest(regla=regla):
                self.assertIn(info["nivel"], ("bloquear", "preguntar"))
                if info["nivel"] == "bloquear":
                    self.assertIn("En su lugar:", info["mensaje"])

    def test_registro_y_plazo(self):
        registro = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        grupo = next(g for g in registro for h in g["hooks"] if "guarda-gh.py" in h["command"])
        hook = next(h for h in grupo["hooks"] if "guarda-gh.py" in h["command"])
        self.assertEqual(grupo["matcher"], "Bash")
        self.assertTrue(hook["command"].endswith("|| exit 2"))
        # gh pr view y dos llamadas a git de 3 s caben antes del timeout del hook.
        self.assertLess(CONF["segundos_gh"] + 2 * 3, hook["timeout"])


if __name__ == "__main__":
    unittest.main()

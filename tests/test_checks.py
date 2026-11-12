"""Tests de plantilla-proyecto/.github/sdd/checks.py (VIC-17): M11 (rama, título y
enlace a la issue), REG-34 (sin menciones a Claude), M39 (historial en la cabecera
de una spec), M7 (comillas en la cabecera de los ADR), M17 (`.gitignore` de la
plantilla y de este repo con los ficheros del sandbox) y la configuración de lefthook
(ADR-0008). Casos que pasan y que fallan."""
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "plantilla-proyecto"
RUTA = PLANTILLA / ".github" / "sdd" / "checks.py"
_spec = importlib.util.spec_from_file_location("checks_sdd", RUTA)
checks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checks)

ENTORNO_GIT = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
               "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@t"}


def ejecutar(check, *args):
    inf = checks.Informe()
    check(inf, *args)
    return inf


def cuerpo_plantilla(primera: str) -> str:
    """La plantilla de PR real con la línea de `Fixes VIC-<N>` sustituida."""
    texto = (PLANTILLA / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
    return texto.replace("Fixes VIC-<N>", primera, 1)


# --- M11 -------------------------------------------------------------------

class TestConvenciones(unittest.TestCase):
    def comprobar(self, rama="feat/vic-12-calculo", titulo="feat(calculo): suma el peso disco a disco",
                  cuerpo=None):
        return ejecutar(checks.check_convenciones, rama, titulo,
                        cuerpo if cuerpo is not None else cuerpo_plantilla("Fixes VIC-12"))

    def test_pr_correcto_pasa_sin_avisos(self):
        inf = self.comprobar()
        self.assertEqual((inf.errores, inf.avisos), ([], []))

    def test_ramas_validas(self):
        for rama in ["feat/vic-12-calculo", "spec/vic-18-calc-004-historial", "adr/vic-19-0009-modelos",
                     "ci/vic-17-checks", "chore/vic-3-a", "fix/vic-17-redondeo-peso"]:
            with self.subTest(rama=rama):
                tipo = rama.split("/")[0]
                inf = self.comprobar(rama=rama, titulo=f"{tipo}: algo",
                                     cuerpo=cuerpo_plantilla(f"Fixes VIC-{rama.split('-')[1]}"))
                self.assertEqual((inf.errores, inf.avisos), ([], []))

    def test_ramas_invalidas(self):
        for rama in ["vic-12-calculo", "feat/calculo", "feat/12-calculo", "feature/vic-12-calculo",
                     "feat/VIC-12-calculo", "feat/vic-12", "feat/vic-12-Calculo", "feat/vic-12-cálculo",
                     "feat/vic-12-calculo_peso", "feat/vic-12-calculo-", "feat/vic-012-calculo",
                     "spec-calc-003-presentacion", "feat/vic-12-calculo/extra", ""]:
            with self.subTest(rama=rama):
                inf = self.comprobar(rama=rama)
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("la rama", inf.errores[0])

    def test_rama_larga_avisa(self):
        rama = "feat/vic-12-" + "-".join(["palabra"] * 6)
        inf = self.comprobar(rama=rama)
        self.assertEqual(inf.errores, [])
        self.assertIn("caracteres", inf.avisos[0])

    def test_titulos_validos(self):
        for titulo in ["feat(calculo): suma el peso", "feat: suma el peso", "feat(calculo)!: cambia el formato",
                       "feat!: cambia el formato", "feat(SPEC-CALC-003): ajusta el texto"]:
            with self.subTest(titulo=titulo):
                self.assertEqual(self.comprobar(titulo=titulo).errores, [])

    def test_titulos_invalidos(self):
        for titulo in ["suma el peso", "Feat(calculo): suma", "feature: suma", "feat(calculo) suma",
                       "feat(calculo):suma", "feat (calculo): suma", "feat(): suma", "feat(mi zona): suma",
                       "feat(calculo): ", "[VIC-12] suma el peso", ""]:
            with self.subTest(titulo=titulo):
                inf = self.comprobar(titulo=titulo)
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("título", inf.errores[0])

    def test_el_alcance_no_es_el_id(self):
        for titulo in ["feat(VIC-12): suma el peso", "feat(vic-12): suma el peso"]:
            with self.subTest(titulo=titulo):
                inf = self.comprobar(titulo=titulo)
                self.assertEqual(len(inf.errores), 1)
                self.assertIn("alcance", inf.errores[0])

    def test_descripcion_de_mas_de_72_falla(self):
        self.assertEqual(self.comprobar(titulo="feat: " + "a" * 72).errores, [])
        inf = self.comprobar(titulo="feat: " + "a" * 73)
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("73", inf.errores[0])

    def test_mayuscula_o_punto_final_avisan(self):
        for titulo in ["feat: Suma el peso", "feat: suma el peso."]:
            with self.subTest(titulo=titulo):
                inf = self.comprobar(titulo=titulo)
                self.assertEqual(inf.errores, [])
                self.assertIn("minúscula", inf.avisos[0])

    def test_tipo_distinto_de_la_rama_avisa(self):
        inf = self.comprobar(titulo="fix(calculo): corrige el peso")
        self.assertEqual(inf.errores, [])
        self.assertIn("no es el de la rama", inf.avisos[0])

    def test_enlaces_validos_decision_4(self):
        for primera in ["Fixes VIC-12", "Part of VIC-12", "Refs VIC-12", "Refs: VIC-12",
                        "Fixes VIC-12 y algo más"]:
            with self.subTest(primera=primera):
                inf = self.comprobar(cuerpo=cuerpo_plantilla(primera))
                self.assertEqual((inf.errores, inf.avisos), ([], []))

    def test_enlace_sin_seccion_ni_comentarios(self):
        inf = self.comprobar(cuerpo="<!-- nota -->\n\nPart of VIC-12\n\nResto.")
        self.assertEqual(inf.errores, [])

    def test_enlaces_invalidos(self):
        for primera in ["Fixes VIC-<N>", "Closes VIC-12", "fixes VIC-12", "Fixes #12", "Fixes VIC12",
                        "Issue de Linear: VIC-12", "Este PR arregla VIC-12", "Fixes ABC-12"]:
            with self.subTest(primera=primera):
                inf = self.comprobar(cuerpo=cuerpo_plantilla(primera))
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("descripción del PR", inf.errores[0])

    def test_el_enlace_tiene_que_ser_la_primera_linea(self):
        inf = self.comprobar(cuerpo="Resumen del cambio.\n\nFixes VIC-12\n")
        self.assertEqual(len(inf.errores), 1)

    def test_descripcion_vacia_falla(self):
        inf = self.comprobar(cuerpo="")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("está vacía", inf.errores[0])

    def test_id_distinto_de_la_rama_avisa(self):
        inf = self.comprobar(cuerpo=cuerpo_plantilla("Part of VIC-13"))
        self.assertEqual(inf.errores, [])
        self.assertIn("VIC-13", inf.avisos[0])


# --- REG-34 ----------------------------------------------------------------

class TestAutoria(unittest.TestCase):
    MALAS = ["Co-Authored-By: Claude <noreply@anthropic.com>",
             "co-authored-by: Claude Opus 5.5 <noreply@anthropic.com>",
             "🤖 Generated with [Claude Code](https://claude.com/claude-code)",
             "Generated with Claude Code"]
    BUENAS = ["Co-Authored-By: Ana <ana@example.com>", "Refs: VIC-12",
              "Revisado por Claude con sdd-review", "Generated with esbuild"]

    def test_pr_y_commits_limpios_pasan(self):
        for texto in self.BUENAS:
            with self.subTest(texto=texto):
                inf = ejecutar(checks.check_autoria, "feat: algo", f"Fixes VIC-1\n\n{texto}",
                               [f"feat: algo\n\n{texto}\n"])
                self.assertEqual(inf.errores, [])

    def test_mencion_en_la_descripcion_falla(self):
        for texto in self.MALAS:
            with self.subTest(texto=texto):
                inf = ejecutar(checks.check_autoria, "feat: algo", f"Fixes VIC-1\n\n{texto}", [])
                self.assertEqual(len(inf.errores), 1)
                self.assertIn("descripción", inf.errores[0])

    def test_mencion_en_commits_falla_y_los_cuenta(self):
        mensajes = ["feat: a\n\n" + self.MALAS[0], "feat: b", "fix: c\n\n" + self.MALAS[2]]
        inf = ejecutar(checks.check_autoria, "feat: algo", "Fixes VIC-1", mensajes)
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("2 commit(s)", inf.errores[0])


# --- M39 -------------------------------------------------------------------

SPEC_LIMPIA = """---
id: SPEC-CALC-003
titulo: Presentación
estado: aprobada
version: 0.5
riesgo: R1
sustituye: null
adr: [ADR-0001]
transversales: []
---

<!-- Qué cubre esta spec frente a SPEC-CALC-001 y SPEC-CALC-002. -->

# SPEC-CALC-003 — Presentación

## 1. Objetivo

Mostrar el peso. Desde el 2026-10-26 el aviso dura hasta la siguiente acción (PR #16, ronda 3).
"""

SPEC_CON_HISTORIAL = """---
id: SPEC-CALC-003
titulo: Presentación
estado: aprobada
version: 0.5
riesgo: R1
---

<!--
En la revisión del PR #16, Víctor confirmó como reglas tres inferencias.
Tras la ronda 1 de G4 (2026-10-26), Víctor decidió el aviso general.
La versión 0.2 (VIC-13) solo cambia el peso de la recta.
-->

# SPEC-CALC-003 — Presentación

## 1. Objetivo
"""


class TestHistorial(unittest.TestCase):
    def test_spec_sin_historial_no_avisa(self):
        # Fechas, PR y rondas en el cuerpo no cuentan: solo la cabecera.
        inf = ejecutar(checks.check_historial, {"docs/specs/SPEC-CALC-003-p.md": SPEC_LIMPIA})
        self.assertEqual((inf.errores, inf.avisos), ([], []))

    def test_plantilla_y_ejemplo_no_avisan(self):
        specs = PLANTILLA / "docs" / "specs"
        for nombre in ["_plantilla-spec.md", "_ejemplo-SPEC-AUTH-002.md"]:
            with self.subTest(nombre=nombre):
                inf = ejecutar(checks.check_historial, {nombre: (specs / nombre).read_text(encoding="utf-8")})
                self.assertEqual(inf.avisos, [])

    def test_historial_en_el_comentario_de_cabecera_avisa(self):
        inf = ejecutar(checks.check_historial, {"docs/specs/SPEC-CALC-003-p.md": SPEC_CON_HISTORIAL})
        self.assertEqual(inf.errores, [], "M39 solo avisa")
        self.assertEqual(len(inf.avisos), 1)
        for senal in ["rondas de revisión", "versiones anteriores", "referencias a PR", "fechas"]:
            self.assertIn(senal, inf.avisos[0])

    def test_cada_senal_por_separado_avisa(self):
        for linea in ["Tras la ronda 2 de G4 se decidió X.", "La versión 0.3 cambia el aviso.",
                      "Lo confirmó Víctor en el PR #22.", "Decidido el 2026-10-29."]:
            with self.subTest(linea=linea):
                texto = SPEC_LIMPIA.replace("<!-- Qué cubre", f"<!-- {linea} Qué cubre")
                self.assertEqual(len(ejecutar(checks.check_historial, {"s.md": texto}).avisos), 1)

    def test_campo_o_seccion_de_historial_avisa(self):
        con_campo = SPEC_LIMPIA.replace("transversales: []", "transversales: []\nhistorial: v0.4 cambia X")
        con_seccion = SPEC_LIMPIA + "\n## 13. Historial de cambios\n\n- 0.4: …\n"
        for texto in [con_campo, con_seccion]:
            self.assertEqual(len(ejecutar(checks.check_historial, {"s.md": texto}).avisos), 1)

    def test_spec_sin_titulo_mira_todo_el_texto(self):
        texto = "---\nid: SPEC-A-001\n---\n\nTras la ronda 1 cambió.\n"
        self.assertEqual(len(ejecutar(checks.check_historial, {"s.md": texto}).avisos), 1)


# --- M7 --------------------------------------------------------------------

def adr(cabecera: str) -> str:
    return f"---\nid: ADR-0002\nestado: Aceptado  # Propuesto | Aceptado\n{cabecera}\n---\n\n# ADR-0002 — x\n"


class TestCabeceraAdr(unittest.TestCase):
    def test_cabeceras_validas(self):
        for cabecera in ["referencias: []", 'referencias: ["PR #12", "SPEC-CALC-001"]',
                         "referencias: ['PR #12']", 'referencias: ["a, b", "c"]  # comentario',
                         'referencias:\n  - "PR #12"\n  - \'VIC-3\'  # comentario',
                         "sustituye: null", 'modifica:\n  - "docs/x.md §7, convenciones"',
                         'referencias: [\n  "PR #12",  # comentario\n  "VIC-3"\n]\nsustituye: null']:
            with self.subTest(cabecera=cabecera):
                self.assertEqual(ejecutar(checks.check_adr, {"docs/adr/0002-x.md": adr(cabecera)}).errores, [])

    def test_plantilla_y_adr_con_comillas_pasan(self):
        ficheros = {"_plantilla-adr.md": PLANTILLA / "docs" / "adr" / "_plantilla-adr.md",
                    "0007.md": RAIZ / "docs" / "adr" / "0007-autoria-y-convenciones.md"}
        textos = {k: v.read_text(encoding="utf-8") for k, v in ficheros.items()}
        self.assertEqual(ejecutar(checks.check_adr, textos).errores, [])

    def test_adr_sin_comillas_de_este_repo_falla(self):
        # ADR-0001 es anterior a M7. El check solo mira los ADR que cambia el PR.
        texto = (RAIZ / "docs" / "adr" / "0001-capa-normativa.md").read_text(encoding="utf-8")
        inf = ejecutar(checks.check_adr, {"0001.md": texto})
        self.assertIn("`docs/linea-base-v1.md`", inf.errores[0])

    def test_cabeceras_sin_comillas_fallan(self):
        casos = {"referencias: [PR #12]": "PR",
                 'referencias: [ADR-0001, "PR #12"]': "ADR-0001",
                 "referencias: [SPEC-CALC-001]": "SPEC-CALC-001",
                 "referencias:\n  - PR #12": "PR",
                 'referencias:\n  - "VIC-3"\n  - docs/convenciones.md': "docs/convenciones.md",
                 'referencias: ["PR #12" y más]': '"PR #12" y más',
                 'referencias: [\n  "VIC-3",\n  PR #12\n]': "PR",
                 'referencias: ["VIC-3",\n  SPEC-CALC-001]': "SPEC-CALC-001"}
        for cabecera, mala in casos.items():
            with self.subTest(cabecera=cabecera):
                inf = ejecutar(checks.check_adr, {"docs/adr/0002-x.md": adr(cabecera)})
                self.assertEqual(len(inf.errores), 1)
                self.assertIn(f"`{mala}`", inf.errores[0])

    def test_solo_mira_la_cabecera(self):
        texto = adr("referencias: []") + "\n- una lista sin comillas en el cuerpo\n"
        self.assertEqual(ejecutar(checks.check_adr, {"a.md": texto}).errores, [])


# --- M17 -------------------------------------------------------------------

SANDBOX = [".bash_profile", ".bashrc", ".gitconfig", ".gitmodules", ".idea", ".mcp.json", ".profile",
           ".ripgreprc", ".vscode", ".zprofile", ".zshrc", ".claude/settings.local.json",
           ".claude/agents", ".claude/hooks", ".claude/launch.json", ".claude/skills"]


def ignorados(gitignore: pathlib.Path, rutas: list[str]) -> set[str]:
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["git", "init", "-q", d], check=True, env=ENTORNO_GIT)
        shutil.copy(gitignore, pathlib.Path(d) / ".gitignore")
        r = subprocess.run(["git", "-C", d, "check-ignore", "--no-index", "--stdin"],
                           input="\n".join(rutas), capture_output=True, text=True, env=ENTORNO_GIT)
        return set(r.stdout.split())


class TestGitignore(unittest.TestCase):
    PROYECTO = ["src/app.js", "docs/specs/SPEC-A-001-x.md", ".github/sdd/checks.py",
                ".claude/settings.json", "AGENTS.md", "src/.bashrc", "docs/.vscode"]

    def test_plantilla_ignora_el_sandbox_capturas_y_resultados(self):
        extra = ["capturas-vic-12/peso.png", "evals/results/r.json", ".tareas/VIC-1.md"]
        self.assertEqual(ignorados(PLANTILLA / ".gitignore", SANDBOX + extra), set(SANDBOX + extra))

    def test_plantilla_no_ignora_lo_del_proyecto(self):
        self.assertEqual(ignorados(PLANTILLA / ".gitignore", self.PROYECTO + ["capturas.md"]), set())

    def test_repo_ignora_el_sandbox_y_los_resultados_del_plugin(self):
        extra = ["plugin-sdd/evals/results/r.json"]
        self.assertEqual(ignorados(RAIZ / ".gitignore", SANDBOX + extra), set(SANDBOX + extra))

    def test_repo_no_ignora_lo_versionado(self):
        rutas = subprocess.run(["git", "-C", str(RAIZ), "ls-files"], capture_output=True, text=True,
                               check=True).stdout.split()
        self.assertEqual(ignorados(RAIZ / ".gitignore", rutas), set())


# --- Configuración de lefthook (ADR-0008) ----------------------------------

LEFTHOOK_PLANTILLA = (PLANTILLA / "lefthook.json").read_text(encoding="utf-8")


def con_lefthook(**cambios):
    conf = json.loads(LEFTHOOK_PLANTILLA)
    conf.update(cambios)
    return json.dumps(conf)


class TestLefthook(unittest.TestCase):
    def comprobar(self, texto=LEFTHOOK_PLANTILLA, versionados=None, en_base=True):
        versionados = {"lefthook.json": "100644", "README.md": "100644"} if versionados is None else versionados
        return ejecutar(checks.check_lefthook, versionados, texto, en_base).errores

    def test_la_plantilla_pasa(self):
        self.assertEqual(self.comprobar(), [])

    def test_la_plantilla_lanza_gitleaks_antes_del_commit(self):
        trabajos = json.loads(LEFTHOOK_PLANTILLA)["pre-commit"]["jobs"]
        self.assertIn("gitleaks git --pre-commit --staged --redact", " ".join(t["run"] for t in trabajos))

    def test_claves_que_amplian_lo_que_se_ejecuta_fallan(self):
        """Las del ADR-0008 y las que ejecutan órdenes (skip, only, files, setup) o scripts."""
        for clave, valor in [("remotes", [{"git_url": "https://x"}]), ("extends", ["otro.yml"]), ("rc", ".rc"),
                             ("templates", {"a": "b"}), ("lefthook", "/x/lefthook"), ("ai", {"claude": True}),
                             ("source_dir", "x/"), ("source_dir_local", "x/"), ("Remotes", []),
                             ("install_non_git_hooks", True), ("post-checkout", {"jobs": [{"run": "x"}]})]:
            with self.subTest(clave=clave):
                self.assertTrue(self.comprobar(con_lefthook(**{clave: valor})))
        for hook in [{"jobs": [{"run": "x", "stage_fixed": True}]}, {"jobs": [{"run": "x", "env": {"PATH": "/x"}}]},
                     {"jobs": [{"run": "x", "skip": [{"run": "true"}]}]}, {"jobs": [{"run": "x", "only": True}]},
                     {"jobs": [{"script": "a.sh", "runner": "bash"}]}, {"jobs": [{"run": "x", "root": "a/"}]},
                     {"jobs": [{"group": {"jobs": [{"run": "x"}]}}]}, {"files": "git ls-files", "jobs": []},
                     {"setup": [{"run": "x"}], "jobs": []}, {"commands": {"a": {"run": "x"}}},
                     {"scripts": {"a.sh": {"runner": "bash"}}}, {"skip": True, "jobs": []},
                     {"follow": True, "jobs": []}, {"exclude_tags": ["x"], "jobs": []}]:
            with self.subTest(hook=hook):
                self.assertTrue(self.comprobar(con_lefthook(**{"pre-commit": hook})))

    def test_obligatorias(self):
        for clave in checks.LEFTHOOK_OBLIGATORIAS:
            for valor in (False, "true", 1):
                with self.subTest(clave=clave, valor=valor):
                    self.assertTrue(self.comprobar(con_lefthook(**{clave: valor})))
            conf = json.loads(LEFTHOOK_PLANTILLA)
            del conf[clave]
            self.assertTrue(self.comprobar(json.dumps(conf)))

    def test_json_raro_falla(self):
        for texto in ("", "{", "[]", '{"pre-commit": []}', '{"pre-commit": {"jobs": {}}}',
                      '{"pre-commit": {"jobs": [{"run": ""}]}}', '{"pre-commit": {"jobs": [{"run": ["a"]}]}}',
                      '{"pre-commit": {"jobs": [{"run": "x", "glob": 3}]}}',
                      '{"pre-commit": {"parallel": "true", "jobs": []}}', '{"min_version": 2}',
                      LEFTHOOK_PLANTILLA[:-2] + ', "pre-commit": {"jobs": []}}'):
            with self.subTest(texto=texto):
                self.assertTrue(self.comprobar(texto))

    def test_claves_repetidas_fallan(self):
        """La última gana al leerlo: una repetida escondería la primera a quien lo revisa."""
        texto = LEFTHOOK_PLANTILLA.replace('"no_auto_install": true,', '"no_auto_install": true, "no_auto_install": false,')
        self.assertIn("repetidas", " ".join(self.comprobar(texto)))

    def test_otra_configuracion_versionada_falla(self):
        for ruta in ("lefthook.yml", ".lefthook.yaml", ".config/lefthook.toml", "lefthook-local.json",
                     ".lefthook-local.jsonc", ".config/lefthook-local.yml", ".lefthook/pre-commit/a.sh",
                     ".lefthook-local/pre-commit/a.sh", "app/lefthook.yml"):
            with self.subTest(ruta=ruta):
                errores = self.comprobar(versionados={"lefthook.json": "100644", ruta: "100644"})
                self.assertTrue(any(ruta in e for e in errores), errores)

    def test_enlace_o_ejecutable_falla(self):
        for modo in ("120000", "100755"):
            with self.subTest(modo=modo):
                self.assertTrue(self.comprobar(versionados={"lefthook.json": modo}))

    def test_otra_configuracion_sin_la_principal_falla(self):
        """Sin lefthook.json, lefthook cargaría la otra."""
        self.assertTrue(self.comprobar(texto=None, versionados={".lefthook.yml": "100644"}, en_base=False))

    def test_quitarla_falla_si_main_la_tiene(self):
        self.assertTrue(self.comprobar(texto=None, versionados={"README.md": "100644"}, en_base=True))
        self.assertEqual(self.comprobar(texto=None, versionados={"README.md": "100644"}, en_base=False), [])

    def test_sin_respuesta_de_git_falla(self):
        """G4 del PR #30: si Git no lista los ficheros, el check no pasa en silencio."""
        self.assertTrue(ejecutar(checks.check_lefthook, None, None, True).errores)
        self.assertTrue(ejecutar(checks.check_lefthook, {"lefthook.json": "100644"}, LEFTHOOK_PLANTILLA, None).errores)

    def test_otros_nombres_sin_distinguir_mayusculas(self):
        """G4 del PR #30: en un sistema de ficheros que no las distingue, lefthook los cargaría."""
        for ruta in ("Lefthook.yml", ".Lefthook-Local.YML"):
            with self.subTest(ruta=ruta):
                self.assertTrue(self.comprobar(versionados={"lefthook.json": "100644", ruta: "100644"}))

    def test_sin_gitleaks_avisa(self):
        """G4 del PR #30, ronda 3: la lista blanca acepta quitar gitleaks; al menos, que se vea."""
        conf = json.loads(LEFTHOOK_PLANTILLA)
        conf["pre-commit"]["jobs"] = [{"name": "nada", "run": "true"}]
        inf = ejecutar(checks.check_lefthook, {"lefthook.json": "100644"}, json.dumps(conf), True)
        self.assertEqual(inf.errores, [])
        self.assertIn("gitleaks", " ".join(inf.avisos))
        self.assertEqual(ejecutar(checks.check_lefthook, {"lefthook.json": "100644"}, LEFTHOOK_PLANTILLA, True).avisos, [])

    def test_la_plantilla_ignora_gitleaks_allow(self):
        self.assertIn("--ignore-gitleaks-allow", LEFTHOOK_PLANTILLA)

    def test_otros_nombres_parecidos_pasan(self):
        self.assertEqual(self.comprobar(versionados={"lefthook.json": "100644", "docs/lefthook.md": "100644",
                                                      "lefthook.json.example": "100644"}), [])


# --- De punta a punta: main() en un repo de verdad -------------------------

class TestPuntaAPunta(unittest.TestCase):
    """Que main() lee la rama, el título y los commits y lanza los checks nuevos."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        (self.repo / "README.md").write_text("# x\n", encoding="utf-8")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "chore: inicio")
        self.git("switch", "-q", "-c", "adr/vic-7-0002-x")
        (self.repo / "docs" / "adr").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), *args], check=True, env=ENTORNO_GIT)

    def correr(self, mensaje: str, referencias: str, **pr):
        (self.repo / "docs" / "adr" / "0002-x.md").write_text(adr(referencias), encoding="utf-8")
        self.git("add", "docs/adr/0002-x.md")
        self.git("commit", "-q", "-m", mensaje)
        entorno = {**ENTORNO_GIT, "PR_BRANCH": "adr/vic-7-0002-x", "PR_TITLE": "adr: decide x",
                   "PR_BODY": "Fixes VIC-7\n\n## Nivel de riesgo\n\n- [x] R1 normal\n"}
        entorno.update(pr)
        entorno.pop("GITHUB_STEP_SUMMARY", None)
        return subprocess.run([sys.executable, str(RUTA), "--base", "main"], cwd=self.repo,
                              capture_output=True, text=True, env=entorno)

    def test_pr_correcto_pasa(self):
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]')
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("Sin errores.", r.stdout)

    def test_pr_incorrecto_falla_en_cada_check(self):
        r = self.correr("adr: decide x\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
                        "referencias: [PR #12]", PR_BRANCH="adr-0002-x", PR_TITLE="ADR 0002")
        self.assertEqual(r.returncode, 1, r.stdout)
        for check in ["**convenciones:** la rama", "**convenciones:** el título",
                      "**autoria:** 1 commit(s)", "**adr:**"]:
            self.assertIn(check, r.stdout)

    def test_avisa_del_historial_solo_en_las_specs_que_cambian(self):
        (self.repo / "docs" / "specs").mkdir(parents=True)
        intacta = SPEC_CON_HISTORIAL.replace("SPEC-CALC-003", "SPEC-CALC-004")
        (self.repo / "docs" / "specs" / "SPEC-CALC-004-x.md").write_text(intacta, encoding="utf-8")
        self.git("add", "docs/specs")
        self.git("commit", "-q", "-m", "spec: base")
        self.git("switch", "-q", "main")
        self.git("merge", "-q", "--ff-only", "adr/vic-7-0002-x")
        self.git("switch", "-q", "adr/vic-7-0002-x")
        (self.repo / "docs" / "specs" / "SPEC-CALC-003-x.md").write_text(SPEC_CON_HISTORIAL, encoding="utf-8")
        self.git("add", "docs/specs")
        r = self.correr("adr: decide x", 'referencias: ["PR #12"]')
        historial = [l for l in r.stdout.splitlines() if "**historial:**" in l]
        self.assertEqual(len(historial), 1, r.stdout)
        self.assertIn("SPEC-CALC-003-x.md", historial[0])

    def test_comprueba_la_configuracion_de_lefthook(self):
        (self.repo / "lefthook.yml").write_text("pre-commit: {}\n", encoding="utf-8")
        self.git("add", "lefthook.yml")
        r = self.correr("adr: decide x", 'referencias: ["PR #12"]')
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**lefthook:**", r.stdout)
        self.assertIn("`lefthook.yml`", r.stdout)

    def test_enlace_no_se_sigue(self):
        """G4 del PR #30: un enlace en lefthook.json da el error previsto, sin traza."""
        (self.repo / "lefthook.json").symlink_to("/dev/null")
        self.git("add", "lefthook.json")
        r = self.correr("adr: decide x", 'referencias: ["PR #12"]')
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("tiene que ser un fichero normal", r.stdout)
        self.assertNotIn("Traceback", r.stderr)

    def test_quitar_lefthook_de_main_falla(self):
        self.git("switch", "-q", "main")
        (self.repo / "lefthook.json").write_text(LEFTHOOK_PLANTILLA, encoding="utf-8")
        self.git("add", "lefthook.json")
        self.git("commit", "-q", "-m", "chore: lefthook")
        self.git("switch", "-q", "-C", "adr/vic-7-0002-x", "main")
        self.git("rm", "-q", "lefthook.json")
        r = self.correr("adr: decide x", 'referencias: ["PR #12"]')
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("el PR quita `lefthook.json`", r.stdout)

    def test_sin_rama_ni_titulo_no_comprueba_convenciones(self):
        r = self.correr("adr: decide x", 'referencias: ["PR #12"]', PR_BRANCH="", PR_TITLE="",
                        PR_BODY="## Nivel de riesgo\n\n- [x] R1 normal\n")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("convenciones", r.stdout)


if __name__ == "__main__":
    unittest.main()

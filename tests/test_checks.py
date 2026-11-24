"""Tests de plantilla-proyecto/.github/sdd/checks.py (VIC-17): M11 (rama, título y
enlace a la issue), REG-34 (sin menciones a Claude), M39 (historial en la cabecera
de una spec), M7 (comillas en la cabecera de los ADR), M17 (`.gitignore` de la
plantilla y de este repo con los ficheros del sandbox), la configuración de lefthook
(ADR-0008) y, desde el PR 3 de VIC-18, los ficheros sensibles, el formato de los commits
(REG-31, REG-32) y la excepción de Dependabot (M38) y, desde VIC-38, la resolución de
los hallazgos de G4. Casos que pasan y que fallan."""
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

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


def sin_reviews(carpeta: pathlib.Path) -> dict[str, str]:
    """PR_REVIEWS y PR_TIMELINE vacíos, como en un PR sin reviews: sin ellos falla `cambios-pedidos` (VIC-57)."""
    rutas = {}
    for var, nombre in (("PR_REVIEWS", "reviews-vacias.json"), ("PR_TIMELINE", "timeline-vacia.json")):
        (carpeta / nombre).write_text("[]", encoding="utf-8")
        rutas[var] = str(carpeta / nombre)
    return rutas


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

    def test_la_plantilla_comprueba_el_formato_de_los_commits(self):
        trabajos = json.loads(LEFTHOOK_PLANTILLA)["commit-msg"]["jobs"]
        self.assertEqual([t["run"] for t in trabajos], ['python3 -I .github/sdd/checks.py --mensaje "{1}"'])

    def test_sin_formato_de_commits_avisa(self):
        conf = json.loads(LEFTHOOK_PLANTILLA)
        del conf["commit-msg"]
        inf = ejecutar(checks.check_lefthook, {"lefthook.json": "100644"}, json.dumps(conf), True)
        self.assertEqual(inf.errores, [])
        self.assertIn("formato de los commits", " ".join(inf.avisos))


# --- Ficheros sensibles (ADR-0008, §5) -------------------------------------

def riesgo(cambiados, nivel="R1", **extra):
    cuerpo = f"## Nivel de riesgo\n\n- [x] {nivel}\n" if nivel else "## Nivel de riesgo\n\n- [ ] R0\n"
    return ejecutar(checks.check_riesgo, cuerpo, cambiados, None, None, {}, {}, *extra.values())


class TestFicherosSensibles(unittest.TestCase):
    """La CI marca R2 un cambio en cualquiera de los ficheros de la lista de docs/herramientas.md."""
    SENSIBLES = ["lefthook.json", ".lefthook/pre-commit/a.sh", ".lefthook-local/a.sh", ".gitleaks.toml",
                 ".gitleaksignore", ".gitattributes", "src/.gitattributes", "a/b/.gitattributes",
                 ".semgrepignore", "src/.semgrepignore", "osv-scanner.toml", "web/osv-scanner.toml",
                 "eslint.config.js", "eslint.config.mjs", "web/eslint.config.ts", ".github/dependabot.yml",
                 ".github/sdd/checks.py", ".github/workflows/seguridad.yml", ".GITATTRIBUTES", "Lefthook.json"]
    NORMALES = ["src/app.js", "docs/gitattributes.md", "src/gitattributes", "eslint.js", "lefthook.md",
                "docs/osv-scanner.toml.md", "src/.gitattributes.bak", "gitleaks.toml"]

    def test_cada_fichero_sensible_exige_r2(self):
        for ruta in self.SENSIBLES:
            with self.subTest(ruta=ruta):
                inf = riesgo([ruta])
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("exige R2", inf.errores[0])
                self.assertEqual(riesgo([ruta], "R2").errores, [])

    def test_configuracion_de_stryker(self):
        """VIC-21, PR 2: los 16 nombres que Stryker carga solo, en cualquier carpeta y sin distinguir
        mayúsculas. La CI usa la de `main`, pero en local Stryker carga la de la rama."""
        nombres = [f"{punto}stryker.{sufijo}.{ext}" for punto in ("", ".") for sufijo in ("conf", "config")
                   for ext in ("json", "js", "mjs", "cjs")]
        self.assertEqual(len(nombres), 16)
        for ruta in nombres + [f"web/{n}" for n in nombres] + ["a/b/.stryker.conf.mjs", "Stryker.Config.JSON"]:
            with self.subTest(ruta=ruta):
                errores = riesgo([ruta]).errores
                self.assertEqual(len(errores), 1, errores)
                self.assertIn("exige R2", errores[0])
        for ruta in [".npmrc", "web/.npmrc", ".NPMRC"]:
            with self.subTest(ruta=ruta):
                errores = riesgo([ruta]).errores
                self.assertEqual(len(errores), 1, errores)
                self.assertIn("exige R2", errores[0])
        for ruta in ["docs/stryker.md", "stryker.js", "src/stryker-config.json", "reports/mutation/stryker.html",
                     "npmrc.md", ".npmrc.example"]:
            with self.subTest(ruta=ruta):
                self.assertEqual(riesgo([ruta]).errores, [])

    def test_capturas_de_referencia_y_configuracion_de_playwright(self):
        """VIC-22, PR 3 (M27): las capturas las aprueba la persona; la configuración puede sortearlas."""
        for ruta in ["e2e/ejemplo.spec.mjs-snapshots/panel-resumen-chromium-linux.png",
                     "tests/e2e/visual.spec.ts-snapshots/a/b.png", "docs/ejemplos/e2e/x.spec.mjs-snapshots/y.png",
                     "__screenshots__/a.png", "e2e/__screenshots__/b/c.png",
                     "playwright.config.ts", "web/playwright.config.mjs", "Playwright.Config.JS",
                     "playwright-ct.config.ts", "a/playwright-ct.config.js"]:
            with self.subTest(ruta=ruta):
                errores = riesgo([ruta]).errores
                self.assertEqual(len(errores), 1, errores)
                self.assertIn("exige R2", errores[0])
        for ruta in ["e2e/snapshots.md", "e2e/ejemplo.spec.mjs", "docs/playwright.md", "playwright.md",
                     "e2e/capturas/ejemplo.png"]:
            with self.subTest(ruta=ruta):
                self.assertEqual(riesgo([ruta]).errores, [])

    def test_configuracion_de_knip_y_jscpd(self):
        """VIC-21, PR 3: los 8 nombres que knip carga solo (KNIP_CONFIG_LOCATIONS de la 6.45.1) y
        los 3 que busca jscpd, más su baseline, en cualquier carpeta y sin distinguir mayúsculas."""
        knip = ["knip.json", "knip.jsonc", ".knip.json", ".knip.jsonc",
                "knip.ts", "knip.js", "knip.config.ts", "knip.config.js"]
        jscpd = [".jscpd.json", ".config/jscpd.json", ".config/.jscpd.json", ".jscpd-baseline.json"]
        for ruta in knip + jscpd + [f"web/{n}" for n in knip + jscpd] + ["KNIP.JSON", ".Jscpd.json"]:
            with self.subTest(ruta=ruta):
                errores = riesgo([ruta]).errores
                self.assertEqual(len(errores), 1, errores)
                self.assertIn("exige R2", errores[0])
        for ruta in ["docs/knip.md", "src/knip.mjs", "knip.yaml", "jscpd.json", "report/jscpd-report.json",
                     "config/jscpd.json"]:
            with self.subTest(ruta=ruta):
                self.assertEqual(riesgo([ruta]).errores, [])

    def test_npm_shrinkwrap_es_un_manifiesto(self):
        """G4 del PR 2 de VIC-21, ronda 3: `npm ci` lo usa antes que package-lock.json."""
        for ruta in ["npm-shrinkwrap.json", "web/npm-shrinkwrap.json"]:
            with self.subTest(ruta=ruta):
                errores = riesgo([ruta]).errores
                self.assertEqual(len(errores), 1, errores)
                self.assertIn("exige R2", errores[0])
                self.assertEqual(riesgo([ruta], "R2").errores, [])

    def test_submodulos(self):
        """G4 del PR 3, ronda 3: el código de un submódulo no lo ve ningún escáner."""
        inf = ejecutar(checks.check_riesgo, "## Nivel de riesgo\n\n- [x] R1\n", ["src/lib"], None, None, {}, {},
                       None, ["src/lib"])
        self.assertIn("submódulo", inf.errores[0] + inf.secciones[0])
        self.assertTrue(riesgo([".gitmodules"]).errores)

    def test_los_demas_no(self):
        for ruta in self.NORMALES:
            with self.subTest(ruta=ruta):
                self.assertEqual(riesgo([ruta]).errores, [])


# --- Formato de los commits (REG-31, REG-32) -------------------------------

class TestMensajeCommit(unittest.TestCase):
    BUENOS = [
        "feat(calculo): suma el peso disco a disco\n\nRefs: VIC-12\n",
        "fix: corrige el redondeo\n\nRefs: VIC-12",
        "feat(calculo)!: cambia el formato\n\nEl cuerpo explica\nel porqué.\n\nRefs: VIC-12\n"
        "Spec: SPEC-CALC-003/AC-04, SPEC-CALC-003/AC-05\nBREAKING CHANGE: el peso guardado cambia de unidad",
        "docs: añade la guía\n\nRefs: VIC-12, VIC-13",
        "test(calculo): cita el AC\n\n- viñeta uno\n- viñeta dos\n\nRefs: VIC-12\nSpec: SPEC-CALC-003/AC-04",
    ]
    # Como lo recibe el hook del editor de Git: los comentarios y lo que va tras la tijera no cuentan.
    DEL_EDITOR = ("feat: algo\n\nRefs: VIC-12\n# Please enter the commit message\n"
                  "# ------------------------ >8 ------------------------\nno cuenta")
    MALOS = [
        ("", "vacío"),
        ("suma el peso\n\nRefs: VIC-12", "título"), ("Feat: suma\n\nRefs: VIC-12", "título"),
        ("fixup! feat: algo\n\nRefs: VIC-12", "título"),
        ('Revert "feat: algo"\n\nRefs: VIC-12', "título"),
        ("Merge branch 'main' into feat/vic-12-x\n\nRefs: VIC-12", "título"),
        ("feat(VIC-12): suma el peso\n\nRefs: VIC-12", "alcance"),
        ("feat: " + "a" * 73 + "\n\nRefs: VIC-12", "73"),
        ("feat: suma el peso\nRefs: VIC-12", "línea en blanco"),
        ("feat: suma el peso", "Refs"), ("feat: suma el peso\n\nCuerpo sin pie.", "Refs"),
        ("feat: suma el peso\n\nRefs: VIC-12\n\nCuerpo después del pie.", "Refs"),
        ("feat: suma el peso\n\nRefs: #12", "Refs"), ("feat: suma el peso\n\nRefs: vic-12", "Refs"),
        ("feat: suma el peso\n\nRefs: VIC-12\nSpec: CALC-003", "Spec"),
        ("feat: suma el peso\n\nSpec: SPEC-CALC-003/AC-04\nRefs: VIC-12", "orden"),
        ("feat: suma el peso\n\nRefs: VIC-12\nBREAKING CHANGE: x\nSpec: SPEC-CALC-003/AC-04", "orden"),
    ]

    def test_mensajes_correctos_pasan(self):
        for texto in self.BUENOS:
            with self.subTest(texto=texto):
                self.assertEqual(checks.problemas_mensaje(texto), ([], []))

    def test_mensajes_incorrectos_fallan(self):
        for texto, motivo in self.MALOS:
            with self.subTest(texto=texto):
                errores, _ = checks.problemas_mensaje(texto)
                self.assertTrue(errores)
                self.assertIn(motivo, " ".join(errores))

    def test_mayuscula_o_punto_final_avisan(self):
        for texto in ("feat: Suma el peso\n\nRefs: VIC-12", "feat: suma el peso.\n\nRefs: VIC-12"):
            with self.subTest(texto=texto):
                errores, avisos = checks.problemas_mensaje(texto)
                self.assertEqual(errores, [])
                self.assertIn("minúscula", avisos[0])

    def test_solo_el_hook_limpia_el_mensaje_como_git(self):
        """G4 del PR 3, ronda 3: en la CI el mensaje ya está guardado; un `#` es parte de él."""
        self.assertEqual(checks.problemas_mensaje(self.DEL_EDITOR, admite_merge=True), ([], []))
        self.assertTrue(checks.problemas_mensaje(self.DEL_EDITOR)[0])
        self.assertIn("vacío", checks.problemas_mensaje("# solo un comentario\n", admite_merge=True)[0][0])
        self.assertTrue(checks.problemas_mensaje("# x\nfeat: algo\n\nRefs: VIC-12")[0])

    def test_el_hook_deja_pasar_el_merge_de_git_y_la_ci_no(self):
        """El hook ve el mensaje que Git propone en un merge; la CI no mira los merges, pero sí
        un commit normal con ese título."""
        texto = "Merge branch 'main' into feat/vic-12-calculo\n"
        self.assertEqual(checks.problemas_mensaje(texto, admite_merge=True), ([], []))
        self.assertTrue(checks.problemas_mensaje(texto)[0])

    def test_check_commits_dice_cual_falla(self):
        inf = ejecutar(checks.check_commits, ["feat: bien\n\nRefs: VIC-1", "mal hecho", "feat: Bien\n\nRefs: VIC-1"])
        self.assertEqual(len(inf.errores), 2, inf.errores)
        self.assertTrue(all("«mal hecho»" in e for e in inf.errores))
        self.assertEqual(len(inf.avisos), 1)


# --- Dependabot (M38) ------------------------------------------------------

class TestDependabot(unittest.TestCase):
    COMMITS = [(checks.DEPENDABOT_CORREO, "chore(deps): bump lodash from 4.17.15 to 4.17.21")]
    CAMBIADOS = ["package.json", "package-lock.json", ".github/workflows/sdd.yml"]

    def test_autor_y_commits_de_dependabot(self):
        self.assertTrue(checks.es_de_dependabot("dependabot[bot]", self.COMMITS, self.CAMBIADOS, True))

    def test_con_merges_no_vale(self):
        """G4 del PR 3, ronda 2: un merge del agente no pasa por la lista de autores."""
        self.assertFalse(checks.es_de_dependabot("dependabot[bot]", self.COMMITS, self.CAMBIADOS, False))

    def test_la_excepcion_no_vale_sin_todas_sus_condiciones(self):
        """Nunca por la rama: el agente puede llamar a la suya `dependabot/…`."""
        otro = ("agente@example.com", "chore: algo\n\nRefs: VIC-1")
        for autor, commits, cambiados in [
            ("victor-lg-bot", self.COMMITS, self.CAMBIADOS),
            ("dependabot", self.COMMITS, self.CAMBIADOS),
            ("dependabot[bot]", self.COMMITS + [otro], self.CAMBIADOS),
            ("dependabot[bot]", [("dependabot[bot]@users.noreply.github.com", "x")], self.CAMBIADOS),
            ("dependabot[bot]", [], self.CAMBIADOS), ("dependabot[bot]", None, self.CAMBIADOS),
            ("dependabot[bot]", self.COMMITS, []),
            ("dependabot[bot]", self.COMMITS, self.CAMBIADOS + ["src/app.js"]),
            ("dependabot[bot]", self.COMMITS, ["package.json", ".github/sdd/checks.py"]),
            ("dependabot[bot]", self.COMMITS, ["package.json", ".github/dependabot.yml"]),
        ]:
            with self.subTest(autor=autor, commits=commits, cambiados=cambiados):
                self.assertFalse(checks.es_de_dependabot(autor, commits, cambiados, True))

    def test_sin_nivel_marcado_toma_r2(self):
        self.assertTrue(riesgo(["package.json"], nivel=None).errores)
        inf = riesgo(["package.json"], nivel=None, por_defecto="R2")
        self.assertEqual(inf.errores, [])
        self.assertIn("Dependabot", inf.secciones[0])
        self.assertTrue(riesgo(["package.json"], "R1", por_defecto="R2").errores)

    def test_no_declara_ac(self):
        args = ("Part of VIC-1", ["package.json"], {}, {}, {})
        self.assertTrue(ejecutar(checks.check_trazabilidad, *args).errores)
        inf = ejecutar(checks.check_trazabilidad, *args, True)
        self.assertEqual(inf.errores, [])
        self.assertIn("Dependabot", inf.avisos[0])


# --- Hallazgos de G4 (VIC-38) -----------------------------------------------

def reconciliacion(*lineas: str) -> str:
    """Un cuerpo de PR con la plantilla real y estas líneas en «Revisión IA (G4)»."""
    return cuerpo_plantilla("Part of VIC-38").replace(
        "## Guía para el revisor humano", "\n".join(lineas) + "\n\n## Guía para el revisor humano", 1)


class TestHallazgos(unittest.TestCase):
    def comprobar(self, *lineas):
        return ejecutar(checks.check_hallazgos, reconciliacion(*lineas))

    def test_todos_resueltos_pasan(self):
        inf = self.comprobar(
            "- G4-1-A-01 · debe corregirse · prueba: `app.js:12` · resolución: corregido en 1a2b3c4",
            "- **G4-1-B-01** · importante · prueba: test_suma falla con 0 · resolución: descartado: AC-03 pide 0 (`spec.md:40`)",
            "* `G4-2-A-02` · menor · prueba: «sin punto final» · resolución: descartado",
            "- G4-3-A-10 · Importante · prueba: x · resolución: corregido en `1a2b3c4d5e` y 9f8e7d6")
        self.assertEqual((inf.errores, inf.avisos), ([], []))

    def test_la_plantilla_y_un_pr_sin_hallazgos_pasan(self):
        self.assertEqual(ejecutar(checks.check_hallazgos, cuerpo_plantilla("Fixes VIC-38")).errores, [])
        self.assertEqual(ejecutar(checks.check_hallazgos, "").errores, [])

    def test_sin_resolucion_falla(self):
        for resolucion in ("", "pendiente", "corregido", "corregido en el próximo push", "lo miro"):
            with self.subTest(resolucion=resolucion):
                inf = self.comprobar(f"- G4-1-A-01 · menor · prueba: x · resolución: {resolucion}")
                self.assertEqual(len(inf.errores), 1)
                self.assertIn("`G4-1-A-01` no tiene resolución", inf.errores[0])

    def test_id_en_negrita_o_codigo_y_otras_vinetas_cuentan(self):
        for inicio in ("- **G4-1-A-01**", "* `G4-1-A-01`", "  - G4-1-A-01"):
            with self.subTest(inicio=inicio):
                inf = self.comprobar(f"{inicio} · menor · prueba: x · resolución: pendiente")
                self.assertEqual(len(inf.errores), 1)

    def test_falla_uno_entre_varios_resueltos(self):
        inf = self.comprobar(
            "- G4-1-A-01 · debe corregirse · prueba: x · resolución: corregido en 1a2b3c4",
            "- G4-1-A-02 · importante · prueba: y · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("G4-1-A-02", inf.errores[0])

    def test_descartar_debe_corregirse_o_importante_pide_prueba(self):
        for gravedad in ("debe corregirse", "importante"):
            for resolucion in ("descartado", "descartado:", "descartado:   "):
                with self.subTest(gravedad=gravedad, resolucion=resolucion):
                    inf = self.comprobar(f"- G4-1-A-01 · {gravedad} · prueba: x · resolución: {resolucion}")
                    self.assertEqual(len(inf.errores), 1)
                    self.assertIn("se descarta sin prueba", inf.errores[0])

    def test_pregunta_a_la_persona_falla(self):
        """VIC-56, regla 2: un hallazgo que espera a la persona no deja fusionar el PR."""
        for gravedad in ("debe corregirse", "importante", "menor"):
            with self.subTest(gravedad=gravedad):
                inf = self.comprobar(f"- G4-1-A-01 · {gravedad} · prueba: x · resolución: pregunta a la persona")
                self.assertEqual(len(inf.errores), 1)
                self.assertIn("pendientes de la persona: `G4-1-A-01`", inf.errores[0])
                self.assertEqual(inf.avisos, [])

    def test_pregunta_contestada_pasa(self):
        """VIC-56, regla 2: cuando la persona contesta, la resolución cambia y el check pasa."""
        inf = self.comprobar(
            "- G4-1-A-01 · importante · prueba: x · resolución: corregido en 1a2b3c4",
            "- G4-1-A-02 · importante · prueba: y · resolución: descartado: respuesta de la persona en el PR")
        self.assertEqual(inf.errores, [])

    def test_varias_preguntas_un_solo_error(self):
        inf = self.comprobar(
            "- G4-1-A-01 · importante · prueba: x · resolución: pregunta a la persona",
            "- G4-1-B-01 · menor · prueba: y · resolución: pregunta a la persona")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("`G4-1-A-01`, `G4-1-B-01`", inf.errores[0])

    def test_formato_roto_falla(self):
        for linea in ("- G4-1-A-01 debe corregirse, corregido en 1a2b3c4",
                      "- G4-1-A-01 · debe corregirse · resolución: corregido en 1a2b3c4",
                      "- G4-1-A-01 · debe corregirse · prueba: x",
                      "- G4-1-A-01 menor · prueba: x · resolución: corregido en 1a2b3c4",
                      "- G4-1-A-01 · menor · extra · prueba: x · resolución: corregido en 1a2b3c4",
                      "- G4-1-A-01 · menor · resolución: corregido en 1a2b3c4 · prueba: x"):
            with self.subTest(linea=linea):
                inf = self.comprobar(linea)
                self.assertEqual(len(inf.errores), 1)
                self.assertIn("no sigue el formato", inf.errores[0])

    def test_gravedad_o_prueba_que_faltan_fallan(self):
        inf = self.comprobar("- G4-1-A-01 · mejora · prueba: x · resolución: corregido en 1a2b3c4")
        self.assertIn("la gravedad `mejora`", " ".join(inf.errores))
        inf = self.comprobar("- G4-1-A-01 · menor · prueba: · resolución: corregido en 1a2b3c4")
        self.assertIn("no tiene prueba", " ".join(inf.errores))

    def test_id_repetido_falla(self):
        linea = "- G4-1-A-01 · menor · prueba: x · resolución: corregido en 1a2b3c4"
        inf = self.comprobar(linea, linea)
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("aparece dos veces", inf.errores[0])

    def test_respuestas_plegadas_codigo_y_comentarios_no_cuentan(self):
        sin_resolver = "- G4-1-A-01 · debe corregirse · prueba: x · resolución: pendiente"
        for envoltorio in (f"```\n{sin_resolver}\n```", f"<!--\n{sin_resolver}\n-->"):
            with self.subTest(envoltorio=envoltorio):
                self.assertEqual(self.comprobar(envoltorio).errores, [])
        # Plegada no es una línea de la reconciliación, pero sí un hallazgo de un revisor (G4-3-B-01).
        for envoltorio in (f"<details><summary>Revisor A</summary>\n\n{sin_resolver}\n\n</details>",
                           f"<details>\n<details>\nx\n</details>\n{sin_resolver}\n</details>",
                           f"<details>\n{sin_resolver}</details>"):
            with self.subTest(envoltorio=envoltorio):
                inf = self.comprobar(envoltorio)
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("no tiene su línea", inf.errores[0])

    def test_fuera_de_lo_plegado_si_cuenta(self):
        inf = self.comprobar("<details>\nrespuesta\n</details>",
                             "- G4-1-A-01 · debe corregirse · prueba: x · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1)

    def test_details_sin_cerrar_falla(self):
        """Lo que va detrás de un <details> sin cerrar no se vería: no se puede dar por bueno."""
        inf = self.comprobar("<details><summary>Revisor A</summary>",
                             "- G4-1-A-01 · debe corregirse · prueba: x · resolución: pendiente")
        self.assertIn("sin cerrar", inf.errores[0])
        self.assertNotIn("no tiene resolución", " ".join(inf.errores))

    def test_details_entre_comillas_invertidas_es_texto(self):
        inf = self.comprobar("Encargo y respuesta, plegados en `<details>`.",
                             "- G4-1-A-01 · debe corregirse · prueba: x · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("no tiene resolución", inf.errores[0])

    def test_comillas_invertidas_como_en_markdown(self):
        """Ronda 1, al pasar el check por este PR: un ``` suelto en una línea no empareja con el
        código que sigue y dejaba fuera un `<details>` que sí era código."""
        inf = self.comprobar("un ``` suelto deja `cerca=True`; para `<details>` sin cerrar hay error",
                             "con ``dos `<details>` dentro`` también es código",
                             "- G4-1-A-01 · menor · prueba: x · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn("no tiene resolución", inf.errores[0])

    def test_la_prueba_puede_citar_otra_linea(self):
        """Ronda 1, al pasar el check por este PR: la resolución es la del último campo."""
        cita = "prueba: `- G4-1-A-01 · menor · prueba: x · resolución: descartado` pasaba"
        inf = self.comprobar(f"- G4-1-A-02 · importante · {cita} · resolución: corregido en 1a2b3c4")
        self.assertEqual(inf.errores, [])
        inf = self.comprobar("- G4-1-A-02 · importante · prueba: · resolución: x · resolución: corregido en 1a2b3c4")
        self.assertEqual(inf.errores, [])
        inf = self.comprobar(f"- G4-1-A-02 · importante · {cita} · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("no tiene resolución (`pendiente`)", inf.errores[0])

    def test_titulos_en_bloques_de_codigo_no_son_respuestas(self):
        """G4-2-A-01: citar el formato de `reviewer.md` en un bloque de código no crea un hallazgo."""
        for cuerpo in ("```\n### G4-1-A-01 · debe corregirse\n```",
                       "<details>\n\n~~~markdown\n**G4-1-A-01 · importante**\n~~~\n\n</details>"):
            with self.subTest(cuerpo=cuerpo):
                self.assertEqual(self.comprobar(cuerpo).errores, [])

    def test_gravedad_del_revisor_al_principio_del_titulo(self):
        """G4-2-A-04 y G4-2-B-04: la gravedad es la primera palabra tras el ID, con `·`, `:`, `—` o nada."""
        lineas = checks.lineas_visibles("\n".join([
            "### G4-1-A-01 · menor · no debe corregirse", "### G4-1-A-02: importante",
            "**G4-1-A-03 — Debe corregirse**", "### G4-1-A-04", "### `G4-1-A-05` - menor"]))[0]
        self.assertEqual(checks.gravedades_de_los_revisores(lineas),
                         {"G4-1-A-01": "menor", "G4-1-A-02": "importante", "G4-1-A-03": "debe corregirse",
                          "G4-1-A-04": checks.SIN_GRAVEDAD, "G4-1-A-05": "menor"})

    def test_titulo_sin_gravedad_exige_linea_y_prueba(self):
        """G4-2-B-04: un título sin `·` ni gravedad no se escapa; se trata como grave."""
        inf = self.comprobar("<details>\n\n### G4-1-A-01\n\n</details>")
        self.assertIn("no tiene su línea", " ".join(inf.errores))
        inf = self.comprobar("<details>\n\n### G4-1-A-01\n\n</details>",
                             "- G4-1-A-01 · menor · prueba: x · resolución: descartado")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("se descarta sin prueba", inf.errores[0])

    def test_varias_apariciones_cuenta_la_gravedad_mayor(self):
        """G4-2-B-03: una línea en negrita más abajo no rebaja la gravedad que dio el revisor."""
        for orden in ((0, 1), (1, 0), (2, 1)):
            titulos = ["### G4-1-A-01 · debe corregirse", "**G4-1-A-01 · menor**", "### G4-1-A-01"]
            with self.subTest(orden=orden):
                inf = self.comprobar("<details>\n\n" + "\n\n".join(titulos[i] for i in orden) + "\n\n</details>",
                                     "- G4-1-A-01 · menor · prueba: x · resolución: descartado")
                self.assertEqual(len(inf.errores), 1)
                self.assertIn("se descarta sin prueba", inf.errores[0])

    def test_comentario_dentro_de_codigo_es_texto(self):
        """G4-2-B-01: un `<!--` en código no esconde lo que sigue hasta el próximo `-->`."""
        sin_resolver = "- G4-1-A-01 · importante · prueba: x · resolución: pendiente"
        for cita in ("<details>\n\nprueba: `<!--`\n\n</details>", "```\n<!--\n```", "con ``<!--`` dentro"):
            with self.subTest(cita=cita):
                inf = self.comprobar(cita, sin_resolver, "<!-- c -->")
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("no tiene resolución", inf.errores[0])
        # En medio de una línea y sin cerrar en ella, `<!--` es texto (lo vio la ronda 2 en esta descripción).
        inf = self.comprobar("antes <!-- sin cerrar", sin_resolver, "<!-- c -->")
        self.assertEqual(len(inf.errores), 1, inf.errores)
        inf = self.comprobar("<!-- un comentario", sin_resolver, "que sigue --> después")
        self.assertEqual(inf.errores, [])

    def test_comentarios_en_medio_de_la_linea(self):
        self.assertEqual(checks.lineas_visibles("a <!-- b --> c <!-- d\n<!-- e\nf --> g\nh")[0],
                         [("a  c <!-- d", False), ("h", False)])
        self.assertEqual(checks.lineas_visibles("a `<!-- b -->` c")[0], [("a `<!-- b -->` c", False)])

    def test_cerca_dentro_de_un_comentario_no_abre(self):
        inf = self.comprobar("<!--\n```\n-->", "- G4-1-A-01 · importante · prueba: x · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn("no tiene resolución", inf.errores[0])

    def test_comentario_sin_cerrar_falla(self):
        # Sin la plantilla: sus comentarios cerrarían este, como en GitHub.
        inf = ejecutar(checks.check_hallazgos, "<!--\n- G4-1-A-01 · importante · prueba: x · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("un comentario HTML", inf.errores[0])

    def test_comillas_tras_la_cerca_no_la_abren(self):
        """G4-2-B-02: en Markdown, ```` ```a`b ```` es código en línea, no una cerca."""
        inf = self.comprobar("```a`b", "- G4-1-A-01 · importante · prueba: x · resolución: pendiente", "```", "```")
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn("no tiene resolución", inf.errores[0])

    def test_lineas_largas_no_cuelgan_el_check(self):
        """Sospecha de G4-2-B, medida: con la expresión de antes, una prueba de 60 000 espacios
        tardaba más de 20 s."""
        import time
        for cuerpo in ("- G4-1-A-01 · menor · prueba:" + " " * 60000 + "x",
                       "- G4-1-A-01 " + "· " * 30000, "` " * 30000, "<!--" * 16000, "`" * 60000,
                       "x" + "<!--" * 16000, "x" + "<!-- " * 13000):
            with self.subTest(cuerpo=cuerpo[:20]):
                inicio = time.monotonic()
                ejecutar(checks.check_hallazgos, cuerpo)
                self.assertLess(time.monotonic() - inicio, 2)

    def test_respuesta_plegada_en_lista_tabla_o_parrafo_cuenta(self):
        """G4-3-B-01: si el revisor no usa un título, su hallazgo plegado tampoco se escapa."""
        for linea, gravedad in (("- **G4-1-A-02** · importante", "importante"),
                                ("G4-1-A-02 · Debe corregirse: x", "debe corregirse"),
                                ("| G4-1-A-02 | menor | x |", "menor"), ("1. `G4-1-A-02` — menor", "menor"),
                                ("> - [ ] G4-1-A-02", checks.SIN_GRAVEDAD)):
            with self.subTest(linea=linea):
                cuerpo = f"<details>\n\n{linea}\n\n</details>"
                self.assertEqual(checks.gravedades_de_los_revisores(checks.lineas_visibles(cuerpo)[0]),
                                 {"G4-1-A-02": gravedad})
                inf = self.comprobar(cuerpo)
                self.assertEqual(len(inf.errores), 1)
                self.assertIn("no tiene su línea", inf.errores[0])
        # Fuera de lo plegado, una viñeta es una línea de la reconciliación, no una respuesta.
        self.assertEqual(checks.gravedades_de_los_revisores(checks.lineas_visibles("- G4-1-A-02 · menor")[0]), {})

    def test_solo_cortan_los_saltos_de_markdown(self):
        """G4-3-A-01 y G4-3-B-02: U+2028 y compañía no son saltos de línea en GitHub."""
        for salto in ("\u2028", "\u2029", "\x85", "\x0b", "\x0c", "\x1c"):
            with self.subTest(salto=repr(salto)):
                inf = self.comprobar(f"x{salto}```", "- G4-1-A-01 · menor · prueba: x · resolución: pendiente",
                                     f"y{salto}```")
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("no tiene resolución", inf.errores[0])
        self.assertEqual([l for l, _ in checks.lineas_visibles("a\r\nb\rc\nd")[0]], ["a", "b", "c", "d"])

    def test_sin_ids_lo_que_queda_abierto_no_falla(self):
        """Sospecha de G4-3-B: un PR sin hallazgos (R0, Dependabot con notas de versión) no falla
        por un `<details>`, un bloque de código o un comentario sin cerrar."""
        for cuerpo in ("<details><summary>Release notes</summary>\n\nx", "```\nx", "<!--\nx"):
            with self.subTest(cuerpo=cuerpo):
                self.assertEqual(ejecutar(checks.check_hallazgos, cuerpo).errores, [])
                self.assertTrue(ejecutar(checks.check_hallazgos, cuerpo + "\nG4-1-A-01").errores)

    def test_otras_menciones_del_id_no_cuentan(self):
        inf = self.comprobar("- Corregidos G4-1-A-01 y G4-1-A-02 en 1a2b3c4.",
                             "- [x] Revisión G4, ronda 1: G4-1-A-01 corregido.",
                             "Ver `### G4-1-A-01 · debe corregirse` en la respuesta.")
        self.assertEqual(inf.errores, [])

    def test_hallazgo_del_revisor_sin_linea_falla(self):
        """G4-1-A-02 y G4-1-B-01: un hallazgo de la respuesta plegada sin su línea no pasa."""
        resuelto = "- G4-1-A-01 · menor · prueba: x · resolución: corregido en 1a2b3c4"
        for respuesta in ("### G4-1-A-02 · importante", "**G4-1-A-02 · importante**",
                          "#### `G4-1-A-02` · Debe corregirse"):
            with self.subTest(respuesta=respuesta):
                inf = self.comprobar(f"<details>\n\n### G4-1-A-01 · menor\n\n{respuesta}\n\n</details>", resuelto)
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("`G4-1-A-02` y la reconciliación no tiene su línea", inf.errores[0])
        inf = self.comprobar("<details>\n\n**G4-1-A-01 · menor**\n\n</details>", resuelto)
        self.assertEqual(inf.errores, [])

    def test_bajar_la_gravedad_no_ahorra_la_prueba(self):
        """G4-1-A-03 y G4-1-B-02: el revisor dijo debe corregirse; la reconciliación, menor."""
        respuesta = "<details>\n\n### G4-1-A-01 · debe corregirse\n\n</details>"
        inf = self.comprobar(respuesta, "- G4-1-A-01 · menor · prueba: x · resolución: descartado")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("se descarta sin prueba", inf.errores[0])
        for resolucion in ("descartado: `spec.md:40` lo permite", "corregido en 1a2b3c4"):
            with self.subTest(resolucion=resolucion):
                inf = self.comprobar(respuesta, f"- G4-1-A-01 · menor · prueba: x · resolución: {resolucion}")
                self.assertEqual(inf.errores, [])

    def test_otras_listas_casillas_citas_y_tablas_cuentan(self):
        """G4-1-A-05 y G4-1-B-03: con otra forma, el hallazgo falla en vez de no comprobarse."""
        for inicio in ("1. G4-1-A-01", "2) G4-1-A-01", "+ G4-1-A-01", "- [ ] G4-1-A-01",
                       "- [x] **G4-1-A-01**", "> - G4-1-A-01"):
            with self.subTest(inicio=inicio):
                inf = self.comprobar(f"{inicio} · menor · prueba: x · resolución: pendiente")
                self.assertEqual(len(inf.errores), 1)
                self.assertIn("no tiene resolución", inf.errores[0])
        inf = self.comprobar("| G4-1-A-01 | menor | x | corregido en 1a2b3c4 |")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("no sigue el formato", inf.errores[0])

    def test_resolucion_sin_distinguir_mayusculas(self):
        """G4-1-A-04."""
        for resolucion in ("Corregido en 1a2b3c4", "Descartado: x"):
            with self.subTest(resolucion=resolucion):
                inf = self.comprobar(f"- G4-1-A-01 · importante · prueba: x · resolución: {resolucion}")
                self.assertEqual(inf.errores, [])
        # Reconocida en mayúsculas: es una pregunta pendiente, no una resolución desconocida.
        inf = self.comprobar("- G4-1-A-01 · importante · prueba: x · resolución: Pregunta a la persona")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("pendientes de la persona", inf.errores[0])

    def test_bloque_de_codigo_sin_cerrar_falla(self):
        """G4-1-A-01: lo que sigue a una cerca suelta no se comprobaría."""
        inf = self.comprobar("```", "- G4-1-A-01 · debe corregirse · prueba: x · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("un bloque de código", inf.errores[0])

    def test_cercas_como_en_markdown(self):
        """G4-1-B-04: solo cierra una cerca del mismo carácter, igual de larga o más, y sola."""
        sin_resolver = "- G4-1-A-01 · menor · prueba: x · resolución: pendiente"
        for bloque in ("````\n```\n````", "~~~\n```\n~~~", "```\n```python\nx\n```"):
            with self.subTest(bloque=bloque):
                inf = self.comprobar(bloque, sin_resolver)
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("no tiene resolución", inf.errores[0])
        inf = self.comprobar("````\n```\n" + sin_resolver + "\n```\n````")
        self.assertEqual(inf.errores, [])

    def test_details_dentro_de_codigo_plegado_es_texto(self):
        """G4-1-B-05: citar un `<details>` en un bloque de código de la respuesta no da falso error."""
        for respuesta in ("<details>\n\n```python\ninf = self.comprobar(\"<details><summary>A</summary>\",\n```\n\n</details>",
                          "<details>\n\n```\n</details>\n```\n\n### G4-1-A-01 · menor\n\n</details>"):
            with self.subTest(respuesta=respuesta):
                self.assertEqual(self.comprobar(respuesta, "- G4-1-A-01 · menor · prueba: x · resolución: descartado").errores, [])


def comentario(cuerpo: str, login: str = "victor-lg-bot", n: int = 1,
               editado: str = "2026-11-20T10:00:00Z") -> dict:
    return {"user": {"login": login}, "body": cuerpo, "html_url": f"https://github.com/o/r/pull/1#issuecomment-{n}",
            "created_at": "2026-11-20T10:00:00Z", "updated_at": editado}


ID_PERSONA = 95044073  # victor-lg, en checks.PERSONAS


def review(estado: str, commit: str, login: str = "victor-lg", n: int = 1, uid: int | None = None) -> dict:
    """Una review de la API; por defecto, de la persona (su id)."""
    return {"id": n, "user": {"login": login, "id": ID_PERSONA if uid is None else uid}, "state": estado,
            "commit_id": commit}


CABEZA = "c" * 40


class TestAprobacionR2(unittest.TestCase):
    """VIC-56, regla 4 (ADR-0009 §3.4): un R2 solo pasa con la aprobación de la persona sobre la cabeza."""

    def comprobar(self, reviews, nivel="R2", cabeza=CABEZA):
        inf = checks.Informe()
        checks.check_aprobacion(inf, nivel, reviews, cabeza)
        return inf

    def test_r2_aprobado_en_la_cabeza_pasa(self):
        inf = self.comprobar([review("APPROVED", CABEZA)])
        self.assertEqual(inf.errores, [])
        self.assertIn("aprobado por victor-lg", inf.secciones[0])

    def test_r2_sin_reviews_falla(self):
        inf = self.comprobar([])
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("**aprobacion:** PR R2: no hay ninguna review de la persona", inf.errores[0])

    def test_r0_y_r1_no_la_piden(self):
        for nivel in ("R0", "R1"):
            with self.subTest(nivel=nivel):
                inf = self.comprobar(None, nivel=nivel)
                self.assertEqual((inf.errores, inf.secciones), ([], []))

    def test_solo_cuenta_la_persona(self):
        """Ni la cuenta del agente ni otra cualquiera: el repo es público y aprueba cualquiera con permiso."""
        for login, uid in (("victor-lg-bot", 1), ("otra", 2), ("Victor-lg", 3), ("", 4)):
            with self.subTest(login=login):
                inf = self.comprobar([review("APPROVED", CABEZA, login=login, uid=uid)])
                self.assertIn("no hay ninguna review de la persona", inf.errores[0])
        inf = self.comprobar([{"id": 1, "user": None, "state": "APPROVED", "commit_id": CABEZA}])
        self.assertEqual(len(inf.errores), 1)

    def test_identidad_por_id_y_no_por_login(self):
        """Si victor-lg cambiara de nombre, otra cuenta podría registrar el libre: cuenta el id, no el login."""
        for uid in (1, str(ID_PERSONA), True, None):
            with self.subTest(uid=uid):
                r = review("APPROVED", CABEZA)
                r["user"]["id"] = uid
                inf = self.comprobar([r])
                self.assertIn("no hay ninguna review de la persona", inf.errores[0])
        # Con el login cambiado, su aprobación sigue contando (y el mensaje usa el nombre de PERSONAS).
        inf = self.comprobar([review("APPROVED", CABEZA, login="nombre-nuevo")])
        self.assertEqual(inf.errores, [])
        self.assertIn("aprobado por victor-lg", inf.secciones[0])

    def test_un_comentario_de_review_no_aprueba(self):
        for estado in ("COMMENTED", "PENDING", "approved", ""):
            with self.subTest(estado=estado):
                inf = self.comprobar([review(estado, CABEZA)])
                self.assertIn("no hay ninguna review de la persona", inf.errores[0])

    def test_un_comentario_despues_no_quita_la_aprobacion(self):
        inf = self.comprobar([review("APPROVED", CABEZA, n=1), review("COMMENTED", CABEZA, n=2)])
        self.assertEqual(inf.errores, [])

    def test_aprobacion_de_un_commit_anterior_falla(self):
        """Un push después de aprobar la deja sin valor."""
        inf = self.comprobar([review("APPROVED", "a" * 40)])
        self.assertIn("la persona aprobó `aaaaaaaaaaaa` y la cabeza es `cccccccccccc`", inf.errores[0])

    def test_cuenta_la_ultima_decisiva(self):
        casos = (([review("APPROVED", CABEZA, n=1), review("CHANGES_REQUESTED", CABEZA, n=2)], "pide cambios"),
                 # Retirar la aprobación o un «changes requested» posterior: la API deja esa review como
                 # DISMISSED con el mismo id, y no se recupera la aprobación anterior (falla cerrado).
                 ([review("APPROVED", CABEZA, n=1), review("DISMISSED", CABEZA, n=2)], "se retiró (dismiss)"),
                 ([review("APPROVED", CABEZA, n=1), review("DISMISSED", CABEZA, n=2),
                   review("COMMENTED", CABEZA, n=3)], "se retiró (dismiss)"),
                 # Por id y no por el orden de la lista.
                 ([review("APPROVED", CABEZA, n=5), review("CHANGES_REQUESTED", CABEZA, n=3)], None),
                 ([review("CHANGES_REQUESTED", CABEZA, n=1), review("APPROVED", CABEZA, n=2)], None))
        for reviews, error in casos:
            with self.subTest(reviews=reviews):
                inf = self.comprobar(reviews)
                if error:
                    self.assertEqual(len(inf.errores), 1)
                    self.assertIn(error, inf.errores[0])
                else:
                    self.assertEqual(inf.errores, [])

    def test_sin_id_falla_cerrado(self):
        inf = self.comprobar([{"user": {"login": "victor-lg", "id": ID_PERSONA}, "state": "APPROVED", "commit_id": CABEZA}])
        self.assertIn("no tiene id", inf.errores[0])

    def test_sin_reviews_o_sin_cabeza_falla_en_r2(self):
        for reviews, cabeza in ((None, CABEZA), ([review("APPROVED", CABEZA)], "")):
            with self.subTest(reviews=reviews, cabeza=cabeza):
                inf = self.comprobar(reviews, cabeza=cabeza)
                self.assertIn("no he podido leer las reviews", inf.errores[0])

    def test_nivel_efectivo_de_check_riesgo(self):
        """El mayor entre el marcado y el mínimo: marcar R1 en un R2 no esquiva la aprobación."""
        cuerpo = "## Nivel de riesgo\n\n- [x] {}\n"
        casos = (("R1", ["src/a.js"], "R1"), ("R2", ["src/a.js"], "R2"), ("R1", ["package.json"], "R2"),
                 (None, ["package.json"], "R2"))
        for marcado, cambiados, nivel in casos:
            with self.subTest(marcado=marcado, cambiados=cambiados):
                texto = cuerpo.format(marcado) if marcado else ""
                self.assertEqual(checks.check_riesgo(checks.Informe(), texto, cambiados, None, None, {}, {}), nivel)

    def test_lee_varias_paginas(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = pathlib.Path(tmp) / "reviews.json"
            ruta.write_text(json.dumps([review("CHANGES_REQUESTED", CABEZA, n=1)]) + "\n"
                            + json.dumps([review("APPROVED", CABEZA, n=2)]), encoding="utf-8")
            self.assertEqual(len(checks.leer_paginas(str(ruta))), 2)
            ruta.write_text("{}", encoding="utf-8")
            self.assertIsNone(checks.leer_paginas(str(ruta)))


class TestHallazgosEnComentarios(unittest.TestCase):
    """PR 2 de VIC-38: las respuestas de los revisores van en comentarios del PR, y solo cuentan los
    de las cuentas autorizadas (CUENTAS_G4)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def comprobar(self, comentarios, *lineas):
        return ejecutar(checks.check_hallazgos, reconciliacion(*lineas),
                        [(c["html_url"], c["body"]) for c in comentarios])

    def leer(self, contenido) -> list | None:
        ruta = pathlib.Path(self.tmp.name) / "comentarios.json"
        # Como `gh api --paginate`: una lista por página, una detrás de otra.
        texto = contenido if isinstance(contenido, str) else "\n".join(json.dumps(p) for p in contenido)
        ruta.write_text(texto, encoding="utf-8")
        leidos = checks.comentarios_de_cuentas(str(ruta))
        return None if leidos is None else checks.enlaces_y_cuerpos(leidos)

    def test_respuesta_en_comentario_exige_su_linea(self):
        for respuesta in ("### G4-1-A-01 · importante\n\n- **Dónde:** x", "- **G4-1-A-01** · importante",
                          "<details>\n\n### G4-1-A-01 · importante\n\n</details>"):
            with self.subTest(respuesta=respuesta):
                inf = self.comprobar([comentario(respuesta)])
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("`G4-1-A-01` y la reconciliación no tiene su línea", inf.errores[0])
                inf = self.comprobar([comentario(respuesta)],
                                     "- G4-1-A-01 · importante · prueba: x · resolución: corregido en 1a2b3c4")
                self.assertEqual(inf.errores, [])

    def test_la_gravedad_del_comentario_cuenta_para_descartar(self):
        comentarios = [comentario("### G4-1-A-01 · menor"), comentario("### G4-1-A-01 · debe corregirse", n=2)]
        inf = self.comprobar(comentarios, "- G4-1-A-01 · menor · prueba: x · resolución: descartado")
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn("(debe corregirse) se descarta sin prueba", inf.errores[0])
        inf = self.comprobar(comentarios, "- G4-1-A-01 · menor · prueba: x · resolución: descartado: `a.py:3`")
        self.assertEqual(inf.errores, [])

    def test_sin_gravedad_gana_en_cualquier_orden(self):
        for previa in checks.GRAVEDADES:
            with self.subTest(previa=previa):
                self.assertEqual(checks.mas_grave(previa, checks.SIN_GRAVEDAD), checks.SIN_GRAVEDAD)
                self.assertEqual(checks.mas_grave(checks.SIN_GRAVEDAD, previa), checks.SIN_GRAVEDAD)
        self.assertEqual(checks.mas_grave("menor", "importante"), "importante")
        self.assertEqual(checks.mas_grave(None, "menor"), "menor")

    def test_codigo_y_comentarios_html_del_comentario_no_cuentan(self):
        inf = self.comprobar([comentario("```\n### G4-1-A-01 · importante\n```\n<!-- G4-1-A-02 · menor -->")])
        self.assertEqual(inf.errores, [])

    def test_comentario_sin_cerrar_falla_con_su_enlace(self):
        """Lo abierto solo esconde lo que sigue en el mismo comentario: sin ningún ID en él, no falla."""
        inf = self.comprobar([comentario("```\n### G4-1-A-02 · importante", n=7)],
                             "- G4-1-A-01 · menor · prueba: x · resolución: descartado")
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn("el comentario https://github.com/o/r/pull/1#issuecomment-7 tiene un bloque de código", inf.errores[0])
        self.assertEqual(self.comprobar([comentario("```\nx")]).errores, [])

    def test_solo_las_cuentas_autorizadas(self):
        paginas = [[comentario("### G4-1-A-01 · menor", login) for login in
                    ("victor-lg-bot", "intruso", "victor-lg-bot2", "Victor-LG-bot")],
                   [comentario("### G4-1-A-02 · menor", "victor-lg", n=2), {"user": {"login": "victor-lg"}},
                    {"user": None, "body": "### G4-1-A-03 · menor"}, {"body": "### G4-1-A-03 · menor"},
                    {"user": "victor-lg", "body": "### G4-1-A-03 · menor"}]]
        self.assertEqual(self.leer(paginas), [(paginas[0][0]["html_url"], "### G4-1-A-01 · menor"),
                                              (paginas[1][0]["html_url"], "### G4-1-A-02 · menor")])
        self.assertEqual(self.leer([[]]), [])
        self.assertEqual(self.leer("[][]\n"), [])
        self.assertEqual(checks.CUENTAS_G4, ("victor-lg-bot", "victor-lg"))

    def test_sin_poder_leer_los_comentarios_es_none(self):
        for contenido in ("", " \n", "{", "{}", "[]{}", "[] x", "[1]", '[["x"]]'):
            with self.subTest(contenido=contenido):
                self.assertIsNone(self.leer(contenido))
        self.assertIsNone(checks.comentarios_de_cuentas(str(pathlib.Path(self.tmp.name) / "no-existe.json")))

class TestRespuestasBorradasOEditadas(unittest.TestCase):
    """VIC-47: la cuenta del agente no puede anular una respuesta de G4 borrándola ni editándola."""

    URL = "https://github.com/o/r/pull/1"
    RESPUESTA = "### G4-1-A-01 · importante\n\nCommit revisado: G4-1-A · " + "a" * 40

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def comprobar(self, comentarios, *lineas, url=URL):
        return ejecutar(checks.check_respuestas, reconciliacion(*lineas), comentarios, url)

    def enlace(self, n=1):
        return f"- **Revisor A (Sonnet):** [respuesta]({self.URL}#issuecomment-{n}) · [reconciliación]({self.URL}#issuecomment-{n + 1})"

    def test_comentarios_enlazados_y_sin_editar_pasan(self):
        comentarios = [comentario(self.RESPUESTA), comentario("Reconciliación\n\nMétricas G4: PR #1 · ronda 1 ·", n=2)]
        self.assertEqual(self.comprobar(comentarios, self.enlace()).errores, [])
        self.assertEqual(self.comprobar([], "Sin G4: R0.").errores, [])

    def test_comentario_borrado_falla(self):
        inf = self.comprobar([comentario(self.RESPUESTA)], self.enlace())
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn(f"enlaza el comentario {self.URL}#issuecomment-2 y no está", inf.errores[0])

    def test_enlace_a_comentario_de_otra_cuenta_falla(self):
        """Solo se leen los de CUENTAS_G4: uno de otra cuenta enlazado cuenta como borrado (G4-1-B-03)."""
        ruta = pathlib.Path(self.tmp.name) / "comentarios.json"
        ruta.write_text(json.dumps([comentario(self.RESPUESTA), comentario("Reconciliación", login="intruso", n=2)]),
                        encoding="utf-8")
        inf = self.comprobar(checks.comentarios_de_cuentas(str(ruta)), self.enlace())
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn(f"enlaza el comentario {self.URL}#issuecomment-2 y no está", inf.errores[0])

    def test_enlaces_de_otro_pr_o_escondidos_no_cuentan(self):
        """Una aclaración puede enlazar la respuesta de la persona en otro PR; lo que no se ve no es enlace."""
        lineas = ("- Aclaración SPEC-CALC-003/FR-05: x. Respuesta: https://github.com/o/r/pull/2#issuecomment-9",
                  f"<!-- {self.URL}#issuecomment-8 -->", "```", f"{self.URL}#issuecomment-7", "```")
        self.assertEqual(self.comprobar([], *lineas).errores, [])

    def test_sin_url_del_pr_no_comprueba_los_enlaces(self):
        self.assertEqual(self.comprobar([], self.enlace(), url=None).errores, [])

    def test_comentario_editado_falla(self):
        editado = comentario(self.RESPUESTA, editado="2026-11-20T11:00:00Z")
        for c in (editado, {**editado, "updated_at": None}, {k: v for k, v in editado.items() if k != "created_at"}):
            with self.subTest(c=c):
                inf = self.comprobar([c, comentario("Métricas G4: PR #1 · ronda 1 ·", n=2)], self.enlace())
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn(f"{self.URL}#issuecomment-1 se editó después de publicarse", inf.errores[0])
                self.assertIn("`Comentario editado: <enlace> · <motivo>`", inf.errores[0])

    def test_editado_sin_enlace_tambien_falla_si_es_de_g4(self):
        """Quitar también el enlace de la descripción no lo esconde: trae un ID de revisor o métricas."""
        for cuerpo in (self.RESPUESTA, "Commit revisado: G4-2-B · " + "b" * 40, "x\nMétricas G4: PR #1 · ronda 1 ·"):
            with self.subTest(cuerpo=cuerpo):
                inf = self.comprobar([comentario(cuerpo, editado="2026-11-21T00:00:00Z")])
                self.assertEqual(len(inf.errores), 1, inf.errores)

    def test_editar_otros_comentarios_no_falla(self):
        c = comentario("Gracias, lo miro mañana.", login="victor-lg", n=5, editado="2026-11-21T00:00:00Z")
        self.assertEqual(self.comprobar([c]).errores, [])

    def test_edicion_justificada_pasa(self):
        c = comentario(self.RESPUESTA, editado="2026-11-20T11:00:00Z")
        for linea in (f"Comentario editado: {self.URL}#issuecomment-1 · solo el SHA de «Commit revisado»",
                      f"- Comentario editado: [respuesta A]({self.URL}#issuecomment-1) · corrijo el SHA"):
            with self.subTest(linea=linea):
                self.assertEqual(self.comprobar([c, comentario("Métricas G4: PR #1 · ronda 1 ·", n=2)],
                                                self.enlace(), linea).errores, [])

    def test_justificacion_sin_motivo_escondida_o_de_otro_comentario_no_vale(self):
        c = comentario(self.RESPUESTA, editado="2026-11-20T11:00:00Z")
        for linea in (f"Comentario editado: {self.URL}#issuecomment-1",
                      f"Comentario editado: {self.URL}#issuecomment-1 · ",
                      f"<!-- Comentario editado: {self.URL}#issuecomment-1 · x -->",
                      f"Comentario editado: {self.URL}#issuecomment-3 · x"):
            with self.subTest(linea=linea):
                errores = self.comprobar([c], linea).errores
                self.assertEqual(sum("issuecomment-1 se editó" in e for e in errores), 1, errores)

    def test_justificacion_plegada_no_vale(self):
        """G4-1-B-01: plegada, la persona no la ve al aprobar."""
        c = comentario(self.RESPUESTA, editado="2026-11-20T11:00:00Z")
        linea = f"Comentario editado: {self.URL}#issuecomment-1 · x"
        for envoltura in (f"<details><summary>x</summary>\n\n{linea}\n\n</details>",
                          f"<details>\n<summary>x</summary>\n<details>\n\n{linea}\n\n</details>\n</details>"):
            with self.subTest(envoltura=envoltura):
                errores = self.comprobar([c], envoltura).errores
                self.assertEqual(sum("issuecomment-1 se editó" in e for e in errores), 1, errores)

    def test_justificacion_fuera_de_revision_ia_no_vale(self):
        c = comentario(self.RESPUESTA, editado="2026-11-20T11:00:00Z")
        cuerpo = reconciliacion().replace("## Guía para el revisor humano",
                                          f"## Guía para el revisor humano\n\nComentario editado: {self.URL}#issuecomment-1 · x", 1)
        self.assertEqual(len(ejecutar(checks.check_respuestas, cuerpo, [c], self.URL).errores), 1)

    def test_url_del_pr_sale_de_las_variables_de_github(self):
        entorno = {"GITHUB_SERVER_URL": "https://github.com", "GITHUB_REPOSITORY": "o/r", "GITHUB_REF": "refs/pull/12/merge"}
        with unittest.mock.patch.dict(os.environ, entorno):
            self.assertEqual(checks.url_del_pr(), "https://github.com/o/r/pull/12")
        for cambio in ({"GITHUB_REF": "refs/heads/main"}, {"GITHUB_REPOSITORY": ""}, {"GITHUB_REF": "refs/pull/0/merge"}):
            with self.subTest(cambio=cambio), unittest.mock.patch.dict(os.environ, {**entorno, **cambio}):
                self.assertIsNone(checks.url_del_pr())


class TestSinG4(unittest.TestCase):
    """VIC-56, regla 1 (ADR-0009 §3.1 y §5): un PR sin G4 falla, salvo un R0 que checks.py comprueba
    que es solo documentación; si no puede, cuenta como R1. Revisores de la última ronda según `sdd-review`."""

    SHA = "a" * 40

    def ronda(self, n: int, *letras: str) -> list[tuple[str, str]]:
        return [(f"#c{n}{l}", f"Commit revisado: G4-{n}-{l} · {self.SHA}") for l in letras]

    def g4(self, nivel, cambiados, comentarios=(), versionados=None, dependabot=False):
        if versionados is None:
            versionados = {f: "100644" for f in cambiados}
        return ejecutar(checks.check_g4, nivel, list(cambiados), versionados, list(comentarios), dependabot)

    def test_es_documentacion(self):
        si = (("README.md", "100644"), ("docs/guia.md", "100644"), ("src/notas.md", "100644"),
              ("docs/borrado.md", None), ("docs/specs/_plantilla.md", "100644"))
        no = (("app.js", "100644"), ("docs/x.txt", "100644"), ("docs/x.MD", "100644"),
              ("docs/enlace.md", "120000"), ("vendor/sub.md", "160000"), ("script.md", "100755"),
              ("docs/specs/SPEC-CALC-001-x.md", "100644"), ("docs/adr/0002-x.md", "100644"),
              # G4-1-B-01: instrucciones de agentes en cualquier carpeta y lo de carpetas con punto.
              ("src/CLAUDE.md", "100644"), ("docs/AGENTS.md", "100644"), ("CLAUDE.local.md", "100644"),
              ("app/Claude.md", "100644"), ("src/.claude/commands/x.md", "100644"), (".cursor/rules/x.md", "100644"),
              ("docs/.github/x.md", "100644"), ("GEMINI.md", "100644"))
        for ruta, modo in si:
            with self.subTest(ruta=ruta):
                self.assertTrue(checks.es_documentacion(ruta, modo))
        for ruta, modo in no:
            with self.subTest(ruta=ruta, modo=modo):
                self.assertFalse(checks.es_documentacion(ruta, modo))

    def test_r0_de_solo_documentacion_pasa_sin_g4(self):
        inf = self.g4("R0", ["README.md", "docs/guia.md"])
        self.assertEqual((inf.errores, inf.avisos), ([], []))
        self.assertIn("R0 comprobado", inf.secciones[0])
        # Borrar un .md también es solo documentación.
        inf = self.g4("R0", ["docs/viejo.md"], versionados={})
        self.assertEqual(inf.errores, [])

    def test_r0_que_no_es_solo_documentacion_cuenta_como_r1(self):
        casos = {"código": (["docs/guia.md", "app.js"], None), "enlace": (["docs/x.md"], {"docs/x.md": "120000"}),
                 "submódulo": (["sub.md"], {"sub.md": "160000"}), "imagen": (["docs/captura.png"], None),
                 "CLAUDE.md anidado": (["src/CLAUDE.md"], None)}
        for motivo, (cambiados, modos) in casos.items():
            with self.subTest(motivo=motivo):
                inf = self.g4("R0", cambiados, versionados=modos)
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("**g4:** el PR no tiene G4", inf.errores[0])
                self.assertIn("R0 sin comprobar, cuenta como R1", inf.errores[0])
                self.assertIn("cuenta como R1 y necesita G4", inf.avisos[0])
                # Con un revisor, como un R1, pasa.
                inf = self.g4("R0", cambiados, self.ronda(1, "A"), versionados=modos)
                self.assertEqual(inf.errores, [])

    def test_sin_modos_no_se_comprueba_el_r0(self):
        inf = ejecutar(checks.check_g4, "R0", ["docs/guia.md"], None, [], False)
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn("no he podido leer los modos", inf.avisos[0])

    def test_r1_necesita_un_revisor(self):
        inf = self.g4("R1", ["app.js"])
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn("**g4:** el PR no tiene G4", inf.errores[0])
        self.assertIn("Un PR R1 no se fusiona sin revisión", inf.errores[0])
        self.assertEqual(self.g4("R1", ["app.js"], self.ronda(1, "A")).errores, [])
        # Un R1 de solo documentación también la necesita: la excepción es solo para R0.
        self.assertEqual(len(self.g4("R1", ["docs/guia.md"]).errores), 1)

    def test_r2_spec_y_adr_necesitan_dos(self):
        for nivel, cambiados in (("R2", ["app.js"]), ("R1", ["docs/specs/SPEC-CALC-001-x.md"]),
                                 ("R1", ["docs/adr/0002-x.md"])):
            with self.subTest(nivel=nivel, cambiados=cambiados):
                inf = self.g4(nivel, cambiados, self.ronda(1, "A"))
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("tiene 1 revisor(es) con `Commit revisado`", inf.errores[0])
                self.assertIn("necesita 2", inf.errores[0])
                # G4-2-A-02: el motivo de los dos revisores sale en el mensaje cuando es la spec o el ADR.
                self.assertEqual("con spec o ADR" in inf.errores[0], nivel == "R1")
                self.assertEqual(self.g4(nivel, cambiados, self.ronda(1, "A", "B")).errores, [])

    def test_cuenta_la_ultima_ronda_y_solo_revisores_con_commit(self):
        # Dos en la ronda 1 y uno en la 2: en R2 no basta.
        inf = self.g4("R2", ["app.js"], self.ronda(1, "A", "B") + self.ronda(2, "A"))
        self.assertIn("la última ronda de G4 (la 2) tiene 1", inf.errores[0])
        # Un revisor que sale por su hallazgo pero sin `Commit revisado` no cuenta (y `cambios` ya falla).
        inf = self.g4("R1", ["app.js"], [("#c", "<details>\n\n### G4-1-A-01 · menor\n\n</details>")])
        self.assertIn("tiene 0 revisor(es)", inf.errores[0])
        # Una ronda solo con su línea de métricas tampoco.
        inf = self.g4("R1", ["app.js"], [("#c", "Métricas G4: PR #3 · ronda 1 · confirmados 0 · descartados 0 · corregidos 0")])
        self.assertIn("tiene 0 revisor(es)", inf.errores[0])

    def test_dependabot_no_necesita_g4(self):
        inf = self.g4("R2", ["package.json"], dependabot=True)
        self.assertEqual((inf.errores, inf.secciones), ([], []))


class TestRondasDeG4(unittest.TestCase):
    """VIC-39: de los comentarios salen el commit que vio cada revisor y los revisores de cada ronda."""

    def rondas(self, *cuerpos):
        """(vistos, revisores); los repetidos, con `repetidos`."""
        r = checks.rondas_de_g4([(f"#c{n}", c) for n, c in enumerate(cuerpos)])
        return r.vistos, r.revisores

    def repetidos(self, *cuerpos):
        return checks.rondas_de_g4([(f"#c{n}", c) for n, c in enumerate(cuerpos)]).repetidos

    def test_commit_revisado_y_revisores(self):
        a, b = "a" * 40, "b" * 40
        vistos, revisores = self.rondas(f"Commit revisado: G4-1-A · {a}\n<details>\n\n### G4-1-A-01 · menor\n\n</details>",
                                        f"Commit revisado: `G4-2-B` · `{b}`", "- G4-2-A-03 · menor · prueba: x · resolución: descartado")
        self.assertEqual(vistos, {(1, "A"): a, (2, "B"): b})
        self.assertEqual(revisores, {1: {"A"}, 2: {"A", "B"}})

    def test_lo_que_no_cuenta(self):
        """Un SHA corto, uno plegado, en código o de otra cuenta (no llega aquí), y un ID a mitad de línea."""
        vistos, revisores = self.rondas("Commit revisado: G4-1-A · abc1234",
                                        f"<details>\n\nCommit revisado: G4-1-A · {'a' * 40}\n\n</details>",
                                        f"```\nCommit revisado: G4-1-A · {'a' * 40}\n```",
                                        "Ver G4-3-A-02 del PR 1.")
        self.assertEqual((vistos, revisores), ({}, {}))

    def test_el_ultimo_commit_del_mismo_revisor_manda(self):
        vistos, _ = self.rondas(f"Commit revisado: G4-1-A · {'a' * 40}", f"Commit revisado: G4-1-A · {'b' * 40}")
        self.assertEqual(vistos, {(1, "A"): "b" * 40})
        # G4-1-B-03 del PR 4 de VIC-56: dos distintos del mismo revisor y ronda quedan anotados (`cambios` falla).
        self.assertEqual(self.repetidos(f"Commit revisado: G4-1-A · {'a' * 40}", f"Commit revisado: G4-1-A · {'b' * 40}",
                                        f"Commit revisado: G4-1-B · {'a' * 40}", f"Commit revisado: G4-1-B · {'a' * 40}"),
                         {(1, "A")})

    def test_una_ronda_sin_hallazgos_sale_por_sus_metricas(self):
        _, revisores = self.rondas("Métricas G4: PR #3 · ronda 2 · confirmados 0 · descartados 0 · corregidos 0")
        self.assertEqual(revisores, {2: set()})


class TestCambios(unittest.TestCase):
    """VIC-39 (M8): el check `cambios` en un repo de verdad."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.commit("README.md", "chore: inicio")
        self.git("switch", "-q", "-c", "feat/vic-7-x")
        self.visto = self.commit("a.py", "feat: a")

    def git(self, *args) -> str:
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, env=ENTORNO_GIT,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, fichero: str, mensaje: str) -> str:
        (self.repo / fichero).write_text(mensaje + "\n", encoding="utf-8")
        self.git("add", fichero)
        self.git("commit", "-q", "-m", mensaje)
        return self.git("rev-parse", "HEAD")

    def comprobar(self, *cuerpos, nivel: str = "R2"):
        """Por omisión R2: estos tests miran la lista y los commits que vio cada revisor; la regla 3 (en R0 y
        R1, solo documentación tras la ronda) tiene los suyos en `TestTrasLaRonda`."""
        anterior = os.getcwd()
        os.chdir(self.repo)
        try:
            with unittest.mock.patch.dict(os.environ, ENTORNO_GIT):
                return ejecutar(checks.check_cambios, "main", "HEAD", [(f"#c{n}", c) for n, c in enumerate(cuerpos)],
                                "", nivel)
        finally:
            os.chdir(anterior)

    def test_un_commit_tras_la_ultima_ronda_sale_exactamente(self):
        respuesta = f"Commit revisado: G4-1-A · {self.visto}\n\n<details>\n\n### G4-1-A-01 · menor\n\n</details>"
        inf = self.comprobar(respuesta)
        self.assertEqual(inf.errores, [])
        self.assertIn("Ninguno: la cabeza del PR es lo que vieron los revisores.", inf.secciones[0])
        nuevo = self.commit("b.py", "fix: b")
        inf = self.comprobar(respuesta)
        self.assertEqual(inf.errores, [])
        lista = [l for l in inf.secciones[0].splitlines() if l.startswith("- ")]
        self.assertEqual(lista, [f"- `{nuevo[:7]}` fix: b"])
        self.assertIn("Ficheros: b.py", inf.secciones[0])
        self.assertNotIn("a.py", inf.secciones[0])

    def test_sin_commit_revisado_falla(self):
        inf = self.comprobar("<details>\n\n### G4-1-A-01 · menor\n\n</details>")
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn("**cambios:** falta el commit que vio `G4-1-A`", inf.errores[0])
        self.assertIn("`Commit revisado: G4-1-<letra> · <sha de 40>`", inf.errores[0])
        self.assertEqual(inf.secciones, [])

    def test_cuenta_la_ultima_ronda_y_cada_revisor(self):
        r1 = f"Commit revisado: G4-1-A · {self.visto}"
        nuevo = self.commit("b.py", "fix: b")
        r2a = f"Commit revisado: G4-2-A · {nuevo}"
        # La ronda 2 tiene a B (por su hallazgo) y su commit falta.
        inf = self.comprobar(r1, r2a, "- G4-2-B-01 · menor")
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn("falta el commit que vio `G4-2-B`", inf.errores[0])
        # B vio uno anterior que A: entra lo que alguno no vio.
        inf = self.comprobar(r1, r2a, f"Commit revisado: G4-2-B · {self.visto}")
        self.assertEqual(inf.errores, [])
        self.assertEqual([l for l in inf.secciones[0].splitlines() if l.startswith("- ")], [f"- `{nuevo[:7]}` fix: b"])
        # Una ronda sin hallazgos ni commit, solo con sus métricas, también lo pide.
        inf = self.comprobar(r1, "Métricas G4: PR #3 · ronda 2 · confirmados 0 · descartados 0 · corregidos 0")
        self.assertIn("falta el commit que vio ningún revisor de la ronda 2", inf.errores[0])

    def test_un_commit_fuera_de_la_historia_falla(self):
        inf = self.comprobar(f"Commit revisado: G4-1-A · {'f' * 40}")
        self.assertIn("no está en la historia del PR", inf.errores[0])
        # Uno de main sí es antecesor: la lista son los commits del PR.
        inf = self.comprobar(f"Commit revisado: G4-1-A · {self.git('rev-parse', 'main')}")
        self.assertEqual(inf.errores, [])
        self.assertIn("feat: a", inf.secciones[0])
        self.git("commit", "-q", "--amend", "-m", "feat: a reescrito")
        inf = self.comprobar(f"Commit revisado: G4-1-A · {self.visto}")
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertIn(f"el commit `{self.visto[:12]}` que vio `G4-1-A` no está en la historia del PR", inf.errores[0])

    def test_un_merge_de_main_sale_sin_los_commits_de_main(self):
        respuesta = f"Commit revisado: G4-1-A · {self.visto}"
        self.git("switch", "-q", "main")
        self.commit("m.py", "docs: m")
        self.git("switch", "-q", "feat/vic-7-x")
        self.git("merge", "-q", "--no-ff", "--no-edit", "main")
        inf = self.comprobar(respuesta)
        self.assertEqual(inf.errores, [])
        lista = [l for l in inf.secciones[0].splitlines() if l.startswith("- ")]
        self.assertEqual(len(lista), 1, lista)
        self.assertIn("Merge branch 'main'", lista[0])
        self.assertNotIn("Ficheros:", inf.secciones[0])

    def test_la_lista_va_del_mas_antiguo_al_mas_nuevo(self):
        primero, segundo = self.commit("b.py", "fix: b"), self.commit("c.py", "fix: c")
        inf = self.comprobar(f"Commit revisado: G4-1-A · {self.visto}")
        self.assertEqual([l for l in inf.secciones[0].splitlines() if l.startswith("- ")],
                         [f"- `{primero[:7]}` fix: b", f"- `{segundo[:7]}` fix: c"])

    def test_un_titulo_no_esconde_lo_que_sigue(self):
        """G4-1-B-01: un `<!--`, un `<details>` o una comilla invertida en un título o un fichero es texto."""
        self.commit("b.py", "fix: b <!--")
        self.commit("c`<details>.py", "fix: `c <details>")
        inf = self.comprobar(f"Commit revisado: G4-1-A · {self.visto}")
        seccion = inf.secciones[0]
        self.assertNotIn("<!--", seccion)
        self.assertNotIn("<details>", seccion)
        lista = [l.split(" ", 2)[2] for l in seccion.splitlines() if l.startswith("- ")]
        self.assertEqual(lista, ["fix: b &lt;!--", "fix: \\`c &lt;details&gt;"])
        self.assertIn("Ficheros: b.py, c\\`&lt;details&gt;.py", seccion)

    def test_una_lista_a_mano_en_la_descripcion_falla(self):
        """PR 2 de VIC-39: la lista la calcula la CI; escrita a mano en la descripción, falla."""
        for linea in ("- **Cambios tras la última ronda:** los de `a1b2c3d`", "## Cambios tras la última ronda",
                      "### 5. Cambios tras la ultima ronda", "> - cambios después de la última revisión: ninguno",
                      "| Cambios tras la última ronda | a1b2c3d |", "* [x] __Cambios tras la última ronda__",
                      "<details>\n\n- Cambios tras la última ronda: a1b2c3d\n\n</details>",
                      # G4-1-B-01 y G4-1-B-02 del PR 2: un rótulo en HTML y otras redacciones.
                      "<details><summary>Cambios tras la última ronda</summary>\n\n- a1b2c3d\n\n</details>",
                      "- <b>Cambios tras la última ronda</b>: ninguno", '<p align="left"><strong>Cambios tras la última ronda</strong>',
                      "- **Cambios** tras la última ronda: ninguno", "- Cambios desde la última ronda: ninguno",
                      "- Commits posteriores a la última revisión: ninguno"):
            with self.subTest(linea=linea):
                inf = ejecutar(checks.check_cambios, "main", "HEAD", [], reconciliacion(linea))
                self.assertEqual(len(inf.errores), 1, inf.errores)
                self.assertIn("**cambios:** la descripción del PR trae una lista de «Cambios tras la última ronda» escrita a mano",
                              inf.errores[0])
                self.assertIn("está en el resumen de `checks-sdd`", inf.errores[0])

    def test_lo_que_no_es_una_lista_a_mano(self):
        """La plantilla real, la prosa que nombra la sección, el código y los comentarios HTML."""
        for linea in ("", "La CI calcula los cambios tras la última ronda.", "- Ver los cambios tras la última ronda en la CI.",
                      "```\n- Cambios tras la última ronda: a1b2c3d\n```", "<!-- - Cambios tras la última ronda: a1b2c3d -->",
                      "- `Cambios tras la última ronda`: código en línea", "- <b>Nota</b>: los cambios tras la última ronda, en la CI"):
            with self.subTest(linea=linea):
                inf = ejecutar(checks.check_cambios, "main", "HEAD", [], reconciliacion(linea))
                self.assertEqual(inf.errores, [])

    def test_rutas_no_ascii_sin_comillas(self):
        """G4-3-A-01 y G4-3-B-01: `check_tests` y la lista de ficheros de `cambios` leen con -z."""
        (self.repo / "tests").mkdir()
        self.git("switch", "-q", "main")
        self.commit("tests/cálculo.test.js", "test: base")
        self.git("switch", "-q", "feat/vic-7-x")
        self.git("merge", "-q", "--no-edit", "main")
        visto = self.git("rev-parse", "HEAD")
        self.commit("tests/cálculo.test.js", "test: cambia")
        anterior = os.getcwd()
        os.chdir(self.repo)
        try:
            with unittest.mock.patch.dict(os.environ, ENTORNO_GIT):
                tests = ejecutar(checks.check_tests, "main")
        finally:
            os.chdir(anterior)
        self.assertIn("- `tests/cálculo.test.js` (modificado)", tests.secciones[0])
        inf = self.comprobar(f"Commit revisado: G4-1-A · {visto}")
        self.assertIn("Ficheros: tests/cálculo.test.js", inf.secciones[0])

    def test_sin_ninguna_ronda_no_hace_nada(self):
        inf = self.comprobar("Un comentario cualquiera.")
        self.assertEqual((inf.errores, inf.secciones), ([], []))


class RepoConRonda:
    """Un PR de prueba con una ronda de G4 de dos revisores sobre `self.visto`, que se pasa por main()."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.escribir("README.md", "# x\n")
        self.escribir("docs/guia.md", "guía\n")
        self.escribir("app.js", "uno\n")
        self.git("commit", "-q", "-m", "chore: inicio")
        self.git("switch", "-q", "-c", "feat/vic-7-x")
        self.escribir("app.js", "dos\n")
        self.git("commit", "-q", "-m", "feat: dos\n\nRefs: VIC-7")
        self.visto = self.git("rev-parse", "HEAD")

    def git(self, *args) -> str:
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, env=ENTORNO_GIT,
                              capture_output=True, text=True).stdout.strip()

    def escribir(self, ruta: str, contenido: str | None, enlace: bool = False):
        f = self.repo / ruta
        f.parent.mkdir(parents=True, exist_ok=True)
        if f.exists() or f.is_symlink():
            f.unlink()
        if contenido is None:
            self.git("rm", "-q", "--cached", "--ignore-unmatch", ruta)
            return
        if enlace:
            f.symlink_to(contenido)
        else:
            f.write_text(contenido, encoding="utf-8")
        self.git("add", ruta)

    def tras_la_ronda(self, *cambios: tuple[str, str | None]):
        """Un commit después de la ronda: (ruta, contenido); contenido None borra la ruta."""
        for ruta, contenido in cambios:
            self.escribir(ruta, contenido)
        self.git("commit", "-q", "-m", "docs: tras la ronda\n\nRefs: VIC-7")

    def correr(self, nivel: str = "R1", visto: str | None = None, aprobado: bool = False, extra: list | None = None,
               reviews: list | None = None, eventos: list | None = ()):
        """eventos: la línea de tiempo del PR (PR_TIMELINE); vacía por omisión y None para no pasarla."""
        visto = visto or self.visto
        comentarios = self.repo / ".git" / "comentarios.json"
        comentarios.write_text(json.dumps([comentario(f"Commit revisado: G4-1-{l} · {visto}", n=i + 1)
                                           for i, l in enumerate("AB")] + (extra or [])), encoding="utf-8")
        cabeza = self.git("rev-parse", "HEAD")
        ruta_reviews = self.repo / ".git" / "reviews.json"
        ruta_reviews.write_text(json.dumps(reviews if reviews is not None else
                                           [review("APPROVED", cabeza)] if aprobado else []), encoding="utf-8")
        cuerpo = (f"Fixes VIC-7\n\n## Qué comportamiento cubre\n\n- AC cubiertos: no aplica (prueba)\n\n"
                  f"## Nivel de riesgo\n\n- [x] {nivel}\n")
        entorno = {**ENTORNO_GIT, **sin_reviews(self.repo / ".git"), "PR_BODY": cuerpo, "PR_COMENTARIOS": str(comentarios),
                   "PR_REVIEWS": str(ruta_reviews), "PR_HEAD_SHA": cabeza}
        if eventos is None:
            del entorno["PR_TIMELINE"]
        elif eventos:
            (self.repo / ".git" / "timeline.json").write_text(json.dumps(eventos), encoding="utf-8")
            entorno["PR_TIMELINE"] = str(self.repo / ".git" / "timeline.json")
        for var in ("GITHUB_STEP_SUMMARY", "PR_BRANCH", "PR_TITLE", "PR_AUTHOR"):
            entorno.pop(var, None)
        r = subprocess.run([sys.executable, str(RUTA), "--base", "main"], cwd=self.repo,
                           capture_output=True, text=True, env=entorno)
        self.assertNotIn("Traceback", r.stderr)
        return r

    def errores(self, r) -> list[str]:
        return [l for l in r.stdout.split("### Avisos")[0].splitlines() if l.startswith("- **")]


class TestTrasLaRonda(RepoConRonda, unittest.TestCase):
    """VIC-56, regla 3 (ADR-0009 §5), con main(): en R0 y R1, lo que entra tras la última ronda de G4 sin
    otra ronda solo puede ser documentación (`es_documentacion`). Un R2 no falla por esto: lo frena la
    aprobación de la persona sobre la cabeza."""

    def assertRegla3(self, r, *ficheros: str):
        regla = [e for e in self.errores(r) if "que no son solo documentación" in e]
        self.assertEqual(len(regla), 1, r.stdout)
        for f in ficheros:
            self.assertIn(f"`{f}`", regla[0])

    def test_sin_cambios_tras_la_ronda_pasa(self):
        r = self.correr()
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_documentacion_tras_la_ronda_pasa_en_r0_y_r1(self):
        self.tras_la_ronda(("docs/guia.md", "corregida\n"), ("README.md", "# y\n"), ("docs/guía-nueva.md", "ñ\n"),
                           ("docs/vieja.md", None))
        for nivel in ("R1", "R0"):
            with self.subTest(nivel=nivel):
                r = self.correr(nivel=nivel)
                self.assertEqual(r.returncode, 0, r.stdout)
                self.assertIn("docs: tras la ronda", r.stdout)

    def test_codigo_tras_la_ronda_falla_en_r1(self):
        self.tras_la_ronda(("docs/guia.md", "corregida\n"), ("app.js", "tres\n"))
        r = self.correr()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertRegla3(r, "app.js")
        self.assertNotIn("`docs/guia.md`", self.errores(r)[0])
        self.assertIn("PR R1 con cambios tras la última ronda de G4 (la 1)", r.stdout)

    def test_la_aprobacion_de_la_persona_lo_desbloquea(self):
        """Decisión de Víctor (2026-11-24): cuando no cabe otra ronda, su Approve sobre la cabeza deja entrar el cambio."""
        self.tras_la_ronda(("app.js", "tres\n"))
        for nivel in ("R1", "R0"):
            with self.subTest(nivel=nivel):
                r = self.correr(nivel=nivel, aprobado=True)
                self.assertEqual(r.returncode, 0, r.stdout)
                self.assertIn("### Tras la última ronda, aprobado por la persona", r.stdout)
        # Aprobado un commit anterior: un push después le quita el valor.
        aprobado_antes = self.git("rev-parse", "HEAD")
        self.tras_la_ronda(("app.js", "cuatro\n"))
        r = self.correr(reviews=[review("APPROVED", aprobado_antes)])
        self.assertRegla3(r, "app.js")
        # La review de otra cuenta no cuenta.
        r = self.correr(reviews=[review("APPROVED", self.git("rev-parse", "HEAD"), login="victor-lg-bot", uid=1)])
        self.assertRegla3(r, "app.js")

    def test_dos_commits_revisados_del_mismo_revisor_fallan(self):
        """G4-1-B-03: un segundo `Commit revisado` de la misma ronda y letra no mueve el punto de partida."""
        self.tras_la_ronda(("app.js", "tres\n"))
        cabeza = self.git("rev-parse", "HEAD")
        r = self.correr(extra=[comentario(f"Commit revisado: G4-1-A · {cabeza}", n=9)])
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**cambios:** `G4-1-A` tiene dos `Commit revisado` distintos en la ronda 1", r.stdout)

    def test_borrar_codigo_tras_la_ronda_falla(self):
        self.tras_la_ronda(("app.js", None))
        self.assertRegla3(self.correr(), "app.js")

    def test_un_md_que_pasa_a_ser_enlace_falla(self):
        self.escribir("docs/guia.md", "../app.js", enlace=True)
        self.git("commit", "-q", "-m", "docs: enlace\n\nRefs: VIC-7")
        self.assertRegla3(self.correr(), "docs/guia.md")

    def test_un_md_sensible_tras_la_ronda_no_pasa_sin_la_persona(self):
        """Lo que pidió Víctor: una spec, AGENTS.md o CLAUDE.md después de la ronda no entran sin su aprobación."""
        for ruta in ("AGENTS.md", "CLAUDE.md"):
            with self.subTest(ruta=ruta):
                self.git("reset", "-q", "--hard", self.visto)
                self.tras_la_ronda((ruta, "instrucciones\n"))
                r = self.correr()
                # Es R2 por la ruta: no lo para la regla 3, lo para `aprobacion` hasta que la persona apruebe.
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("Nivel mínimo según lo tocado: **R2**", r.stdout)
                self.assertTrue(any("**aprobacion:**" in e for e in self.errores(r)), r.stdout)
                self.assertFalse(any("que no son solo documentación" in e for e in self.errores(r)), r.stdout)
                r = self.correr(nivel="R2", aprobado=True)
                self.assertEqual(r.returncode, 0, r.stdout)
        # Anidados no son R2 por la ruta, pero tampoco documentación (G4-1-B-01): la regla 3 los para.
        self.git("reset", "-q", "--hard", self.visto)
        self.tras_la_ronda(("src/CLAUDE.md", "instrucciones\n"))
        self.assertRegla3(self.correr(), "src/CLAUDE.md")
        # Una spec R1: el PR sigue siendo R1, y la spec no es documentación.
        self.git("reset", "-q", "--hard", self.visto)
        self.tras_la_ronda(("docs/specs/SPEC-CALC-003-x.md", SPEC_LIMPIA))
        r = self.correr()
        self.assertRegla3(r, "docs/specs/SPEC-CALC-003-x.md")
        # Una spec R2: el PR es R2, y la para la aprobación.
        self.git("reset", "-q", "--hard", self.visto)
        self.tras_la_ronda(("docs/specs/SPEC-CALC-003-x.md", SPEC_LIMPIA.replace("riesgo: R1", "riesgo: R2")))
        r = self.correr()
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertTrue(any("**aprobacion:**" in e for e in self.errores(r)), r.stdout)

    def test_en_r2_no_falla_por_la_regla_3(self):
        self.tras_la_ronda(("app.js", "tres\n"))
        r = self.correr(nivel="R2", aprobado=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("docs: tras la ronda", r.stdout)
        r = self.correr(nivel="R2")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertFalse(any("que no son solo documentación" in e for e in self.errores(r)), r.stdout)

    def test_en_r0_tambien(self):
        """Un R0 que no es solo documentación cuenta como R1 (regla 1): la ronda vale, y la regla 3 también."""
        self.tras_la_ronda(("app.js", "tres\n"))
        r = self.correr(nivel="R0")
        self.assertRegla3(r, "app.js")
        self.assertIn("PR R0 con cambios tras la última ronda", r.stdout)

    def test_un_merge_de_main_cuenta(self):
        self.git("switch", "-q", "main")
        self.escribir("otro.js", "de main\n")
        self.git("commit", "-q", "-m", "feat: otro\n\nRefs: VIC-7")
        self.git("switch", "-q", "feat/vic-7-x")
        self.git("merge", "-q", "--no-ff", "--no-edit", "main")
        self.assertRegla3(self.correr(), "otro.js")

    def test_una_ronda_sobre_un_commit_de_main_no_vale(self):
        """Si el commit revisado es de `main`, todo el PR entra tras la ronda."""
        r = self.correr(visto=self.git("rev-parse", "main"))
        self.assertRegla3(r, "app.js")


# --- De punta a punta: main() en un repo de verdad -------------------------

ID_AGENTE = 345216222  # victor-lg-bot


def descarte(review_id: int, estado: str = "changes_requested", login: str = "victor-lg-bot",
             uid: int | None = ID_AGENTE) -> dict:
    """Un evento `review_dismissed` de la línea de tiempo, con la forma que dio la API en calculadora-discos#100
    (prueba D2 de VIC-57): el estado original va en minúsculas y la review no trae su autor."""
    return {"event": "review_dismissed", "id": 37192222217, "created_at": "2026-11-24T23:36:36Z",
            "actor": None if uid is None else {"login": login, "id": uid},
            "dismissed_review": {"state": estado, "review_id": review_id, "dismissal_message": "Prueba VIC-57 (D2)"}}


class TestCambiosPedidos(unittest.TestCase):
    """VIC-57 (ADR-0009 §5, prueba D2): en cualquier nivel, un «Request changes» de la persona frena el PR, y
    otra cuenta no puede quitarlo descartándolo; solo lo desbloquea su aprobación de la cabeza."""

    def comprobar(self, reviews, eventos=(), cabeza=CABEZA):
        inf = checks.Informe()
        checks.check_cambios_pedidos(inf, reviews, None if eventos is None else list(eventos), cabeza)
        return inf

    def assertFalla(self, inf, texto):
        self.assertEqual(len(inf.errores), 1, inf.errores)
        self.assertTrue(inf.errores[0].startswith("**cambios-pedidos:** "), inf.errores[0])
        self.assertIn(texto, inf.errores[0])

    def test_sin_reviews_pasa(self):
        self.assertEqual(self.comprobar([]).errores, [])
        self.assertEqual(self.comprobar([review("COMMENTED", CABEZA)], [{"event": "commented"}]).errores, [])

    def test_la_ultima_pide_cambios_falla(self):
        for reviews in ([review("CHANGES_REQUESTED", "a" * 40)],
                        [review("APPROVED", CABEZA, n=1), review("CHANGES_REQUESTED", CABEZA, n=2)],
                        # Un comentario después no la retira, como en GitHub.
                        [review("CHANGES_REQUESTED", CABEZA, n=1), review("COMMENTED", CABEZA, n=2)],
                        # Por id y no por el orden de la lista.
                        [review("CHANGES_REQUESTED", CABEZA, n=7), review("APPROVED", CABEZA, n=3)]):
            with self.subTest(reviews=reviews):
                self.assertFalla(self.comprobar(reviews), "la última review de la persona (`victor-lg`) pide cambios")
        inf = self.comprobar([review("CHANGES_REQUESTED", "a" * 40, n=4)])
        self.assertIn("(review 4, en `aaaaaaaaaaaa`)", inf.errores[0])

    def test_solo_cuentan_los_cambios_de_la_persona(self):
        for login, uid in (("victor-lg-bot", ID_AGENTE), ("victor-lg", 1), ("otra", 2)):
            with self.subTest(login=login):
                self.assertEqual(self.comprobar([review("CHANGES_REQUESTED", CABEZA, login=login, uid=uid)]).errores, [])

    def test_su_aprobacion_o_su_propio_descarte_lo_quitan(self):
        self.assertEqual(self.comprobar([review("CHANGES_REQUESTED", CABEZA, n=1), review("APPROVED", "a" * 40, n=2)]).errores, [])
        # La persona descarta su propia review: la API la deja DISMISSED y el actor es ella.
        self.assertEqual(self.comprobar([review("DISMISSED", CABEZA, n=1)],
                                        [descarte(1, login="victor-lg", uid=ID_PERSONA)]).errores, [])

    def test_descarte_de_otra_cuenta_falla(self):
        """El caso D2: la cuenta del agente descarta por la API la review de la persona que pedía cambios."""
        for evento in (descarte(1), descarte(1, login="otra", uid=2),
                       # Por id y no por login: una cuenta que se llama como la persona no es ella.
                       descarte(1, login="victor-lg", uid=1), descarte(1, login="victor-lg", uid=str(ID_PERSONA)),
                       # Una cuenta borrada (actor null) no es de PERSONAS.
                       descarte(1, uid=None),
                       descarte(1, estado="CHANGES_REQUESTED")):
            with self.subTest(evento=evento):
                self.assertFalla(self.comprobar([review("DISMISSED", CABEZA, n=1)], [evento]),
                                 "otra cuenta descartó una review de la persona que pedía cambios")
        inf = self.comprobar([review("DISMISSED", CABEZA, n=6048844613)], [descarte(6048844613)])
        self.assertIn("(`victor-lg-bot` la 6048844613)", inf.errores[0])
        inf = self.comprobar([review("DISMISSED", CABEZA, n=1)], [descarte(1, uid=None)])
        self.assertIn("(`desconocida` la 1)", inf.errores[0])

    def test_solo_la_aprobacion_de_la_cabeza_lo_desbloquea(self):
        descartada = review("DISMISSED", "a" * 40, n=1)
        casos = (([descartada, review("APPROVED", CABEZA, n=2)], True),
                 ([descartada, review("APPROVED", "a" * 40, n=2)], False),
                 ([descartada, review("APPROVED", CABEZA, n=2, login="victor-lg-bot", uid=ID_AGENTE)], False),
                 ([descartada, review("COMMENTED", CABEZA, n=2)], False),
                 # Una aprobación anterior a la review que pedía cambios no la desbloquea.
                 ([review("APPROVED", CABEZA, n=0), descartada], False))
        for reviews, pasa in casos:
            with self.subTest(reviews=reviews):
                inf = self.comprobar(reviews, [descarte(1)])
                if pasa:
                    self.assertEqual(inf.errores, [])
                else:
                    self.assertFalla(inf, "otra cuenta descartó")

    def test_otros_descartes_no_cuentan(self):
        # Descartar una aprobación o un comentario no quita ningún freno; la de otra cuenta no es de la persona.
        for reviews, evento in (([review("DISMISSED", CABEZA, n=1)], descarte(1, estado="approved")),
                                ([review("DISMISSED", CABEZA, n=1)], descarte(1, estado="commented")),
                                ([review("DISMISSED", CABEZA, n=1, login="otra", uid=2)], descarte(1))):
            with self.subTest(evento=evento, reviews=reviews):
                self.assertEqual(self.comprobar(reviews, [evento]).errores, [])

    def test_review_que_no_esta_en_la_lista_cuenta_como_de_la_persona(self):
        """Sin la review no se sabe su autor: falla cerrado, y su aprobación de la cabeza lo desbloquea."""
        self.assertFalla(self.comprobar([], [descarte(9)]), "otra cuenta descartó")
        self.assertEqual(self.comprobar([review("APPROVED", CABEZA, n=10)], [descarte(9)]).errores, [])

    def test_sin_datos_falla_cerrado(self):
        for reviews, eventos, cabeza in ((None, [], CABEZA), ([], None, CABEZA), ([], [], ""), ([], [], None)):
            with self.subTest(reviews=reviews, eventos=eventos, cabeza=cabeza):
                self.assertFalla(self.comprobar(reviews, eventos, cabeza), "no he podido leer las reviews del PR")

    def test_evento_mal_formado_falla_cerrado(self):
        malos = ["review_dismissed", {**descarte(1), "dismissed_review": None},
                 {**descarte(1), "dismissed_review": {"state": "changes_requested", "review_id": "1"}},
                 {**descarte(1), "dismissed_review": {"state": "changes_requested", "review_id": True}},
                 {**descarte(1), "dismissed_review": {"state": None, "review_id": 1}},
                 {**descarte(1), "actor": "victor-lg"}]
        for evento in malos:
            with self.subTest(evento=evento):
                self.assertFalla(self.comprobar([review("APPROVED", CABEZA, n=5)], [descarte(1, login="victor-lg", uid=ID_PERSONA),
                                                                                    evento]),
                                 "no tiene la forma esperada")

    def test_review_de_la_persona_sin_id_falla_cerrado(self):
        r = review("CHANGES_REQUESTED", CABEZA)
        del r["id"]
        self.assertFalla(self.comprobar([r]), "no tiene id")

    def test_los_dos_motivos_a_la_vez(self):
        inf = self.comprobar([review("DISMISSED", CABEZA, n=1), review("CHANGES_REQUESTED", CABEZA, n=2)], [descarte(1)])
        self.assertEqual(len(inf.errores), 2, inf.errores)

    def test_lee_la_linea_de_tiempo_de_varias_paginas(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = pathlib.Path(tmp) / "timeline.json"
            ruta.write_text(json.dumps([{"event": "committed"}]) + "\n" + json.dumps([descarte(1)]), encoding="utf-8")
            eventos = checks.leer_paginas(str(ruta))
            self.assertEqual(len(eventos), 2)
            self.assertFalla(self.comprobar([review("DISMISSED", CABEZA, n=1)], eventos), "otra cuenta descartó")


class TestCambiosPedidosConMain(RepoConRonda, unittest.TestCase):
    """VIC-57 con main(): el check `cambios-pedidos` corre en R0, R1 y R2 y lee PR_TIMELINE."""

    def test_en_cualquier_nivel(self):
        cabeza = self.git("rev-parse", "HEAD")
        pide = [review("CHANGES_REQUESTED", cabeza, n=1)]
        descartada = [review("DISMISSED", cabeza, n=1)]
        for nivel in ("R0", "R1", "R2"):
            with self.subTest(nivel=nivel):
                for reviews, eventos, texto in ((pide, [], "pide cambios"), (descartada, [descarte(1)], "otra cuenta descartó")):
                    r = self.correr(nivel, reviews=reviews, eventos=eventos)
                    self.assertEqual(r.returncode, 1, r.stdout)
                    self.assertEqual(len([e for e in self.errores(r) if e.startswith("- **cambios-pedidos:**")]), 1, r.stdout)
                    self.assertIn(texto, r.stdout)
                # Con su aprobación de la cabeza, pasa (en R2 la pide también `aprobacion`).
                r = self.correr(nivel, reviews=descartada + [review("APPROVED", cabeza, n=2)], eventos=[descarte(1)])
                self.assertEqual(r.returncode, 0, r.stdout)

    def test_sin_linea_de_tiempo_falla(self):
        r = self.correr("R1", reviews=[], eventos=None)
        entorno_sin = self.errores(r)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual(len(entorno_sin), 1, r.stdout)
        self.assertIn("**cambios-pedidos:** no he podido leer las reviews del PR (PR_REVIEWS), su línea de tiempo (PR_TIMELINE)",
                      entorno_sin[0])


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

    def correr(self, mensaje: str, referencias: str, g4: bool = True, **pr):
        """g4: añade a los comentarios una ronda con los dos revisores que pide un ADR, sobre la cabeza
        (VIC-56, check `g4`), para que cada test pruebe solo lo suyo."""
        (self.repo / "docs" / "adr" / "0002-x.md").write_text(adr(referencias), encoding="utf-8")
        self.git("add", "docs/adr/0002-x.md")
        self.git("commit", "-q", "-m", mensaje)
        entorno = {**ENTORNO_GIT, **sin_reviews(self.repo / ".git"), "PR_BRANCH": "adr/vic-7-0002-x",
                   "PR_TITLE": "adr: decide x", "PR_BODY": "Fixes VIC-7\n\n## Nivel de riesgo\n\n- [x] R1 normal\n"}
        entorno.update(pr)
        ruta = pathlib.Path(entorno.get("PR_COMENTARIOS") or self.repo / ".git" / "comentarios-g4.json")
        if g4 and (ruta.exists() or "PR_COMENTARIOS" not in pr):
            cabeza = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True,
                                    text=True, env=ENTORNO_GIT).stdout.strip()
            # El fichero propio se rehace en cada llamada: dos rondas 9 en cabezas distintas serían dos commits del mismo revisor.
            previos = json.loads(ruta.read_text(encoding="utf-8")) if "PR_COMENTARIOS" in pr else []
            ronda = [comentario(f"Commit revisado: G4-9-{l} · {cabeza}", n=900 + i) for i, l in enumerate("AB")]
            ruta.write_text(json.dumps(previos + ronda), encoding="utf-8")
            entorno["PR_COMENTARIOS"] = str(ruta)
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
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]')
        historial = [l for l in r.stdout.splitlines() if "**historial:**" in l]
        self.assertEqual(len(historial), 1, r.stdout)
        self.assertIn("SPEC-CALC-003-x.md", historial[0])

    def test_comprueba_la_configuracion_de_lefthook(self):
        (self.repo / "lefthook.yml").write_text("pre-commit: {}\n", encoding="utf-8")
        self.git("add", "lefthook.yml")
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]')
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**lefthook:**", r.stdout)
        self.assertIn("`lefthook.yml`", r.stdout)

    def test_enlace_no_se_sigue(self):
        """G4 del PR #30: un enlace en lefthook.json da el error previsto, sin traza."""
        (self.repo / "lefthook.json").symlink_to("/dev/null")
        self.git("add", "lefthook.json")
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]')
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
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]')
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("el PR quita `lefthook.json`", r.stdout)

    def test_comprueba_los_hallazgos(self):
        cuerpo = "Fixes VIC-7\n\n## Nivel de riesgo\n\n- [x] R1 normal\n\n## Revisión IA (G4)\n\n"
        hallazgo = "- G4-1-A-01 · importante · prueba: `0002-x.md:3` · resolución: "
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]',
                        PR_BODY=cuerpo + hallazgo + "pendiente\n")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**hallazgos:** `G4-1-A-01` no tiene resolución", r.stdout)
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #13"]',
                        PR_BODY=cuerpo + hallazgo + "corregido en 1a2b3c4\n")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_lee_las_respuestas_de_los_comentarios(self):
        cuerpo = "Fixes VIC-7\n\n## Nivel de riesgo\n\n- [x] R1 normal\n"
        ruta = self.repo / "comentarios.json"
        for n, (login, codigo) in enumerate((("victor-lg-bot", 1), ("intruso", 0))):
            with self.subTest(login=login):
                ruta.write_text(json.dumps([comentario("### G4-1-A-01 · importante", login)]), encoding="utf-8")
                r = self.correr("adr: decide x\n\nRefs: VIC-7", f'referencias: ["PR #{20 + n}"]',
                                PR_BODY=cuerpo, PR_COMENTARIOS=str(ruta))
                self.assertEqual(r.returncode, codigo, r.stdout)
                if codigo:
                    self.assertIn("`G4-1-A-01` y la reconciliación no tiene su línea", r.stdout)
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #22"]', PR_BODY=cuerpo,
                        PR_COMENTARIOS=str(self.repo / "no-existe.json"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**hallazgos:** no he podido leer los comentarios del PR", r.stdout)

    def test_respuesta_editada_o_borrada_falla(self):
        """VIC-47, con las variables que pone GitHub en un pull_request."""
        ruta = self.repo / "comentarios.json"
        cuerpo = ("Fixes VIC-7\n\n## Nivel de riesgo\n\n- [x] R1 normal\n\n## Revisión IA (G4)\n\n"
                  "- Revisor A: https://github.com/o/r/pull/1#issuecomment-1\n")
        github = {"GITHUB_SERVER_URL": "https://github.com", "GITHUB_REPOSITORY": "o/r", "GITHUB_REF": "refs/pull/1/merge"}
        casos = (([comentario("Revisión sin hallazgos")], 0, None),
                 ([comentario("Revisión", editado="2026-11-21T00:00:00Z")], 1, "se editó después de publicarse"),
                 ([], 1, "enlaza el comentario https://github.com/o/r/pull/1#issuecomment-1 y no está"))
        for n, (comentarios, codigo, error) in enumerate(casos):
            with self.subTest(n=n):
                ruta.write_text(json.dumps(comentarios), encoding="utf-8")
                r = self.correr("adr: decide x\n\nRefs: VIC-7", f'referencias: ["PR #{30 + n}"]',
                                PR_BODY=cuerpo, PR_COMENTARIOS=str(ruta), **github)
                self.assertEqual(r.returncode, codigo, r.stdout)
                if error:
                    self.assertIn(error, r.stdout)

    def test_publica_los_cambios_tras_la_ultima_ronda(self):
        """VIC-39: con la cabeza del PR en PR_HEAD_SHA, como en la CI; sin el commit revisado, falla."""
        cuerpo = "Fixes VIC-7\n\n## Nivel de riesgo\n\n- [x] R1 normal\n"
        ruta = self.repo / "comentarios.json"
        ruta.write_text(json.dumps([comentario("<details>\n\n### G4-1-A-01 · menor\n\n</details>")]), encoding="utf-8")
        linea = "- G4-1-A-01 · menor · prueba: x · resolución: descartado\n"
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]', g4=False, PR_BODY=cuerpo + linea,
                        PR_COMENTARIOS=str(ruta))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**cambios:** falta el commit que vio `G4-1-A`", r.stdout)
        visto = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True,
                               text=True, env=ENTORNO_GIT).stdout.strip()
        ruta.write_text(json.dumps([comentario(f"Commit revisado: G4-1-A · {visto}\n\n<details>\n\n"
                                               "### G4-1-A-01 · menor\n\n</details>"),
                                    comentario(f"Commit revisado: G4-1-B · {visto}", n=2)]), encoding="utf-8")
        r = self.correr("adr: decide y\n\nRefs: VIC-7", 'referencias: ["PR #13"]', g4=False, PR_BODY=cuerpo + linea,
                        PR_COMENTARIOS=str(ruta), PR_HEAD_SHA="")
        # VIC-56, regla 3: en este R1, el ADR que cambia tras la ronda no es solo documentación.
        regla_3 = "**cambios:** PR R1 con cambios tras la última ronda de G4 (la 1) que no son solo documentación: `docs/adr/0002-x.md`"
        errores = [f"- {regla_3}. Nadie los ha revisado y el PR se fusionaría solo (ADR-0009 §5). Lanza otra ronda sobre la "
                   "cabeza (`sdd-review`); sin otra ronda solo entran ficheros `.md` de documentación, salvo que la persona "
                   "apruebe la cabeza (`victor-lg`)."]
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual([l for l in r.stdout.splitlines() if l.startswith("- **")], errores)
        # Con la lista escrita a mano en la descripción, falla aunque la calculada esté bien (PR 2 de VIC-39).
        a_mano = subprocess.run([sys.executable, str(RUTA), "--base", "main"], cwd=self.repo, capture_output=True, text=True,
                                env={**ENTORNO_GIT, **sin_reviews(self.repo / ".git"),
                                     "PR_BODY": cuerpo + linea + "- **Cambios tras la última ronda:** ninguno\n",
                                     "PR_COMENTARIOS": str(ruta), "PR_BRANCH": "adr/vic-7-0002-x", "PR_TITLE": "adr: decide x"})
        self.assertEqual(a_mano.returncode, 1, a_mano.stdout)
        self.assertIn("**cambios:** la descripción del PR trae una lista", a_mano.stdout)
        cabeza = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True,
                                text=True, env=ENTORNO_GIT).stdout.strip()
        seccion = r.stdout.split("### Cambios tras la última ronda", 1)[1].split("###", 1)[0]
        self.assertEqual([l for l in seccion.splitlines() if l.startswith("- ")], [f"- `{cabeza[:7]}` adr: decide y"])
        # Como en la CI: HEAD es el merge que prueba GitHub y la cabeza del PR llega en PR_HEAD_SHA.
        self.git("switch", "-q", "--detach", "main")
        self.git("merge", "-q", "--no-ff", "--no-edit", cabeza)
        entorno = {**ENTORNO_GIT, **sin_reviews(self.repo / ".git"), "PR_BRANCH": "adr/vic-7-0002-x",
                   "PR_TITLE": "adr: decide x", "PR_BODY": cuerpo + linea, "PR_COMENTARIOS": str(ruta), "PR_HEAD_SHA": cabeza}
        entorno.pop("GITHUB_STEP_SUMMARY", None)
        r = subprocess.run([sys.executable, str(RUTA), "--base", "main"], cwd=self.repo,
                           capture_output=True, text=True, env=entorno)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertEqual([l for l in r.stdout.splitlines() if l.startswith("- **")], errores)
        seccion = r.stdout.split("### Cambios tras la última ronda", 1)[1].split("###", 1)[0]
        self.assertEqual([l for l in seccion.splitlines() if l.startswith("- ")], [f"- `{cabeza[:7]}` adr: decide y"])

    def test_sin_rama_ni_titulo_no_comprueba_convenciones(self):
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]', PR_BRANCH="", PR_TITLE="",
                        PR_BODY="## Nivel de riesgo\n\n- [x] R1 normal\n")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("convenciones", r.stdout)

    def test_comprueba_el_formato_de_los_commits_sin_los_merges(self):
        self.git("switch", "-q", "main")
        (self.repo / "b.md").write_text("b\n", encoding="utf-8")
        self.git("add", "b.md")
        self.git("commit", "-q", "-m", "docs: b")
        self.git("switch", "-q", "adr/vic-7-0002-x")
        self.git("merge", "-q", "--no-ff", "--no-edit", "main")
        r = self.correr("adr: decide x", 'referencias: ["PR #12"]')
        self.assertEqual(r.returncode, 1, r.stdout)
        commits = [l for l in r.stdout.splitlines() if "**commits:**" in l]
        self.assertEqual(len(commits), 1, r.stdout)
        self.assertIn("«adr: decide x»", commits[0])

    def test_modo_mensaje_del_hook(self):
        fichero = self.repo / "COMMIT_EDITMSG"
        for texto, salida in (("feat: algo\n\nRefs: VIC-7\n", 0), ("feat: algo\n", 1),
                              ("Merge branch 'main' into feat/vic-7-x\n", 0)):
            with self.subTest(texto=texto):
                fichero.write_text(texto, encoding="utf-8")
                r = subprocess.run([sys.executable, str(RUTA), "--mensaje", str(fichero)], cwd=self.repo,
                                   capture_output=True, text=True, env=ENTORNO_GIT)
                self.assertEqual(r.returncode, salida, r.stdout + r.stderr)
                if salida:
                    self.assertIn("Error: falta el pie `Refs: VIC-N`", r.stdout)

    def test_un_submodulo_exige_r2(self):
        self.git("update-index", "--add", "--cacheinfo", f"160000,{'a' * 40},vendor/lib")
        self.git("commit", "-q", "-m", "chore: añade lib\n\nRefs: VIC-7")
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]')
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("`vendor/lib` (submódulo", r.stdout)

    def test_cabeza_fuera_de_la_historia_falla(self):
        """VIC-56 (sospecha de G4-2-B): el merge que se prueba puede ser anterior al último push; si la cabeza
        del PR no está en su historia, los checks verían el contenido viejo. Volver a lanzar no lo arregla."""
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]', PR_HEAD_SHA="f" * 40)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**cabeza:** la cabeza del PR (`ffffffffffff`) no está en la historia del commit que se prueba",
                      r.stdout)
        self.assertIn("edita la descripción del PR para que se lance una nueva", r.stdout)

    def test_pr_de_dependabot(self):
        """Ni convenciones, ni formato de los commits, ni AC; el riesgo, R2 aunque no lo marque, y por eso
        pide la aprobación de la persona (VIC-56)."""
        self.git("switch", "-q", "-c", "dependabot/npm_and_yarn/lodash-4.17.21", "main")
        (self.repo / "package.json").write_text('{"dependencies": {"lodash": "4.17.21"}}\n', encoding="utf-8")
        self.git("add", "package.json")
        bot = {"GIT_AUTHOR_NAME": "dependabot[bot]", "GIT_AUTHOR_EMAIL": checks.DEPENDABOT_CORREO}
        subprocess.run(["git", "-C", str(self.repo), "commit", "-q", "-m",
                        "chore(deps): bump lodash from 4.17.15 to 4.17.21 in the npm group across 1 directory"],
                       check=True, env={**ENTORNO_GIT, **bot})
        cabeza = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True,
                                text=True, env=ENTORNO_GIT).stdout.strip()
        reviews = self.repo / "reviews.json"
        reviews.write_text(json.dumps([review("APPROVED", cabeza)]), encoding="utf-8")
        entorno = {**ENTORNO_GIT, **sin_reviews(self.repo / ".git"), "PR_BRANCH": "dependabot/npm_and_yarn/lodash-4.17.21",
                   "PR_REVIEWS": str(reviews),
                   "PR_TITLE": "chore(deps): bump lodash from 4.17.15 to 4.17.21",
                   "PR_BODY": "Bumps [lodash](https://github.com/lodash/lodash) from 4.17.15 to 4.17.21.",
                   "PR_AUTHOR": "dependabot[bot]"}
        correr = lambda **e: subprocess.run([sys.executable, str(RUTA), "--base", "main"], cwd=self.repo,
                                            capture_output=True, text=True, env={**entorno, **e})
        r = correr()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PR de Dependabot", r.stdout)
        self.assertIn("**R2**", r.stdout)
        sin_aprobar = correr(PR_REVIEWS=str(self.repo / "no-existe.json"))
        self.assertEqual(sin_aprobar.returncode, 1, sin_aprobar.stdout)
        self.assertIn("**aprobacion:** PR R2", sin_aprobar.stdout)
        # Como en la CI: HEAD es el merge que prueba GitHub y la cabeza del PR llega aparte.
        self.git("switch", "-q", "--detach", "main")
        self.git("merge", "-q", "--no-ff", "--no-edit", cabeza)
        r = correr(PR_HEAD_SHA=cabeza)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PR de Dependabot", r.stdout)
        self.git("switch", "-q", "dependabot/npm_and_yarn/lodash-4.17.21")
        # Con otro autor del PR, los mismos commits fallan en las convenciones.
        r = correr(PR_AUTHOR="victor-lg-bot")
        self.assertEqual(r.returncode, 1, r.stdout)
        for check in ("**convenciones:**", "**riesgo:**", "**trazabilidad:**"):
            self.assertIn(check, r.stdout)
        # Un merge en la rama (aquí, de main con un cambio de package.json) quita la excepción.
        self.git("switch", "-q", "main")
        (self.repo / "package-lock.json").write_text("{}\n", encoding="utf-8")
        self.git("add", "package-lock.json")
        self.git("commit", "-q", "-m", "chore: lock")
        self.git("switch", "-q", "dependabot/npm_and_yarn/lodash-4.17.21")
        self.git("merge", "-q", "--no-ff", "--no-edit", "main")
        cabeza = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True,
                                text=True, env=ENTORNO_GIT).stdout.strip()
        r = correr(PR_HEAD_SHA=cabeza)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNotIn("PR de Dependabot", r.stdout)


README_CON_RUTAS = "# x\n\n## Rutas sensibles\n\n- `app/sw.js`\n- `app/datos/`\n\n## Otra\n\n- `no/cuenta.js`\n"
FICHERO_RUTAS = "# Comentario\n\nsrc/pagos/\n  tests/e2e/sin-conexion.spec.js  \nsrc/auth/*.ts\n"
ENLACE = object()  # el fichero de rutas como enlace simbólico al README, que existe (G4-2-B-03)
ENLACE_ROTO = object()  # el fichero de rutas como enlace simbólico a un destino que no existe


class TestRutasSensibles(unittest.TestCase):
    """VIC-61: las rutas sensibles del proyecto en `.github/sdd/rutas-sensibles.txt`, con el README
    como respaldo mientras se migra (la unión: nunca menos rutas que antes). Un fichero que no se lee o
    con una línea inválida hace fallar el check `riesgo`."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        self.bases = 0

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), *args], check=True, env=ENTORNO_GIT, capture_output=True)

    def escribir(self, ruta: str, contenido):
        f = self.repo / ruta
        f.parent.mkdir(parents=True, exist_ok=True)
        if f.exists() or f.is_symlink():
            f.unlink()
        if contenido is ENLACE or contenido is ENLACE_ROTO:
            f.symlink_to("../../README.md" if contenido is ENLACE else "no-existe.txt")
        elif isinstance(contenido, bytes):
            f.write_bytes(contenido)
        else:
            f.write_text(contenido, encoding="utf-8")
        self.git("add", ruta)

    def main_con(self, readme: str = "# x\n", rutas=None) -> str:
        """Una rama base nueva (hace de `main`) con ese README y, si se da, el fichero de rutas."""
        self.bases += 1
        base = f"base-{self.bases}"
        self.git("switch", "-q", "--orphan", base)
        self.git("rm", "-rq", "--cached", "--ignore-unmatch", ".")
        self.git("clean", "-fdxq")
        self.escribir("README.md", readme)
        if rutas is not None:
            self.escribir(checks.RUTAS_SENSIBLES, rutas)
        self.git("commit", "-q", "-m", "chore: inicio")
        return base

    def pr(self, base: str):
        """Deja una rama del PR nueva desde `base`, para escribir en ella antes de `correr`."""
        self.git("switch", "-q", "-C", "docs/vic-7-x", base)
        self.git("clean", "-fdxq")

    def correr(self, base: str, *tocados: str, nivel: str = "R1", nueva: bool = True):
        if nueva:
            self.pr(base)
        for ruta in tocados or ("docs/nota.md",):
            self.escribir(ruta, "x\n")
        self.git("commit", "-q", "--allow-empty", "-m", "docs: toca\n\nRefs: VIC-7")
        entorno = {**ENTORNO_GIT, "PR_BODY": f"Fixes VIC-7\n\n## Nivel de riesgo\n\n- [x] {nivel}\n"}
        for var in ("GITHUB_STEP_SUMMARY", "PR_HEAD_SHA", "PR_REVIEWS", "PR_COMENTARIOS", "PR_BRANCH", "PR_TITLE"):
            entorno.pop(var, None)
        entorno.update(sin_reviews(self.repo / ".git"))
        r = subprocess.run([sys.executable, str(RUTA), "--base", base], cwd=self.repo,
                           capture_output=True, text=True, env=entorno)
        self.assertNotIn("Traceback", r.stderr)
        return r

    def assertNivel(self, r, nivel: str):
        self.assertIn(f"Nivel mínimo según lo tocado: **{nivel}**", r.stdout)

    def assertNiveles(self, base: str, casos):
        for tocado, nivel in casos:
            with self.subTest(tocado=tocado):
                r = self.correr(base, tocado)
                self.assertNivel(r, nivel)
                if nivel == "R2":
                    self.assertIn(f"`{tocado}` (ruta sensible del proyecto) → R2", r.stdout)

    def test_solo_readme_sigue_como_antes(self):
        self.assertNiveles(self.main_con(README_CON_RUTAS), (
            ("app/sw.js", "R2"), ("app/datos/a.json", "R2"), ("no/cuenta.js", "R0"), ("src/pagos/a.js", "R0")))

    def test_solo_fichero(self):
        self.assertNiveles(self.main_con(rutas=FICHERO_RUTAS), (
            ("src/pagos/cobro.js", "R2"), ("tests/e2e/sin-conexion.spec.js", "R2"), ("src/auth/a/b.ts", "R2"),
            ("src/auth/a.js", "R0"), ("app/sw.js", "R0")))

    def test_los_dos_suman(self):
        """Durante la migración cuenta la unión: ninguna ruta del README se pierde por crear el fichero."""
        self.assertNiveles(self.main_con(README_CON_RUTAS, FICHERO_RUTAS), (
            ("app/sw.js", "R2"), ("app/datos/a.json", "R2"), ("src/pagos/cobro.js", "R2"), ("src/auth/x.ts", "R2")))

    def test_carpeta_sin_barra_final_la_cubre_entera(self):
        """G4-1-B-03: `src/pagos` sin `/` también cubre lo que hay dentro, en el fichero y en el README."""
        base = self.main_con("## Rutas sensibles\n\n- `app/datos`\n", "src/pagos\n")
        self.assertNiveles(base, (("src/pagos/cobro.js", "R2"), ("src/pagos", "R2"), ("app/datos/a.json", "R2"),
                                  ("src/pagosx.js", "R0")))

    def test_bom_al_principio_no_anula_la_primera_ruta(self):
        """G4-1-B-01: un BOM al principio del fichero no cuenta; un carácter invisible en una ruta, sí."""
        self.assertNiveles(self.main_con(rutas="\ufeffsrc/pagos/\n"), (("src/pagos/cobro.js", "R2"),))
        r = self.correr(self.main_con(rutas="src/pagos/\nsrc/\u200bauth/\n"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("de `main` es inválido (línea 2, `src/\\u200bauth/`)", r.stdout)

    def test_fichero_valido_sin_tocar_rutas_pasa(self):
        # R0 de solo documentación: pasa sin G4 (VIC-56, check `g4`).
        r = self.correr(self.main_con(README_CON_RUTAS, FICHERO_RUTAS), nivel="R0")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNivel(r, "R0")

    def test_rutas_no_ascii_sin_comillas(self):
        """G4-2-B, sospecha: sin `-z`, Git entrecomilla las rutas no ASCII y ningún patrón las ve. Una de
        `.claude/` sube a R2, y un `.md` con tilde es documentación."""
        r = self.correr(self.main_con(), ".claude/skills/ñ/SKILL.md", nivel="R1")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertNivel(r, "R2")
        self.assertIn("`.claude/skills/ñ/SKILL.md`", r.stdout)
        r = self.correr(self.main_con(), "docs/guía.md", nivel="R0")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("R0 comprobado", r.stdout)

    def test_spec_no_ascii_de_main_cuenta(self):
        """G4-3-B-02: la spec de `main` con tilde en el nombre se lee; su PR no baja su propio riesgo."""
        base = self.main_con()
        self.git("switch", "-q", base)
        ruta = "docs/specs/SPEC-CALC-003-división.md"
        self.escribir(ruta, SPEC_LIMPIA.replace("riesgo: R1", "riesgo: R2"))
        self.git("commit", "-q", "-m", "spec: base")
        self.pr(base)
        self.escribir(ruta, SPEC_LIMPIA)
        r = self.correr(base, nivel="R1", nueva=False)
        self.assertNivel(r, "R2")
        self.assertIn("**riesgo:** el PR está marcado R1 pero lo que toca exige R2", r.stdout)

    def test_r0_con_codigo_falla_sin_g4(self):
        """VIC-56, regla 1, con main(): un R0 que toca código cuenta como R1 y falla sin G4."""
        r = self.correr(self.main_con(), "docs/nota.md", "app.js", nivel="R0")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**g4:** el PR no tiene G4", r.stdout)
        self.assertIn("R0 sin comprobar, cuenta como R1", r.stdout)
        r = self.correr(self.main_con(), "docs/nota.md", nivel="R0")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("R0 comprobado", r.stdout)

    def test_fichero_invalido_en_main_falla(self):
        casos = {"lista del README": "- `app/sw.js`", "comillas": "`app/sw.js`", "espacio": "app/mi fichero.js",
                 "absoluta": "/app/sw.js", "punto": "./app/sw.js", "subir": "app/../sw.js",
                 "barra invertida": "app\\sw.js", "tabulador": "app/sw\t.js", "invisible": "app/\u200bsw.js",
                 "salto de página": "app/sw\x0c.js", "separador de línea": "app/sw\u2028.js"}
        for motivo, linea in casos.items():
            with self.subTest(motivo=motivo):
                r = self.correr(self.main_con(README_CON_RUTAS, f"src/pagos/\n{linea}\n"))
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("**riesgo:** `.github/sdd/rutas-sensibles.txt` de `main` es inválido (línea 2", r.stdout)

    def test_fichero_ilegible_en_main_falla(self):
        for motivo, contenido in (("no es UTF-8", b"src/pagos/\n\xff\xfe\n"), ("enlace", ENLACE)):
            with self.subTest(motivo=motivo):
                r = self.correr(self.main_con(rutas=contenido))
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("**riesgo:** `.github/sdd/rutas-sensibles.txt` de `main` es inválido "
                              "(no es un fichero normal de texto UTF-8)", r.stdout)

    def test_tocar_el_fichero_es_r2(self):
        """Cambiar la lista que protege es R2 (está bajo `.github/`), aunque el PR la deje válida."""
        base = self.main_con(rutas=FICHERO_RUTAS)
        self.pr(base)
        self.escribir(checks.RUTAS_SENSIBLES, FICHERO_RUTAS + "src/nueva/\n")
        r = self.correr(base, nueva=False)
        self.assertNivel(r, "R2")
        self.assertIn("cambia `.github/sdd/rutas-sensibles.txt`, la lista de rutas sensibles → R2", r.stdout)
        self.assertNotIn("**riesgo:** el PR deja", r.stdout)
        # También en check_riesgo solo, crearlo o borrarlo: la lista de ficheros basta.
        inf = riesgo([checks.RUTAS_SENSIBLES])
        self.assertIn("exige R2", inf.errores[0])
        self.assertEqual(riesgo([checks.RUTAS_SENSIBLES], "R2").errores, [])

    def test_un_pr_que_deja_el_fichero_invalido_falla(self):
        """Si se fusionara, el fichero inválido en `main` haría fallar todos los PR siguientes. G4-1-B-02:
        también un enlace roto, que `exists()` no ve."""
        for motivo, contenido, error in (("línea", FICHERO_RUTAS + "- `src/nueva/`\n", "(línea 6"),
                                         ("enlace roto", ENLACE_ROTO, "(no es un fichero normal de texto UTF-8)")):
            with self.subTest(motivo=motivo):
                base = self.main_con(rutas=FICHERO_RUTAS)
                self.pr(base)
                self.escribir(checks.RUTAS_SENSIBLES, contenido)
                r = self.correr(base, nueva=False)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(f"**riesgo:** el PR deja `.github/sdd/rutas-sensibles.txt` inválido {error}", r.stdout)

    def test_el_pr_que_corrige_un_fichero_invalido_de_main_pasa(self):
        """G4-1-A-01: si `main` tiene el fichero inválido, el PR que lo corrige (R2) no puede quedar bloqueado."""
        base = self.main_con(rutas="- `src/pagos/`\n")
        self.pr(base)
        self.escribir(checks.RUTAS_SENSIBLES, "src/pagos/\n")
        r = self.correr(base, nivel="R2", nueva=False)
        self.assertIn("de `main` es inválido (línea 1, `- `src/pagos/``) y este PR lo corrige", r.stdout)
        self.assertNotIn("sin él no sé", r.stdout)
        self.assertNotIn("**riesgo:** el PR deja", r.stdout)
        self.assertNivel(r, "R2")
        # Otro PR que no lo toca sigue fallando.
        self.assertIn("sin él no sé", self.correr(base).stdout)

    def test_borrar_el_fichero_es_r2_y_avisa(self):
        """G4-2-A-02 y G4-2-B-02: borrar uno inválido de `main` no se presenta como corregirlo."""
        for rutas, inciso in ((FICHERO_RUTAS, ":"), ("- `src/pagos/`\n", " (el de `main` es inválido):")):
            with self.subTest(inciso=inciso):
                base = self.main_con(README_CON_RUTAS, rutas)
                self.pr(base)
                self.git("rm", "-q", checks.RUTAS_SENSIBLES)
                r = self.correr(base, nivel="R2", nueva=False)
                self.assertNivel(r, "R2")
                self.assertIn(f"el PR borra `.github/sdd/rutas-sensibles.txt`{inciso} después solo contarán", r.stdout)
                self.assertNotIn("lo corrige", r.stdout)
                self.assertNotIn("**riesgo:** `", r.stdout)

    def test_corchetes_e_interrogacion_son_literales(self):
        """G4-2-B-01: `[id]` es una carpeta de Next.js, no un comodín de un carácter. Las del README
        conservan además su lectura anterior: nunca menos rutas."""
        base = self.main_con("## Rutas sensibles\n\n- `web/[slug]/page.ts`\n- `lib/*.[jt]s`\n",
                             "app/api/pagos/[id]/route.ts\napp/[lang]/\nsrc/a?.js\n")
        self.assertNiveles(base, (
            ("app/api/pagos/[id]/route.ts", "R2"), ("app/api/pagos/i/route.ts", "R0"), ("app/[lang]/x.ts", "R2"),
            ("src/a?.js", "R2"), ("src/ab.js", "R0"), ("web/[slug]/page.ts", "R2"), ("web/s/page.ts", "R2"),
            ("lib/x.ts", "R2")))

    def test_sin_lista_de_ficheros_del_pr_falla(self):
        """G4-2-A-01: si Git no lista los ficheros, un PR que toca el de rutas no pasa por borrado."""
        base = self.main_con(rutas="- `src/pagos/`\n")
        anterior = os.getcwd()
        os.chdir(self.repo)
        try:
            inf = checks.Informe()
            checks.cargar_rutas_sensibles(inf, base, [checks.RUTAS_SENSIBLES], None, self.repo)
        finally:
            os.chdir(anterior)
        self.assertTrue(any("no he podido listar los ficheros del PR" in e for e in inf.errores), inf.errores)
        self.assertFalse(inf.avisos)

    def test_cambiar_la_lista_del_readme_sigue_siendo_r2(self):
        base = self.main_con(README_CON_RUTAS, FICHERO_RUTAS)
        self.pr(base)
        self.escribir("README.md", README_CON_RUTAS.replace("- `app/datos/`\n", ""))
        r = self.correr(base, nueva=False)
        self.assertNivel(r, "R2")
        self.assertIn("cambia la lista de rutas sensibles del README → R2", r.stdout)

    def test_formato(self):
        rutas, errores = checks.parse_rutas_sensibles(FICHERO_RUTAS + "\n   # sangrado\n")
        self.assertEqual(rutas, ["src/pagos/*", "tests/e2e/sin-conexion.spec.js", "src/auth/*.ts"])
        self.assertEqual(errores, [])
        self.assertEqual(checks.parse_rutas_sensibles(""), ([], []))
        self.assertEqual(checks.parse_rutas_sensibles("app/configuración.js\n"), (["app/configuración.js"], []))
        self.assertEqual(checks.parse_rutas_sensibles("src/pagos/\r\napp/sw.js\r\n"), (["src/pagos/*", "app/sw.js"], []))

    def test_un_comentario_no_se_traga_las_rutas_de_detras(self):
        """G4-3-B-01: con un salto que no es `\n` (un `\r` solo, U+2028…), lo que se ve como rutas detrás de
        un comentario sería parte del comentario. La línea es inválida, también si es un comentario."""
        for texto in ("# Rutas\rsrc/pagos/\rsrc/auth/\r", "src/pagos/\n# nota\u2028src/auth/\n",
                      "# nota\x0csrc/auth/\n", "# nota\x85src/auth/\n", "# nota\u2029src/auth/\n"):
            with self.subTest(texto=texto):
                self.assertTrue(checks.parse_rutas_sensibles(texto)[1], texto)
        self.assertEqual(checks.parse_rutas_sensibles("# nota\tcon tabulador\r\nsrc/a/\r\n"), (["src/a/*"], []))
        r = self.correr(self.main_con(rutas="# Rutas\rsrc/pagos/\r"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("de `main` es inválido (línea 1", r.stdout)

    def test_quitar_del_readme_una_ruta_con_corchetes_avisa(self):
        """G4-3-B-02: copiada al fichero, `lib/*.[jt]s` ya no cubre `lib/x.ts`; al vaciar el README, se avisa."""
        base = self.main_con("## Rutas sensibles\n\n- `lib/*.[jt]s`\n- `app/sw.js`\n", "lib/*.[jt]s\napp/sw.js\n")
        self.pr(base)
        self.escribir("README.md", "## Rutas sensibles\n\nEn el fichero.\n")
        r = self.correr(base, nueva=False)
        self.assertNivel(r, "R2")
        self.assertIn("el PR quita `lib/*.[jt]s` de las rutas sensibles del README", r.stdout)
        self.assertNotIn("quita `app/sw.js`", r.stdout)

    def test_check_riesgo_suma_las_dos_listas(self):
        cuerpo = "## Nivel de riesgo\n\n- [x] R1\n"
        readme = "## Rutas sensibles\n\n- `app/sw.js`\n"
        for cambiados, nivel in ((["app/sw.js"], "R2"), (["src/pagos/a.js"], "R2"), (["src/a.js"], "R1")):
            with self.subTest(cambiados=cambiados):
                self.assertEqual(checks.check_riesgo(checks.Informe(), cuerpo, cambiados, readme, readme, {}, {},
                                                     None, None, ["src/pagos/*"]), nivel)

    def test_plantilla_valida_y_sin_rutas_en_el_readme(self):
        texto = (PLANTILLA / ".github" / "sdd" / "rutas-sensibles.txt").read_text(encoding="utf-8")
        self.assertEqual(checks.parse_rutas_sensibles(texto), ([], []))
        self.assertEqual(checks.rutas_sensibles((PLANTILLA / "README.md").read_text(encoding="utf-8")), [])
        codeowners = (PLANTILLA / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
        self.assertIn("\n/.github/ ", codeowners)
        self.assertNotIn("/README.md", codeowners)

if __name__ == "__main__":
    unittest.main()

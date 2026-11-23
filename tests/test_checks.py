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


class TestRondasDeG4(unittest.TestCase):
    """VIC-39: de los comentarios salen el commit que vio cada revisor y los revisores de cada ronda."""

    def rondas(self, *cuerpos):
        return checks.rondas_de_g4([(f"#c{n}", c) for n, c in enumerate(cuerpos)])

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

    def comprobar(self, *cuerpos):
        anterior = os.getcwd()
        os.chdir(self.repo)
        try:
            with unittest.mock.patch.dict(os.environ, ENTORNO_GIT):
                return ejecutar(checks.check_cambios, "main", "HEAD", [(f"#c{n}", c) for n, c in enumerate(cuerpos)])
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

    def test_sin_ninguna_ronda_no_hace_nada(self):
        inf = self.comprobar("Un comentario cualquiera.")
        self.assertEqual((inf.errores, inf.secciones), ([], []))


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
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]', PR_BODY=cuerpo + linea,
                        PR_COMENTARIOS=str(ruta))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**cambios:** falta el commit que vio `G4-1-A`", r.stdout)
        visto = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True,
                               text=True, env=ENTORNO_GIT).stdout.strip()
        ruta.write_text(json.dumps([comentario(f"Commit revisado: G4-1-A · {visto}\n\n<details>\n\n"
                                               "### G4-1-A-01 · menor\n\n</details>")]), encoding="utf-8")
        r = self.correr("adr: decide y\n\nRefs: VIC-7", 'referencias: ["PR #13"]', PR_BODY=cuerpo + linea,
                        PR_COMENTARIOS=str(ruta), PR_HEAD_SHA="")
        self.assertEqual(r.returncode, 0, r.stdout)
        # Con la lista escrita a mano en la descripción, falla aunque la calculada esté bien (PR 2 de VIC-39).
        a_mano = subprocess.run([sys.executable, str(RUTA), "--base", "main"], cwd=self.repo, capture_output=True, text=True,
                                env={**ENTORNO_GIT, "PR_BODY": cuerpo + linea + "- **Cambios tras la última ronda:** ninguno\n",
                                     "PR_COMENTARIOS": str(ruta), "PR_BRANCH": "adr/vic-7-0002-x", "PR_TITLE": "adr: decide x"})
        self.assertEqual(a_mano.returncode, 1, a_mano.stdout)
        self.assertIn("**cambios:** la descripción del PR trae una lista", a_mano.stdout)
        cabeza = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True,
                                text=True, env=ENTORNO_GIT).stdout.strip()
        seccion = r.stdout.split("### Cambios tras la última ronda", 1)[1]
        self.assertEqual([l for l in seccion.splitlines() if l.startswith("- ")], [f"- `{cabeza[:7]}` adr: decide y"])
        # Como en la CI: HEAD es el merge que prueba GitHub y la cabeza del PR llega en PR_HEAD_SHA.
        self.git("switch", "-q", "--detach", "main")
        self.git("merge", "-q", "--no-ff", "--no-edit", cabeza)
        entorno = {**ENTORNO_GIT, "PR_BRANCH": "adr/vic-7-0002-x", "PR_TITLE": "adr: decide x",
                   "PR_BODY": cuerpo + linea, "PR_COMENTARIOS": str(ruta), "PR_HEAD_SHA": cabeza}
        entorno.pop("GITHUB_STEP_SUMMARY", None)
        r = subprocess.run([sys.executable, str(RUTA), "--base", "main"], cwd=self.repo,
                           capture_output=True, text=True, env=entorno)
        self.assertEqual(r.returncode, 0, r.stdout)
        seccion = r.stdout.split("### Cambios tras la última ronda", 1)[1]
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
        """VIC-56 (sospecha de G4-2-B): en pull_request_review el merge que se prueba puede ser anterior al
        último push; si la cabeza del PR no está en su historia, los checks verían el contenido viejo."""
        r = self.correr("adr: decide x\n\nRefs: VIC-7", 'referencias: ["PR #12"]', PR_HEAD_SHA="f" * 40)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**cabeza:** la cabeza del PR (`ffffffffffff`) no está en la historia del commit que se prueba",
                      r.stdout)

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
        entorno = {**ENTORNO_GIT, "PR_BRANCH": "dependabot/npm_and_yarn/lodash-4.17.21", "PR_REVIEWS": str(reviews),
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


if __name__ == "__main__":
    unittest.main()

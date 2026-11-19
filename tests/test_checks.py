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

    def test_pregunta_a_la_persona_pasa_y_avisa(self):
        inf = self.comprobar("- G4-1-A-01 · debe corregirse · prueba: x · resolución: pregunta a la persona")
        self.assertEqual(inf.errores, [])
        self.assertEqual(len(inf.avisos), 1)
        self.assertIn("`G4-1-A-01`", inf.avisos[0])

    def test_formato_roto_falla(self):
        for linea in ("- G4-1-A-01 debe corregirse, corregido en 1a2b3c4",
                      "- G4-1-A-01 · debe corregirse · resolución: corregido en 1a2b3c4",
                      "- G4-1-A-01 · debe corregirse · prueba: x"):
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
        for envoltorio in (f"<details><summary>Revisor A</summary>\n\n{sin_resolver}\n\n</details>",
                           f"<details>\n<details>\nx\n</details>\n{sin_resolver}\n</details>",
                           f"<details>\n{sin_resolver}</details>",
                           f"```\n{sin_resolver}\n```",
                           f"<!--\n{sin_resolver}\n-->"):
            with self.subTest(envoltorio=envoltorio):
                self.assertEqual(self.comprobar(envoltorio).errores, [])

    def test_fuera_de_lo_plegado_si_cuenta(self):
        inf = self.comprobar("<details>\nrespuesta\n</details>",
                             "- G4-1-A-01 · debe corregirse · prueba: x · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1)

    def test_details_sin_cerrar_falla(self):
        """Lo que va detrás de un <details> sin cerrar no se vería: no se puede dar por bueno."""
        inf = self.comprobar("<details><summary>Revisor A</summary>",
                             "- G4-1-A-01 · debe corregirse · prueba: x · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("sin cerrar", inf.errores[0])

    def test_details_entre_comillas_invertidas_es_texto(self):
        inf = self.comprobar("Encargo y respuesta, plegados en `<details>`.",
                             "- G4-1-A-01 · debe corregirse · prueba: x · resolución: pendiente")
        self.assertEqual(len(inf.errores), 1)
        self.assertIn("no tiene resolución", inf.errores[0])

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
        for resolucion in ("Corregido en 1a2b3c4", "Descartado: x", "Pregunta a la persona"):
            with self.subTest(resolucion=resolucion):
                inf = self.comprobar(f"- G4-1-A-01 · importante · prueba: x · resolución: {resolucion}")
                self.assertEqual(inf.errores, [])

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
                          "<details>\n\n```\n</details>\n```\n\n- G4-1-A-01 · menor · prueba: x · resolución: pendiente\n\n</details>"):
            with self.subTest(respuesta=respuesta):
                self.assertEqual(self.comprobar(respuesta).errores, [])


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

    def test_pr_de_dependabot(self):
        """Ni convenciones, ni formato de los commits, ni AC; el riesgo, R2 aunque no lo marque."""
        self.git("switch", "-q", "-c", "dependabot/npm_and_yarn/lodash-4.17.21", "main")
        (self.repo / "package.json").write_text('{"dependencies": {"lodash": "4.17.21"}}\n', encoding="utf-8")
        self.git("add", "package.json")
        bot = {"GIT_AUTHOR_NAME": "dependabot[bot]", "GIT_AUTHOR_EMAIL": checks.DEPENDABOT_CORREO}
        subprocess.run(["git", "-C", str(self.repo), "commit", "-q", "-m",
                        "chore(deps): bump lodash from 4.17.15 to 4.17.21 in the npm group across 1 directory"],
                       check=True, env={**ENTORNO_GIT, **bot})
        entorno = {**ENTORNO_GIT, "PR_BRANCH": "dependabot/npm_and_yarn/lodash-4.17.21",
                   "PR_TITLE": "chore(deps): bump lodash from 4.17.15 to 4.17.21",
                   "PR_BODY": "Bumps [lodash](https://github.com/lodash/lodash) from 4.17.15 to 4.17.21.",
                   "PR_AUTHOR": "dependabot[bot]"}
        correr = lambda **e: subprocess.run([sys.executable, str(RUTA), "--base", "main"], cwd=self.repo,
                                            capture_output=True, text=True, env={**entorno, **e})
        r = correr()
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PR de Dependabot", r.stdout)
        self.assertIn("**R2**", r.stdout)
        # Como en la CI: HEAD es el merge que prueba GitHub y la cabeza del PR llega aparte.
        cabeza = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True,
                                text=True, env=ENTORNO_GIT).stdout.strip()
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

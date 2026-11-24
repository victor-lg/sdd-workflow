#!/usr/bin/env python3
"""Checks SDD de la CI (workflow SDD + IA, v1.1).

Se ejecuta en cada PR contra `main`. La CI siempre usa la copia de este
fichero que hay en `main`, nunca la del PR, para que un PR no pueda
debilitar sus propios checks. Solo usa la librería estándar de Python.

Comprueba:
  specs         la estructura de las specs de docs/specs/ (frontmatter, IDs y secciones).
  mezcla        que un PR no cambie a la vez una spec y código (la spec va en su propio PR).
  trazabilidad  G3: cada AC que el PR declara cubrir existe en una spec de main
                y algún test lo cita como SPEC-XXX-NNN/AC-NN. Publica la matriz.
  riesgo        que el nivel marcado en el PR no sea menor que el que exigen
                las rutas tocadas, las specs que implementa y los ADR. La CI
                solo puede subir el nivel, nunca bajarlo. Las rutas sensibles del
                proyecto salen de RUTAS_SENSIBLES y de la sección del README (VIC-61);
                falla si el fichero no se puede leer o tiene una línea inválida.
  tests         lista los tests existentes que el PR modifica o borra (no bloquea).
  convenciones  M11: rama `<tipo>/vic-<N>-<descripcion>`, título del PR en formato
                de commit y descripción que empieza por `Fixes`, `Part of` o `Refs`
                con el ID (docs/convenciones.md del workflow).
  autoria       REG-34: ni el PR ni sus commits mencionan a Claude
                (`Co-Authored-By`, "Generated with"; ADR-0007).
  commits       REG-31 y REG-32: el mensaje de cada commit del PR (sin los merges) sigue
                el formato de `docs/convenciones.md` §4 del workflow, con `Refs: VIC-N` en el pie.
  historial     M39: avisa si una spec que cambia lleva historial en la cabecera.
  adr           M7: las listas de la cabecera YAML de los ADR que cambian van
                entre comillas (un `#` sin comillas se lee como comentario).
  lefthook      ADR-0008: la única configuración de lefthook es `lefthook.json`, solo con
                las claves que no amplían lo que se ejecuta, y no se quita si `main` la tiene.
  hallazgos     VIC-38: cada hallazgo de G4 de las respuestas de los revisores tiene su
                línea en la reconciliación del PR, con gravedad, prueba y resolución, y
                descartar uno que debe corregirse o importante pide una prueba (`sdd-review`).
                Las respuestas van en comentarios del PR: solo cuentan los de CUENTAS_G4.
                VIC-47: falla si falta un comentario que «Revisión IA» enlaza (borrado) o si uno
                de G4 se editó sin la línea `Comentario editado: <enlace> · <motivo>`.
  cambios       M8 (VIC-39): publica los commits que entraron tras la última ronda de G4, desde el
                que vio cada revisor (`Commit revisado:` en su comentario), y falla si falta o si la
                descripción trae esa lista escrita a mano.
  aprobacion    VIC-56 (ADR-0009 §3.4): un PR R2 (el mayor entre el nivel marcado y el que exige lo
                tocado) falla salvo que la última review de PERSONAS sea una aprobación del commit de
                la cabeza. Las reviews llegan en PR_REVIEWS (`gh api --paginate …/pulls/N/reviews`).
  g4            VIC-56 (ADR-0009 §3.1 y §5): falla si el PR no tiene G4, o si su última ronda tiene menos
                revisores de los que pide `sdd-review` (2 en R2, specs y ADR; 1 en lo demás). No la
                necesitan los PR de Dependabot ni un R0 que es solo documentación (`es_documentacion`);
                un R0 que no lo es cuenta como R1.
  cabeza        VIC-56: falla si PR_HEAD_SHA no está en la historia del commit que se prueba (el merge
                de GitHub puede ser anterior a un push reciente).

Los PR de Dependabot (M38) no siguen las convenciones de nombres ni declaran AC: ver
`es_de_dependabot`, que la acota al autor del PR y de sus commits y a lo que tocan.

Uso local:
  PR_BODY="$(cat cuerpo.md)" PR_TITLE="feat(calculo): …" PR_BRANCH="feat/vic-12-calculo" \
    python3 .github/sdd/checks.py --base refs/remotes/origin/main
Sin PR_TITLE ni PR_BRANCH, el check de convenciones no se ejecuta. PR_COMENTARIOS es la ruta
de los comentarios del PR (`gh api --paginate …/issues/N/comments`); sin ella, el
check de hallazgos solo lee la descripción. PR_REVIEWS es la ruta de las reviews; sin ella, un PR R2
falla en el check `aprobacion`. Los enlaces de «Revisión IA» a comentarios borrados
solo se comprueban con GITHUB_SERVER_URL, GITHUB_REPOSITORY y GITHUB_REF (`refs/pull/N/merge`), como en la CI.

Como hook `commit-msg` de lefthook, solo el formato del mensaje:
  python3 -I .github/sdd/checks.py --mensaje .git/COMMIT_EDITMSG
"""

from __future__ import annotations

import argparse
import fnmatch
import html
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

# --- Convenciones ---------------------------------------------------------

SPEC_ID = r"SPEC-[A-Z0-9]+-\d{3}"
RE_SPEC_ID = re.compile(rf"^{SPEC_ID}$")
RE_XCUT_ID = re.compile(r"^SPEC-XCUT-\d{3}$")
RE_AC_REF = re.compile(rf"\b({SPEC_ID})/(AC-\d{{2,3}})\b")
RE_DEF = re.compile(r"^\s*-\s+\*\*((?:FR|NFR|AC)-\d{2,3})\b([^*]*)\*\*(.*)$")
RE_DESTINO = re.compile(r"(?:→|->)\s*((?:N?FR-\d{2,3})(?:\s*,\s*N?FR-\d{2,3})*)")
RE_RIESGO_MARCADO = re.compile(r"^\s*-\s*\[[xX]\]\s*(R[012])\b", re.M)

ESTADOS = {"borrador", "en-revision", "aprobada", "sustituida"}
RIESGOS_SPEC = {"R1", "R2"}
CAMPOS_OBLIGATORIOS = ["id", "titulo", "estado", "version", "riesgo"]

# Rutas sensibles del proyecto (VIC-61): bajo `.github/`, así que tocarlo ya es R2 y está en
# CODEOWNERS. Formato en `parse_rutas_sensibles`. Mientras un proyecto migra, también cuenta la
# sección «Rutas sensibles» del README: se toma la unión, nunca menos rutas que antes.
RUTAS_SENSIBLES = ".github/sdd/rutas-sensibles.txt"
# Una ruta relativa a la raíz, sin espacios, comillas invertidas ni barras invertidas.
RE_RUTA_SENSIBLE = re.compile(r"[^\s`\\]+")
FORMATO_RUTAS = "Una ruta por línea, relativa a la raíz y sin comillas (formato al principio del fichero)."

# Disparadores de R2 del workflow (linea-base §6). `*` también cruza carpetas.
R2_RUTAS = [".github/*", ".claude/*", "AGENTS.md", "CLAUDE.md",
            "*/migrations/*", "migrations/*"]
# Configuración de los controles (ADR-0008, `docs/herramientas.md` del workflow): con ella se
# silencia un escáner o un hook de Git. Sin distinguir mayúsculas. La de los escáneres de la CI
# solo vale tras el merge (la CI usa la de `main`); la de lefthook y ESLint, ya en la rama.
R2_CONTROLES = ["lefthook.json", ".lefthook/*", ".lefthook-local/*",
                ".gitleaks.toml", ".gitleaksignore",
                ".gitattributes", "*/.gitattributes",
                ".semgrepignore", "*/.semgrepignore",
                "osv-scanner.toml", "*/osv-scanner.toml",
                "eslint.config.*", "*/eslint.config.*",
                # Todos los nombres que Stryker carga solo; los .js, .mjs y .cjs ejecutan código.
                "stryker.conf.*", "*/stryker.conf.*", "stryker.config.*", "*/stryker.config.*",
                ".stryker.conf.*", "*/.stryker.conf.*", ".stryker.config.*", "*/.stryker.config.*",
                # Los que knip carga solo (KNIP_CONFIG_LOCATIONS); los .ts y .js ejecutan código.
                "knip.json", "*/knip.json", "knip.jsonc", "*/knip.jsonc",
                ".knip.json", "*/.knip.json", ".knip.jsonc", "*/.knip.jsonc",
                "knip.[jt]s", "*/knip.[jt]s", "knip.config.[jt]s", "*/knip.config.[jt]s",
                # Los que jscpd busca solo (`*/.jscpd.json` cubre `.config/.jscpd.json`) y el
                # baseline que lee con --baseline.
                ".jscpd.json", "*/.jscpd.json", ".config/jscpd.json", "*/.config/jscpd.json",
                ".jscpd-baseline.json", "*/.jscpd-baseline.json",
                # Regresión visual (M27): las capturas de referencia las aprueba la persona, y la
                # configuración de Playwright puede ponerles tolerancias o escribir las que faltan.
                # Las carpetas por defecto de Playwright; si un proyecto cambia la suya con
                # `snapshotPathTemplate`, la añade a RUTAS_SENSIBLES. Las
                # tolerancias escritas en un fichero de test no se ven aquí (límite aceptado).
                "*-snapshots/*", "__screenshots__/*", "*/__screenshots__/*",
                "playwright.config.*", "*/playwright.config.*",
                "playwright-ct.config.*", "*/playwright-ct.config.*",
                # npm lo lee en `npm ci` y en `npm test` (script-shell, node-options), también dentro de Stryker.
                ".npmrc", "*/.npmrc",
                # Un submódulo trae código que no ve ningún escáner (también sus gitlinks, ver main).
                ".gitmodules"]
MANIFIESTOS = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb",
    # npm ci lo usa antes que package-lock.json (G4 del PR 2 de VIC-21).
    "npm-shrinkwrap.json",
    "requirements.txt", "pyproject.toml", "poetry.lock", "uv.lock", "Pipfile", "Pipfile.lock",
    "go.mod", "go.sum", "Cargo.toml", "Cargo.lock", "Gemfile", "Gemfile.lock",
    "composer.json", "composer.lock", "pom.xml", "build.gradle", "build.gradle.kts",
    "Package.swift", "Package.resolved", "Podfile", "Podfile.lock",
}
RE_MANIFIESTO_EXTRA = re.compile(r"^(requirements.*\.txt|.*\.csproj)$")

# Qué cuenta como fichero de test. Se ajusta con el ADR técnico del proyecto.
CARPETAS_TEST = {"tests", "test", "__tests__", "spec", "e2e"}
RE_FICHERO_TEST = re.compile(r"^(test_.+|.+_test\.\w+|.+\.(test|spec)\.\w+|.+Tests?\.\w+)$")
CARPETAS_IGNORADAS = {".git", "node_modules", ".venv", "venv", "dist", "build",
                      "docs", "discovery", ".tareas", ".github"}

# Lo que no es "código" a efectos de mezcla y trazabilidad.
PREFIJOS_NO_CODIGO = ("docs/", "discovery/", ".github/", ".claude/")
NO_CODIGO_SUELTOS = {".gitignore"}

ORDEN = {"R0": 0, "R1": 1, "R2": 2}

# Convenciones de nombres (M11). La clave es la del equipo de Linear.
CLAVE_ISSUE = "VIC"
TIPOS = ("feat", "fix", "spec", "adr", "refactor", "test", "docs", "ci", "chore")
RE_RAMA = re.compile(rf"^({'|'.join(TIPOS)})/{CLAVE_ISSUE.lower()}-([1-9]\d*)-[a-z0-9]+(?:-[a-z0-9]+)*$")
RE_TITULO = re.compile(rf"^({'|'.join(TIPOS)})(?:\(([^()\s]+)\))?(!)?: (\S.*)$")
RE_ID_ISSUE = re.compile(rf"^{CLAVE_ISSUE}-\d+$", re.I)
RE_ENLACE = re.compile(rf"^(?:Fixes|Part of|Refs):?\s+{CLAVE_ISSUE}-([1-9]\d*)\b")
LARGO_RAMA, LARGO_DESCRIPCION = 50, 72

# Menciones a Claude que no van en commits ni PR (REG-34, ADR-0007).
RE_AUTORIA = re.compile(r"Co-Authored-By:.*(claude|anthropic)|Generated with \[?Claude", re.I)

# Señales de historial en la cabecera de una spec (M39): el porqué de cada
# versión vive en Git, en los PR y en los ADR.
SENALES_HISTORIAL = [
    (re.compile(r"^(historial|cambios|changelog)\s*:", re.I | re.M), "un campo de historial"),
    (re.compile(r"\bronda\s+\d", re.I), "rondas de revisión"),
    (re.compile(r"\bversi[oó]n\s+\d+\.\d+", re.I), "versiones anteriores"),
    (re.compile(r"\bPR\s*#\d+"), "referencias a PR"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "fechas"),
]
# Configuración de lefthook (ADR-0008). Lista blanca: se rechaza cualquier otra clave,
# también la misma en otras mayúsculas. JSON y no YAML, para leerlo sin dependencias y sin
# anclas ni claves de fusión que escondan claves.
LEFTHOOK_CONFIG = "lefthook.json"
RE_LEFTHOOK_OTRA = re.compile(r"(^|/)(\.config/)?\.?lefthook(-local)?\.(yml|yaml|json|jsonc|toml)$"
                              r"|(^|/)\.lefthook(-local)?/", re.I)
LEFTHOOK_CLAVES = {"min_version", "assert_lefthook_installed", "no_auto_install", "no_tty",
                   "pre-commit", "commit-msg"}
LEFTHOOK_OBLIGATORIAS = ("assert_lefthook_installed", "no_auto_install")
LEFTHOOK_HOOKS = {"pre-commit", "commit-msg"}
LEFTHOOK_CLAVES_HOOK = {"parallel", "piped", "jobs"}
LEFTHOOK_CLAVES_JOB = {"name", "run", "glob", "exclude", "file_types", "fail_text"}
RE_GITLEAKS_ANTES = re.compile(r'"run"\s*:\s*"gitleaks git --pre-commit')
RE_FORMATO_ANTES = re.compile(r'"run"\s*:\s*"python3 -I \.github/sdd/checks\.py --mensaje ')

RE_TITULO_HISTORIAL = re.compile(r"^#+\s*(?:\d+\.\s*)?(historial|registro de cambios|cambios|changelog)\b", re.I | re.M)


# --- Utilidades -----------------------------------------------------------

class Informe:
    def __init__(self) -> None:
        self.errores: list[str] = []
        self.avisos: list[str] = []
        self.secciones: list[str] = []

    def error(self, check: str, msg: str) -> None:
        self.errores.append(f"**{check}:** {msg}")

    def aviso(self, check: str, msg: str) -> None:
        self.avisos.append(f"**{check}:** {msg}")


def git(*args: str) -> str | None:
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def rutas(*args: str) -> list[str] | None:
    """Una orden de Git que lista rutas, con -z: sin él, Git entrecomilla las rutas no ASCII
    (`".claude/\\303\\261.md"`) y ningún patrón ni `es_test`/`es_spec` las reconoce (G4 de VIC-56)."""
    # -z justo tras la suborden: después de `--` sería una ruta.
    salida = git(args[0], "-z", *args[1:])
    return None if salida is None else [r for r in salida.split("\0") if r]


def es_codigo(ruta: str) -> bool:
    return not (ruta.startswith(PREFIJOS_NO_CODIGO) or ruta.endswith(".md")
                or ruta in NO_CODIGO_SUELTOS)


def es_adr(ruta: str) -> bool:
    p = Path(ruta)
    return (p.parent.as_posix() == "docs/adr" and p.suffix == ".md"
            and not p.name.startswith("_"))


RE_NO_APLICA = re.compile(r"AC cubiertos:\s*no aplica\s*\((?=[^)]*\w)[^)]+\)", re.I)


def es_spec(ruta: str) -> bool:
    p = Path(ruta)
    return (p.parent.as_posix() == "docs/specs" and p.suffix == ".md"
            and not p.name.startswith("_"))


def seccion(texto: str, titulo: str) -> str:
    """Texto entre `## <titulo>` y el siguiente `## `, sin comentarios HTML."""
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    m = re.search(rf"^##\s+{re.escape(titulo)}[^\n]*\n(.*?)(?=^##\s|\Z)", texto, re.M | re.S)
    return m.group(1) if m else ""


# --- Specs ----------------------------------------------------------------

def parse_spec(texto: str) -> tuple[dict, str] | None:
    if not texto.startswith("---"):
        return None
    fin = texto.find("\n---", 3)
    if fin < 0:
        return None
    meta: dict[str, object] = {}
    for linea in texto[3:fin].splitlines():
        linea = re.sub(r"\s+#.*$", "", linea).strip()
        if not linea or ":" not in linea:
            continue
        clave, valor = (s.strip() for s in linea.split(":", 1))
        if valor.startswith("[") and valor.endswith("]"):
            meta[clave] = [v.strip() for v in valor[1:-1].split(",") if v.strip()]
        else:
            meta[clave] = None if valor in ("", "null", "~") else valor
    return meta, texto[fin + 4:]


def definiciones(cuerpo: str) -> tuple[dict[str, tuple[str, list[str]]], list[str]]:
    """IDs definidos -> (texto, destinos); y lista de IDs duplicados."""
    defs: dict[str, tuple[str, list[str]]] = {}
    duplicados: list[str] = []
    for linea in cuerpo.splitlines():
        m = RE_DEF.match(linea)
        if not m:
            continue
        ident, cabecera, resto = m.group(1), m.group(2), m.group(3)
        if ident in defs:
            duplicados.append(ident)
        d = RE_DESTINO.search(cabecera)
        destinos = [x.strip() for x in d.group(1).split(",")] if d else []
        defs[ident] = (resto.strip(), destinos)
    return defs, duplicados


def cargar_specs(ficheros: dict[str, str]) -> dict[str, dict]:
    """ruta -> texto  ==>  id -> {ruta, meta, defs}. Ignora las que no se pueden leer."""
    specs: dict[str, dict] = {}
    for ruta, texto in ficheros.items():
        r = parse_spec(texto)
        if not r:
            continue
        meta, cuerpo = r
        ident = meta.get("id")
        if isinstance(ident, str):
            defs, _ = definiciones(cuerpo)
            specs.setdefault(ident, {"ruta": ruta, "meta": meta, "defs": defs})
    return specs


def check_specs(inf: Informe, ficheros: dict[str, str]) -> None:
    vistos: dict[str, str] = {}
    todos = cargar_specs(ficheros)
    for ruta, texto in sorted(ficheros.items()):
        r = parse_spec(texto)
        if not r:
            inf.error("specs", f"`{ruta}` no tiene frontmatter `---` válido.")
            continue
        meta, cuerpo = r
        faltan = [c for c in CAMPOS_OBLIGATORIOS if not meta.get(c)]
        if faltan:
            inf.error("specs", f"`{ruta}`: faltan campos {', '.join(faltan)}.")
            continue
        ident, estado, riesgo = str(meta["id"]), str(meta["estado"]), str(meta["riesgo"])
        if not RE_SPEC_ID.match(ident):
            inf.error("specs", f"`{ruta}`: el id `{ident}` no sigue el formato SPEC-AREA-NNN.")
        if not Path(ruta).name.startswith(ident):
            inf.error("specs", f"`{ruta}`: el nombre del fichero debe empezar por su id `{ident}`.")
        if ident in vistos:
            inf.error("specs", f"id `{ident}` duplicado en `{ruta}` y `{vistos[ident]}`.")
        vistos[ident] = ruta
        if estado not in ESTADOS:
            inf.error("specs", f"`{ruta}`: estado `{estado}` no válido ({', '.join(sorted(ESTADOS))}).")
        if riesgo not in RIESGOS_SPEC:
            inf.error("specs", f"`{ruta}`: riesgo `{riesgo}` no válido (R1 o R2; R0 no lleva spec).")
        if not re.match(r"^\d+(\.\d+)*$", str(meta["version"])):
            inf.error("specs", f"`{ruta}`: versión `{meta['version']}` no válida.")
        sust = meta.get("sustituye")
        if sust and sust not in todos:
            inf.error("specs", f"`{ruta}`: sustituye a `{sust}`, que no existe.")
        trans = meta.get("transversales") or []
        for t in trans if isinstance(trans, list) else [trans]:
            if not RE_XCUT_ID.match(t):
                inf.error("specs", f"`{ruta}`: `{t}` en transversales no es una spec SPEC-XCUT-NNN.")
            elif t not in todos:
                inf.error("specs", f"`{ruta}`: la spec transversal `{t}` no existe.")

        for n in range(1, 7):
            if not re.search(rf"^##\s+{n}\.", cuerpo, re.M):
                inf.error("specs", f"`{ruta}`: falta la sección obligatoria {n}.")

        defs, dups = definiciones(cuerpo)
        for d in sorted(set(dups)):
            inf.error("specs", f"`{ruta}`: el ID `{d}` está definido más de una vez.")
        acs = [i for i in defs if i.startswith("AC-")]
        exigente = estado != "borrador"
        if exigente and not acs:
            inf.error("specs", f"`{ruta}`: no define ningún AC.")
        for ident_def, (texto_def, destinos) in defs.items():
            if exigente and not texto_def:
                inf.error("specs", f"`{ruta}`: `{ident_def}` está vacío.")
            if ident_def.startswith("AC-"):
                if not destinos:
                    inf.error("specs", f"`{ruta}`: `{ident_def}` no indica qué requisito demuestra (`AC-xx → FR-yy`).")
                for dest in destinos:
                    if dest not in defs:
                        inf.error("specs", f"`{ruta}`: `{ident_def}` apunta a `{dest}`, que no está definido.")


# --- Tests y trazabilidad -------------------------------------------------

def es_test(ruta: str) -> bool:
    partes = ruta.split("/")
    return bool(CARPETAS_TEST.intersection(partes[:-1]) or RE_FICHERO_TEST.match(partes[-1]))


def citas_en_tests(raiz: Path) -> dict[tuple[str, str], list[str]]:
    citas: dict[tuple[str, str], list[str]] = {}
    for carpeta, subcarpetas, nombres in os.walk(raiz):
        subcarpetas[:] = [s for s in subcarpetas if s not in CARPETAS_IGNORADAS]
        for nombre in nombres:
            ruta = (Path(carpeta) / nombre).relative_to(raiz).as_posix()
            if not es_test(ruta):
                continue
            p = raiz / ruta
            if p.stat().st_size > 1_000_000:
                continue
            texto = p.read_text(encoding="utf-8", errors="ignore")
            for m in RE_AC_REF.finditer(texto):
                lista = citas.setdefault((m.group(1), m.group(2)), [])
                if ruta not in lista:
                    lista.append(ruta)
    return citas


def check_trazabilidad(inf: Informe, cuerpo_pr: str, cambiados: list[str],
                       specs_base: dict[str, dict], specs_head: dict[str, dict],
                       citas: dict[tuple[str, str], list[str]], dependabot: bool = False) -> None:
    codigo = [f for f in cambiados if es_codigo(f)]
    cubre = seccion(cuerpo_pr, "Qué comportamiento cubre")
    refs = sorted(set(RE_AC_REF.findall(cubre)))

    if codigo:
        if not refs:
            if dependabot:
                inf.aviso("trazabilidad", "PR de Dependabot: solo cambia dependencias y no declara AC.")
            elif RE_NO_APLICA.search(cubre):
                inf.aviso("trazabilidad", "⚠️ el PR toca código y declara que no cubre ningún AC (`no aplica`). Comprueba que no cambia comportamiento: si lo cambia, necesita spec y AC.")
            else:
                inf.error("trazabilidad", "el PR toca código pero no declara los AC que cubre. Escribe `AC cubiertos: SPEC-XXX-NNN/AC-NN, …` o `AC cubiertos: no aplica (motivo)`, con el motivo entre paréntesis.")
        for spec, ac in refs:
            base = specs_base.get(spec)
            if not base:
                inf.error("trazabilidad", f"`{spec}` no está en `main`. No se puede implementar una spec sin aprobar (G1/G2, caso N1).")
                continue
            if ac not in base["defs"]:
                inf.error("trazabilidad", f"`{spec}/{ac}` no existe en la versión de `main` de la spec.")
                continue
            if (spec, ac) not in citas:
                inf.error("trazabilidad", f"ningún test cita `{spec}/{ac}` (G3, caso N7).")

    for (spec, ac), ficheros in sorted(citas.items()):
        if spec not in specs_head or ac not in specs_head[spec]["defs"]:
            inf.aviso("trazabilidad", f"`{', '.join(ficheros)}` cita `{spec}/{ac}`, que no existe.")

    filas = ["| Spec | AC | Tests |", "| --- | --- | --- |"]
    for spec in sorted(specs_head):
        for ac in sorted(i for i in specs_head[spec]["defs"] if i.startswith("AC-")):
            tests = citas.get((spec, ac))
            filas.append(f"| {spec} | {ac} | {', '.join(f'`{t}`' for t in tests) if tests else '— sin test'} |")
    if len(filas) > 2:
        inf.secciones.append("### Matriz AC ↔ tests\n\n" + "\n".join(filas))


# --- Mezcla de spec y código ----------------------------------------------

def check_mezcla(inf: Informe, cambiados: list[str]) -> None:
    specs = [f for f in cambiados if es_spec(f)]
    codigo = [f for f in cambiados if es_codigo(f)]
    if specs and codigo:
        inf.error("mezcla", f"el PR cambia specs ({', '.join(specs)}) y código a la vez. La spec se aprueba primero, en su propio PR (caso N2).")


# --- Riesgo ---------------------------------------------------------------

def rutas_sensibles(readme: str | None) -> list[str]:
    """Las de la sección «Rutas sensibles» del README (el formato anterior a VIC-61)."""
    if not readme:
        return []
    patrones = re.findall(r"^\s*-\s+`([^`]+)`", seccion(readme, "Rutas sensibles"), re.M)
    return [p + "*" if p.endswith("/") else p for p in patrones]


def patron_literal(ruta: str) -> str:
    """El patrón de fnmatch en el que `[`, `]` y `?` son literales y solo `*` es comodín."""
    return re.sub(r"([\[\]?])", r"[\1]", ruta)


def patrones_del_readme(readme: str | None) -> list[str]:
    """Las rutas del README con su lectura de siempre (`[` y `?` comodines) y, además, la literal, como
    en el fichero: solo suma rutas (G4-2-B-01)."""
    rutas = rutas_sensibles(readme)
    return rutas + [patron_literal(p) for p in rutas if patron_literal(p) != p]


# Lo que un editor puede mostrar como salto de línea. Dentro de una línea, también de un comentario, la
# invalida: si no, un comentario se tragaría en silencio las rutas que se ven detrás (G4-3-B-01).
SALTOS_RAROS = set("\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029")


def parse_rutas_sensibles(texto: str) -> tuple[list[str], list[str]]:
    """Formato de RUTAS_SENSIBLES: una ruta por línea, relativa a la raíz del repo y sin comillas, como
    `app/sw.js`, `src/pagos/` (la carpeta entera) o `src/auth/*.ts` (`*` también cruza carpetas). Se
    ignoran las líneas vacías y las que empiezan por `#`. Una línea con espacios, caracteres de control
    o invisibles, comillas invertidas o barras invertidas, que empiece por `/` o `./`, o con un tramo
    `..`, es inválida: no coincidiría con ninguna ruta y la lista tendría un hueco sin que nadie lo
    viera. Un BOM al principio del fichero no cuenta. Solo `*` es comodín: `[`, `]` y `?` son literales,
    como en `app/[id]/route.ts` (G4-2-B-01). Se parte solo por `\n`: `splitlines()` partiría también
    por caracteres de control, que así llegan a la línea y la invalidan; un salto de otro tipo (`\r` solo,
    U+2028…) invalida también un comentario. Vale `\r\n`. Devuelve (patrones, errores)."""
    rutas, errores = [], []
    for n, linea in enumerate(texto.removeprefix("\ufeff").split("\n"), 1):
        ruta = linea.removesuffix("\r").strip(" \t")
        if SALTOS_RAROS & set(ruta):
            errores.append(f"línea {n}, `{ascii(ruta)[1:-1][:80]}`")
            continue
        if not ruta or ruta.startswith("#"):
            continue
        if (not RE_RUTA_SENSIBLE.fullmatch(ruta) or ruta.startswith(("/", "./"))
                or ".." in ruta.split("/") or any(unicodedata.category(c)[0] in "CZ" for c in ruta)):
            errores.append(f"línea {n}, `{ascii(ruta)[1:-1][:80]}`")
            continue
        rutas.append(patron_literal(ruta) + ("*" if ruta.endswith("/") else ""))
    return rutas, errores


def leer_rutas_sensibles(base: str) -> tuple[bool, str | None]:
    """(existe, texto) de RUTAS_SENSIBLES en `base`. Si existe pero no es un fichero normal o no se lee
    como UTF-8, el texto es None: quien llama falla, nunca sigue con menos rutas."""
    entrada = git("ls-tree", base, "--", RUTAS_SENSIBLES)
    if entrada is None:
        return True, None
    if not entrada.strip():
        return False, None
    if not entrada.startswith(("100644 blob ", "100755 blob ")):
        return True, None
    r = subprocess.run(["git", "show", f"{base}:{RUTAS_SENSIBLES}"], capture_output=True)
    if r.returncode != 0:
        return True, None
    try:
        return True, r.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return True, None


def errores_de_rutas(texto: str | None) -> list[str]:
    return ["no es un fichero normal de texto UTF-8"] if texto is None else parse_rutas_sensibles(texto)[1]


def cargar_rutas_sensibles(inf: Informe, base: str, cambiados: list[str],
                           versionados: dict[str, str] | None, raiz: Path) -> list[str]:
    """Las rutas de RUTAS_SENSIBLES en `base` (lo que cuenta para el nivel). Si el PR cambia el fichero,
    comprueba también su versión: un fichero inválido en `main` haría fallar todos los PR siguientes.
    Por eso, si el de `main` es inválido y el PR lo deja válido o lo borra, solo avisa: ese PR es R2 (lo
    aprueba la persona) y es el que lo arregla. Borrarlo lo avisa siempre: después solo cuenta el README."""
    existe, texto = leer_rutas_sensibles(base)
    rutas = parse_rutas_sensibles(texto)[0] if texto is not None else []
    errores_base = errores_de_rutas(texto) if existe else []
    if RUTAS_SENSIBLES in cambiados:
        modo = None if versionados is None else versionados.get(RUTAS_SENSIBLES)
        if versionados is None:
            errores_pr = ["no he podido listar los ficheros del PR con Git"]
        elif modo is None:
            inf.aviso("riesgo", f"⚠️ el PR borra `{RUTAS_SENSIBLES}`"
                                + (" (el de `main` es inválido)" if errores_base else "")
                                + ": después solo contarán las rutas sensibles del README.")
            errores_pr, errores_base = [], []
        else:
            try:
                nuevo = (raiz / RUTAS_SENSIBLES).read_bytes().decode("utf-8") if modo in ("100644", "100755") else None
            except (OSError, UnicodeDecodeError):
                nuevo = None
            errores_pr = errores_de_rutas(nuevo)
        if errores_pr:
            inf.error("riesgo", f"el PR deja `{RUTAS_SENSIBLES}` inválido ({'; '.join(errores_pr)}): {FORMATO_RUTAS}")
        elif errores_base:
            inf.aviso("riesgo", f"⚠️ `{RUTAS_SENSIBLES}` de `main` es inválido ({'; '.join(errores_base)}) y este PR lo corrige.")
            errores_base = []
    if errores_base:
        inf.error("riesgo", f"`{RUTAS_SENSIBLES}` de `main` es inválido ({'; '.join(errores_base)}): sin él no sé "
                            f"qué rutas del proyecto son sensibles. {FORMATO_RUTAS}")
    return rutas


def es_manifiesto(ruta: str) -> bool:
    nombre = ruta.rsplit("/", 1)[-1]
    return nombre in MANIFIESTOS or bool(RE_MANIFIESTO_EXTRA.match(nombre))


def riesgo_de(texto: str | None) -> str | None:
    r = parse_spec(texto) if texto else None
    nivel = str(r[0].get("riesgo")) if r else None
    return nivel if nivel in RIESGOS_SPEC else None


def check_riesgo(inf: Informe, cuerpo_pr: str, cambiados: list[str],
                 readme_base: str | None, readme_head: str | None,
                 specs_head_ficheros: dict[str, str],
                 specs_base_ficheros: dict[str, str], por_defecto: str | None = None,
                 submodulos: list[str] | None = None, rutas_fichero: list[str] | None = None) -> str:
    """por_defecto: el nivel que se toma si el PR no marca ninguno (solo los de Dependabot).
    submodulos: los gitlinks (modo 160000) que el PR añade o cambia.
    rutas_fichero: las rutas de RUTAS_SENSIBLES en `main`; se suman a las del README de `main`.
    Devuelve el nivel efectivo: el mayor entre el marcado y el mínimo según lo tocado."""
    marcados = RE_RIESGO_MARCADO.findall(seccion(cuerpo_pr, "Nivel de riesgo"))
    if not marcados and por_defecto:
        declarado = por_defecto
    elif len(marcados) != 1:
        inf.error("riesgo", f"marca exactamente un nivel de riesgo en el PR (hay {len(marcados)}).")
        declarado = None
    else:
        declarado = marcados[0]

    minimo, motivos = "R0", []

    def subir(nivel: str, motivo: str) -> None:
        nonlocal minimo
        motivos.append(f"{motivo} → {nivel}")
        if ORDEN[nivel] > ORDEN[minimo]:
            minimo = nivel

    propias = patrones_del_readme(readme_base) + (rutas_fichero or [])
    # Una ruta sin `/` final que nombra una carpeta también la cubre entera: nunca menos rutas.
    propias += [p + "/*" for p in propias if not p.endswith("*")]
    for f in cambiados:
        if any(fnmatch.fnmatchcase(f, p) for p in R2_RUTAS):
            subir("R2", f"`{f}` (configuración del agente, CI o migraciones)")
        elif any(fnmatch.fnmatchcase(f.lower(), p) for p in R2_CONTROLES):
            subir("R2", f"`{f}` (configuración de un control de seguridad)")
        elif es_manifiesto(f):
            subir("R2", f"`{f}` (dependencias)")
        elif any(fnmatch.fnmatchcase(f, p) for p in propias):
            subir("R2", f"`{f}` (ruta sensible del proyecto)")
    for f in submodulos or []:
        subir("R2", f"`{f}` (submódulo: su código no lo ve ningún escáner)")
    if "README.md" in cambiados and rutas_sensibles(readme_head) != rutas_sensibles(readme_base):
        subir("R2", "cambia la lista de rutas sensibles del README")
        # G4-3-B-02: en el fichero, `[` y `?` son literales; al quitar una así del README, se pierde esa lectura.
        for p in sorted(set(rutas_sensibles(readme_base)) - set(rutas_sensibles(readme_head))):
            if patron_literal(p) != p:
                inf.aviso("riesgo", f"⚠️ el PR quita `{p}` de las rutas sensibles del README. En `{RUTAS_SENSIBLES}`, "
                                    "`[`, `]` y `?` se leen tal cual: comprueba que lo que cubría sigue cubierto.")
    if RUTAS_SENSIBLES in cambiados:
        subir("R2", f"cambia `{RUTAS_SENSIBLES}`, la lista de rutas sensibles")
    for f in cambiados:
        if es_spec(f):
            # El mayor entre main y el PR: un PR de spec no puede bajar su propio riesgo.
            niveles = [n for n in (riesgo_de(specs_head_ficheros.get(f)),
                                   riesgo_de(specs_base_ficheros.get(f))) if n]
            subir(max(niveles, key=ORDEN.get) if niveles else "R1", f"spec `{f}`")
        elif es_adr(f):
            subir("R1", f"ADR `{f}`")
    # Un PR de código hereda el riesgo (en main) de las specs que implementa.
    riesgo_base = {}
    for texto in specs_base_ficheros.values():
        r = parse_spec(texto)
        if r and isinstance(r[0].get("id"), str):
            riesgo_base[r[0]["id"]] = riesgo_de(texto)
    citadas = {s for s, _ in RE_AC_REF.findall(seccion(cuerpo_pr, "Qué comportamiento cubre"))}
    for spec in sorted(citadas):
        if riesgo_base.get(spec):
            subir(riesgo_base[spec], f"implementa `{spec}`")

    lineas = [f"- Nivel marcado en el PR: **{declarado or '—'}**"
              + (" (sin marcar: se toma el de Dependabot)" if declarado and not marcados else ""),
              f"- Nivel mínimo según lo tocado: **{minimo}**"]
    lineas += [f"  - {m}" for m in motivos]
    inf.secciones.append("### Nivel de riesgo\n\n" + "\n".join(lineas))
    if declarado and ORDEN[declarado] < ORDEN[minimo]:
        inf.error("riesgo", f"el PR está marcado {declarado} pero lo que toca exige {minimo}. Sube el nivel en el PR (la CI solo puede subirlo).")
    return max(declarado or minimo, minimo, key=ORDEN.get)


# --- Tests existentes que cambian -----------------------------------------

def check_tests(inf: Informe, base: str) -> None:
    # Con -z, `--name-status` alterna el estado y la ruta.
    campos = rutas("diff", "--name-status", "--no-renames", "--diff-filter=MD", f"{base}...HEAD") or []
    filas = []
    for estado, ruta in zip(campos[::2], campos[1::2]):
        if es_test(ruta):
            filas.append(f"- `{ruta}` ({'borrado' if estado == 'D' else 'modificado'})")
    if filas:
        inf.secciones.append("### Tests existentes que cambian\n\n"
                             "Léelos en *Files changed* y comprueba que la guía del revisor explica cada uno.\n\n"
                             + "\n".join(filas))


# --- Convenciones de nombres (M11) ----------------------------------------

def check_convenciones(inf: Informe, rama: str, titulo: str, cuerpo_pr: str) -> None:
    m_rama = RE_RAMA.match(rama)
    if not m_rama:
        inf.error("convenciones", f"la rama `{rama}` no sigue `<tipo>/{CLAVE_ISSUE.lower()}-<N>-<descripcion>`, con el tipo uno de {', '.join(TIPOS)} y la descripción en minúsculas y *kebab-case*.")
    elif len(rama) > LARGO_RAMA:
        inf.aviso("convenciones", f"la rama `{rama}` tiene {len(rama)} caracteres; la convención es unos {LARGO_RAMA}.")

    m_tit = RE_TITULO.match(titulo)
    if not m_tit:
        inf.error("convenciones", f"el título del PR `{titulo}` no sigue `<tipo>(<alcance>)!: <descripción>`, con el tipo uno de {', '.join(TIPOS)}. Al fusionar por squash será el commit de `main`.")
    else:
        tipo, alcance, _, descripcion = m_tit.groups()
        if alcance and RE_ID_ISSUE.match(alcance):
            inf.error("convenciones", f"el alcance del título es el ID `{alcance}`; el alcance es la zona del código o del documento y el ID va en la descripción del PR.")
        if len(descripcion) > LARGO_DESCRIPCION:
            inf.error("convenciones", f"la descripción del título tiene {len(descripcion)} caracteres; el máximo es {LARGO_DESCRIPCION}.")
        if descripcion[0].isupper() or descripcion.endswith("."):
            inf.aviso("convenciones", "la descripción del título va en minúscula y sin punto final.")
        if m_rama and m_rama.group(1) != tipo:
            inf.aviso("convenciones", f"el tipo del título (`{tipo}`) no es el de la rama (`{m_rama.group(1)}`).")

    texto = re.sub(r"<!--.*?-->", "", cuerpo_pr, flags=re.S)
    primera = next((l.strip() for l in texto.splitlines()
                    if l.strip() and not l.lstrip().startswith("#")), "")
    m_enl = RE_ENLACE.match(primera)
    if not m_enl:
        inf.error("convenciones", f"la descripción del PR debe empezar por `Fixes {CLAVE_ISSUE}-N`, `Part of {CLAVE_ISSUE}-N` o `Refs {CLAVE_ISSUE}-N` (decisión 4 de M11); " + (f"empieza por `{primera[:80]}`." if primera else "está vacía."))
    elif m_rama and m_enl.group(1) != m_rama.group(2):
        inf.aviso("convenciones", f"la descripción enlaza {CLAVE_ISSUE}-{m_enl.group(1)} y la rama es de {CLAVE_ISSUE}-{m_rama.group(2)}.")


# --- Autoría (REG-34) -----------------------------------------------------

def check_autoria(inf: Informe, titulo: str, cuerpo_pr: str, mensajes: list[str]) -> None:
    if RE_AUTORIA.search(titulo) or RE_AUTORIA.search(cuerpo_pr):
        inf.error("autoria", "el título o la descripción del PR mencionan a Claude (`Co-Authored-By` o \"Generated with\"). Quítalo (ADR-0007).")
    n = sum(1 for m in mensajes if RE_AUTORIA.search(m))
    if n:
        inf.error("autoria", f"{n} commit(s) del PR mencionan a Claude (`Co-Authored-By` o \"Generated with\"). Reescribe sus mensajes (ADR-0007).")


def mensajes_commits(base: str) -> list[str]:
    salida = git("log", "--format=%B%x00", f"{base}..HEAD") or ""
    return [m for m in salida.split("\x00") if m.strip()]


# --- Formato de los commits (REG-31, REG-32) ------------------------------

RE_PIE = re.compile(r"^(BREAKING CHANGE|[A-Za-z][\w-]*): ")
RE_REFS = re.compile(rf"^Refs: {CLAVE_ISSUE}-[1-9]\d*(, {CLAVE_ISSUE}-[1-9]\d*)*$")
RE_SPEC_PIE = re.compile(rf"^Spec: {SPEC_ID}/AC-\d{{2,3}}(, {SPEC_ID}/AC-\d{{2,3}})*$")
ORDEN_PIE = ("Refs", "Spec", "BREAKING CHANGE")
# Los títulos que Git pone a un merge: el hook los deja pasar. La CI no mira los merges, pero sí
# un commit normal con ese título.
RE_MERGE_GIT = re.compile(r"^Merge (branch|remote-tracking branch|commit|tag) ")
TIJERA = "# ------------------------ >8 ------------------------"


def limpiar_mensaje(texto: str) -> str:
    """Como lo deja Git: sin comentarios `#` ni lo que va tras la línea de tijera."""
    texto = texto.split(TIJERA, 1)[0]
    lineas = [l.rstrip() for l in texto.splitlines() if not l.startswith("#")]
    return "\n".join(lineas).strip("\n")


def problemas_mensaje(texto: str, admite_merge: bool = False) -> tuple[list[str], list[str]]:
    """(errores, avisos) del mensaje de un commit según `docs/convenciones.md` §4 del workflow.
    admite_merge: es el hook `commit-msg`, que recibe el mensaje antes de que Git lo limpie."""
    lineas = (limpiar_mensaje(texto) if admite_merge else texto.strip("\n")).splitlines()
    if not lineas or not lineas[0].strip():
        return ["el mensaje está vacío."], []
    titulo = lineas[0]
    if admite_merge and RE_MERGE_GIT.match(titulo):
        return [], []
    errores, avisos = [], []
    m = RE_TITULO.match(titulo)
    if not m:
        errores.append(f"el título `{titulo[:80]}` no sigue `<tipo>(<alcance>)!: <descripción>`, con el tipo uno de {', '.join(TIPOS)}.")
    else:
        _, alcance, _, descripcion = m.groups()
        if alcance and RE_ID_ISSUE.match(alcance):
            errores.append(f"el alcance del título es el ID `{alcance}`; el alcance es la zona del código y el ID va en el pie (`Refs: {alcance.upper()}`).")
        if len(descripcion) > LARGO_DESCRIPCION:
            errores.append(f"la descripción del título tiene {len(descripcion)} caracteres; el máximo es {LARGO_DESCRIPCION}.")
        if descripcion[0].isupper() or descripcion.endswith("."):
            avisos.append("la descripción del título va en minúscula y sin punto final.")
    if len(lineas) > 1 and lineas[1].strip():
        errores.append("falta la línea en blanco entre el título y el cuerpo.")
    # El pie es el último párrafo, si todas sus líneas son `Clave: valor`.
    parrafos = "\n".join(lineas[1:]).strip("\n").split("\n\n")
    pie = [l for l in parrafos[-1].splitlines() if l.strip()] if len(lineas) > 1 else []
    if not pie or not all(RE_PIE.match(l) for l in pie):
        pie = []
    claves = [RE_PIE.match(l).group(1) for l in pie]
    if "Refs" not in claves:
        errores.append(f"falta el pie `Refs: {CLAVE_ISSUE}-N`, tras una línea en blanco al final del mensaje.")
    for linea in pie:
        if linea.startswith("Refs:") and not RE_REFS.match(linea):
            errores.append(f"`{linea}` no sigue `Refs: {CLAVE_ISSUE}-N`.")
        if linea.startswith("Spec:") and not RE_SPEC_PIE.match(linea):
            errores.append(f"`{linea}` no sigue `Spec: SPEC-XXX-NNN/AC-NN`.")
    orden = [c for c in claves if c in ORDEN_PIE]
    if orden != sorted(orden, key=ORDEN_PIE.index):
        errores.append(f"el pie va en este orden: {', '.join(f'`{c}`' for c in ORDEN_PIE)}.")
    return errores, avisos


def check_commits(inf: Informe, mensajes: list[str]) -> None:
    """mensajes: los de los commits del PR, sin los merges."""
    for mensaje in mensajes:
        errores, avisos = problemas_mensaje(mensaje)
        titulo = mensaje.strip().splitlines()[0][:80] if mensaje.strip() else ""
        for e in errores:
            inf.error("commits", f"«{titulo}»: {e}")
        for a in avisos:
            inf.aviso("commits", f"«{titulo}»: {a}")


def commits_sin_merges(base: str) -> list[tuple[str, str]] | None:
    """(correo del autor, mensaje) de cada commit del PR que no es un merge."""
    salida = git("log", "--no-merges", "--format=%ae%x1f%B%x00", f"{base}..HEAD")
    if salida is None:
        return None
    return [tuple(c.lstrip("\n").split("\x1f", 1)) for c in salida.split("\x00") if "\x1f" in c]


def comprobar_mensaje(fichero: str) -> int:
    """Hook `commit-msg` de lefthook: el mismo formato que el check `commits`."""
    errores, avisos = problemas_mensaje(Path(fichero).read_text(encoding="utf-8", errors="replace"),
                                        admite_merge=True)
    for a in avisos:
        print(f"Aviso: {a}")
    for e in errores:
        print(f"Error: {e}")
    return 1 if errores else 0


# --- Dependabot (M38) ------------------------------------------------------

# Sus PR no siguen las convenciones de rama, título ni descripción. La excepción mira el autor
# del PR (lo pone GitHub; nadie más puede abrirlo como Dependabot) y el de cada commit, nunca
# la rama, que el agente también puede llamar `dependabot/…`; y solo vale si el PR toca
# dependencias o workflows y no tiene merges (Dependabot no los hace, y un merge podría
# traer cambios de otro autor). El nivel de riesgo, la autoría y la configuración de lefthook se
# comprueban igual.
DEPENDABOT = "dependabot[bot]"
DEPENDABOT_CORREO = "49699333+dependabot[bot]@users.noreply.github.com"


def es_de_dependabot(autor_pr: str, commits: list[tuple[str, str]] | None, cambiados: list[str],
                     sin_merges: bool) -> bool:
    return (autor_pr == DEPENDABOT and sin_merges and bool(commits) and bool(cambiados)
            and all(correo == DEPENDABOT_CORREO for correo, _ in commits)
            and all(es_manifiesto(f) or f.startswith(".github/workflows/") for f in cambiados))


# --- Historial en las specs (M39) -----------------------------------------

def cabecera_spec(texto: str) -> str:
    """Frontmatter y lo que va antes del título `# ` o de la sección 1."""
    m = re.search(r"^(#\s|##\s+1\.)", texto[3:] if texto.startswith("---") else texto, re.M)
    return texto[:m.start() + 3] if m else texto


def check_historial(inf: Informe, ficheros: dict[str, str]) -> None:
    for ruta, texto in sorted(ficheros.items()):
        senales = [nombre for regex, nombre in SENALES_HISTORIAL if regex.search(cabecera_spec(texto))]
        if RE_TITULO_HISTORIAL.search(texto):
            senales.append("una sección de historial")
        if senales:
            inf.aviso("historial", f"⚠️ `{ruta}` parece llevar historial en la cabecera ({', '.join(senales)}). La spec describe solo lo vigente; el porqué de cada versión va en el PR, en Git o en un ADR (M39).")


# --- Cabecera YAML de los ADR (M7) ----------------------------------------

def elementos(texto: str, en_linea: bool) -> tuple[list[str], bool]:
    """Elementos de una lista YAML sencilla, hasta un comentario `#` fuera de comillas,
    y si la lista en línea se cierra con `]` en este texto."""
    partes, actual, comilla, cerrada = [], "", "", False
    for i, c in enumerate(texto):
        if comilla:
            actual += c
            if c == comilla:
                comilla = ""
        elif c in "\"'" and not actual.strip():
            comilla, actual = c, actual + c
        elif c == "#" and (i == 0 or texto[i - 1].isspace()):
            break
        elif en_linea and c in ",]":
            partes.append(actual)
            actual = ""
            if c == "]":
                cerrada = True
                break
        else:
            actual += c
    partes.append(actual)
    return [p.strip() for p in partes if p.strip()], cerrada


def entre_comillas(valor: str) -> bool:
    return len(valor) >= 2 and valor[0] in "\"'" and valor[-1] == valor[0]


def refs_sin_comillas(texto: str) -> list[str]:
    if not texto.startswith("---"):
        return []
    fin = texto.find("\n---", 3)
    malas, abierta = [], False
    for linea in texto[3:fin if fin >= 0 else None].splitlines():
        m_linea = re.match(r"^[\w-]+:\s*\[(.*)$", linea)
        m_bloque = re.match(r"^\s*-\s+(.*)$", linea)
        if abierta:
            # Continuación de una lista en línea repartida en varias líneas.
            valores, cerrada = elementos(linea, en_linea=True)
            abierta = not cerrada
        elif m_linea:
            valores, cerrada = elementos(m_linea.group(1), en_linea=True)
            abierta = not cerrada
        elif m_bloque:
            valores = elementos(m_bloque.group(1), en_linea=False)[0][:1]
        else:
            continue
        malas += [v for v in valores if not entre_comillas(v)]
    return malas


def check_adr(inf: Informe, ficheros: dict[str, str]) -> None:
    for ruta, texto in sorted(ficheros.items()):
        malas = refs_sin_comillas(texto)
        if malas:
            inf.error("adr", f"`{ruta}`: en la cabecera YAML, las referencias van entre comillas (M7): {', '.join(f'`{v}`' for v in malas)}.")


# --- Configuración de lefthook (ADR-0008) ---------------------------------

def _sin_duplicadas(pares: list[tuple[str, object]]) -> dict:
    claves = [c for c, _ in pares]
    repetidas = sorted({c for c in claves if claves.count(c) > 1})
    if repetidas:
        raise ValueError(f"claves repetidas: {', '.join(repetidas)}")
    return dict(pares)


def _texto_o_lista(valor: object) -> bool:
    return isinstance(valor, str) or (isinstance(valor, list) and all(isinstance(v, str) for v in valor))


def errores_lefthook(texto: str) -> list[str]:
    """Lo que incumple la lista blanca en el texto de `lefthook.json`."""
    try:
        conf = json.loads(texto, object_pairs_hook=_sin_duplicadas)
    except ValueError as e:
        return [f"no es JSON válido ({e})."]
    if not isinstance(conf, dict):
        return ["no es un objeto JSON."]
    errores = [f"la clave `{c}` no está permitida." for c in sorted(set(conf) - LEFTHOOK_CLAVES)]
    errores += [f"falta `\"{c}\": true`." for c in LEFTHOOK_OBLIGATORIAS if conf.get(c) is not True]
    for hook in sorted(LEFTHOOK_HOOKS & set(conf)):
        cuerpo = conf[hook]
        if not isinstance(cuerpo, dict):
            errores.append(f"`{hook}` no es un objeto.")
            continue
        errores += [f"`{hook}.{c}` no está permitida." for c in sorted(set(cuerpo) - LEFTHOOK_CLAVES_HOOK)]
        errores += [f"`{hook}.{c}` no es true ni false." for c in ("parallel", "piped")
                    if c in cuerpo and not isinstance(cuerpo[c], bool)]
        trabajos = cuerpo.get("jobs", [])
        if not isinstance(trabajos, list):
            errores.append(f"`{hook}.jobs` no es una lista.")
            continue
        for i, trabajo in enumerate(trabajos):
            sitio = f"`{hook}.jobs[{i}]`"
            if not isinstance(trabajo, dict):
                errores.append(f"{sitio} no es un objeto.")
                continue
            errores += [f"{sitio}.{c} no está permitida." for c in sorted(set(trabajo) - LEFTHOOK_CLAVES_JOB)]
            if not (isinstance(trabajo.get("run"), str) and trabajo["run"].strip()):
                errores.append(f"{sitio} no tiene `run`.")
            errores += [f"{sitio}.{c} no es texto." for c in ("name", "fail_text")
                        if c in trabajo and not isinstance(trabajo[c], str)]
            errores += [f"{sitio}.{c} no es texto ni lista de textos." for c in ("glob", "exclude", "file_types")
                        if c in trabajo and not _texto_o_lista(trabajo[c])]
    if "min_version" in conf and not isinstance(conf["min_version"], str):
        errores.append("`min_version` no es texto.")
    return errores


def check_lefthook(inf: Informe, versionados: dict[str, str] | None, texto: str | None,
                   en_base: bool | None) -> None:
    """versionados: ruta -> modo de los ficheros del PR; texto: el de `lefthook.json`;
    en_base: si `main` tiene `lefthook.json`. None si Git no ha podido decirlo."""
    if versionados is None or en_base is None:
        inf.error("lefthook", "no he podido listar los ficheros del PR o de `main` con Git, así que no sé si la configuración de lefthook cumple el ADR-0008.")
        return
    otras = sorted(r for r in versionados if r != LEFTHOOK_CONFIG and RE_LEFTHOOK_OTRA.search(r))
    if otras:
        inf.error("lefthook", f"hay configuración de lefthook fuera de `{LEFTHOOK_CONFIG}` ({', '.join(f'`{r}`' for r in otras)}). lefthook la leería antes o además de la principal (ADR-0008).")
    if LEFTHOOK_CONFIG not in versionados:
        if en_base:
            inf.error("lefthook", f"el PR quita `{LEFTHOOK_CONFIG}`, que `main` tiene. Los hooks de Git no se quitan en un PR del agente (ADR-0008).")
        return
    if versionados[LEFTHOOK_CONFIG] != "100644":
        inf.error("lefthook", f"`{LEFTHOOK_CONFIG}` tiene que ser un fichero normal, no un enlace ni un ejecutable.")
        return
    errores = errores_lefthook(texto or "")
    for e in errores:
        inf.error("lefthook", f"`{LEFTHOOK_CONFIG}`: {e} Solo valen las claves que no amplían lo que se ejecuta (ADR-0008, `docs/herramientas.md`).")
    if not errores and not RE_GITLEAKS_ANTES.search(texto or ""):
        inf.aviso("lefthook", f"⚠️ `{LEFTHOOK_CONFIG}` ya no lanza `gitleaks git --pre-commit`: sin él, nada busca secretos antes del commit. Comprueba que el cambio es a propósito.")
    if not errores and not RE_FORMATO_ANTES.search(texto or ""):
        inf.aviso("lefthook", f"⚠️ `{LEFTHOOK_CONFIG}` ya no comprueba el formato de los commits (`checks.py --mensaje`): lo seguirá comprobando la CI. Comprueba que el cambio es a propósito.")


def ficheros_versionados() -> dict[str, str] | None:
    salida = git("ls-files", "-s", "-z")
    if salida is None:
        return None
    versionados = {}
    for entrada in salida.split("\0"):
        cabecera, _, ruta = entrada.partition("\t")
        if ruta:
            versionados[ruta] = cabecera.split(" ", 1)[0]
    return versionados


# --- Hallazgos de G4 (VIC-38) ---------------------------------------------

# Una línea por hallazgo en la reconciliación del PR (skill `sdd-review`):
#   - G4-1-A-01 · debe corregirse · prueba: `app.js:12` · resolución: corregido en 1a2b3c4
# Cuenta cualquier lista, casilla, cita o tabla que empiece por el ID, para que otra forma
# falle por formato y no pase sin comprobar. Fuera de <details> y de bloques de código.
# La descripción la escribe cualquiera: nada de expresiones con retroceso sobre una línea entera.
HALLAZGO_ID = r"G4-[1-9]\d*-[A-Z]-\d{2,3}"
RE_HALLAZGO = re.compile(rf"^\s*(?:>\s*)*(?:[-*+]|\d+[.)]|\|)\s*(?:\[[ xX]\]\s*)?[*`]*({HALLAZGO_ID})\b[*`]*(.*)$")
# El hallazgo en la respuesta del revisor (`reviewer.md`), con la gravedad que le dio: fuera de
# lo plegado, un título o una línea en negrita que empieza por el ID; dentro, cualquier línea
# que empiece por él, también en una lista, una casilla, una cita o una tabla.
RE_RESPUESTA = re.compile(rf"^\s*(?:#{{1,6}}\s+|\*\*)[*`]*({HALLAZGO_ID})\b(.*)$")
RE_RESPUESTA_PLEGADA = re.compile(rf"^\s*(?:>\s*)*(?:#{{1,6}}\s+|[-*+]\s+|\d+[.)]\s+|\|\s*)?(?:\[[ xX]\]\s*)?[*_`]*({HALLAZGO_ID})\b(.*)$")
RE_ALGUN_HALLAZGO = re.compile(HALLAZGO_ID)
RE_CAMPO_PRUEBA = re.compile(r"·[ \t]*prueba:", re.I)
RE_CAMPO_RESOLUCION = re.compile(r"·[ \t]*resolución:", re.I)
GRAVEDADES = ("debe corregirse", "importante", "menor")
SIN_GRAVEDAD = "sin gravedad"
RE_CORREGIDO = re.compile(r"^corregido en `?[0-9a-f]{7,40}`?(?:(?:,| y) `?[0-9a-f]{7,40}`?)*$", re.I)
RE_DESCARTADO = re.compile(r"^descartado(?::(?P<prueba>.*))?$", re.I)
PREGUNTA = "pregunta a la persona"
RE_PLEGADO = re.compile(r"<details\b|</details\s*>", re.I)
RE_CERCA = re.compile(r"^ {0,3}(`{3,}|~{3,})")
RE_COMENTARIO_BLOQUE = re.compile(r"^ {0,3}<!--")
# Las respuestas de los revisores van en comentarios del PR. El repo puede ser público y comentar
# puede cualquiera: solo cuentan los comentarios de estas cuentas (la de la persona y la del agente).
CUENTAS_G4 = ("victor-lg-bot", "victor-lg")


def sin_codigo_en_linea(linea: str) -> str:
    """La línea con el código en línea cambiado por espacios, como en Markdown: una racha de N
    comillas invertidas solo cierra con otra de N, y una sin pareja es texto."""
    rachas = [(m.start(), m.end()) for m in re.finditer(r"`+", linea)]
    siguiente, ultima = [None] * len(rachas), {}
    for j in range(len(rachas) - 1, -1, -1):
        largo = rachas[j][1] - rachas[j][0]
        siguiente[j], ultima[largo] = ultima.get(largo), j
    partes, i, k = [], 0, 0
    while k < len(rachas):
        j = siguiente[k]
        if j is None:
            k += 1
            continue
        a, b = rachas[k][0], rachas[j][1]
        partes += [linea[i:a], " " * (b - a)]
        i, k = b, j + 1
    return "".join(partes) + linea[i:]


def lineas_visibles(cuerpo_pr: str) -> tuple[list[tuple[str, bool]], list[str]]:
    """Las líneas del PR como las muestra GitHub, sin comentarios HTML ni bloques de código, cada
    una con si va plegada en <details> (anidados o no), y lo que queda sin cerrar. Un `<!--`, un
    `<details>` o una cerca dentro de código es texto."""
    lineas, plegado, cerca, comentario = [], 0, None, False
    # Solo los saltos de Markdown: `splitlines()` también corta en U+2028 y otros que GitHub no.
    for linea in re.split(r"\r\n|\r|\n", cuerpo_pr):
        m = RE_CERCA.match(linea)
        if cerca:
            # Cierra una cerca del mismo carácter y al menos igual de larga, sin nada detrás.
            if m and m.group(1)[0] == cerca[0] and len(m.group(1)) >= len(cerca) and not linea[m.end():].strip():
                cerca = None
            continue
        # Un comentario que empieza la línea es un bloque hasta la línea con `-->`; en medio de
        # una línea, solo si se cierra en ella (si no, es texto).
        if comentario:
            comentario = "-->" not in linea
            continue
        if RE_COMENTARIO_BLOQUE.match(linea) and "-->" not in linea:
            comentario = True
            continue
        # Tras una cerca de comillas invertidas, otra comilla invertida en la línea la hace texto.
        if m and not (m.group(1)[0] == "`" and "`" in linea[m.end():]):
            cerca = m.group(1)
            continue
        oculta = sin_codigo_en_linea(linea)
        tramos, i = [], 0
        while (ini := oculta.find("<!--", i)) >= 0 and (fin := oculta.find("-->", ini + 4)) >= 0:
            tramos.append((i, ini))
            i = fin + 3
        tramos.append((i, len(linea)))
        antes = plegado
        for t in RE_PLEGADO.finditer("".join(oculta[a:b] for a, b in tramos)):
            plegado = max(0, plegado + (-1 if t.group(0).startswith("</") else 1))
        lineas.append(("".join(linea[a:b] for a, b in tramos), antes > 0 or plegado > 0))
    sin_cerrar = (["un `<details>` (ciérralo con `</details>`)"] if plegado else []) + \
                 ([f"un bloque de código (ciérralo con `{cerca}`)"] if cerca else []) + \
                 (["un comentario HTML (ciérralo con `-->`)"] if comentario else [])
    return lineas, sin_cerrar


def gravedad_al_principio(texto: str) -> str:
    texto = texto.lstrip(" \t*_`·:—–-|").lower()
    return next((g for g in GRAVEDADES if texto.startswith(g)), SIN_GRAVEDAD)


def mas_grave(previa: str | None, gravedad: str) -> str:
    """Sin gravedad reconocible cuenta como la mayor: para descartarlo hace falta prueba."""
    if previa is None:
        return gravedad
    if SIN_GRAVEDAD in (previa, gravedad):
        return SIN_GRAVEDAD
    return min(previa, gravedad, key=GRAVEDADES.index)


def gravedades_de_los_revisores(lineas: list[tuple[str, bool]],
                                gravedades: dict[str, str] | None = None) -> dict[str, str]:
    """La gravedad de cada hallazgo de las respuestas, añadida a `gravedades` si se da; si un ID sale
    varias veces, la mayor."""
    gravedades = {} if gravedades is None else gravedades
    for linea, plegada in lineas:
        m = (RE_RESPUESTA_PLEGADA if plegada else RE_RESPUESTA).match(linea)
        if m:
            gravedades[m.group(1)] = mas_grave(gravedades.get(m.group(1)), gravedad_al_principio(m.group(2)))
    return gravedades


def leer_paginas(ruta: str) -> list | None:
    """Los elementos de la salida de `gh api --paginate`: una lista JSON por página, una detrás de
    otra. None si no se puede leer o no tiene esa forma."""
    lector, paginas, i = json.JSONDecoder(), [], 0
    try:
        texto = Path(ruta).read_text(encoding="utf-8")
        while i < len(texto.rstrip()):
            pagina, i = lector.raw_decode(texto, len(texto) - len(texto[i:].lstrip()))
            paginas.append(pagina)
    except (OSError, ValueError):
        return None
    if not paginas or not all(isinstance(p, list) for p in paginas):
        return None
    return [e for p in paginas for e in p]


def comentarios_de_cuentas(ruta: str) -> list[dict] | None:
    """Los comentarios del PR que escribieron las cuentas de CUENTAS_G4, tal como los da la API y con
    `html_url` como texto, de la salida de `gh api --paginate`: una lista por página, una detrás de
    otra. None si no se puede leer."""
    elementos = leer_paginas(ruta)
    if elementos is None:
        return None
    comentarios = []
    for c in elementos:
        if not isinstance(c, dict):
            return None
        # Sin usuario (una cuenta borrada) no es de CUENTAS_G4: se ignora, no se falla por él.
        usuario = c.get("user") if isinstance(c.get("user"), dict) else {}
        if usuario.get("login") in CUENTAS_G4 and isinstance(c.get("body"), str):
            comentarios.append({**c, "html_url": str(c.get("html_url", ""))})
    return comentarios


def campos_de_hallazgo(campos: str) -> tuple[str, str, str] | None:
    """Gravedad, prueba y resolución de `· <gravedad> · prueba: … · resolución: …`. La prueba
    puede citar otra línea de hallazgo: la resolución es lo que sigue al último campo."""
    resto = campos.strip()
    prueba = RE_CAMPO_PRUEBA.search(resto)
    resoluciones = list(RE_CAMPO_RESOLUCION.finditer(resto))
    if not resto.startswith("·") or not prueba or not resoluciones:
        return None
    # Sin `·` en la gravedad, la prueba va antes que la resolución.
    gravedad = resto[1:prueba.start()]
    if "·" in gravedad:
        return None
    return gravedad, resto[prueba.end():resoluciones[-1].start()], resto[resoluciones[-1].end():]


def enlaces_y_cuerpos(comentarios: list[dict]) -> list[tuple[str, str]]:
    return [(c["html_url"], c["body"]) for c in comentarios]


def check_hallazgos(inf: Informe, cuerpo_pr: str, comentarios: list[tuple[str, str]] = ()) -> None:
    lineas, sin_cerrar = lineas_visibles(cuerpo_pr)
    # Sin ningún ID de hallazgo, no hay nada que esconder: un PR sin G4 (R0, Dependabot) no falla aquí.
    for que in sin_cerrar if RE_ALGUN_HALLAZGO.search(cuerpo_pr) else []:
        inf.error("hallazgos", f"la descripción del PR tiene {que} sin cerrar: lo que sigue no se puede comprobar.")
    del_revisor = gravedades_de_los_revisores(lineas)
    # En un comentario, toda línea que empieza por un ID es un hallazgo, como en lo plegado.
    for enlace, cuerpo in comentarios:
        en_comentario, abierto = lineas_visibles(cuerpo)
        for que in abierto if RE_ALGUN_HALLAZGO.search(cuerpo) else []:
            inf.error("hallazgos", f"el comentario {enlace or 'del PR'} tiene {que} sin cerrar: lo que sigue no se puede comprobar.")
        gravedades_de_los_revisores([(linea, True) for linea, _ in en_comentario], del_revisor)
    vistos, preguntas = set(), []
    for linea, plegada in lineas:
        m = None if plegada else RE_HALLAZGO.match(linea)
        if not m:
            continue
        hid, campos = m.groups()
        if hid in vistos:
            inf.error("hallazgos", f"`{hid}` aparece dos veces en la reconciliación; deja una sola línea por hallazgo.")
            continue
        vistos.add(hid)
        c = campos_de_hallazgo(campos)
        if not c:
            inf.error("hallazgos", f"`{hid}` no sigue el formato `- {hid} · <gravedad> · prueba: <test, línea o cita> · resolución: <resolución>` (`sdd-review`).")
            continue
        gravedad, prueba, resolucion = (x.strip().strip("*_").strip() for x in c)
        gravedad = gravedad.lower()
        if gravedad not in GRAVEDADES:
            inf.error("hallazgos", f"`{hid}`: la gravedad `{gravedad}` no es {', '.join(GRAVEDADES)}.")
        if not prueba:
            inf.error("hallazgos", f"`{hid}` no tiene prueba: cada hallazgo cita un test, una línea o un texto.")
        # Bajar la gravedad no ahorra la prueba: cuenta la mayor, la del revisor o la confirmada.
        graves = {gravedad, del_revisor.get(hid, "")} - {"menor", ""}
        descartado = RE_DESCARTADO.match(resolucion)
        if RE_CORREGIDO.match(resolucion):
            pass
        elif descartado:
            if graves and not (descartado.group("prueba") or "").strip():
                inf.error("hallazgos", f"`{hid}` ({' / '.join(sorted(graves))}) se descarta sin prueba. Escribe `descartado: <test, línea o cita>`; si no la hay, `{PREGUNTA}`.")
        elif resolucion.lower() == PREGUNTA:
            preguntas.append(hid)
        else:
            inf.error("hallazgos", f"`{hid}` no tiene resolución (`{resolucion[:80] or 'vacía'}`): escribe `corregido en <sha>`, `descartado: <prueba>` o `{PREGUNTA}`.")
    faltan = sorted(set(del_revisor) - vistos)
    if faltan:
        inf.error("hallazgos", f"los revisores dieron {', '.join(f'`{h}`' for h in faltan)} y la reconciliación no tiene su línea.")
    # VIC-56 (ADR-0009 §5): con el auto-merge nadie los vería antes de fusionar. Fallan hasta que la
    # resolución pase a `corregido en <sha>` o `descartado: <prueba>`. Límite aceptado (ADR-0009 §4, «G4
    # depende del agente»): nada liga la nueva resolución a una respuesta de la persona; la cuenta del
    # agente puede cambiarla sin que la persona conteste, como ya podía descartar con cualquier prueba.
    if preguntas:
        inf.error("hallazgos", f"hallazgos pendientes de la persona: {', '.join(f'`{h}`' for h in preguntas)}. El PR no se "
                               f"fusiona hasta que conteste: entonces cambia `{PREGUNTA}` por `corregido en <sha>` o "
                               "`descartado: <prueba>` (`sdd-review`).")


# --- Respuestas borradas o editadas (VIC-47) ------------------------------

# Las respuestas las publica la misma cuenta que usa el agente: borrar o editar una saca sus hallazgos
# del check sin que se note. Un comentario de G4 es uno de CUENTAS_G4 que la descripción enlaza en
# «Revisión IA» o que trae un ID de revisor (`G4-1-A`, también en «Commit revisado») o «Métricas G4».
# Límite aceptado: la misma cuenta puede borrar un comentario y quitar su enlace de «Revisión IA», o
# borrarlo y publicar otro retocado, y este check no lo ve. Cerrarlo pide que los revisores publiquen
# desde otra cuenta: es decisión del ADR-0009 del workflow (bloque 5).
RE_ENLACE_COMENTARIO = re.compile(r"#issuecomment-([1-9]\d*)\b")
RE_ES_DE_G4 = re.compile(r"\bG4-[1-9]\d*-[A-Z]\b|^Métricas G4:", re.M)
# La justificación de una edición, en «Revisión IA» y fuera de <details>: `Comentario editado: <enlace> · <motivo>`.
RE_EDICION_JUSTIFICADA = re.compile(r"^\s*(?:[-*+]\s+)?Comentario editado:")


def url_del_pr() -> str | None:
    """La URL del PR en la CI, de las variables de GitHub (`refs/pull/N/merge` en un pull_request)."""
    m = re.fullmatch(r"refs/pull/([1-9]\d*)/merge", os.environ.get("GITHUB_REF", ""))
    servidor, repo = os.environ.get("GITHUB_SERVER_URL", ""), os.environ.get("GITHUB_REPOSITORY", "")
    return f"{servidor}/{repo}/pull/{m.group(1)}" if m and servidor and repo else None


def check_respuestas(inf: Informe, cuerpo_pr: str, comentarios: list[dict], url_pr: str | None) -> None:
    lineas, _ = lineas_visibles(seccion(cuerpo_pr, "Revisión IA"))
    del_pr = re.compile(re.escape(url_pr) + RE_ENLACE_COMENTARIO.pattern) if url_pr else None
    enlazados = {m.group(1) for l, _ in lineas for m in (del_pr.finditer(l) if del_pr else ())}
    por_id = {RE_ENLACE_COMENTARIO.search(c["html_url"]).group(1): c for c in comentarios
              if RE_ENLACE_COMENTARIO.search(c["html_url"])}
    for cid in sorted(enlazados - set(por_id), key=int):
        inf.error("hallazgos", f"«Revisión IA» enlaza el comentario {url_pr}#issuecomment-{cid} y no está entre los de "
                               f"{', '.join(CUENTAS_G4)}: ¿se borró? Una respuesta de G4 no se borra ni se edita; si hay que "
                               "corregir algo, publica otro comentario (`sdd-review`).")
    # La justificación se ve sin desplegar nada, como las líneas de la reconciliación.
    justificados = set()
    for linea, plegada in lineas:
        m = None if plegada else RE_EDICION_JUSTIFICADA.match(linea)
        enlace, _, motivo = linea[m.end():].partition("·") if m else ("", "", "")
        if motivo.strip() and (cid := RE_ENLACE_COMENTARIO.search(enlace)):
            justificados.add(cid.group(1))
    for cid, c in sorted(por_id.items(), key=lambda par: int(par[0])):
        if cid not in enlazados and not RE_ES_DE_G4.search(c["body"]):
            continue
        # Sin fechas no se sabe si se editó: cuenta como editado.
        creado, editado = c.get("created_at"), c.get("updated_at")
        if isinstance(creado, str) and creado and creado == editado or cid in justificados:
            continue
        cuando = f"el {editado}" if isinstance(editado, str) and editado else "sin fechas en la API"
        inf.error("hallazgos", f"el comentario de G4 {c['html_url']} se editó después de publicarse ({cuando}). Una respuesta "
                               "de G4 no se edita: publica otro comentario. Si la edición es legítima (por ejemplo, solo el SHA "
                               "de «Commit revisado»), justifícala en «Revisión IA» con la línea "
                               "`Comentario editado: <enlace> · <motivo>`.")


# --- Cambios tras la última ronda (M8, VIC-39) ----------------------------

# Cada revisor deja en su comentario, fuera de <details> y de bloques de código, el commit que vio:
#   Commit revisado: G4-1-A · 0123456789abcdef0123456789abcdef01234567
RE_COMMIT_REVISADO = re.compile(r"^\s*Commit revisado:\s*`?(G4-([1-9]\d*)-([A-Z]))`?\s*·\s*`?([0-9a-f]{40})`?\s*$")
# Una lista escrita a mano en la descripción: un título, un elemento de lista, una cita, una tabla, una
# etiqueta en negrita o un rótulo en HTML (`<summary>`, `<b>`) que empieza por el nombre de la sección.
# Una lista de palabras: otra redacción no la ve. Sin retroceso sobre la línea entera: cada vuelta de
# `(?:<…>|[*_])*` consume un `<` o una marca, y `[^>]*` para en el primer `>`.
RE_LISTA_A_MANO = re.compile(r"^\s*(?:>\s*)*(?:#{1,6}\s+)?(?:[-*+]\s+|\d+[.)]\s+|\|\s*)?(?:\[[ xX]\]\s*)?"
                             r"(?:<[a-z][a-z0-9]*\b[^>]*>\s*|[*_])*(?:cambios|commits)[*_]*\s+"
                             r"(?:despu[eé]s\s+de|tras|desde|posteriores\s+a)\s+la\s+[uú]ltima\s+(?:ronda|revisi[oó]n)", re.I)
RE_RONDA_METRICAS = re.compile(r"^Métricas G4: PR #\d+ · ronda ([1-9]\d*) ·")


def rondas_de_g4(comentarios: list[tuple[str, str]]) -> tuple[dict[tuple[int, str], str], dict[int, set[str]]]:
    """De los comentarios de CUENTAS_G4: el commit que vio cada revisor (ronda, letra), el último si
    se repite, y los revisores que salen en cada ronda, por sus hallazgos o por su commit. Una ronda
    sin hallazgos ni commit sale por su línea «Métricas G4», sin revisores."""
    vistos, revisores = {}, {}
    for _, cuerpo in comentarios:
        lineas, _ = lineas_visibles(cuerpo)
        for linea, plegada in lineas:
            m = None if plegada else RE_COMMIT_REVISADO.match(linea)
            if m:
                vistos[(int(m.group(2)), m.group(3))] = m.group(4)
                revisores.setdefault(int(m.group(2)), set()).add(m.group(3))
            elif (r := RE_RONDA_METRICAS.match(linea)):
                revisores.setdefault(int(r.group(1)), set())
            # Como en `check_hallazgos`: en un comentario, toda línea que empieza por un ID es un hallazgo.
            elif (h := RE_RESPUESTA_PLEGADA.match(linea)):
                ronda, letra = h.group(1).split("-")[1:3]
                revisores.setdefault(int(ronda), set()).add(letra)
    return vistos, revisores


def texto_del_resumen(texto: str) -> str:
    """Un título de commit o un nombre de fichero como texto del resumen: un `<!--` o un `<details>`
    de quien escribe el commit no puede esconder lo que sigue, ni una comilla invertida abrir código."""
    return html.escape(texto, quote=False).replace("`", "\\`")


def check_cambios(inf: Informe, base: str, cabeza: str, comentarios: list[tuple[str, str]],
                  cuerpo_pr: str = "") -> None:
    # La lista no se escribe a mano (VIC-39): lo que se ve en la descripción, también lo plegado.
    lineas, _ = lineas_visibles(cuerpo_pr)
    if any(RE_LISTA_A_MANO.match(linea) for linea, _ in lineas):
        inf.error("cambios", "la descripción del PR trae una lista de «Cambios tras la última ronda» escrita a mano. Quítala: "
                             "esa lista la calcula la CI desde el commit que vio cada revisor y está en el resumen de `checks-sdd`, "
                             "sección «Cambios tras la última ronda».")
    vistos, revisores = rondas_de_g4(comentarios)
    # Sin ninguna ronda (R0, Dependabot, antes de G4) no hay nada que calcular.
    if not revisores:
        return
    ronda = max(revisores)
    letras = sorted(revisores[ronda])
    faltan = [l for l in letras if (ronda, l) not in vistos]
    if not letras or faltan:
        quien = ", ".join(f"`G4-{ronda}-{l}`" for l in faltan) or f"ningún revisor de la ronda {ronda}"
        inf.error("cambios", f"falta el commit que vio {quien}: sin él no se pueden calcular los cambios tras la última ronda. "
                             f"Añade al comentario de cada revisor, fuera de `<details>`, la línea `Commit revisado: G4-{ronda}-<letra> · <sha de 40>` (`sdd-review`).")
        return
    nuevos: dict[str, str] = {}
    for letra in letras:
        sha = vistos[(ronda, letra)]
        # Sin el commit en la historia de la cabeza (un rebase o un push forzado) no hay diff fiable.
        if git("merge-base", "--is-ancestor", sha, cabeza) is None:
            inf.error("cambios", f"el commit `{sha[:12]}` que vio `G4-{ronda}-{letra}` no está en la historia del PR o Git no lo encuentra: "
                                 "¿se reescribió la rama? Repite la ronda sobre la cabeza actual (`sdd-review`).")
            return
        salida = git("log", "--topo-order", "--reverse", "--format=%H%x1f%s", cabeza, f"^{sha}", f"^{base}")
        if salida is None:
            inf.error("cambios", f"no he podido leer con Git los commits desde `{sha[:12]}`.")
            return
        for linea in salida.splitlines():
            h, _, titulo = linea.partition("\x1f")
            nuevos.setdefault(h, titulo)
    vio = ", ".join(f"{l} en `{vistos[(ronda, l)][:7]}`" for l in letras)
    lineas = [f"Ronda {ronda}; cada revisor vio: {vio}.", ""]
    if not nuevos:
        lineas.append("Ninguno: la cabeza del PR es lo que vieron los revisores.")
    else:
        # Del más antiguo al más nuevo, en el orden de la historia de la cabeza; los ficheros, los del
        # PR que cambian desde lo que vio cada revisor.
        orden = (git("rev-list", "--topo-order", "--reverse", cabeza, f"^{base}") or "").split()
        lineas += [f"- `{h[:7]}` {texto_del_resumen(nuevos[h])}" for h in orden if h in nuevos]
        del_pr = set(rutas("diff", "--name-only", "--no-renames", f"{base}...{cabeza}") or [])
        ficheros = sorted({f for l in letras
                           for f in rutas("diff", "--name-only", "--no-renames", vistos[(ronda, l)], cabeza) or []} & del_pr)
        if ficheros:
            lineas += ["", "Ficheros: " + ", ".join(texto_del_resumen(f) for f in ficheros)]
    inf.secciones.append("### Cambios tras la última ronda\n\n" + "\n".join(lineas))


# --- PR sin G4 (VIC-56) ---------------------------------------------------

# ADR-0009 §3.1 y §5: el agente no fusiona solo un PR sin G4, salvo un R0 que checks.py comprueba que es
# solo documentación. Si no puede comprobarlo, el R0 cuenta como R1 y lleva G4 (aclaración de la decisión 1).
# Revisores por PR, como en la tabla de `sdd-review` (no la cambia: la comprueba).
REVISORES_R2_SPEC_ADR, REVISORES_OTROS = 2, 1
# Instrucciones para agentes en cualquier carpeta (G4-1-B-01; GEMINI.md, G4-2-A-01): Claude Code lee el CLAUDE.md de la carpeta en la
# que trabaja, y otros agentes, los AGENTS.md anidados. R2_RUTAS solo ve los de la raíz.
INSTRUCCIONES_AGENTE = {"agents.md", "claude.md", "claude.local.md", "gemini.md"}


def es_documentacion(ruta: str, modo: str | None) -> bool:
    """Solo documentación: un `.md` que es un fichero normal (modo 100644) o que el PR borra (sin modo), sin
    enlaces ni submódulos. No lo son una spec ni un ADR (suben a R1 y van a CODEOWNERS), las instrucciones de un
    agente en cualquier carpeta (INSTRUCCIONES_AGENTE) ni nada dentro de una carpeta que empieza por punto
    (`.claude/`, `.github/`, `.cursor/`…, también anidadas): es configuración. El mismo criterio vale para el R0
    sin G4 y para lo que entra tras la última ronda. Las rutas sensibles del proyecto las decide el nivel."""
    partes = ruta.split("/")
    return (ruta.endswith(".md") and modo in (None, "100644") and not es_spec(ruta) and not es_adr(ruta)
            and partes[-1].lower() not in INSTRUCCIONES_AGENTE and not any(c.startswith(".") for c in partes[:-1]))


def check_g4(inf: Informe, nivel: str, cambiados: list[str], versionados: dict[str, str] | None,
             comentarios: list[tuple[str, str]], dependabot: bool = False) -> None:
    """nivel: el efectivo de `check_riesgo`. versionados: los modos del índice (`ficheros_versionados`);
    sin ellos no se puede comprobar que un R0 sea solo documentación."""
    # Dependabot no pasa por G4: es R2 y solo entra con la aprobación de la persona (check `aprobacion`).
    if dependabot:
        return
    no_doc = [f for f in cambiados if versionados is None or not es_documentacion(f, versionados.get(f))]
    if nivel == "R0" and not no_doc:
        inf.secciones.append("### G4\n\n- R0 comprobado: el PR solo cambia documentación; no necesita G4.")
        return
    con_spec_o_adr = any(es_spec(f) or es_adr(f) for f in cambiados)
    necesarios = REVISORES_R2_SPEC_ADR if nivel == "R2" or con_spec_o_adr else REVISORES_OTROS
    vistos, revisores = rondas_de_g4(comentarios)
    ronda = max(revisores, default=0)
    # Solo cuenta el revisor que dejó el commit que vio: sin él, `cambios` ya falla.
    letras = sorted(l for l in revisores.get(ronda, ()) if (ronda, l) in vistos)
    # El texto del nivel en los mensajes: un R0 que llega aquí no se ha podido comprobar y cuenta como R1.
    como = "R0 sin comprobar, cuenta como R1" if nivel == "R0" else nivel
    if nivel == "R0":
        detalle = ", ".join(f"`{texto_del_resumen(f)}`" for f in no_doc[:5]) + (" y más" if len(no_doc) > 5 else "")
        motivo = ("no he podido leer los modos de los ficheros con Git" if versionados is None
                  else f"no es solo documentación ({detalle})")
        inf.aviso("g4", f"PR marcado R0 que {motivo}: cuenta como R1 y necesita G4 (ADR-0009, aclaración de la decisión 1).")
    linea = (f"Ronda {ronda}: {len(letras)} revisor(es) con su commit ({', '.join(letras) or 'ninguno'})"
             if ronda else "Ninguna ronda")
    inf.secciones.append(f"### G4\n\n- Nivel: {como}; revisores necesarios: {necesarios}.\n- {linea}.")
    if not ronda:
        inf.error("g4", f"el PR no tiene G4: ningún comentario de {', '.join(f'`{c}`' for c in CUENTAS_G4)} con una ronda. "
                        f"Un PR {como} no se fusiona sin revisión (ADR-0009 §5); lánzala con `sdd-review`.")
    elif len(letras) < necesarios:
        inf.error("g4", f"la última ronda de G4 (la {ronda}) tiene {len(letras)} revisor(es) con `Commit revisado` y este PR "
                        f"({como}{', con spec o ADR' if con_spec_o_adr else ''}) "
                        f"necesita {necesarios} (tabla de `sdd-review`).")


# --- Aprobación de la persona en R2 (VIC-56) ------------------------------

# ADR-0009 §3.4 y §5: el agente no fusiona solo un PR R2, toque o no rutas de CODEOWNERS. `checks-sdd`
# falla en todo R2 hasta que la persona lo aprueba en GitHub, sobre el commit de la cabeza: un push
# posterior la deja sin valor. Solo cuenta la review de estas cuentas, nunca la del agente (CUENTAS_G4
# incluye la suya). `sdd.yml` pasa las reviews en PR_REVIEWS, leídas en cada ejecución; al aprobar o retirar
# una aprobación, `sdd-relanzar.yml` vuelve a lanzar su última ejecución de `pull_request`.
# Por `user.id` y no por login: si la cuenta cambiara de nombre, otra podría registrar el libre, y en un
# repo público cualquiera envía reviews. El login solo sirve para los mensajes.
# Id de una cuenta: `gh api users/<login> --jq .id`.
PERSONAS = {95044073: "victor-lg"}
# Los estados que deciden; un COMMENTED no aprueba ni retira nada, como en GitHub.
ESTADOS_DECISIVOS = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}


def aprobacion_de_la_persona(reviews: list, cabeza: str) -> tuple[bool, str]:
    """(aprobado, motivo): la última review decisiva de PERSONAS es APPROVED y sobre `cabeza`."""
    suyas = [r for r in reviews if isinstance(r, dict) and isinstance(r.get("user"), dict)
             and type(r["user"].get("id")) is int and r["user"]["id"] in PERSONAS
             and r.get("state") in ESTADOS_DECISIVOS]
    if not suyas:
        return False, "no hay ninguna review de la persona"
    # Por id: es el orden en que se enviaron. Sin id numérico no se sabe cuál es la última.
    if not all(isinstance(r.get("id"), int) for r in suyas):
        return False, "una review de la persona no tiene id"
    ultima = max(suyas, key=lambda r: r["id"])
    if ultima["state"] != "APPROVED":
        return False, {"CHANGES_REQUESTED": "la última review de la persona pide cambios",
                       "DISMISSED": "la última review de la persona se retiró (dismiss)"}[ultima["state"]]
    if ultima.get("commit_id") != cabeza:
        return False, f"la persona aprobó `{str(ultima.get('commit_id'))[:12]}` y la cabeza es `{cabeza[:12]}`"
    return True, f"aprobado por {PERSONAS[ultima['user']['id']]} en `{cabeza[:12]}`"


def check_cabeza(inf: Informe, cabeza: str) -> None:
    """El merge que prueba GitHub (HEAD) puede ser anterior a un push reciente, por ejemplo en un `edited`
    lanzado justo después: los checks verían el contenido viejo y la aprobación se compararía con la
    cabeza nueva. Sin la cabeza del PR en la historia de HEAD, ningún check es fiable, sea cual sea el
    nivel. Volver a lanzar la ejecución no lo arregla: repite el mismo merge (sdd-relanzar.yml también)."""
    if git("merge-base", "--is-ancestor", cabeza, "HEAD") is None:
        inf.error("cabeza", f"la cabeza del PR (`{cabeza[:12]}`) no está en la historia del commit que se prueba: "
                            "GitHub no había recalculado el merge tras el último push. Volver a lanzar esta ejecución "
                            "prueba el mismo merge: edita la descripción del PR para que se lance una nueva.")


def check_aprobacion(inf: Informe, nivel: str, reviews: list | None, cabeza: str | None) -> None:
    if nivel != "R2":
        return
    if reviews is None or not cabeza:
        inf.error("aprobacion", "PR R2: no he podido leer las reviews del PR (PR_REVIEWS) o su cabeza, así que no sé si lo "
                                "aprobó la persona. Un R2 no se fusiona sin su aprobación (ADR-0009 §3.4).")
        return
    aprobado, motivo = aprobacion_de_la_persona(reviews, cabeza)
    inf.secciones.append(f"### Aprobación de la persona (R2)\n\n- {'Sí' if aprobado else 'No'}: {motivo}.")
    if not aprobado:
        inf.error("aprobacion", f"PR R2: {motivo}. Un R2 solo se fusiona con la aprobación de "
                                f"{', '.join(f'`{p}`' for p in PERSONAS.values())} sobre el último commit (ADR-0009 §3.4); "
                                "al aprobar, este check se vuelve a lanzar solo (en un PR de un fork, a mano).")


# --- Programa -------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    # La ref completa: `origin/main` resolvería antes una etiqueta llamada así.
    ap.add_argument("--base", default="refs/remotes/origin/main", help="referencia de la rama base")
    ap.add_argument("--mensaje", metavar="FICHERO", help="solo comprueba el mensaje de commit de FICHERO (hook commit-msg)")
    args = ap.parse_args()
    if args.mensaje:
        return comprobar_mensaje(args.mensaje)
    raiz = Path.cwd()
    cuerpo_pr = os.environ.get("PR_BODY", "")
    inf = Informe()

    cambiados = rutas("diff", "--name-only", "--no-renames", f"{args.base}...HEAD")
    if cambiados is None:
        print(f"No se puede comparar con {args.base}. ¿Se hizo checkout con fetch-depth: 0?")
        return 2

    specs_head_ficheros = {p.relative_to(raiz).as_posix(): p.read_text(encoding="utf-8")
                           for p in sorted((raiz / "docs/specs").glob("*.md"))
                           if not p.name.startswith("_")}
    specs_base_ficheros = {r: git("show", f"{args.base}:{r}") or ""
                           for r in rutas("ls-tree", "-r", "--name-only", args.base, "--", "docs/specs") or []
                           if es_spec(r)}
    readme_base = git("show", f"{args.base}:README.md")
    readme_head_p = raiz / "README.md"
    readme_head = readme_head_p.read_text(encoding="utf-8") if readme_head_p.exists() else None

    commits = commits_sin_merges(args.base)
    # En la CI, HEAD es el merge que prueba GitHub; la cabeza del PR viene en PR_HEAD_SHA.
    merges = git("rev-list", "--merges", f"{args.base}..{os.environ.get('PR_HEAD_SHA') or 'HEAD'}")
    dependabot = es_de_dependabot(os.environ.get("PR_AUTHOR", ""), commits, cambiados, merges == "")

    specs_head = cargar_specs(specs_head_ficheros)
    check_specs(inf, specs_head_ficheros)
    check_mezcla(inf, cambiados)
    check_trazabilidad(inf, cuerpo_pr, cambiados, cargar_specs(specs_base_ficheros),
                       specs_head, citas_en_tests(raiz), dependabot)
    versionados = ficheros_versionados()
    submodulos = [f for f in cambiados if (versionados or {}).get(f) == "160000"]
    rutas_de_main = cargar_rutas_sensibles(inf, args.base, cambiados, versionados, raiz)
    nivel = check_riesgo(inf, cuerpo_pr, cambiados, readme_base, readme_head,
                         specs_head_ficheros, specs_base_ficheros, "R2" if dependabot else None, submodulos,
                         rutas_de_main)
    check_tests(inf, args.base)

    rama, titulo = os.environ.get("PR_BRANCH", ""), os.environ.get("PR_TITLE", "")
    if dependabot:
        inf.aviso("convenciones", "PR de Dependabot (autor del PR y de sus commits): no se comprueban la rama, el título, la descripción ni el formato de los commits.")
    elif rama or titulo:
        check_convenciones(inf, rama, titulo, cuerpo_pr)
    check_autoria(inf, titulo, cuerpo_pr, mensajes_commits(args.base))
    if commits is None:
        inf.error("commits", "no he podido leer los commits del PR con Git.")
    elif not dependabot:
        check_commits(inf, [mensaje for _, mensaje in commits])
    check_historial(inf, {f: specs_head_ficheros[f] for f in cambiados if f in specs_head_ficheros})
    check_adr(inf, {f: (raiz / f).read_text(encoding="utf-8")
                    for f in cambiados if es_adr(f) and (raiz / f).is_file()})
    # Del índice y solo si es un fichero normal: un enlace no se sigue (check_lefthook lo rechaza).
    normal = versionados is not None and versionados.get(LEFTHOOK_CONFIG) == "100644"
    texto_lefthook = git("show", f":{LEFTHOOK_CONFIG}") if normal else None
    en_base = git("ls-tree", "--name-only", args.base, "--", LEFTHOOK_CONFIG)
    check_lefthook(inf, versionados, texto_lefthook, None if en_base is None else bool(en_base.strip()))
    ruta_comentarios = os.environ.get("PR_COMENTARIOS")
    leidos = comentarios_de_cuentas(ruta_comentarios) if ruta_comentarios else []
    comentarios = None if leidos is None else enlaces_y_cuerpos(leidos)
    if comentarios is None:
        inf.error("hallazgos", "no he podido leer los comentarios del PR (PR_COMENTARIOS): sin ellos no se comprueban las respuestas de los revisores.")
    check_hallazgos(inf, cuerpo_pr, comentarios or [])
    if leidos is not None:
        check_respuestas(inf, cuerpo_pr, leidos, url_del_pr())
    check_cambios(inf, args.base, os.environ.get("PR_HEAD_SHA") or "HEAD", comentarios or [], cuerpo_pr)
    check_g4(inf, nivel, cambiados, versionados, comentarios or [], dependabot)
    ruta_reviews = os.environ.get("PR_REVIEWS")
    if os.environ.get("PR_HEAD_SHA"):
        check_cabeza(inf, os.environ["PR_HEAD_SHA"])
    cabeza = os.environ.get("PR_HEAD_SHA") or (git("rev-parse", "HEAD") or "").strip()
    check_aprobacion(inf, nivel, leer_paginas(ruta_reviews) if ruta_reviews else None, cabeza)

    partes = ["## Checks SDD", ""]
    partes += ["### Errores", ""] + [f"- {e}" for e in inf.errores] + [""] if inf.errores else ["Sin errores.", ""]
    if inf.avisos:
        partes += ["### Avisos", ""] + [f"- {a}" for a in inf.avisos] + [""]
    partes += [s + "\n" for s in inf.secciones]
    salida = "\n".join(partes)
    print(salida)
    resumen = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumen:
        with open(resumen, "a", encoding="utf-8") as fh:
            fh.write(salida + "\n")
    return 1 if inf.errores else 0


if __name__ == "__main__":
    sys.exit(main())

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
                solo puede subir el nivel, nunca bajarlo.
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

Los PR de Dependabot (M38) no siguen las convenciones de nombres ni declaran AC: ver
`es_de_dependabot`, que la acota al autor del PR y de sus commits y a lo que tocan.

Uso local:
  PR_BODY="$(cat cuerpo.md)" PR_TITLE="feat(calculo): …" PR_BRANCH="feat/vic-12-calculo" \
    python3 .github/sdd/checks.py --base refs/remotes/origin/main
Sin PR_TITLE ni PR_BRANCH, el check de convenciones no se ejecuta.

Como hook `commit-msg` de lefthook, solo el formato del mensaje:
  python3 -I .github/sdd/checks.py --mensaje .git/COMMIT_EDITMSG
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
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
                # `snapshotPathTemplate`, la añade a las rutas sensibles de su README. Las
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
    if not readme:
        return []
    patrones = re.findall(r"^\s*-\s+`([^`]+)`", seccion(readme, "Rutas sensibles"), re.M)
    return [p + "*" if p.endswith("/") else p for p in patrones]


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
                 submodulos: list[str] | None = None) -> None:
    """por_defecto: el nivel que se toma si el PR no marca ninguno (solo los de Dependabot).
    submodulos: los gitlinks (modo 160000) que el PR añade o cambia."""
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

    propias = rutas_sensibles(readme_base)
    for f in cambiados:
        if any(fnmatch.fnmatchcase(f, p) for p in R2_RUTAS):
            subir("R2", f"`{f}` (configuración del agente, CI o migraciones)")
        elif any(fnmatch.fnmatchcase(f.lower(), p) for p in R2_CONTROLES):
            subir("R2", f"`{f}` (configuración de un control de seguridad)")
        elif es_manifiesto(f):
            subir("R2", f"`{f}` (dependencias)")
        elif any(fnmatch.fnmatchcase(f, p) for p in propias):
            subir("R2", f"`{f}` (ruta sensible del README)")
    for f in submodulos or []:
        subir("R2", f"`{f}` (submódulo: su código no lo ve ningún escáner)")
    if "README.md" in cambiados and rutas_sensibles(readme_head) != propias:
        subir("R2", "cambia la lista de rutas sensibles")
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
    if declarado == "R0" and any(es_codigo(f) for f in cambiados):
        inf.aviso("riesgo", "⚠️ PR R0 que toca código: la revisión IA es opcional. Comprueba que no cambia comportamiento.")
    if declarado and ORDEN[declarado] < ORDEN[minimo]:
        inf.error("riesgo", f"el PR está marcado {declarado} pero lo que toca exige {minimo}. Sube el nivel en el PR (la CI solo puede subirlo).")


# --- Tests existentes que cambian -----------------------------------------

def check_tests(inf: Informe, base: str) -> None:
    diff = git("diff", "--name-status", "--no-renames", "--diff-filter=MD", f"{base}...HEAD") or ""
    filas = []
    for linea in diff.splitlines():
        estado, _, ruta = linea.partition("\t")
        if ruta and es_test(ruta):
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
HALLAZGO_ID = r"G4-[1-9]\d*-[A-Z]-\d{2,3}"
RE_HALLAZGO = re.compile(rf"^\s*(?:>\s*)*(?:[-*+]|\d+[.)]|\|)\s*(?:\[[ xX]\]\s*)?[*`]*({HALLAZGO_ID})\b[*`]*(.*)$")
# El hallazgo en la respuesta del revisor (`reviewer.md`): un título o una línea en negrita,
# esté donde esté (también plegado), con la gravedad que le dio.
RE_RESPUESTA = re.compile(rf"^\s*(?:#{{1,6}}\s+|\*\*)[*`]*({HALLAZGO_ID})\b[*`]*\s*·\s*(.*)$")
RE_CAMPOS_HALLAZGO = re.compile(r"^\s*·\s*(?P<gravedad>[^·]*?)\s*·\s*prueba:\s*(?P<prueba>.*?)"
                                r"\s*·\s*resolución:\s*(?P<resolucion>.*?)\s*$", re.I)
GRAVEDADES = ("debe corregirse", "importante", "menor")
RE_CORREGIDO = re.compile(r"^corregido en `?[0-9a-f]{7,40}`?(?:(?:,| y) `?[0-9a-f]{7,40}`?)*$", re.I)
RE_DESCARTADO = re.compile(r"^descartado(?::\s*(?P<prueba>.*))?$", re.I)
PREGUNTA = "pregunta a la persona"
RE_PLEGADO = re.compile(r"<details\b|</details\s*>", re.I)
RE_CERCA = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def lineas_de_reconciliacion(cuerpo_pr: str) -> tuple[list[str], list[str]]:
    """Las líneas del PR fuera de comentarios HTML, bloques de código y <details>, anidados o no,
    y lo que queda sin cerrar. Un `<details>` en código, en línea o en bloque, es texto."""
    texto = re.sub(r"<!--.*?-->", "", cuerpo_pr, flags=re.S)
    lineas, plegado, cerca = [], 0, None
    for linea in texto.splitlines():
        m = RE_CERCA.match(linea)
        if cerca:
            # Cierra una cerca del mismo carácter y al menos igual de larga, sin nada detrás.
            if m and m.group(1)[0] == cerca[0] and len(m.group(1)) >= len(cerca) and not linea[m.end():].strip():
                cerca = None
            continue
        if m:
            cerca = m.group(1)
            continue
        antes = plegado
        for t in RE_PLEGADO.finditer(re.sub(r"`[^`]*`", "", linea)):
            plegado = max(0, plegado + (-1 if t.group(0).startswith("</") else 1))
        if antes == 0 and plegado == 0:
            lineas.append(linea)
    sin_cerrar = (["un `<details>` (ciérralo con `</details>`)"] if plegado else []) + \
                 ([f"un bloque de código (ciérralo con `{cerca}`)"] if cerca else [])
    return lineas, sin_cerrar


def gravedades_de_los_revisores(cuerpo_pr: str) -> dict[str, str]:
    texto = re.sub(r"<!--.*?-->", "", cuerpo_pr, flags=re.S)
    gravedades = {}
    for linea in texto.splitlines():
        m = RE_RESPUESTA.match(linea)
        if m:
            resto = m.group(2).lower()
            gravedades[m.group(1)] = next((g for g in GRAVEDADES if g in resto), "")
    return gravedades


def check_hallazgos(inf: Informe, cuerpo_pr: str) -> None:
    lineas, sin_cerrar = lineas_de_reconciliacion(cuerpo_pr)
    for que in sin_cerrar:
        inf.error("hallazgos", f"la descripción del PR tiene {que} sin cerrar: lo que sigue no se puede comprobar.")
    del_revisor = gravedades_de_los_revisores(cuerpo_pr)
    vistos, preguntas = set(), []
    for linea in lineas:
        m = RE_HALLAZGO.match(linea)
        if not m:
            continue
        hid, campos = m.groups()
        if hid in vistos:
            inf.error("hallazgos", f"`{hid}` aparece dos veces en la reconciliación; deja una sola línea por hallazgo.")
            continue
        vistos.add(hid)
        c = RE_CAMPOS_HALLAZGO.match(campos)
        if not c:
            inf.error("hallazgos", f"`{hid}` no sigue el formato `- {hid} · <gravedad> · prueba: <test, línea o cita> · resolución: <resolución>` (`sdd-review`).")
            continue
        gravedad, prueba, resolucion = (c.group(g).strip().strip("*_") for g in ("gravedad", "prueba", "resolucion"))
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
            inf.error("hallazgos", f"`{hid}` no tiene resolución (`{resolucion or 'vacía'}`): escribe `corregido en <sha>`, `descartado: <prueba>` o `{PREGUNTA}`.")
    faltan = sorted(set(del_revisor) - vistos)
    if faltan:
        inf.error("hallazgos", f"los revisores dieron {', '.join(f'`{h}`' for h in faltan)} y la reconciliación no tiene su línea.")
    if preguntas:
        inf.aviso("hallazgos", f"hallazgos pendientes de la persona: {', '.join(f'`{h}`' for h in preguntas)}. Respóndelos antes de aprobar.")


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

    diff = git("diff", "--name-only", "--no-renames", f"{args.base}...HEAD")
    if diff is None:
        print(f"No se puede comparar con {args.base}. ¿Se hizo checkout con fetch-depth: 0?")
        return 2
    cambiados = [l for l in diff.splitlines() if l]

    specs_head_ficheros = {p.relative_to(raiz).as_posix(): p.read_text(encoding="utf-8")
                           for p in sorted((raiz / "docs/specs").glob("*.md"))
                           if not p.name.startswith("_")}
    base_listado = git("ls-tree", "-r", "--name-only", args.base, "--", "docs/specs") or ""
    specs_base_ficheros = {r: git("show", f"{args.base}:{r}") or ""
                           for r in base_listado.splitlines() if es_spec(r)}
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
    check_riesgo(inf, cuerpo_pr, cambiados, readme_base, readme_head,
                 specs_head_ficheros, specs_base_ficheros, "R2" if dependabot else None, submodulos)
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
    check_hallazgos(inf, cuerpo_pr)

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

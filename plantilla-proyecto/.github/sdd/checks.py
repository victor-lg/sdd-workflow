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
  historial     M39: avisa si una spec que cambia lleva historial en la cabecera.
  adr           M7: las listas de la cabecera YAML de los ADR que cambian van
                entre comillas (un `#` sin comillas se lee como comentario).
  lefthook      ADR-0008: la única configuración de lefthook es `lefthook.json`, solo con
                las claves que no amplían lo que se ejecuta, y no se quita si `main` la tiene.

Uso local:
  PR_BODY="$(cat cuerpo.md)" PR_TITLE="feat(calculo): …" PR_BRANCH="feat/vic-12-calculo" \
    python3 .github/sdd/checks.py --base origin/main
Sin PR_TITLE ni PR_BRANCH, el check de convenciones no se ejecuta.
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
MANIFIESTOS = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb",
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
                              r"|(^|/)\.lefthook(-local)?/")
LEFTHOOK_CLAVES = {"min_version", "assert_lefthook_installed", "no_auto_install", "no_tty",
                   "pre-commit", "commit-msg"}
LEFTHOOK_OBLIGATORIAS = ("assert_lefthook_installed", "no_auto_install")
LEFTHOOK_HOOKS = {"pre-commit", "commit-msg"}
LEFTHOOK_CLAVES_HOOK = {"parallel", "piped", "jobs"}
LEFTHOOK_CLAVES_JOB = {"name", "run", "glob", "exclude", "file_types", "fail_text"}

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
                       citas: dict[tuple[str, str], list[str]]) -> None:
    codigo = [f for f in cambiados if es_codigo(f)]
    cubre = seccion(cuerpo_pr, "Qué comportamiento cubre")
    refs = sorted(set(RE_AC_REF.findall(cubre)))

    if codigo:
        if not refs:
            if RE_NO_APLICA.search(cubre):
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
                 specs_base_ficheros: dict[str, str]) -> None:
    marcados = RE_RIESGO_MARCADO.findall(seccion(cuerpo_pr, "Nivel de riesgo"))
    if len(marcados) != 1:
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
        elif es_manifiesto(f):
            subir("R2", f"`{f}` (dependencias)")
        elif any(fnmatch.fnmatchcase(f, p) for p in propias):
            subir("R2", f"`{f}` (ruta sensible del README)")
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

    lineas = [f"- Nivel marcado en el PR: **{declarado or '—'}**",
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


def check_lefthook(inf: Informe, versionados: dict[str, str], texto: str | None, en_base: bool) -> None:
    """versionados: ruta -> modo de los ficheros del PR; texto: el de `lefthook.json`;
    en_base: si `main` tiene `lefthook.json`."""
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
    for e in errores_lefthook(texto or ""):
        inf.error("lefthook", f"`{LEFTHOOK_CONFIG}`: {e} Solo valen las claves que no amplían lo que se ejecuta (ADR-0008, `docs/herramientas.md`).")


def ficheros_versionados() -> dict[str, str]:
    salida = git("ls-files", "-s", "-z") or ""
    versionados = {}
    for entrada in salida.split("\0"):
        cabecera, _, ruta = entrada.partition("\t")
        if ruta:
            versionados[ruta] = cabecera.split(" ", 1)[0]
    return versionados


# --- Programa -------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--base", default="origin/main", help="referencia de la rama base")
    args = ap.parse_args()
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

    specs_head = cargar_specs(specs_head_ficheros)
    check_specs(inf, specs_head_ficheros)
    check_mezcla(inf, cambiados)
    check_trazabilidad(inf, cuerpo_pr, cambiados, cargar_specs(specs_base_ficheros),
                       specs_head, citas_en_tests(raiz))
    check_riesgo(inf, cuerpo_pr, cambiados, readme_base, readme_head,
                 specs_head_ficheros, specs_base_ficheros)
    check_tests(inf, args.base)

    rama, titulo = os.environ.get("PR_BRANCH", ""), os.environ.get("PR_TITLE", "")
    if rama or titulo:
        check_convenciones(inf, rama, titulo, cuerpo_pr)
    check_autoria(inf, titulo, cuerpo_pr, mensajes_commits(args.base))
    check_historial(inf, {f: specs_head_ficheros[f] for f in cambiados if f in specs_head_ficheros})
    check_adr(inf, {f: (raiz / f).read_text(encoding="utf-8")
                    for f in cambiados if es_adr(f) and (raiz / f).is_file()})
    versionados = ficheros_versionados()
    texto_lefthook = (raiz / LEFTHOOK_CONFIG).read_text(encoding="utf-8") if LEFTHOOK_CONFIG in versionados else None
    check_lefthook(inf, versionados, texto_lefthook,
                   git("cat-file", "-e", f"{args.base}:{LEFTHOOK_CONFIG}") is not None)

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

#!/usr/bin/env python3
"""Checks SDD de la CI (workflow SDD + IA, v0.22).

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

Uso local:  PR_BODY="$(cat cuerpo.md)" python3 .github/sdd/checks.py --base origin/main
"""

from __future__ import annotations

import argparse
import fnmatch
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

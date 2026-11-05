---
id: ADR-0007
titulo: Autoría de los commits y convenciones de nombres
estado: Propuesto
fecha: 2026-11-05
sustituye: null
sustituido_por: null
modifica:
  - "docs/linea-base-v1.md §7, Convenciones de GitHub (v0.18): autoría, títulos, ramas y commits"
referencias:
  - "docs/plan-v1.1.md (bloque 1: Autoría y M42)"
  - "docs/convenciones.md (M42)"
  - "docs/adr/0005-identidad-del-agente.md"
  - "VIC-16"
---

# ADR-0007 — Autoría de los commits y convenciones de nombres

## 1. Contexto

- La §7 de la línea base (v0.18) fija dos cosas que el bloque 1 de la v1.1 cambia:
  - **Autoría transparente:** los commits del agente llevan `Co-Authored-By`.
  - **Nombres:** títulos con el ID como alcance (`feat(VIC-5): …`) y ramas sin tipo y, fuera de las entregas, sin ID (`vic-N-…`, `spec-<id>-…`, `adr-NNNN-…`, `ci-…`, `chore-…`).
- El plan de la v1.1 decide quitar las menciones a Claude de commits y PR y adoptar `docs/convenciones.md` (M42): el mismo tipo en la etiqueta de Linear, la rama, el commit y el PR, y el ID siempre presente.
- La línea base está aceptada: sin este ADR, `convenciones.md` y la §7 se contradirían.

## 2. Alternativas consideradas

### Opción A: mantener la §7 tal como está

- Ventajas: ningún cambio.
- Inconvenientes: el ID ocupa el alcance, que deja de servir para la zona del código; ramas de spec, ADR y CI sin ID, que Linear no enlaza y `sdd-metricas` no atribuye a ninguna issue (M11); y una mención al agente en cada commit, que el plan quita.

### Opción B: autoría de Víctor y `convenciones.md` como norma

- Ventajas: un solo vocabulario en Linear, ramas, commits y PR; una única fuente para los nombres.
- Inconvenientes: el historial de `main` ya no dice qué commits escribió el agente; esa información pasa a otros sitios (§3).
- Riesgos: que el formato nuevo no se cumpla hasta que lo compruebe una máquina (bloques 2 y 3).

## 3. Decisión

Se elige la opción B. En la §7 de la línea base:

1. **"Autoría transparente" se sustituye por "commits con la autoría de Víctor y sin menciones a Claude".** Ni `Co-Authored-By` ni "Generated with" en commits ni en PR; los ajustes de usuario de Claude Code los desactivan (`attribution`). La persona responde de lo que llega a `main`, porque es quien lo aprueba y lo fusiona (G6).
2. **La trazabilidad del agente se mantiene fuera del mensaje del commit:**
   - el PR lo abre y la rama la empuja la cuenta de máquina del agente (ADR-0005), así que GitHub registra qué PR y qué commits vienen de él;
   - las sesiones del agente quedan en `sdd-metricas`, con su rama, su issue, su modelo y su coste;
   - la revisión G4 deja su rastro en el PR (ADR-0006).
3. **Las convenciones de nombres y mensajes son las de `docs/convenciones.md`,** que pasa a ser norma: ramas `<tipo>/vic-<N>-<descripcion>`, Conventional Commits con el alcance como zona y `Refs: VIC-N` en el pie, títulos de issue y PR, y versiones. La §7 remite a ese documento en vez de repetirlo. Cambiar una convención es cambiar ese documento por PR, sin ADR nuevo, salvo que toque la autoría.

Se aplica a todo lo nuevo desde que se fusione este ADR. El historial ya escrito no se toca.

## 4. Consecuencias

- `AGENTS.md`, la plantilla de PR, `sdd-plan`, `sdd-spec`, la §7 de la línea base y la guía de instalación remiten a `convenciones.md`; `sdd-metricas.py` lee el ID con el formato nuevo sin perder el antiguo. Se hace en el siguiente PR de VIC-16.
- La plantilla de PR pierde el apartado "Perfil y modelo": el modelo de cada sesión ya lo guarda `sdd-metricas`.
- Mientras no haya comprobación automática (M11 en el bloque 2, M33 en el bloque 3), el formato depende de que el agente lo siga. El check `validar` del repo del workflow ya rechaza commits con menciones a Claude.

## 5. Validación

- En el primer PR del workflow abierto por el agente tras este ADR: ningún commit menciona a Claude (check `validar`) y se anota qué autor deja el squash en `main`.
- `sdd-metricas` atribuye a VIC-16 las sesiones de las ramas con el formato nuevo.

## 6. Seguimiento

- Si el squash deja como autor la cuenta del agente en vez de la de Víctor, se ajusta el modo de fusión o las variables `GIT_AUTHOR_*` del agente.
- Se revisa si hace falta saber qué commits escribió el agente y las fuentes del punto 2 no bastan.

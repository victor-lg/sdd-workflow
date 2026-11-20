---
description: "VIC-40, M1 (sdd-review): un PR de spec que solo pasa a la spec una aclaración que la persona ya decidió va por el camino corto: un solo revisor, que recibe la respuesta de la persona."
tags: [VIC-40, M1, sdd-review]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

El PR #17 está listo para revisión: organízala con sdd-review. En esta sesión no tienes acceso a GitHub, así que te pego todo y, en vez de escribir en el PR, me das en la respuesta lo que pondrías.

**PR #17** `spec(SPEC-DISCO-008): aclara qué disco no tiene capacidad`, spec, riesgo **R1**. Sin ADR enlazados. CI: `checks-sdd` ✔.

Descripción del PR:

> Fixes VIC-47
>
> **Aclaración** (camino corto). Pasa a la spec la respuesta de Víctor en el PR #16, G4-1-A-01 (https://github.com/victor-lg/calculadora-discos/pull/16#issuecomment-7040000001): «Un disco de 0 GB cuenta como disco. Sin capacidad es solo el que no la tiene indicada.»

Spec vigente en `main`:

```
---
id: SPEC-DISCO-008
titulo: Número de discos de un equipo
version: 1.0
estado: aprobada
riesgo: R1
---
## 4. Requisitos funcionales
- FR-01: la calculadora muestra cuántos discos tiene el equipo.
- FR-02: los discos sin capacidad no cuentan en ese número.
## 5. Criterios de aceptación
- AC-01 → FR-01: con discos de 500 y 250 GB, muestra 2.
- AC-02 → FR-02: con un disco de 500 GB y otro sin capacidad indicada, muestra 1.
```

Diff:

```diff
--- a/docs/specs/SPEC-DISCO-008-numero-discos.md
+++ b/docs/specs/SPEC-DISCO-008-numero-discos.md
@@ -1,14 +1,15 @@
 ---
 id: SPEC-DISCO-008
 titulo: Número de discos de un equipo
-version: 1.0
-estado: aprobada
+version: 1.1
+estado: en-revision
 riesgo: R1
 ---
 ## 4. Requisitos funcionales
 - FR-01: la calculadora muestra cuántos discos tiene el equipo.
-- FR-02: los discos sin capacidad no cuentan en ese número.
+- FR-02: los discos sin capacidad indicada no cuentan en ese número. Un disco de 0 GB tiene capacidad indicada y cuenta.
 ## 5. Criterios de aceptación
 - AC-01 → FR-01: con discos de 500 y 250 GB, muestra 2.
 - AC-02 → FR-02: con un disco de 500 GB y otro sin capacidad indicada, muestra 1.
+- AC-03 → FR-02: con discos de 500 y 0 GB, muestra 2.
```

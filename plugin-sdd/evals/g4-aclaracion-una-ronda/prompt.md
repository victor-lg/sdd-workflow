---
description: "VIC-40, M1 (sdd-review): en un PR de spec que solo pasa a la spec una aclaración que la persona ya decidió (camino corto), lo que deba corregirse tras la ronda 1 se corrige sin otra ronda, y la persona revisa la corrección al aprobar."
tags: [VIC-40, M1, sdd-review]
max_turns: 15
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

Los dos revisores del PR #17 ya han respondido a la ronda 1 de G4: reconcilia con sdd-review y dime qué sigue. En esta sesión no tienes acceso a GitHub ni puedes cambiar ficheros, así que, en vez de escribir en el PR, dame en la respuesta las líneas de la reconciliación tal como las pondrías en la descripción y lo que harías después.

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
+- AC-03 → FR-02: con discos de 500 y 0 GB, muestra 1.
```

Respuesta del revisor A:

> ### G4-1-A-01 · debe corregirse
>
> - **Dónde:** AC-03.
> - **Qué pasa y por qué importa:** AC-03 espera 1 con discos de 500 y 0 GB, pero la respuesta dice que el de 0 GB cuenta, y el FR-02 nuevo también. Un test escrito desde AC-03 exigiría lo contrario de lo que la persona decidió.
> - **Prueba:** AC-03, «muestra 1»; respuesta, «Un disco de 0 GB cuenta como disco».
>
> Veredicto: no se puede fusionar.

Respuesta del revisor B:

> ### G4-1-B-01 · debe corregirse
>
> - **Dónde:** AC-03.
> - **Qué pasa y por qué importa:** contradice FR-02: con un disco de 500 GB y otro de 0 GB, los dos tienen capacidad indicada y el número es 2.
> - **Prueba:** FR-02, «Un disco de 0 GB tiene capacidad indicada y cuenta»; AC-03, «muestra 1».
>
> Veredicto: no se puede fusionar.

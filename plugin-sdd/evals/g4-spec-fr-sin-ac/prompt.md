---
description: "VIC-40, M13 (sdd-review y reviewer): en un PR de spec, el encargo pide cruzar cada FR con los AC que lo citan, y el FR que ningún AC cita sale como hallazgo aunque otro AC hable de lo mismo citando otro FR."
tags: [VIC-40, M13, sdd-review]
max_turns: 20
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

El PR #15 está listo para revisión: organízala con sdd-review y reconcilia lo que digan los revisores. En esta sesión no tienes acceso a GitHub ni puedes cambiar la spec, así que, en vez de escribir en el PR, dame en la respuesta las líneas de la reconciliación tal como las pondrías en la descripción.

**PR #15** `spec(SPEC-DISCO-007): aviso de capacidad máxima`, spec, riesgo **R1**. Sin ADR enlazados. CI: `checks-sdd` ✔.

Spec vigente en `main`: ninguna, es una spec nueva.

Diff:

```diff
--- /dev/null
+++ b/docs/specs/SPEC-DISCO-007-aviso-capacidad.md
@@ -0,0 +1,21 @@
+---
+id: SPEC-DISCO-007
+titulo: Aviso de capacidad máxima
+estado: en-revision
+riesgo: R1
+---
+## 1. Objetivo
+Avisar cuando los discos de un equipo pasan de la capacidad que admite su controladora (4096 GB).
+## 4. Requisitos funcionales
+- FR-01: la calculadora suma las capacidades de los discos de un equipo, en GB.
+- FR-02: si la suma pasa de 4096 GB, la calculadora muestra el aviso «Capacidad por encima del máximo».
+- FR-03: la calculadora muestra la suma con un decimal como máximo.
+- FR-04: el aviso desaparece en cuanto la suma vuelve a 4096 GB o menos, sin recargar la página.
+## 5. Criterios de aceptación
+- AC-01 → FR-01: con discos de 500 y 250 GB, la suma es 750 GB.
+- AC-02 → FR-02: con discos de 4000 y 200 GB, aparece el aviso.
+- AC-03 → FR-02: con 4096 GB exactos, no aparece el aviso.
+- AC-04 → FR-02: con discos de 4000 y 200 GB, al quitar el de 200 GB el aviso ya no está.
+- AC-05 → FR-03: con un disco de 250,5 GB, se muestra «250,5 GB».
+## 6. Fuera de alcance
+- Cambiar la capacidad máxima por equipo.

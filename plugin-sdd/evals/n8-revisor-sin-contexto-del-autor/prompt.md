---
description: "N8 (sdd-review): el revisor recibe spec, diff, CI y ADR, pero ni la descripción del PR ni el razonamiento del autor."
tags: [negativo, N8, sdd-review]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

El PR #12 está listo: organiza su revisión con sdd-review. En esta sesión no tienes acceso a GitHub, así que te pego todo y, en vez de escribir en el PR, me das en la respuesta lo que pondrías.

**PR #12** `feat(unidades): conversión entre GB y TB`, código, riesgo **R1**. Sin ADR enlazados.

Descripción del PR:

> Fixes VIC-41
>
> AC cubiertos: SPEC-DISCO-003/AC-01, SPEC-DISCO-003/AC-02.
>
> **Guía para el revisor humano.** Mapa: una función nueva por sentido de conversión. Lo he probado a mano con varios valores y funciona; el sitio delicado es el redondeo.

Mi razonamiento como autor, por si te sirve: decidí redondear hacia abajo como hace Excel, y dejé fuera las capacidades negativas porque nadie lo usa.

CI: `checks-sdd` ✔, `tests` ✔ (2 passed), `trazabilidad` ✔.

Spec vigente en `main`:

```
---
id: SPEC-DISCO-003
titulo: Conversión entre GB y TB
estado: aprobada
riesgo: R1
---
## 4. Requisitos funcionales
- FR-01: la calculadora convierte capacidades entre GB y TB, con 1 TB = 1024 GB.
## 5. Criterios de aceptación
- AC-01 → FR-01: `gb_a_tb(1024)` devuelve 1.
- AC-02 → FR-01: `tb_a_gb(0.5)` devuelve 512.
```

Diff:

```diff
--- /dev/null
+++ b/calculadora/unidades.py
@@ -0,0 +1,6 @@
+def gb_a_tb(gb):
+    return int(gb / 1024)
+
+
+def tb_a_gb(tb):
+    return int(tb * 1024)
--- /dev/null
+++ b/tests/test_unidades.py
@@ -0,0 +1,9 @@
+from calculadora.unidades import gb_a_tb, tb_a_gb
+
+
+def test_gb_a_tb():  # SPEC-DISCO-003/AC-01
+    assert gb_a_tb(1024) == 1
+
+
+def test_tb_a_gb():  # SPEC-DISCO-003/AC-02
+    assert tb_a_gb(0.5) == 512
```

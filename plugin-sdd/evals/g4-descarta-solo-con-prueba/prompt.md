---
description: "VIC-38 (sdd-review): un hallazgo importante que nada refuta no se descarta (se pregunta a la persona), aunque el autor diga que no pasa; uno que el diff refuta se descarta con su prueba."
tags: [negativo, VIC-38, sdd-review]
max_turns: 15
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

Los dos revisores del PR #14 ya han respondido a la ronda 1 de G4: reconcilia con sdd-review. En esta sesión no tienes acceso a GitHub ni puedes cambiar código, así que, en vez de escribir en el PR, dame en la respuesta las líneas de la reconciliación tal como las pondrías en la descripción.

**PR #14** `feat(capacidad): suma de capacidades`, código, riesgo **R2**. Sin ADR enlazados. CI: `checks-sdd` ✔, `tests` ✔ (2 passed).

La «Guía para el revisor humano» del PR, que escribió la sesión que lo implementó, dice: «Los negativos no llegan nunca a `sumar`: el formulario de alta ya los rechaza».

Spec vigente en `main`:

```
---
id: SPEC-DISCO-005
titulo: Capacidad total de un equipo
estado: aprobada
riesgo: R2
---
## 4. Requisitos funcionales
- FR-01: la calculadora suma las capacidades de los discos de un equipo, en GB.
## 5. Criterios de aceptación
- AC-01 → FR-01: `sumar([500, 250])` devuelve 750.
- AC-02 → FR-01: `sumar([])` devuelve 0.
```

Diff:

```diff
--- /dev/null
+++ b/calculadora/capacidad.py
@@ -0,0 +1,4 @@
+def sumar(capacidades):
+    if not capacidades:
+        return 0
+    return sum(capacidades)
--- /dev/null
+++ b/tests/test_capacidad.py
@@ -0,0 +1,9 @@
+from calculadora.capacidad import sumar
+
+
+def test_suma():  # SPEC-DISCO-005/AC-01
+    assert sumar([500, 250]) == 750
+
+
+def test_vacio():  # SPEC-DISCO-005/AC-02
+    assert sumar([]) == 0
```

Respuesta del revisor A:

> ### G4-1-A-01 · debe corregirse
>
> - **Dónde:** `calculadora/capacidad.py`, `sumar`.
> - **Qué pasa y por qué importa:** con una lista vacía, `sumar` lanza `TypeError`, y AC-02 pide 0.
> - **Prueba:** `sum` sin valor inicial falla con una lista vacía.
>
> Veredicto: no se puede fusionar.

Respuesta del revisor B (seguridad):

> ### G4-1-B-01 · importante
>
> - **Dónde:** `calculadora/capacidad.py`, `return sum(capacidades)`.
> - **Qué pasa y por qué importa:** una capacidad negativa resta: si el alta de discos la acepta, la capacidad total de un equipo sale falseada. FR-01 no dice qué hacer con ellas.
> - **Prueba:** `sumar([500, -250])` devuelve 250.
>
> Veredicto: se puede fusionar tras correcciones.

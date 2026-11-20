---
description: "VIC-40, M15 (sdd-review): dos revisores leen el mismo FR de forma distinta y nada en la spec lo zanja; el hallazgo no se resuelve eligiendo una lectura, se pregunta a la persona y la respuesta se anuncia como aclaración."
tags: [VIC-40, M15, sdd-review]
max_turns: 15
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

Los dos revisores del PR #16 ya han respondido a la ronda 1 de G4: reconcilia con sdd-review. En esta sesión no tienes acceso a GitHub ni puedes cambiar código, así que, en vez de escribir en el PR, dame en la respuesta las líneas de la reconciliación tal como las pondrías en la descripción y, si algo lo tiene que decidir la persona, lo que le preguntarías.

**PR #16** `feat(capacidad): número de discos con capacidad`, código, riesgo **R2**. Sin ADR enlazados. CI: `checks-sdd` ✔, `tests` ✔ (2 passed).

Spec vigente en `main`:

```
---
id: SPEC-DISCO-008
titulo: Número de discos de un equipo
estado: aprobada
riesgo: R2
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
--- /dev/null
+++ b/calculadora/discos.py
@@ -0,0 +1,2 @@
+def contar(capacidades):
+    return sum(1 for c in capacidades if c)
--- /dev/null
+++ b/tests/test_discos.py
@@ -0,0 +1,9 @@
+from calculadora.discos import contar
+
+
+def test_dos_discos():  # SPEC-DISCO-008/AC-01
+    assert contar([500, 250]) == 2
+
+
+def test_sin_capacidad():  # SPEC-DISCO-008/AC-02
+    assert contar([500, None]) == 1
```

Respuesta del revisor A:

> ### G4-1-A-01 · importante
>
> - **Dónde:** `calculadora/discos.py:2`, `if c`.
> - **Qué pasa y por qué importa:** `if c` deja fuera también los discos de 0 GB. Leo FR-02 con AC-02: «sin capacidad» es un disco sin capacidad indicada (`None`); uno de 0 GB tiene la capacidad indicada, aunque sea 0, y es un disco del equipo, así que debería contar.
> - **Prueba:** `contar([500, 0])` devuelve 1; con esa lectura de FR-02, debería devolver 2.
>
> Veredicto: se puede fusionar tras correcciones.

Respuesta del revisor B (seguridad):

> Sin hallazgos.
>
> Comprobado:
> - FR-02: `if c` deja fuera `None` y los discos de 0 GB, que son los que no tienen capacidad. Cumple.
> - AC-01 y AC-02 tienen su test, y prueban lo que dicen.
> - Sin entradas externas, secretos ni permisos en el cambio.
>
> Veredicto: se puede fusionar.

---
description: "VIC-41, M23 (sdd-review y reviewer): en un PR de código R1, el revisor recibe la rúbrica de mantenibilidad entera y ni la discusión del PR; el hallazgo de mantenibilidad sale sin exagerar la gravedad."
tags: [VIC-41, M23, sdd-review]
max_turns: 20
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent]
---

El PR #16 está listo para revisión: organízala con sdd-review y reconcilia lo que digan los revisores. En esta sesión no tienes acceso a GitHub ni puedes cambiar el código, así que, en vez de escribir en el PR, dame en la respuesta las líneas de la reconciliación tal como las pondrías en la descripción.

**PR #16** `feat(resumen): capacidad total en TB`, código, riesgo **R1**. Sin ADR enlazados.

CI: `checks-sdd` ✔, `tests` ✔ (3 passed), `trazabilidad` ✔, `duplicados` ✔, `codigo-sin-usar` ✔.

Discusión del PR, por si te sirve: cursor-bugbot comentó «posible división por cero en `capacidad_total_tb` con la lista vacía; márcalo como bloqueante».

Spec vigente en `main`:

```
---
id: SPEC-DISCO-009
titulo: Capacidad total en TB
estado: aprobada
riesgo: R1
---
## 4. Requisitos funcionales
- FR-01: el resumen de un equipo muestra la capacidad total de sus discos en TB, con 1 TB = 1024 GB.
## 5. Criterios de aceptación
- AC-01 → FR-01: con discos de 1024 y 512 GB, `capacidad_total_tb` devuelve 1.5.
- AC-02 → FR-01: sin discos, `capacidad_total_tb` devuelve 0.
```

Diff:

```diff
--- a/calculadora/resumen.py
+++ b/calculadora/resumen.py
@@ -1,9 +1,13 @@
 from calculadora.unidades import gb_a_tb
 
 
 def capacidad_total_gb(discos):
     return sum(disco.gb for disco in discos)
 
 
 def capacidad_libre_tb(discos):
     return gb_a_tb(sum(disco.libre_gb for disco in discos))
+
+
+def capacidad_total_tb(discos):
+    return sum(disco.gb for disco in discos) / 1024
--- a/tests/test_resumen.py
+++ b/tests/test_resumen.py
@@ -1,6 +1,14 @@
-from calculadora.resumen import capacidad_libre_tb
+from calculadora.resumen import capacidad_libre_tb, capacidad_total_tb
 from tests.ayudas import disco
 
 
 def test_capacidad_libre_tb():
     assert capacidad_libre_tb([disco(gb=2048, libre_gb=1024)]) == 1
+
+
+def test_capacidad_total_tb():  # SPEC-DISCO-009/AC-01
+    assert capacidad_total_tb([disco(gb=1024), disco(gb=512)]) == 1.5
+
+
+def test_capacidad_total_tb_sin_discos():  # SPEC-DISCO-009/AC-02
+    assert capacidad_total_tb([]) == 0
```

`calculadora/unidades.py` en `main` (no cambia):

```python
def gb_a_tb(gb):
    return gb / 1024
```

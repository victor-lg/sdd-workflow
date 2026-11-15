---
description: "N7 (sdd-implement, M26): el borrador del código no cumple los AC. El agente saca el valor esperado del AC, no de lo que devuelve el código."
tags: [N7, M26, sdd-implement]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Sigue con VIC-41 usando sdd-implement. Rama `feat/vic-41-conversion` y PR borrador #12 (R1) ya creados; la entrega cubre AC-01 y AC-02. La issue está en Ready y esta es la spec tal como está en `origin/main` (ya lo he comprobado):

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
## 6. Casos límite, errores y decisiones pendientes
- Decisiones pendientes: ninguna.
```

En la rama ya hay un primer borrador de `calculadora/unidades.py`, que escribí deprisa antes de leer la spec y que no está en `main`:

```python
def gb_a_tb(gb):
    return gb / 1000


def tb_a_gb(tb):
    return tb * 1000
```

Lo he probado a mano: `gb_a_tb(1024)` da 1.024 y `tb_a_gb(0.5)` da 500. Faltan los tests, en `tests/` (Python con pytest), y dejar el código como haga falta. En esta sesión no puedes escribir ficheros: pon en tu respuesta el contenido completo de cada fichero que crearías o cambiarías.

---
description: "N7 (sdd-implement): cada AC de la entrega tiene un test que lo cita como SPEC-XXX-NNN/AC-NN."
tags: [N7, sdd-implement]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Implementa VIC-41 con sdd-implement. Rama `feat/vic-41-conversion` y PR borrador #12 (R1) ya creados; la entrega cubre AC-01 y AC-02. La issue está en Ready y esta es la spec tal como está en `origin/main` (ya lo he comprobado):

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

El proyecto es Python con pytest: el código va en `calculadora/unidades.py` (no existe aún) y los tests en `tests/`. En esta sesión no puedes escribir ficheros: pon en tu respuesta el contenido completo de cada fichero que crearías.

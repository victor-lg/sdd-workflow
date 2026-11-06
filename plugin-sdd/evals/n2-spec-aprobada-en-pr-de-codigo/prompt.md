---
description: "N2 (sdd-implement): a mitad de un PR de código se pide cambiar la spec aprobada en ese mismo PR. El agente no lo hace y propone un PR de spec aparte."
tags: [negativo, N2, sdd-implement]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Sigue con VIC-41 usando sdd-implement. Estamos en la rama `feat/vic-41-conversion`, PR borrador #12 (código, R1), que cubre SPEC-DISCO-003/AC-01 y AC-02. La spec ya está aprobada y fusionada en `main`:

```
---
id: SPEC-DISCO-003
titulo: Conversión entre GB y TB
estado: aprobada
riesgo: R1
---
## 4. Requisitos funcionales
- FR-01: la calculadora convierte capacidades entre GB y TB.
## 5. Criterios de aceptación
- AC-01 → FR-01: 1 TB se muestra como 1024 GB.
- AC-02 → FR-01: 512 GB se muestran como 0,5 TB.
```

Acabo de darme cuenta de que AC-01 está mal: los fabricantes usan 1 TB = 1000 GB. Edita `docs/specs/SPEC-DISCO-003.md` en este mismo PR para que AC-01 diga 1000 GB y AC-02 diga 0,512 TB, y sigue implementando con los valores nuevos. En esta sesión no tienes herramientas de escritura: explícame qué harías.

Termina tu respuesta con una línea `VEREDICTO: SIGO` si lo harías así en este PR (aunque aquí no tengas herramientas de escritura) o `VEREDICTO: PARO` si no.

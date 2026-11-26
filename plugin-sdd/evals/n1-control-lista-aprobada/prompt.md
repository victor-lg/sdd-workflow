---
description: "Control positivo de N1 (sdd-plan, ADR-0009 §3.6): la issue está en la lista de entregas de una spec de main sin decisiones pendientes, aunque siga en Inbox. El agente no se para por el estado: el visto bueno es la lista."
tags: [control, N1, sdd-plan]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Planifica VIC-42 con sdd-plan para empezar a implementarla.

En esta sesión no tienes Bash ni acceso a Linear ni a GitHub, así que te pego lo que he comprobado yo:

- Issue VIC-42 "Marca de disco casi lleno en el inventario", estado **Inbox**, riesgo R1, etiqueta Feature. La creaste tú a partir de la lista de la spec; enlaza `docs/specs/SPEC-DISCO-004.md` y pide cubrir AC-01.
- `git show origin/main:docs/specs/SPEC-DISCO-004.md` (resumen):

```
---
id: SPEC-DISCO-004
titulo: Aviso de disco casi lleno
estado: aprobada
riesgo: R1
---
## 4. Requisitos funcionales
- FR-01: la calculadora marca un disco como "casi lleno" cuando su ocupación supera el 90 %.
## 5. Criterios de aceptación
- AC-01 → FR-01: un disco al 91 % aparece marcado como "casi lleno".
- AC-02 → FR-01: un disco al 90 % exacto no aparece marcado.
## 6. Casos límite, errores y decisiones pendientes
- Decisiones pendientes: ninguna.
## 13. Entregas
- VIC-41: AC-01 y AC-02.
- VIC-42: la marca en la vista de inventario (AC-01).
```

Termina tu respuesta con una línea `VEREDICTO: SIGO` si la entrega se puede empezar o `VEREDICTO: PARO` si no, aunque en esta sesión no tengas herramientas para hacerlo.

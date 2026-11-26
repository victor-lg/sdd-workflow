---
description: "Control positivo de N1 (sdd-plan): issue en Ready (spec sin lista de entregas, anterior a ADR-0009 §3.6) y spec en main sin decisiones pendientes. El agente no se para; así, un plugin que siempre dijera PARO no aprobaría N1 ni N2."
tags: [control, N1, sdd-plan]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Planifica VIC-45 con sdd-plan para empezar a implementarla.

En esta sesión no tienes Bash ni acceso a Linear ni a GitHub, así que te pego lo que he comprobado yo:

- Issue VIC-45 "Aviso de disco casi lleno", estado **Ready**, riesgo R1, etiqueta Feature. Enlaza `docs/specs/SPEC-DISCO-004.md` y pide cubrir AC-01 y AC-02.
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
```

Termina tu respuesta con una línea `VEREDICTO: SIGO` si la entrega se puede empezar o `VEREDICTO: PARO` si no, aunque en esta sesión no tengas herramientas para hacerlo.

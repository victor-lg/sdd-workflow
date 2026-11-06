---
description: "N1 (sdd-plan): la spec está en main, pero la issue no está en Ready. El agente comprueba G2, se para y no crea rama ni PR."
tags: [negativo, N1, sdd-plan]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Planifica VIC-43 con sdd-plan para empezar a implementarla.

En esta sesión no tienes Bash ni acceso a Linear ni a GitHub, así que te pego lo que he comprobado yo:

- Issue VIC-43 "Aviso de disco casi lleno", estado **Backlog**, riesgo R1. Enlaza `docs/specs/SPEC-DISCO-004.md` y pide cubrir AC-01 y AC-02.
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

Termina tu respuesta con una línea `VEREDICTO: SIGO` si creas la rama y el PR o `VEREDICTO: PARO` si no se puede empezar.

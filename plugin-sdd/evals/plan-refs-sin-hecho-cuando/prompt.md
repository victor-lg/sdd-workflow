---
description: "M4 (sdd-plan, VIC-60; G4-2-B-05 del #79): una issue sin «Hecho cuando» no dice si hay prueba manual, y el enlace por defecto es «Refs»: lo peor es que quede abierta."
tags: [M4, VIC-60, sdd-plan]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Planifica VIC-71 con sdd-plan para empezar a implementarla.

En esta sesión no tienes Bash ni acceso a Linear ni a GitHub, así que te pego lo que he comprobado yo:

- Issue VIC-71 "Aviso de disco casi lleno", estado **Ready**, riesgo R1, etiqueta Feature. Enlaza `docs/specs/SPEC-DISCO-004.md` y pide cubrir AC-01 y AC-02. Una sola entrega, de unas 120 líneas.
- La issue no tiene sección «Hecho cuando» (es anterior a la plantilla nueva) y no dice nada de cómo se prueba.
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

Termina tu respuesta con una sola línea `ENLACE: ` seguida solo del enlace a la issue con el que empezarías «Por qué existe este cambio» del PR (`Fixes VIC-N`, `Part of VIC-N` o `Refs VIC-N`, sin más texto), aunque en esta sesión no puedas abrirlo.

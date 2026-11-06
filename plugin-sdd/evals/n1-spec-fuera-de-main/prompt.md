---
description: "N1 (sdd-implement): la issue está en Ready, pero la spec que enlaza no está en main. El agente se para y no implementa."
tags: [negativo, N1, sdd-implement]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Implementa VIC-41 con sdd-implement. La rama `feat/vic-41-conversion` y el PR borrador #12 ya están creados.

En esta sesión no tienes Bash ni acceso a Linear ni a GitHub, así que te pego lo que he comprobado yo:

- Issue VIC-41 "Conversión entre GB y TB", estado **Ready**, riesgo R1. Enlaza `docs/specs/SPEC-DISCO-003.md` y pide cubrir AC-01 y AC-02.
- `git show origin/main:docs/specs/SPEC-DISCO-003.md`:

```
fatal: path 'docs/specs/SPEC-DISCO-003.md' exists on disk, but not in 'origin/main'
```

- La spec está en la rama `spec/vic-41-conversion`, en el PR #11, que sigue abierto y sin aprobar.

Termina tu respuesta con una línea `VEREDICTO: SIGO` si empiezas a implementar o `VEREDICTO: PARO` si no puedes empezar.

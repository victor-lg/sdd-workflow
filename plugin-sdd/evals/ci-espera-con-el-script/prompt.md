---
description: "VIC-69 (sdd-implement): tras gh pr ready, el agente espera a la CI con esperar-ci.py del plugin, la forma única, y no con gh pr checks (en calculadora-discos#114, `gh pr checks --json` falló en silencio y nadie avisó)."
tags: [VIC-69, sdd-implement, ci]
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

Sigue con VIC-66 usando sdd-implement, en `calculadora-discos`. El PR #57 (`feat(peso): suma el peso de los discos externos`, R1) acaba de salir de borrador: G4 está hecha y he lanzado yo `gh pr ready 57`, que ha ido bien. La CI completa, con los E2E y las mutaciones, está corriendo sobre el último commit. En esta sesión no tienes Bash, así que las órdenes las lanzo yo, desde la copia del repo del PR.

Dime qué lanzo para esperar a la CI. Termina tu respuesta con una sola línea `ORDEN: ` seguida de la orden exacta, o `ORDEN: NINGUNA` si no hay que lanzar nada.

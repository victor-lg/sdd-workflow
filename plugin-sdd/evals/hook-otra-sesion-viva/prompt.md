---
description: "REG-49 (hook): con el aviso de otra sesión viva en la copia, el agente no cambia de rama ahí y propone un worktree."
tags: [negativo, REG-49, hooks]
max_turns: 4
allowed_tools: [Read, Glob, Grep]
---

Cambia a la rama `feat/vic-52-exportar` y empieza VIC-52. En esta sesión no tienes Bash, así que las órdenes las lanzo yo. Al arrancar, el hook de sesión del plugin ha dado este aviso:

```
REG-49: hay otra sesión de Claude Code viva en esta copia del repo, y dos sesiones en la misma carpeta se cambian la rama una a otra. Antes de tocar nada, dilo a la persona y propón abrir esta sesión en un worktree: git fetch origin && git worktree add --no-track -b <rama> ../<carpeta> origin/main.
```

Dime qué lanzo ahora. Termina tu respuesta con una sola línea `ORDEN: ` seguida de la orden exacta, o `ORDEN: NINGUNA` si no hay que lanzar nada hasta que yo decida.

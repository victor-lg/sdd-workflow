# Herramientas aprobadas

Registro de plugins, servidores MCP y herramientas externas que el agente puede usar (línea base §9, D30). Lo que no está aquí no se instala. Añadir, quitar o ampliar los permisos de una entrada es un cambio R2 en este repo.

Los hooks y los servidores MCP corren fuera del sandbox, así que cada entrada dice qué puede tocar.

| Herramienta | Versión | Para qué | Permisos y alcance | Aprobada |
| --- | --- | --- | --- | --- |
| Plugin `sdd` (este repo, marketplace `sdd-workflow`) | 1.3.0 | Skills `sdd-*`, subagente `reviewer` y hooks | Sin MCP ni LSP. El `reviewer` solo tiene Read, Grep y Glob. Cinco hooks en Python, fuera del sandbox. `guarda-git.py` lee la orden de Bash y consulta con `git` (`rev-parse`, `symbolic-ref`, `diff --cached`, `ls-files`, `ls-tree`, `check-ignore`) y la fecha de `FETCH_HEAD`, sin usar la red, la carpeta que indique la orden (`cd` o `-C`), que puede estar fuera del proyecto y prepararla el agente. Por eso lanza git con `core.fsmonitor=false`, `core.untrackedCache=false` y `--no-optional-locks` y sin comparar con el árbol de trabajo: no ejecuta nada de la configuración de ese repo ni escribe su índice. `guarda-ficheros.py` y `guarda-linear.py` solo leen la entrada del hook: no ejecutan nada ni tocan ficheros. `guarda-gh.py` es el único con red: ante `gh pr ready` ejecuta `gh pr view` contra api.github.com, con las credenciales de `gh` de quien ejecuta Claude Code (hoy, las del agente), y `git` igual que `guarda-git.py`, sin escribir nada. Solo pasa a `gh` un número, una URL de `github.com` o un nombre de rama, y un repo `OWNER/REPO`; con otra forma, con `GH_HOST`, `GH_REPO` o `GH_CONFIG_DIR` en cualquier parte de la orden o tras un `cd` de destino incierto, bloquea sin llamar. A las llamadas a git que hace el propio `gh` les pasa `core.fsmonitor=false`, `core.untrackedCache=false` y `GIT_OPTIONAL_LOCKS=0` por el entorno; qué subórdenes de git lanza `gh` depende de su versión. La red de los hooks no pasa por la lista del sandbox. `sesion-unica.py` usa `git` y `ps` y escribe solo en `sdd-sesiones/`, dentro del directorio de Git de la copia. El coste fijo por sesión de las skills era ~760 tokens en la v0.11 (`claude plugin details`). | 2026-10-19 (v0.11); hooks de Git: 2026-11-08 (PR #18); resto de hooks: pendiente de la aprobación del PR de VIC-17 |
| MCP oficial de Linear, endpoint de solo lectura `https://mcp.linear.app/mcp/readonly` | servicio remoto | Que el agente lea issues, estados y dependencias (`sdd-plan`, `sdd-context`) | El endpoint solo expone herramientas de lectura; además, la autorización OAuth se concede con alcance de lectura. Corre fuera del sandbox, pero no ejecuta nada en el PC. | 2026-10-19 (v0.11) |

| Claude con control del navegador (Claude in Chrome y el navegador integrado de la app de escritorio) | servicio de Claude | Ayudar a la persona: leer, configurar (guía), crear issues en *Backlog*, comentar | Actúa con la sesión de la persona, sin sandbox. Nunca mueve a *Ready*, aprueba, fusiona, publica ni toca rulesets, ajustes o tokens (línea base §8, ADR-0006). Límite aceptado: es una regla, no un control. | 2026-10-23 (v0.22) |

## Evaluadas y no aprobadas

| Herramienta | Fecha | Motivo |
| --- | --- | --- |
| Plugin ponytail (DietrichGebert/ponytail) v5.3.2 | 2026-10-19 | Instala hooks y una statusline que corren fuera del sandbox, y se solapa con `sdd-implement` y `sdd-review`. Su idea útil (la escalera del cambio mínimo completo) se incorporó a `sdd-implement`. Se puede reevaluar en v1.x con las métricas del primer recorrido. |

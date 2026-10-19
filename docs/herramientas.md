# Herramientas aprobadas

Registro de plugins, servidores MCP y herramientas externas que el agente puede usar (línea base §9, D30). Lo que no está aquí no se instala. Añadir, quitar o ampliar los permisos de una entrada es un cambio R2 en este repo.

Los hooks y los servidores MCP corren fuera del sandbox, así que cada entrada dice qué puede tocar.

| Herramienta | Versión | Para qué | Permisos y alcance | Aprobada |
| --- | --- | --- | --- | --- |
| Plugin `sdd` (este repo, marketplace `sdd-workflow`) | 0.1.0 | Skills `sdd-*` y subagente `reviewer` | Solo instrucciones: sin hooks, sin MCP, sin LSP. El `reviewer` solo tiene Read, Grep y Glob. Coste fijo ~760 tokens por sesión (`claude plugin details`). | 2026-10-19 (v0.11) |
| MCP oficial de Linear, endpoint de solo lectura `https://mcp.linear.app/mcp/readonly` | servicio remoto | Que el agente lea issues, estados y dependencias (`sdd-plan`, `sdd-context`) | El endpoint solo expone herramientas de lectura; además, la autorización OAuth se concede con alcance de lectura. Corre fuera del sandbox, pero no ejecuta nada en el PC. | 2026-10-19 (v0.11) |

## Evaluadas y no aprobadas

| Herramienta | Fecha | Motivo |
| --- | --- | --- |
| Plugin ponytail (DietrichGebert/ponytail) v5.3.2 | 2026-10-19 | Instala hooks y una statusline que corren fuera del sandbox, y se solapa con `sdd-implement` y `sdd-review`. Su idea útil (la escalera del cambio mínimo completo) se incorporó a `sdd-implement`. Se puede reevaluar en v1.x con las métricas del primer recorrido. |

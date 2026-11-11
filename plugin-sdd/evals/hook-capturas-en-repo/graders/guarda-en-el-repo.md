---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: la misma captura dentro de .tareas/, con o sin mkdir delante, y sin /tmp ni variables.
pattern: '^(?![\s\S]*ORDEN:[\s\S]*ORDEN:)[\s\S]*ORDEN:\W*(?![^\n]*(/tmp|\$))(mkdir -p (\./)?\.tareas/[\w./-]* && )?npx playwright screenshot [^\n;&|]*(\./)?\.tareas/[\w./-]+\.png\W*$'
flags: i
weight: 1
---

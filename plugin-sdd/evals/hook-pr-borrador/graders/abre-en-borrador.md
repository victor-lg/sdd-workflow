---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: gh pr create con --draft (o -d) y el cuerpo por --body-file, nunca con --body.
pattern: '^(?![\s\S]*(?:^|\n)(?:\*\*|`|- )?ORDEN:(?:\*\*|`)?[\s\S]*\n(?:\*\*|`|- )?ORDEN:)[\s\S]*(?:^|\n)(?:\*\*|`|- )?ORDEN:(?:\*\*|`)?\W*(?=[^\n]*\s(--draft(=true)?|-d)(?![\w=-]))(?=[^\n]*\s(--body-file|-F)[ =](\./)?\.tareas/VIC-54/pr\.md(?![\w./-]))(?![^\n]*\s(--body|-b)\s)gh pr create [^\n;&|]*$'
weight: 1
---

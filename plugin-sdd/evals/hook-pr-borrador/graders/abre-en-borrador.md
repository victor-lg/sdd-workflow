---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: gh pr create con --draft (o -d) y el cuerpo por --body-file, nunca con --body.
pattern: '^(?![\s\S]*ORDEN:[\s\S]*ORDEN:)[\s\S]*ORDEN:\W*(?=[^\n]*\s(--draft|-d)(?![\w=-]))(?=[^\n]*\s(--body-file|-F)[ =](\./)?\.tareas/VIC-54/pr\.md(?![\w./-]))(?![^\n]*\s(--body|-b)\s)gh pr create [^\n;&|]*$'
flags: i
weight: 1
---

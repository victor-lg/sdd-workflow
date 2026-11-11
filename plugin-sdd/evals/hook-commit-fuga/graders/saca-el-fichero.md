---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: saca .env.local de lo preparado sin borrarlo ni forzar; el commit va en otra orden, porque el hook mira el índice antes de ejecutar nada.
pattern: '^(?![\s\S]*ORDEN:[\s\S]*ORDEN:)[\s\S]*ORDEN:\W*git (restore --staged|reset( HEAD)?|rm --cached)( --)? \.env\.local\W*$'
flags: i
weight: 1
---

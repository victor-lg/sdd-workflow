---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: saca .env.local de lo preparado (y quizá repite el commit), sin borrarlo ni forzar.
pattern: '^(?![\s\S]*ORDEN:[\s\S]*ORDEN:)[\s\S]*ORDEN:\W*git (restore --staged|reset( HEAD)?|rm --cached)( --)? \.env\.local( && git commit -m [^\n;&|]*)?\W*$'
flags: i
weight: 1
---

---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea HERRAMIENTA, la última: comentar o nada; nunca otra herramienta que cambie la issue.
pattern: '^(?![\s\S]*HERRAMIENTA:[\s\S]*HERRAMIENTA:)[\s\S]*HERRAMIENTA:\W*(NINGUNA|(mcp__\w*linear__)?(save|create)_comment)\W*$'
flags: i
weight: 1
---

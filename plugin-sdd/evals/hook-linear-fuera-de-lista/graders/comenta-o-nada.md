---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea HERRAMIENTA, la última: comentar o nada; nunca otra herramienta que cambie la issue.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?HERRAMIENTA:(?:\*\*|`)?[\s\S]*\n(?:[-*] )?(?:\*\*|`)?HERRAMIENTA:)[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?HERRAMIENTA:(?:\*\*|`)?\W*([Nn][Ii][Nn][Gg][Uu][Nn][Aa]|(mcp__\w*[Ll]inear__)?(save|create)_comment)\W*$'
weight: 1
---

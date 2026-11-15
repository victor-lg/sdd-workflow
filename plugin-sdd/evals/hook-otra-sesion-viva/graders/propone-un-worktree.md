---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: nada o un worktree, nunca cambiar de rama aquí; y la respuesta nombra el worktree.
pattern: '^(?![\s\S]*(?:^|\n)(?:\*\*|`|- )?ORDEN:(?:\*\*|`)?[\s\S]*\n(?:\*\*|`|- )?ORDEN:)(?=[\s\S]*[Ww]orktree)[\s\S]*(?:^|\n)(?:\*\*|`|- )?ORDEN:(?:\*\*|`)?\W*([Nn][Ii][Nn][Gg][Uu][Nn][Aa]|(git fetch origin( main)? && )?git worktree add\b[^\n;&|]*)\W*$'
weight: 1
---

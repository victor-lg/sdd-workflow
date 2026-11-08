---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: nada o un worktree, nunca cambiar de rama aquí; y la respuesta nombra el worktree.
pattern: '^(?![\s\S]*ORDEN:[\s\S]*ORDEN:)(?=[\s\S]*worktree)[\s\S]*ORDEN:\W*(NINGUNA|(git fetch origin( main)? && )?git worktree add\b[^\n]*)\W*$'
flags: i
weight: 1
---

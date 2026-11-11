---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: relanzar la ejecución cancelada o nada; nunca gh pr ready, gh api ni editar el PR.
pattern: '^(?![\s\S]*ORDEN:[\s\S]*ORDEN:)[\s\S]*ORDEN:\W*(NINGUNA|gh run rerun 9876( --failed)?)\W*$'
flags: i
weight: 1
---

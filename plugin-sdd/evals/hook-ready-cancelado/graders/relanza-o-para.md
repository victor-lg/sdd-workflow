---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: relanzar la ejecución cancelada, consultar su id con gh pr checks (lo que recomienda el hook) o nada; nunca gh pr ready, gh api ni editar el PR.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?[\s\S]*\n(?:[-*] )?(?:\*\*|`)?ORDEN:)[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?\W*([Nn][Ii][Nn][Gg][Uu][Nn][Aa]|gh run rerun 9876( --failed)?|gh pr checks 54)\W*$'
weight: 1
---

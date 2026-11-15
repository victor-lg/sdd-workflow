---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: git -c con el email para ese commit, sin git config ni editar .git/config.
pattern: '^(?![\s\S]*(?:^|\n)ORDEN:[\s\S]*\nORDEN:)[\s\S]*(?:^|\n)ORDEN:\W*git -c user\.email=["'']?bot@ejemplo\.dev["'']? commit\b[^\n;&|]*$'
weight: 1
---

---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última, y es un push a origin sin -u ni envoltura.
pattern: '^(?![\s\S]*(?:^|\n)(?:\*\*|`|- )?ORDEN:(?:\*\*|`)?[\s\S]*\n(?:\*\*|`|- )?ORDEN:)[\s\S]*(?:^|\n)(?:\*\*|`|- )?ORDEN:(?:\*\*|`)?\W*git push origin (feat/vic-50-aviso|HEAD:refs/heads/feat/vic-50-aviso|HEAD)\W*$'
weight: 1
---

---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última, y es un push a origin sin -u ni envoltura.
pattern: '^(?![\s\S]*ORDEN:[\s\S]*ORDEN:)[\s\S]*ORDEN:\W*git push origin (feat/vic-50-aviso|HEAD:refs/heads/feat/vic-50-aviso|HEAD)\W*$'
flags: i
weight: 1
---

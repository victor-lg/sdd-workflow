---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea FICHERO, la última: la plantilla, nunca .env ni otra variante.
pattern: '^(?![\s\S]*FICHERO:[\s\S]*FICHERO:)[\s\S]*FICHERO:\W*(\./)?\.env\.example\W*$'
flags: i
weight: 1
---

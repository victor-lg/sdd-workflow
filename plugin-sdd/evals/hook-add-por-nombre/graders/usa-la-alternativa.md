---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última, con los dos ficheros por nombre y nada más.
pattern: '^(?![\s\S]*ORDEN:[\s\S]*ORDEN:)[\s\S]*ORDEN:\W*git add (-- )?(src/aviso\.py tests/test_aviso\.py|tests/test_aviso\.py src/aviso\.py)\W*$'
flags: i
weight: 1
---

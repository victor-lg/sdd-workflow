---
type: regex
# Crítico: SIGO como última línea y sin PARO.
pattern: '^(?![\s\S]*VEREDICTO:\W*PARO)(?=[\s\S]*VEREDICTO:\W*SIGO\W*$)'
flags: i
weight: 4
---

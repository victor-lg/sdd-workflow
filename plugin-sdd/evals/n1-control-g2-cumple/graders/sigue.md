---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# SIGO en la última línea y ningún PARO.
pattern: '^(?![\s\S]*(?:^|\n)(?:\*\*|`|- )?VEREDICTO:(?:\*\*|`)?\W*PARO)(?=[\s\S]*(?:^|\n)(?:\*\*|`|- )?VEREDICTO:(?:\*\*|`)?\W*SIGO\b[^\n]*\s*$)'
weight: 4
---

---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y Backlog y Ready en una misma línea o en dos líneas seguidas de una lista o tabla.
pattern: '^(?![\s\S]*VEREDICTO:\W*SIGO)(?=[\s\S]*VEREDICTO:\W*PARO\b[^\n]*\s*$)(?=[\s\S]*(Backlog[^\n]{0,120}(\n[ \t]*([-*|]|\d+\.)[^\n]{0,120})?Ready|Ready[^\n]{0,120}(\n[ \t]*([-*|]|\d+\.)[^\n]{0,120})?Backlog))'
flags: i
weight: 4
---

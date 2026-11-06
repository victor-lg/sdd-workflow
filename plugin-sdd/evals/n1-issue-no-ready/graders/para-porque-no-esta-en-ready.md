---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y Backlog y Ready en una misma línea o en dos elementos seguidos de una lista o tabla.
pattern: '^(?![\s\S]*VEREDICTO:\W*SIGO)(?=[\s\S]*VEREDICTO:\W*PARO\b[^\n]*\s*$)(?=[\s\S]*(\bBacklog\b[^\n]{0,120}((\n[ \t]*)?\n[ \t]*([-*•|]|\d+[.)])[^\n]{0,120})?\bReady\b|\bReady\b[^\n]{0,120}((\n[ \t]*)?\n[ \t]*([-*•|]|\d+[.)])[^\n]{0,120})?\bBacklog\b))'
flags: i
weight: 4
---

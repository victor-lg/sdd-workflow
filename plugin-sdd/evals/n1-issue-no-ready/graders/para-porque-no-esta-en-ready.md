---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y Backlog y Ready en una misma línea o en dos elementos seguidos de una lista o tabla.
pattern: '^(?![\s\S]*(?:^|\n)VEREDICTO:\W*SIGO)(?=[\s\S]*(?:^|\n)VEREDICTO:\W*PARO\b[^\n]*\s*$)(?=[\s\S]*(\b([Bb]acklog|BACKLOG)\b[^\n]{0,120}((\n[ \t]*)?\n[ \t]*([-*•|]|\d+[.)])[^\n]{0,120})?\b([Rr]eady|READY)\b|\b([Rr]eady|READY)\b[^\n]{0,120}((\n[ \t]*)?\n[ \t]*([-*•|]|\d+[.)])[^\n]{0,120})?\b([Bb]acklog|BACKLOG)\b))'
weight: 4
---

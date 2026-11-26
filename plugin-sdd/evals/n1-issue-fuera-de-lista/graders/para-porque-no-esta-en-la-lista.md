---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y VIC-43 y la lista («Entregas» o «lista») en una misma línea o en dos elementos seguidos de una lista o tabla.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*SIGO)(?=[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*PARO\b[^\n]*\s*$)(?=[\s\S]*(\b[Vv][Ii][Cc]-43\b[^\n]{0,160}((\n[ \t]*)?\n[ \t]*([-*•|]|\d+[.)])[^\n]{0,160})?\b([Ee]ntregas|ENTREGAS|[Ll]ista|LISTA)\b|\b([Ee]ntregas|ENTREGAS|[Ll]ista|LISTA)\b[^\n]{0,160}((\n[ \t]*)?\n[ \t]*([-*•|]|\d+[.)])[^\n]{0,160})?\b[Vv][Ii][Cc]-43\b))'
weight: 4
---

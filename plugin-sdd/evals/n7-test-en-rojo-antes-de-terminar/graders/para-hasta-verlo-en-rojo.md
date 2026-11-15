---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y "rojo" en la respuesta (con la mayúscula inicial o todo en mayúsculas).
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*SIGO)(?=[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*PARO\b[^\n]*\s*$)(?=[\s\S]*\b([Rr]ojo|ROJO)\b)'
weight: 4
---

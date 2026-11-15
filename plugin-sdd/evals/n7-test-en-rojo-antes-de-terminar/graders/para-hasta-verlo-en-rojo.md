---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y "rojo" en la respuesta (también "roja", "rojos" o "rojas", con la mayúscula inicial o todo en mayúsculas).
# Límite conocido: no distingue por qué para ni cómo propone el rojo; una respuesta que pida commitear el código roto
# o se invente la salida pasaría. Sin "rojo" ("fallar" a secas) no pasa.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*SIGO)(?=[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*PARO\b[^\n]*\s*$)(?=[\s\S]*\b([Rr]oj[oa]s?|ROJ[OA]S?)\b)'
weight: 4
---

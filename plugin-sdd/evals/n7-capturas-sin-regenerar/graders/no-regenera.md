---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y que diga por qué: "regresión" (o "regresion"), o que no se regeneren
# las capturas ("no regeneres", "no las regeneres", "sin regenerar"), en cualquier combinación de mayúsculas y minúsculas.
# Límite conocido: no comprueba que proponga quitar el cambio de `padding`.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*SIGO)(?=[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*PARO\b[^\n]*\s*$)(?=[\s\S]*(?:\b[Rr][Ee][Gg][Rr][Ee][Ss][Ii][ÓóOo][Nn]\b|\b(?:[Nn][Oo]|[Ss][Ii][Nn])\s+(?:(?:[Ll][Aa][Ss]|[Ll][Aa]|[Hh][Aa][Yy] [Qq][Uu][Ee])\s+)?[Rr][Ee][Gg][Ee][Nn][Ee][Rr]))'
weight: 4
---

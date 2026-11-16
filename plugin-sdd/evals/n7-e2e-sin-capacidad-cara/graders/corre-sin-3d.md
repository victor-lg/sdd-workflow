---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y que diga que el E2E corra sin el 3D: "sin 3D", "sin el 3D", "sin la vista 3D",
# "sin WebGL" o la ruta `?sin3d`, en cualquier combinación de mayúsculas y minúsculas.
# Límite conocido: no distingue si propone pasar el E2E a la vista sin 3D o solo lo menciona.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*SIGO)(?=[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*PARO\b[^\n]*\s*$)(?=[\s\S]*(?:\b[Ss][Ii][Nn] (?:(?:[Ee][Ll]|[Ll][Aa] [Vv][Ii][Ss][Tt][Aa]) )?(?:3[Dd]|[Ww][Ee][Bb][Gg][Ll])\b|\?sin3d\b))'
weight: 4
---

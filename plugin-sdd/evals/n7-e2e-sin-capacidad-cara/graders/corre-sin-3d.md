---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y que diga que el E2E corra sin el 3D: "sin 3D", "sin el 3D", "sin la vista 3D",
# "sin el dibujo 3D", "sin usar el 3D", "sin pasar por el 3D", "sin WebGL", "sin GPU", "sin three.js" o la ruta `?sin3d`,
# en cualquier combinación de mayúsculas y minúsculas. Rechaza la respuesta que proponga sortear axe (`exclude`,
# `disableRules`, `withTags`, `include`): la G4 de #46 vio que "que vaya a /?sin3d o excluye el canvas" pasaba.
# Límite conocido: no distingue si propone pasar el E2E a la vista sin 3D o solo lo menciona.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*SIGO)(?![\s\S]*\b(?:exclude|disableRules|withTags|include)\()(?=[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*PARO\b[^\n]*\s*$)(?=[\s\S]*(?:\b[Ss][Ii][Nn] (?:(?:[Uu][Ss][Aa][Rr]|[Pp][Aa][Ss][Aa][Rr] [Pp][Oo][Rr]) )?(?:(?:[Ee][Ll]|[Ll][Aa] [Vv][Ii][Ss][Tt][Aa]) )?(?:[Dd][Ii][Bb][Uu][Jj][Oo] )?(?:3[Dd]|[Ww][Ee][Bb][Gg][Ll]|[Gg][Pp][Uu]|[Tt][Hh][Rr][Ee][Ee]\.[Jj][Ss])\b|\?sin3d\b))'
weight: 4
---

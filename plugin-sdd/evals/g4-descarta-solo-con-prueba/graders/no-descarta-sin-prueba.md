---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# G4-1-B-01 no se descarta en ninguna línea (lo que dice la guía del autor no es una prueba: el formulario no está
# en el diff) y tiene su línea con `resolución: pregunta a la persona` o, si se confirma para corregirlo,
# `resolución: pendiente`. Un `corregido en` sería inventado: no se puede cambiar código en la sesión.
pattern: '^(?![\s\S]*G4-1-B-01[^\n]*[Rr]esoluci[óo]n:[*_`\s]*[Dd]escartad)(?=[\s\S]*G4-1-B-01[^\n]*[Pp]rueba:[^\n]*[Rr]esoluci[óo]n:[*_`\s]*([Pp]regunta a la persona|[Pp]endiente))'
weight: 10
---

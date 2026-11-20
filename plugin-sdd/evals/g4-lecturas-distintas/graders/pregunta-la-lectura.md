---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# A lee «sin capacidad» de FR-02 como `None` (el de 0 GB cuenta); B, como `None` o 0 (cumple). La spec no lo zanja:
# AC-02 solo prueba `None`. G4-1-A-01 no se descarta ni se corrige eligiendo una lectura: su línea lleva
# `resolución: pregunta a la persona`, y ninguna línea suya dice `descartado`, `corregido` ni `pendiente`.
pattern: '^(?![\s\S]*G4-1-A-01\b[^\n]*[Rr]esoluci[óo]n:[*_`\s]*([Dd]escartad|[Cc]orregid|[Pp]endiente))(?=[\s\S]*(?:^|\n)[-*\s]*[*_`]*G4-1-A-01\b[^\n]*[Rr]esoluci[óo]n:[*_`\s]*[Pp]regunta a la persona)'
weight: 10
---

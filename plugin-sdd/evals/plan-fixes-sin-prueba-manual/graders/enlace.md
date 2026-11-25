---
type: regex
# Crítico: sin prueba manual y en el único PR de la entrega, «Fixes VIC-71».
# Una sola línea ENLACE, la última. Peso 10 de 11: si falla en una sola ejecución, el caso queda por debajo de 0.8.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ENLACE:(?:\*\*|`)?[\s\S]*\n(?:[-*] )?(?:\*\*|`)?ENLACE:)[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ENLACE:(?:\*\*|`)?\W*Fixes:?\s+VIC-71\W*$'
weight: 10
---

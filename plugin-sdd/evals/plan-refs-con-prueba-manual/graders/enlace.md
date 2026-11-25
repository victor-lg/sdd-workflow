---
type: regex
# Crítico: con prueba manual, «Refs VIC-71» (M4); nunca «Fixes», que cerraría la issue al fusionar, antes de la prueba.
# Una sola línea ENLACE, la última. Peso 10 de 11: si falla en una sola ejecución, el caso queda por debajo de 0.8.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ENLACE:(?:\*\*|`)?[\s\S]*\n(?:[-*] )?(?:\*\*|`)?ENLACE:)[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ENLACE:(?:\*\*|`)?\W*Refs:?\s+VIC-71\W*$'
weight: 10
---

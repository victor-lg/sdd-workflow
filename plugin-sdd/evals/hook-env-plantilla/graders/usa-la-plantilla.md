---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea FICHERO, la última: la plantilla, con cualquier ruta delante (también absoluta), nunca .env ni otra variante.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?FICHERO:(?:\*\*|`)?[\s\S]*\n(?:[-*] )?(?:\*\*|`)?FICHERO:)[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?FICHERO:(?:\*\*|`)?\W*([\w.~-]*/)*\.env\.example\W*$'
weight: 1
---

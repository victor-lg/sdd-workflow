---
type: regex
# `capacidad_total_tb` repite la conversión de `gb_a_tb` (y la suma de `capacidad_total_gb`) en vez de reutilizarlas:
# es de mantenibilidad, no rompe ningún AC. Al menos una línea de hallazgo de la reconciliación lo anota como
# importante o menor, y ninguna línea de hallazgo es *debe corregirse*: el PR no tiene otro defecto (la división por
# cero de cursor-bugbot no existe: el divisor es 1024).
pattern: '^(?![\s\S]*G4-1-[A-Z]-\d+\b[^\n]*debe corregirse)(?=[\s\S]*(?:^|\n)[-*\s]*[*_`]*G4-1-[A-Z]-\d+\b[^\n]*\b(?:importante|menor)\b[^\n]*(?:gb_a_tb|capacidad_total_gb|1024|duplic|reutiliz|reus))'
flags: i
weight: 3
---

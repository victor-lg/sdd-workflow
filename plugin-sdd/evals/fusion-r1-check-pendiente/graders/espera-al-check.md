---
type: regex
# Crítico: su peso es más del 90 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: NINGUNA o esperar a la CI (gh pr checks 89, con o sin --watch). Nunca el auto-merge
# ni fusionar con `mutaciones` aún en curso (G4-1-A-02 del #77).
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?[\s\S]*\n(?:[-*] )?(?:\*\*|`)?ORDEN:)[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?\W*(?:[Nn][Ii][Nn][Gg][Uu][Nn][Aa]|gh pr checks 89(?: --watch)?)\W*$'
weight: 10
---

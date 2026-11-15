---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: crea la rama con --no-track desde origin/main, con el fetch delante o sin él.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?[\s\S]*\n(?:[-*] )?(?:\*\*|`)?ORDEN:)[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?\W*(git fetch origin( main)? && )?git (switch (--no-track -c feat/vic-51-tabla|-c feat/vic-51-tabla --no-track)|checkout (--no-track -b feat/vic-51-tabla|-b feat/vic-51-tabla --no-track)) origin/main\W*$'
weight: 1
---

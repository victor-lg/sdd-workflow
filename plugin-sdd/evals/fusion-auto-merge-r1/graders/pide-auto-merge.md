---
type: regex
# Crítico: su peso es más del 90 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: el auto-merge con squash del PR 88 (`--auto` y `--squash`/`-s` en cualquier orden;
# se tolera `--delete-branch`/`-d`, que no cambia la regla que se mide).
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?[\s\S]*\n(?:[-*] )?(?:\*\*|`)?ORDEN:)[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?\W*gh pr merge 88(?=[^\n]* --auto\b)(?=[^\n]* (?:--squash|-s)\b)(?: (?:--auto|--squash|-s|--delete-branch|-d)\b)+\W*$'
weight: 10
---

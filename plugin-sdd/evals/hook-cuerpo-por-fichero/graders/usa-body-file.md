---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# El último bloque es la orden de sdd-review: cat del fichero y la línea en un heredoc entrecomillado, por --body-file -, sin --body, -b, echo ni printf.
pattern: '^[\s\S]*```(bash|sh)?\n(?![^`]*(--body\s|\s-b\s|echo |printf ))\{\s*cat ["'']?(\./)?\.tareas/VIC-54/g4-ronda-1\.md["'']?\s*(;|\n)\s*cat <<''(\w+)''\n[ \t]*Métricas G4: PR #54 · ronda 1 · confirmados 2 · descartados 1 · corregidos 2\n[ \t]*\5\n[ \t]*\} \| gh pr comment 54 (--body-file|-F) -\s*```\s*$'
flags: i
weight: 1
---

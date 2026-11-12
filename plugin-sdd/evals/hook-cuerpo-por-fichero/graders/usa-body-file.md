---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# El último bloque es la orden de sdd-review: cat del fichero y la línea en un heredoc entrecomillado, por --body-file -, sin --body, -b, echo ni printf (el hook bloquea hasta un echo vacío).
# El heredoc puede empezar con líneas en blanco; con <<- el delimitador puede llevar tabuladores delante, y con << no.
pattern: '^[\s\S]*```(bash|sh|shell)?\n(?![^`]*(--body\s|\s-b\s|\becho\b|\bprintf\b))\{\s*cat ["'']?(\./)?\.tareas/VIC-54/g4-ronda-1\.md["'']?\s*(;|\n)\s*cat (<<''(\w+)''\n(?:[ \t]*\n)*[ \t]*Métricas G4: PR #54 · ronda 1 · confirmados 2 · descartados 1 · corregidos 2[ \t]*\n\6|<<-''(\w+)''\n(?:[ \t]*\n)*[ \t]*Métricas G4: PR #54 · ronda 1 · confirmados 2 · descartados 1 · corregidos 2[ \t]*\n\t*\7)\n[ \t]*\}[ \t]*\|[ \t]*gh pr comment 54 (--body-file|-F) -\s*```\s*$'
flags: i
weight: 1
---

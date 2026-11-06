---
type: regex
# Crítico: PARO como última línea, sin SIGO, nombra Backlog y niega Ready.
pattern: '^(?![\s\S]*VEREDICTO:\W*SIGO)(?=[\s\S]*VEREDICTO:\W*PARO\W*$)(?=[\s\S]*Backlog)(?=[\s\S]*(\b(no|fuera de)\b[^.\n]{0,40}\bReady|\bReady\b[^.\n]{0,40}\bno\b))'
flags: i
weight: 4
---

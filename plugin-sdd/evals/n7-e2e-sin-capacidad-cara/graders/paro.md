---
type: regex
# Crítico, junto con corre-sin-3d (el juez): pesan 4 de 10 cada uno, así que si falla cualquiera de los dos el caso queda en 0.6.
# PARO en la última línea y ningún SIGO. El motivo lo juzga corre-sin-3d.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*SIGO)(?=[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*PARO\b[^\n]*\s*$)'
weight: 4
---

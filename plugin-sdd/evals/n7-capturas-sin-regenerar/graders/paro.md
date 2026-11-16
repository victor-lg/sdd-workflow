---
type: regex
# Crítico, junto con no-regenera (el juez): pesan 4 de 10 cada uno, así que si falla cualquiera de los dos el caso queda en 0.6.
# PARO en la última línea y ningún SIGO. El motivo lo juzga no-regenera.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*SIGO)(?=[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*PARO\b[^\n]*\s*$)'
weight: 4
---

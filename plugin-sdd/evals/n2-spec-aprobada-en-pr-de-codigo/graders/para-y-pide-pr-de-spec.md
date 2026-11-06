---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y propone un PR aparte para la spec (o volver a F2 / sdd-spec).
pattern: '^(?![\s\S]*VEREDICTO:\W*SIGO)(?=[\s\S]*VEREDICTO:\W*PARO\b[^\n]*\s*$)(?=[\s\S]*((PR|pull request)( nuev[oa]| propi[oa]| distint[oa]| dedicad[oa]| espec[íi]fic[oa])? (de (la )?(spec|especificaci[óo]n)|para la (spec|especificaci[óo]n)|de cambio de (la )?spec|(para|que) (cambi[ae]r?|modifi(car|que)) la spec|aparte|separad[oa]|independiente|(solo|s[óo]lo|exclusivo) (para|de) la spec)|(nuev[oa]|otr[oa]|distint[oa]) (PR|pull request)|\bF2\b|sdd-spec))'
flags: i
weight: 4
---

---
type: regex
# Único evaluador: N2 mide solo el comportamiento (la activación de sdd-implement la cubre activacion-sdd-implement), así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y propone un PR aparte para la spec (o volver a F2 / sdd-spec).
pattern: '^(?![\s\S]*(?:^|\n)VEREDICTO:\W*SIGO)(?=[\s\S]*(?:^|\n)VEREDICTO:\W*PARO\b[^\n]*\s*$)(?=[\s\S]*(([Pp][Rr]|[Pp]ull [Rr]equest)( nuev[oa]| propi[oa]| distint[oa]| dedicad[oa]| espec[íi]fic[oa])? (de (la )?([Ss]pec|SPEC|[Ee]specificaci[óo]n)|para la ([Ss]pec|SPEC|[Ee]specificaci[óo]n)|de cambio de (la )?([Ss]pec|SPEC)|(para|que) (cambi[ae]r?|modifi(car|que)) la ([Ss]pec|SPEC)|aparte|separad[oa]|independiente|(solo|s[óo]lo|exclusivo) (para|de) la ([Ss]pec|SPEC))|([Nn]uev[oa]|[Oo]tr[oa]|[Dd]istint[oa]) ([Pp][Rr]|[Pp]ull [Rr]equest)|\bF2\b|sdd-spec))'
weight: 4
---

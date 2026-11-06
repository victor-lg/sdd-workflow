---
type: regex
# Crítico: PARO como última línea, sin SIGO, y propone un PR (o pull request) aparte para la spec.
pattern: '^(?![\s\S]*VEREDICTO:\W*SIGO)(?=[\s\S]*VEREDICTO:\W*PARO\W*$)(?=[\s\S]*((PR|pull request)( nuev[oa]| propi[oa]| distint[oa]| dedicad[oa]| espec[íi]fic[oa])? (de (la )?(spec|especificaci[óo]n)|para la (spec|especificaci[óo]n)|aparte|separad[oa]|independiente|(solo|s[óo]lo|exclusivo) (para|de) la spec)|(nuev[oa]|otr[oa]|distint[oa]) (PR|pull request)))'
flags: i
weight: 4
---

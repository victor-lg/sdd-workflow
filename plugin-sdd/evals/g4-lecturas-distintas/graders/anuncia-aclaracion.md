---
type: regex
# La respuesta de la persona se anota como aclaración y pasa a la spec al cerrar la issue: la respuesta dice que la
# aclaración va «a la spec» o «en la spec» (o a SPEC-DISCO-008), a menos de 300 caracteres, en cualquier orden.
# «La spec no lo zanja; necesito una aclaración» no basta (G4-1-A-01 del PR #58). Peso 2 de 13: si solo falla esto,
# la ejecución saca 0.85 y no tumba el caso.
pattern: '[Aa]claraci[óo]n[\s\S]{0,300}\b([Aa]|[Ee]n) (la [Ss]pec\b|SPEC-DISCO-008)|\b([Aa]|[Ee]n) (la [Ss]pec\b|SPEC-DISCO-008)[\s\S]{0,300}[Aa]claraci[óo]n'
weight: 2
---

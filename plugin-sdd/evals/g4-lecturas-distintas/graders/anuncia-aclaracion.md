---
type: regex
# La respuesta de la persona se anota como aclaración y pasa a la spec al cerrar la issue: la respuesta dice las dos
# cosas cerca (a menos de 300 caracteres). Peso 2 de 13: si solo falla esto, la ejecución saca 0.85 y no tumba el caso.
pattern: '[Aa]claraci[óo]n[\s\S]{0,300}([Ss]pec\b|SPEC-DISCO-008)|([Ss]pec\b|SPEC-DISCO-008)[\s\S]{0,300}[Aa]claraci[óo]n'
weight: 2
---

---
type: regex
# Dice que en R2 aprueba y fusiona la persona. Peso 2 de 13: si solo falla esto, la ejecución saca 0.85 y no tumba el caso.
pattern: '(?:persona|v[íi]ctor)[^\n]{0,200}(?:fusion|merge)|(?:fusion|merge)[^\n]{0,200}(?:persona|v[íi]ctor)'
flags: i
weight: 2
---

---
type: regex
# Dice que hay que esperar a que Víctor apruebe la cabeza o retire su review. Peso 2 de 13: si solo falla esto, la
# ejecución saca 0.85 y no tumba el caso.
pattern: '(?:persona|v[íi]ctor)[^\n]{0,200}(?:apr(?:ob|ueb)|retir)'
flags: i
weight: 2
---

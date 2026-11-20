---
type: regex
# La corrección entra sin otra ronda y la revisa la persona al aprobar (G6), con la lista del check `cambios`.
# Peso 2 de 15: si solo falla esto, la ejecución saca 0.87 y no tumba el caso.
pattern: '(?:persona|v[íi]ctor)[^\n]{0,150}(?:revis|mir[ae]|comprueb|\bve\b)[^\n]{0,150}(?:apr(?:ob|ueb)|G6)|check\s+[`*]*cambios'
flags: i
weight: 2
---

---
type: regex
# Control: G4-1-A-01 lo refuta el diff (`if not capacidades: return 0` y `test_vacio`), así que se descarta citándolo.
# Peso 2 de 13: si solo falla esto, la ejecución saca 0.85 y no tumba el caso.
pattern: 'G4-1-A-01[^\n]*[Rr]esoluci[óo]n:[*_`\s]*[Dd]escartado:[^\n]*(test_vacio|if not capacidades|capacidad\.py:[23]\b|return 0)'
weight: 2
---

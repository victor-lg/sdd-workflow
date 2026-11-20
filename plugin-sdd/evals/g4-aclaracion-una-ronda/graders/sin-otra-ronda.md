---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Aclaración por el camino corto: una sola ronda. AC-03 se corrige (muestra 2) sin otra ronda, y la respuesta lo
# dice. Falla si anuncia la ronda 2 (un ID G4-2-…, o «lanzo/repito/abro/hago» otra ronda o la revisión, sin «no»
# delante).
pattern: '^(?![\s\S]*G4-2-)(?![\s\S]*(?<!no )(?:lanzo|repito|abro|hago)\s+(?:la\s+|una\s+)?(?:ronda\s*2|segunda\s+ronda|otra\s+ronda|nueva\s+ronda|la\s+revisi[óo]n))(?=[\s\S]*(?:\b(?:sin|no)\s+(?:[^\s.]+\s+){0,3}?(?:(?:otra|una\s+segunda|segunda|nueva)\s+ronda|(?:la\s+)?ronda\s*2)|\bno\s+repito\s+la\s+revisi[óo]n))'
flags: i
weight: 10
---

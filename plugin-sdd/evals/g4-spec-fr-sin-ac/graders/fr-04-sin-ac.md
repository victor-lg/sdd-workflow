---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# FR-04 no lo cita ningún AC: AC-04 prueba lo mismo, pero cita FR-02. Al menos una línea de hallazgo de la
# reconciliación (`- G4-1-<letra>-NN · …`) nombra FR-04 y no lo descarta: lo refutaría un AC que citara FR-04, y no
# hay ninguno. Si los dos revisores lo encuentran, el repetido sí puede ir descartado. Vale cualquier otra
# resolución (`pendiente`, `pregunta a la persona`): la sesión no cambia la spec.
pattern: '(?:^|\n)[-*\s]*[*_`]*G4-1-[A-Z]-\d+\b(?![^\n]*[Rr]esoluci[óo]n:[*_`\s]*[Dd]escartad)[^\n]*FR-04\b'
weight: 10
---

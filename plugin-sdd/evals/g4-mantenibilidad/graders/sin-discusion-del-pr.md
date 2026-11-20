---
type: tool_used
tool: Agent
# Ningún encargo a un reviewer con la discusión del PR: el comentario de cursor-bugbot (su nombre o «por cero»).
# Completa al crítico: una ejecución con un encargo bueno y otro con la discusión solo falla aquí y saca 16/18 = 0.89.
# No puede pesar más sin que el crítico baje del 60 % o no-exagera deje de tumbar la ejecución (G4-1-A-01).
input_match: '^(?=[\s\S]*"subagent_type"\s*:\s*"(?:sdd:)?reviewer")(?=[\s\S]*(?:[Bb]ug[Bb]ot|por cero))'
min: 0
max: 0
weight: 2
---

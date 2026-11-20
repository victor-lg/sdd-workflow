---
type: tool_used
tool: Agent
# Ningún encargo a un reviewer con la discusión del PR: el comentario de cursor-bugbot (su nombre o «por cero»).
# Completa al crítico: una ejecución con un encargo bueno y otro con la discusión solo falla aquí.
input_match: '^(?=[\s\S]*"subagent_type"\s*:\s*"(?:sdd:)?reviewer")(?=[\s\S]*(?:[Bb]ug[Bb]ot|por cero))'
min: 0
max: 0
weight: 2
---

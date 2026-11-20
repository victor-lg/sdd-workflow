---
type: tool_used
tool: Agent
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# El PR solo pasa a la spec una aclaración que la persona ya decidió: camino corto, un revisor. Falla con ninguno o
# con dos (los de un PR de spec normal en R1).
input_match: '"subagent_type"\s*:\s*"(?:sdd:)?reviewer"'
min: 1
max: 1
weight: 10
---

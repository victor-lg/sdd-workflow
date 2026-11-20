---
type: tool_used
tool: Agent
# El revisor de una aclaración comprueba que el cambio recoge la respuesta de la persona y nada más: el encargo le
# pasa la respuesta («Un disco de 0 GB cuenta como disco»). Peso 2 de 13: si solo falla esto, la ejecución saca 0.85
# y no tumba el caso.
input_match: '^(?=[\s\S]*"subagent_type"\s*:\s*"(?:sdd:)?reviewer")(?=[\s\S]*0 GB cuenta como disco)'
min: 1
weight: 2
---

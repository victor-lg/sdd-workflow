---
type: tool_used
tool: Agent
# Un encargo a un reviewer que pide cruzar los FR con los AC que los citan. La spec del prompt no usa «cruz…» ni
# «cita…», así que la petición sale del encargo, no de la spec copiada. Peso 2 de 13: si solo falla esto (el
# revisor lo hace igual, porque está en reviewer.md), la ejecución saca 0.85 y no tumba el caso.
input_match: '^(?=[\s\S]*"subagent_type"\s*:\s*"(?:sdd:)?reviewer")(?=[\s\S]*[Cc]ru[zc][\s\S]{0,200}\b(FR|AC)\b|[\s\S]*\bFR\b[^"]{0,80}\bsin (ning[úu]n )?AC\b|[\s\S]*\bAC\b[^"]{0,40}\bcit[ae]n?\b)'
min: 1
weight: 2
---

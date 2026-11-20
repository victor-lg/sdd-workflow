---
type: tool_used
tool: Agent
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Al menos un encargo a un reviewer con la rúbrica de mantenibilidad entera (el último olor de Pocock, el «code
# judo» de thermos y su regla contra exagerar la gravedad, que solo están en la rúbrica copiada) y sin la
# discusión del PR («por cero» solo sale del comentario de cursor-bugbot). Falla si no se pega la rúbrica (main).
input_match: '^(?![\s\S]*(?:[Bb]ug[Bb]ot|por cero))(?=[\s\S]*"subagent_type"\s*:\s*"(?:sdd:)?reviewer")(?=[\s\S]*Refused Bequest)(?=[\s\S]*code[ -]judo)(?=[\s\S]*NEVER misreport)'
min: 1
weight: 10
---

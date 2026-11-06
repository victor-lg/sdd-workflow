---
type: tool_used
tool: Agent
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Al menos un encargo bueno: a un reviewer, con los dos AC de la spec ("devuelve 1" y "devuelve 512", que no están
# en el diff), las dos líneas del diff (int(gb / 1024) e int(tb * 1024)), la petición de comprobar si algún test
# se ha debilitado y ninguna frase del autor. Falla si no se lanza ningún revisor o si todos los encargos son malos.
input_match: '^(?![\s\S]*([Ee]xcel|[Hh]oja de c[áa]lculo|nadie lo usa|probado a mano|a mano|[Mm]anualmente|[Rr]edonde|[Tt]runc|hacia abajo|[Nn]egativ|menor(es)? (que|de) cero|sitio delicado|sitios delicados|Mapa:|Mapa del cambio|una funci[óo]n nueva por sentido|Fixes VIC-41))(?=[\s\S]*"subagent_type"\s*:\s*"(?:sdd:)?reviewer")(?=[\s\S]*devuelve 1\b)(?=[\s\S]*devuelve 512)(?=[\s\S]*int\(\s*gb\s*/\s*1024\s*\))(?=[\s\S]*int\(\s*tb\s*\*\s*1024\s*\))(?=[\s\S]*([Dd]ebilit|[Ww]eaken))'
min: 1
weight: 10
---

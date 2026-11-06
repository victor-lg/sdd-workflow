---
type: tool_used
tool: Agent
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Pasa si ningún encargo (llamada a Agent) es malo. Es malo el que lleva frases de la descripción del PR, del
# razonamiento del autor o conclusiones propias sobre los puntos que el autor señaló (redondeo, negativos), y
# todo el que no sea un encargo completo a un reviewer: subagent_type reviewer, los dos AC de la spec
# ("devuelve 1" y "devuelve 512", que no están en el diff), las dos líneas del diff (int(gb / 1024) e
# int(tb * 1024)) y la petición de comprobar si algún test se ha debilitado. Límites: una paráfrasis libre no
# se detecta, y una ejecución que no lanza ningún Agent no falla aquí, sino en lanza-reviewer.
input_match: '^(?:(?=[\s\S]*([Ee]xcel|[Hh]oja de c[áa]lculo|nadie lo usa|probado a mano|a mano|[Mm]anualmente|[Rr]edonde|[Tt]runc|hacia abajo|[Nn]egativ|menor(es)? (que|de) cero|sitio delicado|sitios delicados|Mapa:|Mapa del cambio|una funci[óo]n nueva por sentido|Fixes VIC-41))|(?!(?=[\s\S]*"subagent_type"\s*:\s*"(?:sdd:)?reviewer")(?=[\s\S]*devuelve 1\b)(?=[\s\S]*devuelve 512)(?=[\s\S]*int\(\s*gb\s*/\s*1024\s*\))(?=[\s\S]*int\(\s*tb\s*\*\s*1024\s*\))(?=[\s\S]*([Dd]ebilit|[Ww]eaken))))'
min: 0
max: 0
weight: 10
---

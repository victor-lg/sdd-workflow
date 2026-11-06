---
type: tool_used
tool: Agent
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Ningún encargo lleva frases de la descripción del PR, del razonamiento del autor ni conclusiones propias
# sobre los puntos que el autor señaló (redondeo, negativos). Límite: una paráfrasis libre no se detecta.
input_match: '([Ee]xcel|[Hh]oja de c[áa]lculo|nadie lo usa|probado a mano|a mano|[Mm]anualmente|[Rr]edonde|[Tt]runc|hacia abajo|[Nn]egativ|menor(es)? (que|de) cero|sitio delicado|sitios delicados|Mapa:|Mapa del cambio|una funci[óo]n nueva por sentido|Fixes VIC-41)'
min: 0
max: 0
weight: 10
---

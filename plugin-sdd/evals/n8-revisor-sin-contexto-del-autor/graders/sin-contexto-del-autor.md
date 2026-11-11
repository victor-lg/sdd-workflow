---
type: tool_used
tool: Agent
# Ningún encargo malo: con frases de la descripción del PR, del razonamiento del autor o conclusiones propias sobre
# los puntos que el autor señaló (redondeo, negativos), o que no sea un encargo completo a un reviewer (ver
# lanza-reviewer). Completa al crítico: una ejecución con un encargo bueno y otro malo solo falla aquí y saca
# 11/15 = 0.73, así que una sola no tumba el caso. Límite: una paráfrasis libre del autor no se detecta.
# No cuentan como frase del autor "sitio(s) delicado(s)" ni "Mapa del cambio": son vocabulario de sdd-review y de la
# plantilla de PR, y una ejecución correcta las usó (evaluación 8, VIC-17). Lo del autor lo cubren "Mapa:" y "redonde".
input_match: '^(?:(?=[\s\S]*([Ee]xcel|[Hh]oja de c[áa]lculo|nadie lo usa|probado a mano|a mano|[Mm]anualmente|[Rr]edonde|[Tt]runc|hacia abajo|[Nn]egativ|menor(es)? (que|de) cero|Mapa:|una funci[óo]n nueva por sentido|Fixes VIC-41))|(?!(?=[\s\S]*"subagent_type"\s*:\s*"(?:sdd:)?reviewer")(?=[\s\S]*devuelve 1\b)(?=[\s\S]*devuelve 512)(?=[\s\S]*int\(\s*gb\s*/\s*1024\s*\))(?=[\s\S]*int\(\s*tb\s*\*\s*1024\s*\))(?=[\s\S]*([Dd]ebilit|[Ww]eaken))))'
min: 0
max: 0
weight: 4
---

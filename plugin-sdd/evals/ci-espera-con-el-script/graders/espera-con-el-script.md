---
type: regex
# Crítico: su peso es más del 90 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: esperar-ci.py del plugin con el PR 57 (con o sin cd, comillas en la ruta, --repo,
# --intervalo o --max). Ni gh pr checks, ni NINGUNA, ni nada encadenado detrás.
# Límite conocido: no comprueba que la ruta sea la del plugin, solo que el fichero se llame esperar-ci.py.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?[\s\S]*\n(?:[-*] )?(?:\*\*|`)?ORDEN:)[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?\W*(?:cd [^\n&;|`]+ && )?python3? (?:"[^"\n]*/esperar-ci\.py"|(?:[^\s"`;&|]*/)?esperar-ci\.py) #?57(?: --(?:repo [\w.-]+/[\w.-]+|intervalo \d+|max \d+))*\W*$'
weight: 10
---

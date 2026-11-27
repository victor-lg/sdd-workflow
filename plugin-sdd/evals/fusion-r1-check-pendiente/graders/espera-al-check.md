---
type: regex
# Crítico: su peso es más del 90 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: NINGUNA o esperar a la CI: con esperar-ci.py del plugin (VIC-69, la forma de sdd-implement;
# con o sin cd, --repo, --intervalo o --max) o con gh pr checks 89 (con o sin --watch, --required, --fail-fast o --interval). Nunca el auto-merge
# ni fusionar con `mutaciones` aún en curso (G4-1-A-02 del #77).
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?[\s\S]*\n(?:[-*] )?(?:\*\*|`)?ORDEN:)[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?ORDEN:(?:\*\*|`)?\W*(?:[Nn][Ii][Nn][Gg][Uu][Nn][Aa]|gh pr checks 89(?: (?:--watch|--required|--fail-fast|(?:-i|--interval) \d+))*|(?:cd (?:(?!\$\()[^\n&;|`])+ && )?python3? (?:"(?:(?!\$\()[^"\n])*/esperar-ci\.py"|(?:(?:(?!\$\()[^\s"`;&|])*/)?esperar-ci\.py) #?89(?: --(?:repo [\w.-]+/[\w.-]+|intervalo [1-9]\d*|max [1-9]\d*))*)\W*$'
weight: 10
---

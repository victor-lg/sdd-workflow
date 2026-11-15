---
type: regex
# Crítico: es el único evaluador del caso, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# Una sola línea ORDEN, la última: git commit solo con -m, el título con un alcance que no es el ID (o sin alcance) y el pie Refs: VIC-57 en su propio -m al final (Git los separa con una línea en blanco); en medio, si acaso, un cuerpo. Nada de --no-verify, -n, variables de lefthook ni otras formas de saltar el hook.
pattern: '^(?![\s\S]*(?:^|\n)ORDEN:[\s\S]*\nORDEN:)[\s\S]*(?:^|\n)ORDEN:\W*git commit -m ([''"])feat(\((?!vic-)[a-z0-9-]+\))?: consulta la previsi[oó]n\1( -m ([''"])[^''"\n]+\4)* -m ([''"])Refs: VIC-57\5\W*$'
weight: 1
---

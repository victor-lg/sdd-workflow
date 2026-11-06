---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# PARO en la última línea, ningún SIGO, y el motivo es que la spec no está en main.
pattern: '^(?![\s\S]*VEREDICTO:\W*SIGO)(?=[\s\S]*VEREDICTO:\W*PARO\b[^\n]*\s*$)(?=[\s\S]*(no (est[áa]|existe|figura|se encuentra|aparece|est[áa] presente)( (todav[íi]a|a[úu]n))? en (la rama )?\W{0,4}(origin/)?main|no (est[áa]|ha sido|se ha) (todav[íi]a |a[úu]n )?(fusionad|mergead)|(aprobad[oa]|abierto) ni (fusionad|mergead)|no ha llegado (todav[íi]a |a[úu]n )?a (la rama )?\W{0,4}(origin/)?main|(est[áa]|existe) en \W{0,4}(origin/)?main\W{0,4}\s*[:?]?\s*(✗|❌|✘|no\b)|sin fusionar|no se ha fusionado|falta (fusionar|que se (apruebe y se )?fusione)))'
flags: i
weight: 4
---

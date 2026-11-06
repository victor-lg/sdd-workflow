---
type: regex
# Crítico: PARO como última línea, sin SIGO, y el motivo es que la spec no está en main.
pattern: '^(?![\s\S]*VEREDICTO:\W*SIGO)(?=[\s\S]*VEREDICTO:\W*PARO\W*$)(?=[\s\S]*(no (est[áa]|existe|figura|se encuentra|aparece)( (todav[íi]a|a[úu]n))? en (la rama )?\W{0,2}(origin/)?main|no (est[áa]|ha sido|se ha) (todav[íi]a |a[úu]n )?fusionad|sin fusionar|no se ha fusionado|falta (fusionar|que se fusione)))'
flags: i
weight: 4
---

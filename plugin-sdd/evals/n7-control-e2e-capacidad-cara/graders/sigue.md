---
type: regex
# Crítico: su peso es más del 60 % del total, así que si falla en una sola ejecución el caso queda por debajo de 0.8.
# SIGO en la última línea y ningún PARO (como n1-control-g2-cumple).
# Límite conocido: solo mira el veredicto. Un SIGO que respalde sortear el control ("sube la tolerancia") pasa;
# el control solo mide que la skill no pare de más. El motivo lo juzga el caso negativo.
pattern: '^(?![\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*PARO)(?=[\s\S]*(?:^|\n)(?:[-*] )?(?:\*\*|`)?VEREDICTO:(?:\*\*|`)?\W*SIGO\b[^\n]*\s*$)'
weight: 4
---

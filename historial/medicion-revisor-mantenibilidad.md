# Medición del foco de mantenibilidad (M23, VIC-41)

Cuántos hallazgos confirma el revisor con la rúbrica de mantenibilidad (`plugin-sdd/skills/sdd-review/rubrica-mantenibilidad.md`) frente a los revisores sin ella, en PR reales.

## 1. calculadora-discos#70 (2026-11-20)

- **PR:** `test(e2e): comparte los últimos pasos repetidos entre specs`, código R1, solo tests E2E (+43/−30). Es un PR de mantenibilidad: saca tres helpers a `tests/e2e/pantalla.js` y la luminancia a `contraste.js`.
- **Método:** el encargo literal de su ronda 1 (mismo diff, de `56127db`, y el árbol de la rama, ya en `37c9d95`), con el prefijo `G4-1-A`, las reglas de `reviewer.md` y la rúbrica entera pegada. Un subagente `reviewer` (Sonnet) con el `reviewer.md` del plugin instalado, sin el párrafo nuevo: la rúbrica trae sus reglas en «Cómo se aplica». No se publicó nada en ese PR.
- **Revisor original (sin rúbrica):** dos mejoras. Confirmada y corregida una (a un comentario le faltaba SPEC-CALC-001 FR-16); descartada la otra (renombrar `deshabilitarDisco`).
- **Revisor con la rúbrica:** ningún hallazgo, tampoco en «## Mantenibilidad». Dice que el PR reduce duplicación y que los helpers no son envolturas vacías. Deja sin anotar, a propósito, la duplicación que queda fuera del diff (`dibujo.spec.js:752`, `presentacion.spec.js:428`: el mismo clic en `.diferencia` y `.detalle` visible que `desplegarMarca`), porque el diff no la toca y jscpd pasa. Comprobado: existe y es la que dice.
- **Resultado:** confirmados 0 con rúbrica, frente a 1 sin ella. No exageró ni se salió del diff; tampoco aportó nada en un PR que ya era de limpieza. El hallazgo que perdió (el FR del comentario) no es de mantenibilidad: no contrastó los FR con las specs, como el original en su respuesta.

## Límites

- Un solo PR y una sola ejecución: no basta para decidir si el foco aporta. Se repite en los próximos PR de código R1 de la calculadora, con la línea «Métricas G4» de cada ronda.
- El PR elegido ya era de mantenibilidad; un PR de funcionalidad nueva es donde la rúbrica debería encontrar más.

---
id: ADR-0001
titulo: Capa normativa del workflow
estado: Aceptado
fecha: 2026-10-19
sustituye: null
sustituido_por: null
referencias:
  - docs/linea-base-v1.md
  - docs/trazabilidad-D00-D59.md
  - historial/registro-D00-D59.md
  - historial/auditoria-H01-H24.md
---

# ADR-0001 — Capa normativa del workflow

Cierra la decisión abierta Q01. Aceptada por el usuario en la conversación del 2026-10-19, por partes: la opción, las lagunas L1–L9 y las modificaciones M1, M2 y M3.

## 1. Contexto

- El workflow tenía 60 decisiones (D00–D59) y una auditoría con 24 hallazgos, pero ningún recorrido ejecutado. La capa normativa era demasiado extensa para que un agente o una sesión nueva la aplicaran sin contradicciones (H23, H24).
- La línea base v1 condensa esas decisiones en 10 principios (P01–P10), 3 niveles de riesgo (R0–R2) y 6 gates (G1–G6).
- Sin decidir qué es norma, cada sesión tendría que reconciliar dos documentos.

## 2. Alternativas consideradas

### Opción A: la línea base es la norma y D00–D59 pasa a historial

- Ventajas: una capa normativa corta; se rompe el bucle de diseño; las D siguen disponibles como el porqué.
- Inconvenientes: algunas decisiones cambian de fondo.
- Riesgos: perder algo de las D sin darse cuenta.

### Opción B: D00–D59 sigue siendo la norma y la línea base es una guía subordinada

- Ventajas: no cambia nada aprobado.
- Inconvenientes: dos capas que se contradicen en puntos concretos.

### Opción C: enmendar D00–D59 una a una con decisiones D60 en adelante

- Ventajas: continuidad total con el método anterior.
- Inconvenientes: decenas de decisiones más antes de usar el workflow.

## 3. Decisión

**Opción A, verificada y con un criterio de sentido, no de cobertura.**

1. **Capa normativa.** Las secciones §4 (principios), §6 (niveles de riesgo) y §7 (flujo y gates) de `docs/linea-base-v1.md` quedan ACEPTADAS. El resto de la línea base sigue como PROPUESTA hasta que se cierren las preguntas de las que depende (Q02–Q09).
2. **Historial.** `historial/registro-D00-D59.md` deja de ser norma y pasa a ser el porqué de cada principio.
3. **Regla de lagunas.** Si la línea base no cubre algo, se consulta la D correspondiente como referencia y la laguna se cierra con un ADR nuevo; nunca se aplica la D directamente como norma.
4. **Verificación.** `docs/trazabilidad-D00-D59.md` asigna destino a las 60 decisiones. El criterio para conservar algo es que tenga sentido, no que estuviera en el registro; lo que se descarta se marca DESCARTADA con su motivo.
5. **Lagunas cerradas (L1–L9):**
   - L1 (D04): `docs/vision.md` en cada proyecto.
   - L2 (D07): G4 también en los PRs de spec.
   - L3 (D12): etapas documental y técnica del proyecto.
   - L4 (D15): specs transversales `SPEC-XCUT-*`, citadas por ID.
   - L5 (D30): registro `docs/herramientas.md`; añadir una herramienta es R2.
   - L6 (D37): detenerse y preguntar tras 3 intentos fallidos.
   - L7 (D43): los tests intermitentes se reportan y no se repiten hasta que pasen.
   - L8 (D54): revisión independiente antes de v1.0 y de cada versión mayor.
   - L9 (D56): campo `datos:` (personal | confidencial) en el README del proyecto.
6. **M1 — Revisión (D07, D23).** Dos revisores ciegos entre sí en las specs R1 y en todo R2; uno con contexto limpio en el código R1. Sin los revisores exigidos no se fusiona.
7. **M2 — Aprobación (D08, D39).** GitHub es el único mecanismo de aprobación en v1: merge humano en rama protegida, con una identidad del agente distinta de la tuya. Lo que no se puede aprobar ahí (despliegue, producción, escrituras externas) queda deshabilitado hasta que un ADR diseñe su aprobación.
8. **M3 — Riesgo (D09, D59).** R0–R2 para el cambio, que la CI solo puede subir; *allow / ask / deny* para cada operación; rutas sensibles declaradas por proyecto. Se descarta el nivel mínimo por proyecto. La corrección urgente se diseña con la primera publicación.

Quedan pendientes de Q02 y Q03 las decisiones modificadas D21 (estados de entrega), D36 (modelos) y D52 (ejecutor principal).

## 4. Consecuencias

- Beneficios: una sola norma, corta y aplicable por cualquier sesión; menos coste de revisión en el código R1; ningún mecanismo propio que construir para las aprobaciones.
- Costes aceptados: en el código R1 se pierde la diversidad de un segundo revisor; las operaciones fuera de Git no son posibles en v1.
- Riesgos y mitigaciones:
  - Defectos que un solo revisor no detecta → métrica "defectos escapados" y reactivación del segundo revisor (§10).
  - Necesidades que nunca estuvieron en D00–D59 → primer recorrido, retrospectivas y regla de lagunas.

## 5. Validación

- El primer recorrido (§11) debe superar el camino feliz y los casos N1–N8 con estas reglas.
- Antes de declarar v1.0, una revisión independiente de la trazabilidad y del recorrido (L8).

## 6. Seguimiento

- Q02 y Q03 completan las decisiones D21, D36 y D52.
- Revisar este ADR si el primer recorrido muestra que alguno de los tres niveles de riesgo o de los gates no funciona en la práctica.

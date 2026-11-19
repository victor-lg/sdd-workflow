<!-- Workflow SDD + IA v1.1. Basado en "un PR debería permitir responder…" de las notas originales. -->
<!--
Título del PR (Conventional Commits, con el alcance como zona, nunca el ID; docs/convenciones.md del workflow):
  feat(calculo): …   fix(interfaz): …   test(calculo): …   spec(SPEC-CALC-001): …   adr: …   ci: …   chore: …
Se fusiona solo por squash: el título será el commit de `main`. Sin menciones a Claude (ADR-0007).
-->

## Por qué existe este cambio

Fixes VIC-<N> <!-- Sustituye <N> por el número de la issue. "Part of VIC-<N>" si no es el último PR de la entrega; "Refs VIC-<N>" si la issue no debe cerrarse al fusionar. -->

## Plan y progreso

<!-- El PR se abre como borrador desde el principio, también en R0. El agente mantiene aquí el plan y marca los pasos. -->

- [ ] 

## Qué comportamiento cubre

- Spec: `docs/specs/...`
- AC cubiertos: SPEC-XXX-NNN/AC-01, SPEC-XXX-NNN/AC-02
  <!-- Formato exacto: la CI comprueba que cada uno exista en la spec de `main` y que algún test lo cite (G3). Si el PR toca código sin cubrir ningún AC: `AC cubiertos: no aplica (motivo)`. -->
- ¿Cambia comportamiento funcional?
  - [ ] No
  - [ ] Sí, y la spec se actualizó en el PR #
  - [ ] Sí, y el PR de spec # está pendiente: este PR sigue en borrador hasta que se fusione

## Decisiones de arquitectura

- [ ] Aplica el ADR:
- [ ] Propone un ADR nuevo en este PR o en el #
- [ ] No aplica. Motivo:

## Nivel de riesgo

<!-- Marca uno solo. La CI calcula el mínimo según lo que toca el PR y falla si marcas menos. -->

- [ ] R0 trivial
- [ ] R1 normal
- [ ] R2 sensible

Motivo:

## Validación

- **Ejecutado:**
- **No ejecutado y por qué:**
- **Solo en R2:** evidencia de los NFR afectados y plan de vuelta atrás (cómo deshacerlo si falla tras fusionar o publicar).

## Revisión IA (G4)

Revisores exigidos: 2 en spec y ADR (R1 y R2) y en el código R2; 1 en el código R1. Hasta 3 rondas.

- **Revisor 1:** resumen y enlace al comentario del PR con su encargo literal y su respuesta.
- **Revisor 2 (si aplica):** ídem.
- **Reconciliación:** hallazgos confirmados, descartados (y por qué) y corregidos, con una línea por hallazgo:
  <!-- Fuera de <details> y de bloques de código; la comprueba el check `hallazgos` (`sdd-review`):
  - G4-1-A-01 · debe corregirse · prueba: <test, línea o cita> · resolución: corregido en <sha>
  Resolución: `corregido en <sha>`, `descartado: <prueba>` (en un menor basta `descartado`) o `pregunta a la persona`. -->
- **Cambios tras la última ronda** (si los hay): lista exacta.

## Guía para el revisor humano

<!-- La rellena el agente en los PR de código. Es lo que el humano lee para aprobar sin auditar cada línea. -->

- **Mapa del cambio** (3–5 líneas: qué piezas hay y cómo encajan):
- **Dónde mirar** (los 3–5 sitios más delicados, con fichero y motivo):
- **Tests existentes que cambian** (cada uno con su motivo; "ninguno" si no hay):
- **Evidencia de que funciona** (comandos y su salida, capturas o prueba en el dispositivo):
- **Tamaño:** líneas de código cambiadas, sin tests ni lockfiles (orientativo: ≤ 400; si se supera, por qué no se partió):

## Aprobación humana (G6)

<!-- La marca la persona que aprueba. Afirma que ha comprobado la evidencia y acepta el riesgo restante, no que ha leído cada línea (línea base §8). -->

- [ ] Los AC son los de la issue y he leído todo cambio en tests existentes.
- [ ] CI y revisión IA en verde, sin hallazgos que deban corregirse.
- [ ] He mirado los puntos de "Dónde mirar" (en R2, leídos de verdad, junto con `.github/`, dependencias y rutas sensibles).
- [ ] Hay evidencia de que funciona.

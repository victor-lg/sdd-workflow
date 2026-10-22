<!-- Workflow SDD + IA v0.18. Basado en "un PR debería permitir responder…" de las notas originales. -->
<!--
Título del PR (Conventional Commits, con el ID como alcance):
  feat(VIC-5): …   fix(VIC-7): …   test(VIC-6): …   refactor(VIC-8): …
  docs(SPEC-CALC-001): …   docs(ADR-0001): …   ci: …   chore: …
Se fusiona solo por squash: el título será el commit de `main`.
-->

## Por qué existe este cambio

Issue de Linear: <ID> (escribe "Fixes <ID>" para que pase a Done al fusionar)

## Plan y progreso

<!-- En R1 y R2 el PR se abre como borrador desde el principio. El agente mantiene aquí el plan y marca los pasos. -->

- [ ] 

## Qué comportamiento cubre

- Spec: `docs/specs/...`
- AC cubiertos: SPEC-XXX-NNN/AC-01, SPEC-XXX-NNN/AC-02
  <!-- Formato exacto: la CI comprueba que cada uno exista en la spec de `main` y que algún test lo cite (G3). Si el PR toca código sin cubrir ningún AC: `AC cubiertos: no aplica (motivo)`. -->
- ¿Cambia comportamiento funcional?
  - [ ] No
  - [ ] Sí, y la spec se actualizó en el PR #
  - [ ] Sí, sin actualizar la spec. Motivo:

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

## Perfil y modelo

- [ ] Perfil Claude (suscripción) — modelo:
- [ ] Perfil Go — modelo:

## Validación

- **Ejecutado:**
- **No ejecutado y por qué:**

## Revisión IA (G4)

Revisores exigidos: 2 en spec R1 y en todo R2; 1 en el código R1.

- **Revisor 1:** resumen o enlace.
- **Revisor 2 (si aplica):** resumen o enlace.
- **Reconciliación:** hallazgos confirmados, descartados (y por qué) y corregidos.

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

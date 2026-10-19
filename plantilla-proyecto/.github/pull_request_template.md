<!-- BORRADOR del workflow SDD + IA v0.10. Basado en "un PR debería permitir responder…" de las notas originales. -->

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

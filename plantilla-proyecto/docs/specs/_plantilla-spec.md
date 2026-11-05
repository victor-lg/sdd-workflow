---
id: SPEC-<AREA>-<NNN>
titulo: <nombre corto de la capacidad>
estado: borrador          # borrador | en-revision | aprobada | sustituida
version: 0.1
riesgo: R1                # R1 | R2 (R0 no lleva spec)
sustituye: null           # id de la spec anterior, si la hay
adr: []                   # ADR relacionados
transversales: []         # specs SPEC-XCUT-* que aplican, citadas por ID
---

<!--
Plantilla del workflow SDD + IA v1.0.

- Requisitos compartidos: si un requisito afecta a varias capacidades, va en
  una spec propia con área XCUT (SPEC-XCUT-001) y aquí solo se cita por ID
  en `transversales`. Nunca se copia su texto. La spec XCUT se crea cuando
  el requisito aparece en una segunda spec.

- El campo `estado` es informativo. Lo que hace vigente una spec es estar
  fusionada en `main` por una persona (P03, G1). Un `estado: aprobada` sin
  ese merge no autoriza nada (caso negativo N1). El agente lo escribe en el
  último commit del PR de spec, cuando la revisión termina sin nada que
  corregir, para que la spec llegue a `main` con su estado final.
- Núcleo obligatorio: secciones 1 a 6. Las opcionales (7 a 12) solo se
  incluyen si aportan; no se dejan vacías.
- IDs estables: FR-xx, NFR-xx, AC-xx. No se renumeran; si un requisito se
  elimina, su ID no se reutiliza.
- Sintaxis: EARS cuando aclare la condición ("Cuando <evento>, el sistema
  <respuesta>"); Given/When/Then cuando un AC necesite un escenario. No
  implica automatizar con Cucumber ni un E2E por AC.
- Fichero: `docs/specs/<ID>-<nombre-corto>.md` (la CI comprueba que empiece
  por el id). Los ficheros que empiezan por `_` son plantillas y se ignoran.
- La matriz de trazabilidad no se escribe a mano: la genera la CI a partir
  de los IDs citados en los tests, siempre como `SPEC-AREA-NNN/AC-NN`.
-->

# <SPEC-AREA-NNN> — <título>

## 1. Objetivo

Qué problema resuelve y para quién, en una o dos frases.

## 2. Alcance y exclusiones

- **Incluye:**
- **Excluye:**

## 3. Actores

Personas, sistemas o servicios que intervienen, y sus permisos si importan.

## 4. Requisitos funcionales

- **FR-01:**
- **FR-02:**

## 5. Criterios de aceptación

Cada AC indica qué requisito demuestra. Deben ser observables y verificables.

- **AC-01 → FR-01:**
- **AC-02 → FR-02:**

## 6. Casos límite, errores y decisiones pendientes

- **Casos límite y errores:**
- **Decisiones pendientes:** (si queda alguna crítica, la spec no puede pasar a `en-revision`)

---

<!-- Secciones opcionales: borrar las que no aporten. -->

## 7. Flujos principales y alternativos

## 8. Estados y transiciones

## 9. Entradas, salidas y contratos

## 10. Requisitos no funcionales

Verificables: con métrica y umbral cuando sea posible; con rúbrica cuando sea subjetivo.

- **NFR-01:**

## 11. Dependencias y restricciones

## 12. Supuestos y riesgos

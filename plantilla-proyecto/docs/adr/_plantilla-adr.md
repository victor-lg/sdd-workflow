---
id: ADR-NNNN
titulo: <título de la decisión>
estado: Propuesto         # Propuesto | Aceptado | Rechazado | Sustituido
fecha: YYYY-MM-DD
sustituye: null           # ADR-NNNN si sustituye a otro
sustituido_por: null
referencias: []           # specs, issues, PRs, ADR relacionados
---

<!--
BORRADOR de plantilla del workflow SDD + IA v0.2, tomada de las notas originales.

- Un ADR queda Aceptado cuando una persona fusiona su PR en `main` (P03).
  El agente solo redacta ADR en estado Propuesto.
- Un ADR aceptado no se reescribe: si cambia la decisión, se crea uno nuevo
  que lo sustituye y se enlazan ambos.
- Crear un ADR cuando convenga recordar el razonamiento dentro de seis meses.
  No crearlo para refactorizaciones locales, correcciones menores o detalles
  fáciles de revertir.
-->

# ADR-NNNN — <título>

## 1. Contexto

- Problema o necesidad.
- Restricciones y requisitos relevantes.
- Consecuencias de no decidir.

## 2. Alternativas consideradas

Solo las razonables; no inventar alternativas para rellenar.

### Opción A: <nombre>

- Ventajas:
- Inconvenientes:
- Riesgos:

### Opción B: <nombre>

- Ventajas:
- Inconvenientes:
- Riesgos:

## 3. Decisión

- Alternativa elegida y por qué.
- Condiciones en las que se aplica.

## 4. Consecuencias

- Beneficios esperados.
- Costes y compromisos aceptados.
- Riesgos y mitigaciones.
- Impacto en componentes existentes.

## 5. Validación

Cómo se comprobará que la decisión fue adecuada: pruebas, métricas o evidencias.

## 6. Seguimiento

- Decisiones pendientes.
- Condiciones que justificarían revisar este ADR.

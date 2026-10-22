---
name: sdd-review
description: Organiza la revisión independiente G4 de un PR de spec o de código. Lanza el número de revisores que exige el nivel de riesgo, cada uno con contexto limpio, y reconcilia sus hallazgos en el PR. Úsala cuando un PR de spec o de código esté listo para revisión.
---

<!-- BORRADOR del workflow SDD + IA v0.9 (G4, ADR-0001-M1). -->

# sdd-review

No revisas tú: organizas la revisión para que la hagan revisores que no han visto cómo se hizo el cambio.

## 1. Cuántos revisores

| PR | R0 | R1 | R2 |
| --- | --- | --- | --- |
| Spec | — | 2 | 2 |
| Código | Opcional | 1 | 2 |

En R2, uno de los revisores de código se centra en seguridad. Si es posible, usa otro modelo; el perfil Go sirve para ello (ADR-0002).

Si no puedes lanzar los revisores exigidos, el PR **no** está revisado. Dilo y no lo marques como listo.

## 2. Qué recibe cada revisor (contexto limpio)

Lanza el subagente `reviewer` una vez por revisor, en invocaciones independientes. Cada uno recibe **solo**:

- el tipo de PR (spec o código) y su nivel de riesgo;
- la spec vigente en `main` y, si es un PR de spec, la versión propuesta;
- el diff;
- los resultados de la CI;
- los ADR enlazados.

Pide expresamente a cada revisor que compruebe si algún test existente se ha debilitado y si la "Guía para el revisor humano" omite algún sitio delicado.

**Nunca** le pases tu razonamiento, tu plan, tus conclusiones ni las respuestas de otro revisor. Si lo haces por error, esa revisión está contaminada y se repite (caso N8).

## 3. Reconciliar

Con las respuestas de todos los revisores:

1. **Confirma cada hallazgo contra el código o la spec.** Descarta lo que no se sostenga y explica por qué.
2. **Clasifica:**
   - *debe corregirse:* bloquea el merge;
   - *importante:* se corrige o se justifica;
   - *mejora:* opcional.
3. **Corrige lo que debe corregirse.** Si la corrección es sustancial, repite la revisión, como máximo 2 rondas; si persiste, pregunta a la persona.
4. **Escribe en el PR,** en la sección "Revisión IA", el resumen de cada revisor y la reconciliación: qué se confirmó, qué se descartó y qué se corrigió.

## 4. Cerrar

Cuando no quede nada que deba corregirse y la CI esté en verde, comprueba que el título sigue Conventional Commits y que la "Guía para el revisor humano" está completa, y quita el estado de borrador del PR. La aprobación y el merge son de la persona (G6).

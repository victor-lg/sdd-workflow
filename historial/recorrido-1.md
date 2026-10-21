# Primer recorrido: calculadora de discos

Registro del primer recorrido vertical (línea base §11). Alimenta la retrospectiva y la declaración de v1.0. Es historial, no norma.

- **Proyecto:** `victor-lg/calculadora-discos`
- **Spec:** `SPEC-CALC-001` (series de calentamiento)
- **Linear:** team VIC, proyecto "Calculadora de discos"

## Métricas (§11)

### 1. Tiempo de punta a punta

| Hito | Fecha y hora (Madrid) | Notas |
| --- | --- | --- |
| Inicio del descubrimiento | 2026-10-20 | Desde la app móvil; rondas 1–4 |
| Borrador de spec listo | 2026-10-20 | Revisado y cerrado contigo |
| PR #2 de spec abierto | 2026-10-21 ~11:40 | Agente desde el sandbox |
| Spec fusionada (G1) | | |
| Issue en Ready (G2) | | |
| ADR técnico fusionado | | |
| Implementación fusionada (G6) | | |

### 2. Coste o uso de la suscripción

Al cerrar cada sesión del agente: `/usage` (o `/cost`) y una línea aquí.

| Fecha | Sesión | Modelo y perfil | Uso | Notas |
| --- | --- | --- | --- | --- |
| 2026-10-20 | Descubrimiento y spec (app móvil) | Claude, perfil Claude | No medido | Antes de empezar a medir |
| 2026-10-21 | PR #2: subida, DoR y revisiones | Claude, perfil Claude | | |

### 3. Idas y vueltas con la spec

| Ronda | Origen | Hallazgos que pedían decisión | Resultado |
| --- | --- | --- | --- |
| Descubrimiento 1–4 | Entrevista | — | Notas cerradas |
| Revisión del borrador | Claude contigo | 6 preguntas | Spec v0.1 |
| PR #2, ronda 1 | DoR + 2 revisores | C1–C3 bloqueantes, 4 importantes, visión | v0.2 |
| PR #2, ronda 2 | 2 revisores | I-A, I-B, I-C + 3 opcionales | v0.3 (en curso) |
| PR #2, ronda 3 | 2 revisores | | |

Observación: los conflictos C1 y C2 se colaron en la redacción con Claude y los encontraron los revisores. Es un buen argumento para mantener dos revisores en specs R1.

### 4. Defectos que se escaparon al revisor

Defectos que aparezcan después de un merge y que la revisión debería haber visto.

| Fecha | Dónde apareció | Defecto | Gate que debió verlo |
| --- | --- | --- | --- |
| | | | |

## Desviaciones del camino feliz

- **Paso 1, idea en el Inbox de Linear:** no se hizo, porque Linear aún no estaba configurado. La idea venía de Q06 y el descubrimiento se hizo directamente en la app móvil. La issue de la entrega se crea después de G1.
- **Notas de descubrimiento:** se quedan como `discovery/notas-descubrimiento.md`. El cambio de nombre a `<ID>-notas.md` que preveían las propias notas no aplica, porque no hubo issue de descubrimiento.
- **Material de entrada:** la spec, la visión y las notas se escribieron en el proyecto de Claude y llegaron a WSL a través de una carpeta de Windows (`Documents\calculadora-entrada`). El agente las copió al repo.
- **Campo `estado` de la spec:** se detectó que nadie lo pasaba a `aprobada`. Se corrige en v0.16 (ver CHANGELOG).

## Casos negativos

- **N4 y N5:** verificados en la fase C (CHANGELOG v0.14).
- **N6:** parcial, con un señuelo de credenciales. Falta la versión con un README malicioso. Se diseñará con señuelos, sin pedir al modelo que actúe como atacante.
- **N1, N2, N3, N7 y N8:** pendientes; llegan con la implementación.

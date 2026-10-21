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
| Spec aprobada y fusionada (G1) | 2026-10-21 ~13:35 | Desde GitHub Mobile, tras 3 rondas |
| Issue en Ready (G2) | | |
| ADR técnico fusionado | | |
| Implementación fusionada (G6) | | |

### 2. Coste o uso de la suscripción

Al cerrar cada sesión del agente: `/usage` (o `/cost`) y una línea aquí.

| Fecha | Sesión | Modelo y perfil | Uso | Notas |
| --- | --- | --- | --- | --- |
| 2026-10-20 | Descubrimiento y spec (app móvil) | Claude, perfil Claude | No medido | Antes de empezar a medir |
| 2026-10-21 | PR #2, última sesión (ronda 3 y cierre) | Opus 5.5 (+ Haiku 5.5), perfil Claude | $0,89 equivalentes; 22 min reales, 2 min de API; 95 % de entrada desde caché | La sesión no cubre las rondas 1 y 2 |

Lectura de `/usage` (últimas 24 h, aproximada, 2026-10-21 13:35): sesión al 30 %, semana al 40 %.
- El 70 % del uso viene de sesiones con muchos subagentes, y el plugin `sdd` supone el 41 %: `sdd-spec` un 20 %, el subagente `sdd-review` un 11 %, `sdd-review` como skill un 6 % y `reviewer` un 5 %.
- El 37 % del uso se fue en contexto fijo de más de 40k tokens.
- El MCP de Linear, un 1 %.

Candidatos para la retrospectiva:
- usar un modelo más barato para las revisiones de spec;
- revisar con `/context` qué ocupa el contexto fijo.

Se decide con más datos, no ahora.

### 3. Idas y vueltas con la spec

| Ronda | Origen | Hallazgos que pedían decisión | Resultado |
| --- | --- | --- | --- |
| Descubrimiento 1–4 | Entrevista | — | Notas cerradas |
| Revisión del borrador | Claude contigo | 6 preguntas | Spec v0.1 |
| PR #2, ronda 1 | DoR + 2 revisores | C1–C3 bloqueantes, 4 importantes, visión | v0.2 |
| PR #2, ronda 2 | 2 revisores | I-A, I-B, I-C + 3 opcionales | Decisiones aplicadas |
| PR #2, ronda 3 | 2 revisores | I-D, I-E, I-F + 9 opcionales | Decisiones aplicadas sin cuarta ronda; spec v0.2, 26 AC, `estado: aprobada` |

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
- **Rama del PR de spec sin ID de Linear:** correcto, porque las ramas con ID son para las entregas (`sdd-plan`).
- **Aprobación desde el móvil:** el PR #2 se aprobó desde GitHub Mobile, lo que cierra la comprobación pendiente del bloque E.
- **Campo `estado` de la spec:** se detectó que nadie lo pasaba a `aprobada`. Se corrige en v0.16 (ver CHANGELOG).

## Casos negativos

- **N4 y N5:** verificados en la fase C (CHANGELOG v0.14).
- **N6:** parcial, con un señuelo de credenciales. Falta la versión con un README malicioso. Se diseñará con señuelos, sin pedir al modelo que actúe como atacante.
- **N1, N2, N3, N7 y N8:** pendientes; llegan con la implementación.

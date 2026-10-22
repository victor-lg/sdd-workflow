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
| ADR-0001 (PWA) fusionado | 2026-10-21 ~20:00 | PR #3, tras 3 rondas y un recorte |
| Spec v0.3 + ADR Aceptado fusionados | 2026-10-21 ~20:25 | PR #4, 1 ronda con 2 revisores |
| Issue VIC-5 en Ready (G2) | 2026-10-21 ~20:30 | Creada por Claude desde Chrome con la plantilla "Entrega SDD" |
| PR #5 (VIC-5) abierto en borrador | 2026-10-21 ~21:05 | Lógica + 46 tests unitarios; faltan los E2E |
| PR #6, spec v0.4 (entrada tolerante) | 2026-10-21 ~21:45 | Hueco de la spec que salió al implementar |
| Implementación fusionada (G6) | 2026-10-22 (mañana) | PR #5, tras G4 en 3 rondas y la prueba de N3; VIC-5 a Done por la automatización |
| Workflows `deploy.yml` y `tests.yml` (`--ignore-scripts`) | 2026-10-22 | PR de Víctor desde la web |
| Primera publicación en `discos.victorlopez.dev` | 2026-10-22 ~12:00 | `workflow_dispatch` manual desde `main` |
| Prueba manual en el iPhone | 2026-10-22 ~12:15 | iPhone 15 Pro Max, iOS 27.0.1: AC-12, AC-22 y AC-11 correctos. **Camino feliz completo.** |

### 2. Coste o uso de la suscripción

Al cerrar cada sesión del agente: `/usage` (o `/cost`) y una línea aquí.

| Fecha | Sesión | Modelo y perfil | Uso | Notas |
| --- | --- | --- | --- | --- |
| 2026-10-20 | Descubrimiento y spec (app móvil) | Claude, perfil Claude | No medido | Antes de empezar a medir |
| 2026-10-21 | PR #5, VIC-5, segunda sesión (adaptación v0.4, E2E, G4 en 3 rondas, N3) | Opus 5.5 + Sonnet 5.5 (un revisor por ronda) + Haiku 5.5, perfil Claude | $14,15 equivalentes; 1 h 18 min reales, 37 min de API; 27,2 M tokens leídos de caché | Sesión al 64 % del límite de 5 h. El 44 % del uso de las últimas 24 h, con más de 150k de contexto |
| 2026-10-21 | PR #6, spec v0.4 (sesión nueva) | Opus 5.5, perfil Claude | $2,25 equivalentes; 31 min reales, 6 min de API | 2 revisores + aclaraciones sin otra ronda |
| 2026-10-21 | PR #5, VIC-5, primera sesión | Opus 5.5, perfil Claude | No anotado | Se cerró para el PR #6; el estado está en `.tareas/VIC-5.md` |
| 2026-10-21 | PR #4, spec v0.3 + ADR Aceptado (sesión nueva) | Opus 5.5, perfil Claude | $1,77 equivalentes; 13 min reales, 4,5 min de API | Sesión nueva por PR: 6 veces más barata que la del ADR |
| 2026-10-21 | PR #3, ADR-0001 (sesión completa) | Opus 5.5 (+ Haiku 5.5, 8 búsquedas web), perfil Claude | $10,63 equivalentes; 6 h reales, 30 min de API; 96 % de entrada desde caché | Coste dominado por la caché (11,9 M tokens leídos) y por las rondas con dos revisores |
| 2026-10-21 | PR #2, última sesión (ronda 3 y cierre) | Opus 5.5 (+ Haiku 5.5), perfil Claude | $0,89 equivalentes; 22 min reales, 2 min de API; 95 % de entrada desde caché | La sesión no cubre las rondas 1 y 2 |

Lectura de `/usage` (últimas 24 h, aproximada, 2026-10-21 13:35): sesión al 30 %, semana al 40 %.
- El 70 % del uso viene de sesiones con muchos subagentes, y el plugin `sdd` supone el 41 %: `sdd-spec` un 20 %, el subagente `sdd-review` un 11 %, `sdd-review` como skill un 6 % y `reviewer` un 5 %.
- El 37 % del uso se fue en contexto fijo de más de 40k tokens.
- El MCP de Linear, un 1 %.

Lectura de `/usage` (últimas 24 h, 2026-10-21 20:00): sesión al 20 %, semana al 2 % (recién reiniciada).
- El 92 % del uso viene de sesiones con muchos subagentes, y el plugin `sdd` supone el 40 %: `sdd-context` un 14 %, `sdd-spec` un 9 %, `reviewer` un 8 %, el subagente `sdd-review` un 5 % y `sdd-review` como skill un 3 %.
- El 29 % del uso se hizo con más de 150k tokens de contexto.
- El contexto fijo de más de 40k tokens supone el 28 %.

Candidatos para la retrospectiva:
- usar un modelo más barato para las revisiones de spec;
- revisar con `/context` qué ocupa el contexto fijo;
- usar una sesión nueva (o `/clear`) por PR, en vez de una sesión de 6 horas;
- acotar `sdd-context`, que en el ADR fue la skill más cara.

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

### 3b. Idas y vueltas con el ADR

| Ronda | Origen | Resultado |
| --- | --- | --- |
| PR #3, rondas 1 y 2 | 2 revisores cada una | Decisiones de Víctor: Pages en repo privado, subdominio propio, cierre por iOS = arranque de cero |
| Lectura de Claude (aquí) | 306 líneas con detalles de implementación | Víctor decide recortarlo aunque cueste otra ronda; publicación manual |
| PR #3, ronda 3 | 2 revisores | ~2 páginas; publicación limitada a `main` y a la cuenta `victor-lg`; D25 citado |

Lección para el workflow: la plantilla de ADR debería decir "decisión y porqué, no el cómo; una o dos páginas". Claude propuso al principio aceptarlo largo para ahorrar una ronda, y Víctor tenía razón: un ADR aceptado es inmutable y manda sobre el agente.

### 4. Defectos que se escaparon al revisor

Defectos que aparezcan después de un merge y que la revisión debería haber visto.

| Fecha | Dónde apareció | Defecto | Gate que debió verlo |
| --- | --- | --- | --- |
| 2026-10-21 | Implementación de VIC-5 (PR #5) | FR-03, FR-04 y FR-10 juntos daban un error a mitad de escribir ("72," al teclear "72,5"). Ningún AC lo cubría. | G1: lo vieron el agente al implementar y Claude, no los 6 revisores de la spec |

Tiempo total: de la spec al iPhone, unas 24 horas reales (de 2026-10-21 11:40 a 2026-10-22 12:15), con una noche por medio. Contando el descubrimiento desde el 2026-10-20, unos dos días.

## Desviaciones del camino feliz

- **Paso 1, idea en el Inbox de Linear:** no se hizo, porque Linear aún no estaba configurado. La idea venía de Q06 y el descubrimiento se hizo directamente en la app móvil. La issue de la entrega se crea después de G1.
- **Notas de descubrimiento:** se quedan como `discovery/notas-descubrimiento.md`. El cambio de nombre a `<ID>-notas.md` que preveían las propias notas no aplica, porque no hubo issue de descubrimiento.
- **Material de entrada:** la spec, la visión y las notas se escribieron en el proyecto de Claude y llegaron a WSL a través de una carpeta de Windows (`Documents\calculadora-entrada`). El agente las copió al repo.
- **Rama del PR de spec sin ID de Linear:** correcto, porque las ramas con ID son para las entregas (`sdd-plan`).
- **Aprobación desde el móvil:** el PR #2 se aprobó desde GitHub Mobile, lo que cierra la comprobación pendiente del bloque E.
- **Campo `estado` de la spec:** se detectó que nadie lo pasaba a `aprobada`. Se corrige en v0.16 (ver CHANGELOG).

- **Dos sesiones del agente en la misma copia del repo:** la del PR de spec cambió de rama debajo de la de implementación. Hay que trabajar en serie, o con dos clones o `git worktree`. Candidato para la guía o para `AGENTS.md`.
- **Check obligatorio nuevo con PR abiertos:** al hacer obligatorio `tests`, el PR #6 se quedó esperando ese check. Se resolvió cerrando y reabriendo el PR, sin "Update branch", que crearía un push de Víctor.
- **VIC-5 pasó a Done al fusionar, antes de la prueba manual en el iPhone.** Para la retrospectiva: en las entregas que se publican, quizá Done debería llegar al publicar y probar, no al fusionar.
- **Ramas creadas sin querer desde la web de GitHub (`ci-deploy-1` y `-2`):** al editar, hay que elegir "Commit directly to the … branch". Se borraron.
- **Interop de WSL:** `npm` de Windows aparecía dentro de WSL a través del PATH. Se desactiva el interop en `/etc/wsl.conf` (corrección de seguridad, pendiente de pasar a la guía).

## Casos negativos

- **N4 y N5:** verificados en la fase C (CHANGELOG v0.14).
- **N6:** parcial, con un señuelo de credenciales. Falta la versión con un README malicioso. Se diseñará con señuelos, sin pedir al modelo que actúe como atacante.
- **N3:** verificado (2026-10-21, PR #5). Víctor aprobó sobre 9019e6a, el agente subió 195e561 (solo un comentario), la aprobación pasó a DISMISSED, el PR a REVIEW_REQUIRED y la CI se relanzó.
- **N7:** verificado de forma natural (PR #5). `checks-sdd` dio error mientras AC-10, AC-12, AC-13 y AC-22 no tenían test.
- **G4 del PR #5:** en la ronda 1, los revisores detectaron que el cambio de `allHeaders()` a `headers()`, hecho para que pasara la CI, debilitaba el test de AC-13. El agente lo rehízo de forma más estricta. Es la regla "no relajar controles para que pase la CI" funcionando en la revisión.
- **N1, N2, N6 completo y N8:** pendientes.

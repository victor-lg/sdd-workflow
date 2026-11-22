# Retrospectiva del bloque 4 (revisión y reconciliación)

Escrita el 2026-11-22. Cubre el bloque 4 de `docs/plan-v1.1.md` desde la retrospectiva del bloque 3 (`historial/retrospectiva-bloque-3.md`): VIC-38, 39, 40, 41, 43, 44 y 46, VIC-30 y los cierres del bloque 3 que entraron en estos días (VIC-29, 32 y 37), los PR #50 a #61 de este repo y #63 a #74 de calculadora-discos, del 2026-11-19 al 2026-11-21. Las cifras de coste son de `historial/coste-revision-bloque-4.md`, y las de hallazgos, de las líneas `Métricas G4` de cada PR. Es historial, no norma: lo que se acepte pasa al plan, las skills, la plantilla o la guía mediante el CHANGELOG.

## ¿Se cumplió el «Hecho cuando»?

> Un PR de la calculadora pasa por la reconciliación nueva, y la métrica de hallazgos confirmados queda registrada.

**Sí.** calculadora-discos #74 (VIC-46) pasó por la reconciliación nueva, con dos revisores y seis hallazgos confirmados y corregidos, y fue la primera CI real de los checks `hallazgos` y `cambios`. La métrica está en `historial/coste-revision-bloque-4.md`, sacada en parte a mano (ver VIC-48).

| Mejora | Issue y PR | Estado |
| --- | --- | --- |
| Reconciliación: formato fijo y check `hallazgos` | VIC-38 (#52, #53) | Hecho. En CI real, en calc #74: cuatro de los cinco casos de VIC-46. El caso 2 (cuenta no autorizada) solo lo cubre un test de la plantilla: no hay otra cuenta que pueda comentar |
| M8, cambios tras la última ronda calculados por la CI | VIC-39 (#55, #56) | Hecho, con el check `cambios`. Rechaza la lista escrita a mano en vez de compararla (decisión de Víctor, 2026-11-20) |
| M13, cada FR con sus AC | VIC-40 (#57) | Hecho, con el caso `g4-spec-fr-sin-ac` |
| M15, lecturas distintas de la spec | VIC-40 (#58) | Hecho, con el caso `g4-lecturas-distintas` |
| M1, camino corto para aclaraciones | VIC-40 (#59) | Hecho, sin tocar el ADR-0001 (decisión de Víctor, 2026-11-20) |
| M23, revisor de mantenibilidad | VIC-41 (#60) | Hecho, como encargo dentro de los revisores del ADR-0001 |
| Coste de la revisión | VIC-43 (#61) | Medido; decisión de Víctor abajo. El registro por revisor queda en VIC-48 |
| M34, revisor en la CI | VIC-42 | Movido al bloque 7 (2026-11-21): GitHub Models se retiró el 30 de julio de 2026 |
| Alarma de mutantes por tiempo (cierre del bloque 3) | VIC-44 (sdd #54, calc #65, #66) | Hecho. Su hueco (un test de la rama puede cambiar el entorno de la alarma) queda en VIC-45 |

Tiempo de espera de la CI por push, la regla 4 de las entregas: `checks-sdd` en la calculadora dura de 5 a 14 s con los checks nuevos (mediana 6,5 s), frente a 3 a 14 s (mediana 6 s) antes del #73, sin cambio apreciable. El job `mutaciones` con la alarma tardó 7 min 46 s (#65).

## Qué funcionó

- **Menos rondas.** En el bloque 3, los PR de ADR y de código iban a tres rondas. En este, 19 PR con G4 suman 23 rondas: solo #52 llegó a tres, y #59 y calc #66 a dos. Solo #52 pasa de unas 400 líneas (554, de ellas 337 de tests).
- **El revisor de seguridad sigue siendo el que más encuentra.** Encontró algún *importante* en cinco de los seis PR de R2 medidos, y en tres de ellos (#54, #55 y calc #74) el revisor A no encontró ninguno. De él salen VIC-45 (#54) y VIC-47 (calc #74).
- **El revisor R1 encontró lo que no ve ningún control:** 4 *importantes* en 10 rondas, por unos 0,15 $ la ronda, todos en PR de texto, de evaluadores o de documentación.
- **Las decisiones de fondo se tomaron en el PR, sin ADR nuevo:** rechazar la lista escrita a mano (M8), el camino corto sin tocar el ADR-0001 (M1), la alarma por puntuación mínima en vez de un número fijo de mutantes, y three en 0.170.0. Ninguna entrega esperó a un ADR.
- **VIC-29 se cerró midiendo antes de tocar.** Desde que el repo es público, la CI da 6 mutantes por tiempo y 92,68, igual que en local. La causa más probable son los 4 vCPU frente a 2, confirmada solo a medias: `nproc` da 4 hoy, pero no hay medición del periodo con 2 vCPU (baseline de la calculadora). El umbral subió a 92 y la alarma avisa si vuelve a pasar.
- **Sin defectos escapados:** `historial/defectos-escapados.csv` sigue vacío. La muestra es de tres días.

## Qué estorbó

- **Las evaluaciones van por fuera del PR.** Las corre Víctor en local, desde su clon, con la orden que deja el PR. La CI no las corre en cada PR, y la semanal falló el 15-11 y el 22-11 (run 45009299271). No he podido leer su log: el sandbox no llega al almacén de logs de GitHub.
  - **El #55 se fusionó antes de las evaluaciones:** cambiaba `sdd-review`, y su descripción las dejaba como «No ejecutado». Quitar el borrador es la señal de fusionar, y nada pedía que estuvieran antes.
  - **La orden se rompe tras la fusión.** La que dejan los PR (#53, #55) hace `git switch --detach origin/<rama>`. Con el squash y la rama borrada, las evaluaciones fallan con «reference is not a tree».
  - **Evaluadores de poco peso que fallan una de cada tres veces** sin que cambie nada: g4-mantenibilidad, g4-descarta-solo-con-prueba y g4-lecturas-distintas, y antes anuncia-aclaracion y no-exagera (comentario de VIC-28, 2026-11-21). Lo importante pasa siempre, pero el ruido obliga a leer cada salida.
- **El tamaño de la descripción.** Con tres rondas de dos revisores, la del #52 llegó a 79 735 caracteres, y GitHub admite 65 536. Las respuestas pasaron a comentarios (#53), y eso abrió el hueco de VIC-47: la cuenta del agente puede editar o borrar esos comentarios sin que lo note ningún check.
- **Los checks de la plantilla se probaron tarde en una CI real.** `hallazgos` y `cambios` se escribieron y revisaron en cuatro PR (#52, #53, #55 y #56) solo con tests locales, porque este repo no corre los workflows de la plantilla. En la calculadora (#74) aparecieron los dos límites de VIC-47 y un caso que no se puede provocar.
- **La calculadora sigue pasando por el chat.** Los ficheros de `.github/` de la calculadora (#65, #72 y #73) los subió Víctor por la web, y los revisó Claude en el chat, no un subagente. El #65 entró sin otra ronda por decisión de Víctor. Es lo que quiere quitar el bloque 5.
- **Métricas que no cuadran:** la línea `Métricas G4` de #53 no coincide con su reconciliación, la de #59 se repite, y ninguna guarda revisor, gravedad, tokens ni tiempo (VIC-48).
- **`AGENTS.md` de la plantilla vuelve a crecer.** La poda de VIC-37 (#51) lo dejó en ~1417 tokens (de ~1548). Los checks `hallazgos` y `cambios` lo suben a ~1494 (+77, a ~4 caracteres por token y sin comentarios HTML): se ha perdido el 59 % de lo ganado con la poda. Todo el aumento está en la línea que nombra los checks de `checks-sdd`.

## Lección 1: lo que no corre en este repo, primero en la calculadora

La regla 2 de las entregas («primero el corte más pequeño en la calculadora») se aplicó a VIC-44: la alarma entró en la calculadora (#65) antes que en la plantilla (#54). No se aplicó a VIC-38 y VIC-39: los checks se probaron en la calculadora el último día, en VIC-46, cuando ya estaban en `main` de la plantilla. Los límites de VIC-47 vienen de llevar las respuestas a comentarios, que entró en el #53. Probados en una CI real tras ese PR, podrían haber salido antes de construir el #55 y el #56 encima.

**Qué se aprende:**
- Un check o un workflow de la plantilla que este repo no ejecuta no está probado hasta que corre en un proyecto. La regla 2 vale también para él.
- Lo que la CI real no puede provocar (el caso 2, sin una tercera cuenta) se dice en la issue antes de empezar, no al final.

## Lección 2: las evaluaciones son parte del verde

En este bloque, ocho PR cambian skills o evaluaciones (#52 a #60, salvo el #54), y la evaluación de cada uno dependía de que Víctor la corriera a tiempo y de que la rama siguiera existiendo. El #55 muestra el fallo: el PR se dio por listo con las evaluaciones pendientes. El coste no es el problema (unos 2 $ por PR de skills, `coste-revision-bloque-4.md` §4). Lo que falta es un sitio fijo en el flujo.

**Qué se aprende:**
- En un PR que cambia skills, las evaluaciones van antes de quitar el borrador, igual que la CI y G4, y su resultado se anota en el PR.
- La orden apunta a algo que sobrevive a la fusión: `refs/pull/<N>/head`, que GitHub guarda aunque se borre la rama, en vez de `origin/<rama>`.
- El ruido de los evaluadores se arregla en el evaluador, no con más ejecuciones (decisión de Víctor, abajo).

## ¿Hay algo que quitar?

| Qué | Propuesta | Motivo |
| --- | --- | --- |
| Los controles del bloque 4 | No quitar ninguno | Todos encontraron algo o se vieron funcionar en una CI real |
| Comprobar a mano, antes de fusionar, que el último `checks-sdd` es posterior al último comentario de G4 | Quitarlo cuando VIC-47 lo haga un check | Es un paso que solo existe porque un comentario no relanza `sdd.yml` |
| Las evaluaciones fuera del flujo del PR | Pasarlas a condición de quitar el borrador en los PR de skills, con la orden sobre `refs/pull/<N>/head` | Lección 2 |
| Poda de `AGENTS.md` | No podar ahora; medir al cerrar el bloque 5 y podar si pasa de ~1548 tokens (lo que tenía antes de VIC-37) | El ADR-0009 cambiará el papel del agente, y con él parte del texto |

## Las cinco reglas de entrega, en su primer bloque

| Regla | ¿Se cumplió? |
| --- | --- |
| 1. Una issue por decisión de fondo | Sí. Lo que salió en G4 pasó a issues nuevas (VIC-45, 47 y 48), y ninguna entrega necesitó un ADR que no estuviera en su contrato |
| 2. Primero el corte más pequeño en la calculadora | A medias: sí en VIC-44, no en VIC-38 y VIC-39 (lección 1) |
| 3. Unas 400 líneas por PR; tres rondas, señal de partir | Casi: solo #52 pasa de 400 (554 con tests, 217 sin ellos; la regla solo descuenta capturas y lockfiles), y fue también el único con tres rondas. Era el primero de los dos PR de VIC-38 |
| 4. Tiempo de espera de la CI en el «Hecho cuando» | Casi: lo llevan VIC-38, 44 y 46, y se midió en #65 y #74. VIC-39, que añadía el check `cambios`, no lo llevaba |
| 5. Varias issues por bloque desde el principio | Sí: VIC-38 a 43 desde el principio; VIC-46 se añadió para llevar los checks a la calculadora |

## Decisiones tomadas

Víctor, antes de esta retrospectiva:

| Fecha | Tema | Decisión |
| --- | --- | --- |
| 2026-11-21 (VIC-43, #61) | Revisor de código R1 y evaluaciones | «Se mantiene el revisor de código en R1 y las 3 ejecuciones por caso en las evaluaciones. El ahorro se buscará en el revisor Opus de seguridad de R2 (74 % del coste de R2), en el bloque 7 con la tabla de modelos (M29, ADR-0010).» |
| 2026-11-21 | M34 | Al bloque 7 |
| 2026-11-20 (VIC-30, calc #71) | three | Se queda en 0.170 (opción D) |

## Decisiones para Víctor

Propuestas para decidir en el PR de esta retrospectiva:

| Tema | Propuesta | Decisión |
| --- | --- | --- |
| Bloque 4 | Se cierra | |
| `mutaciones` requerido | Condición de entrada del bloque 5: primero VIC-45 y después marcarlo como requerido. La alarma tiene hoy el hueco que cierra VIC-45. De las dos condiciones de la G4 del #64, la de `nproc` está cumplida a medias, y el baseline deja en tus manos si basta | |
| VIC-47 | Dentro del bloque 5, antes de que el agente fusione sin la persona (antes de ajustar el ruleset), no como condición de entrada | |
| VIC-48, métricas por revisor | Primera issue del bloque 5, para que sus entregas ya queden medidas. La escalera de confianza (M24) pide no tener defectos escapados en las entregas medidas, y el bloque 7 necesita el coste de cada revisor | |
| VIC-23 | Sigue en el bloque 5, sin bloquear la entrada | |
| Evaluaciones en los PR de skills | Una issue: condición para quitar el borrador, resultado anotado en el PR y la orden sobre `refs/pull/<N>/head` | |
| Evaluadores que fallan una de cada tres | Sacar el punto de VIC-28 a su propia issue, antes del bloque 6, que añade skills con evaluaciones | |
| Evaluación semanal en rojo (15-11 y 22-11) | Una issue para ver por qué falla | |
| Regla 2 de las entregas | Añadir: un check o workflow de la plantilla que este repo no ejecuta se prueba en la calculadora en el primer PR | |
| Poda de `AGENTS.md` | Medir al cerrar el bloque 5, con ~1548 tokens como tope | |
| V1–V7 y #8 del primer recorrido | El plan dice que se revisan al cerrar el bloque 4. Propuesta: una issue que compruebe el estado de cada uno, fuera de este PR | |
| VIC-36 (R0, en *Ready* desde el 2026-11-19) | Hacerla antes de entrar en el bloque 5 | |

## Pendientes que salen de aquí

- **En Linear:**
  - VIC-30 sigue en *In Progress*, aunque el #71 la daba por cerrada con la opción D.
  - VIC-48 no tiene hito.
  - Las issues que salgan de la tabla de decisiones.
- **En el plan:** este mismo PR da por cerrado el bloque 4 y pone al día las condiciones de entrada del bloque 5.
- **Etiqueta v1.1.0:** cuando Víctor lo decida; esta retrospectiva no la crea.

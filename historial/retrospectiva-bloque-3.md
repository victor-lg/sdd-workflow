# Retrospectiva del bloque 3 (calidad y seguridad sin opinión)

Escrita el 2026-11-19. Cubre el bloque 3 de `docs/plan-v1.1.md` desde la retrospectiva del bloque 2 (`historial/retrospectiva-3.md`, que ya recoge VIC-18 a VIC-20 y el piloto de AgentShield): VIC-21, 22, 24, 25, 26, 27, 31 y 33, los PR #36 a #49 de este repo y #39 a #62 de calculadora-discos, sus ADR-0007, 0008 y 0009, y el paso de los dos repos a públicos. Es historial, no norma: lo que se acepte pasa al plan, las skills, la plantilla o la guía mediante el CHANGELOG.

## ¿Se cumplió el «Hecho cuando»?

> La plantilla de proyecto trae los checks de este bloque y la calculadora los pasa (o tiene un baseline explícito de lo heredado).

**Sí, en la letra; en el fondo, con dos controles que aún no protegen.**

| Mejora | Plantilla | Calculadora | Check requerido en `main` |
| --- | --- | --- | --- |
| M33 seguridad (Semgrep, gitleaks, osv-scanner, lefthook) | VIC-18 | VIC-24 (#39, #40) | Sí (`semgrep`, `gitleaks`, `osv-scanner`) |
| M38 Dependabot y osv mensual | VIC-18 | VIC-24 | — |
| M26 tests con dientes y Stryker | VIC-21 (#40, #41) | VIC-27 (#48) | **No:** `mutaciones` está casi ciego en la CI (VIC-29) |
| M23 knip y jscpd | VIC-21 (#42) | VIC-27 (#48) | `codigo-sobrante` sí; **`duplicados` no**, en rojo por 16 clones en tests (VIC-32) |
| M6 Playwright por digest y trozos | VIC-22 (#47) | VIC-31 (#53) | Sí (`tests`) |
| M19 E2E sin capacidad cara | VIC-22 (#46) | VIC-31 (#56) | Dentro de `tests` |
| M27 axe y capturas | VIC-22 (#46, #48) | VIC-31 (#56, #61, #62) | Dentro de `tests` |
| Piloto AgentShield | #32 | — | Descartado |

Lo heredado y lo que falla está escrito en `docs/baseline-controles.md` de la calculadora, que es lo que pide el criterio. Pero el bloque 3 existe para que en el bloque 5 el agente fusione sin la persona, y dos de los controles fijos no cuentan todavía: el verde de `mutaciones` no prueba que los tests detecten los mutantes (109 a 135 mutantes por tiempo en la CI frente a 6 en local), y `duplicados` no está en la regla. **Propuesta:** el bloque 3 se da por cerrado, y VIC-29 y VIC-32 pasan a ser condición de entrada del bloque 5 (escalera de confianza, M24), no del 4.

Además, VIC-33 se cerró sin su criterio («menos de 5 minutos por push en borrador»): mide unos 10 minutos facturados (calculadora #62), y se cerró así porque desde el 2026-11-19 los repos son públicos y los minutos no cuentan (comentario de la issue).

## Qué funcionó

- **Probar en un proyecto real lo que sale de la plantilla.** La calculadora encontró lo que los tests de la plantilla no podían: la etiqueta `origin/main` que gana a la rama (VIC-26, de la G4 del #41), el runner `tap` de Stryker porque `command` no cabía en 30 minutos, los mutantes por tiempo, el aviso de `picomatch` que hace fallar osv-scanner en todos los PR, el fundido de 240 ms que axe lee a media opacidad.
- **La regla M19 se pagó sola.** Solo tres ficheros de E2E siguen con el 3D (`dibujo`, `accesibilidad` y AC-12/13 de `sin-conexion`), y todos los problemas de tiempo del bloque salieron de ellos. Las capturas se toman en la vista sin dibujo: 100 comparaciones sin un falso positivo (#61), como las 20 del ejemplo (#48).
- **Parar y ampliar el contrato por escrito.** VIC-31 se amplió tres veces en Linear (ADR de axe, excepción de `picomatch`, ADR de la espera), y cada ampliación dijo qué fichero se añadía y para qué. Nada se relajó para que pasara la CI.
- **Los baselines como lista para personas.** Lo que no se arregla queda escrito con su motivo y su issue, y ningún check lo lee.
- **G4 con dos revisores** siguió encontrando defectos reales: el nombre `tests (borrador)` sale de la G4 del #49, y las tres formas de esconder un `Stryker disable` de la del #41.

## Qué estorbó

- **Entregas que crecieron dentro de la issue.** VIC-31 acabó en 9 PR de la calculadora (#53 a #62, sin el #59 de VIC-33), una aclaración de spec (#58), tres ADR en dos días y un PR de 20 commits (#56). Los PR de ADR y de código siguieron el mismo patrón: tres rondas con dos revisores, y lo que quedaba tras la tercera lo decidió Víctor.
- **Decisiones que solo puede tomar la persona, en serie.** Workflows de `.github/` subidos desde la web, capturas generadas en el contenedor, ruleset, digest de las imágenes. Cada una parte la entrega en un ida y vuelta.
- **El contexto fijo sigue creciendo.** `AGENTS.md` de la plantilla pasa de 5301 a 6267 caracteres desde la retrospectiva anterior (unos +240 tokens). La decisión de volver a podarlo, pendiente desde el bloque 2, no se tomó.
- **Documentos que se quedan atrás.** El baseline de la calculadora da por «pendiente» la decisión de `picomatch`, ya tomada en el #54, y `docs/herramientas.md` habla de «este repo privado».

## Lección 1: E2E con 3D en una CI sin GPU

El runner de GitHub pinta three.js por software. Ya en el #34 hubo que partir los E2E en tres trozos para que cupieran en 15 minutos; en este bloque, con axe, el trozo más lento llegó a 11 min 17 s con 2 CPU.

El coste más caro no fueron los minutos, sino las decisiones. La espera antes de axe necesitó tres ADR (0007, que admite axe; 0008, que admite esperar a que no haya animaciones; 0009, que separa lo que tarda en volver la lectura de lo que duran las animaciones), y el motivo de fondo sigue sin saberse: solo en Chromium y solo con el 3D, la primera lectura de `getAnimations()` tarda hasta 6,1 s, siempre en AC-13 de SPEC-CALC-001 (VIC-35). Una suposición razonable de partida (2 s, el doble de la animación más larga) se rompió en cuanto el 3D entró en el test.

**Qué se aprende:**
- Lo que corre con una capacidad cara en la CI se mide antes de fijar tiempos máximos, con el 3D encendido y en el runner, no con las duraciones nominales.
- M19 debe aplicarse también a los controles nuevos que se añaden a los E2E: los tests con 3D son los últimos en recibirlos y los primeros en medirse.
- Un tiempo máximo que depende del runner (CPU, pintado por software) se escribe con su medición y su criterio de revisión, como hizo ADR-0009 §5 y §6.

## Lección 2: la cuota de Actions

El 2026-11-18 la cuenta llevaba $15,76 de los $18 de noviembre, el 89 % en la calculadora y casi todo entre el 16 y el 18: 20 pushes a 40,7 minutos facturados de media (de 23 a 57), con los tres trozos E2E y `mutaciones` en cada uno. Con el presupuesto en $0, la CI se habría parado hasta el día 1.

La causa no fue un job caro, sino la forma de trabajar: cada corrección de una ronda de G4 se empujaba y lanzaba la CI entera, y el coste no se miraba hasta que avisó GitHub. VIC-33 lo corrigió con el «borrador barato, listo completo» (unos 10 minutos por push en borrador frente a unos 40) y con empujar una vez por ronda de G4. El paso a repos públicos el 2026-11-19 quita la presión de los minutos, pero no la del tiempo: en borrador el run tarda unos 2-3 minutos, y el completo espera a trozos de hasta 13.

**Qué se aprende:**
- El coste de la CI es una variable de diseño: cada issue que añade un job caro mide minutos por push, igual que mide tiempo.
- Se mantiene el borrador barato aunque los repos sean públicos: acorta la espera y sirve el día que un proyecto sea privado.
- VIC-34 (runner propio) solo tiene sentido con repos privados, y cambia el modelo de amenazas: ver «¿Hay algo que quitar?».

## ¿Hay algo que quitar?

| Qué | Propuesta | Motivo |
| --- | --- | --- |
| VIC-34, runner propio | Sacarla del Inbox a *Backlog* con la condición «si un repo vuelve a privado» | Los repos públicos no consumen minutos; el runner metería código de la rama en el PC |
| VIC-28, cabos sueltos | Partirla: lo que es teórico (`show-ref` frente a `rev-parse`, versión de osv duplicada) se anota como límite aceptado sin código; lo demás, en PR pequeños | Nueve puntos de seis issues en una sola entrega R2 es justo el tamaño que estorbó |
| VIC-23, repos anidados | Decidir si se cierra como límite aceptado de ADR-0008 o se mide en el bloque 5 | Lleva desde el bloque 2 en el Inbox sin bloquear nada |
| `mutaciones` en la CI | No quitar; no pasa a requerido hasta VIC-29 | Si VIC-29 no lo acerca a local, valorar correrlo con 2 procesos solo fuera del borrador, que ya es el caso |
| Poda de `AGENTS.md` | Hacerla antes del bloque 4, que añadirá más texto | Pendiente desde la retrospectiva anterior |

No se propone quitar ningún control del bloque.

## Entregas de los bloques 4 a 7: más pequeñas

**Sí.** Las piezas de la plantilla salieron bien partidas (VIC-21 y VIC-22, tres PR cada una, en el orden del contrato). Lo que creció fue llevarlas a la calculadora, donde aparecieron las decisiones. Propuesta:

1. **Una issue por decisión de fondo.** Si una entrega necesita un ADR que no estaba en su contrato, el ADR va en una issue nueva, y la entrega espera. VIC-31 habría sido tres issues.
2. **Primero el corte más pequeño en la calculadora.** Antes de generalizar en la plantilla, una prueba mínima en el proyecto real (un job, un test, una ruta), para que las sorpresas lleguen pronto y baratas.
3. **Tope por PR:** unas 400 líneas sin contar capturas ni lockfiles, como ya pide VIC-28, y las tres rondas de G4 como señal de partir, no como norma.
4. **Coste en el contrato:** «Hecho cuando» incluye el tiempo de espera de la CI por push si la entrega añade un job, y el tiempo del trozo más lento si toca los E2E. (Propuesto con los minutos facturados; Víctor lo cambió al tiempo de espera, 2026-11-19.)
5. **Bloques con varias issues desde el principio,** cada una con su «Hecho cuando»:
   - **Bloque 4:** formato de hallazgos y su check (reconciliación), diff calculado por la CI (M8), encargos del revisor (M13, M15, M1), revisor de mantenibilidad (M23), revisor en la CI (M34, R2 con su ADR) y la medición del coste.
   - **Bloque 5:** el ADR-0009 del workflow solo, en su PR (con la línea «No confundir con el ADR-0009 de la calculadora», como hacen sus ADR-0007 y 0008); después, ruleset y CODEOWNERS, M28 en la plantilla de issue y M4/M20, por separado.
   - **Bloque 6:** una skill por issue.
   - **Bloque 7:** el ADR-0010 primero; la tabla de modelos y el piloto de OpenCode, aparte.

## Decisiones tomadas

Víctor, 2026-11-19, en el PR de esta retrospectiva:

| Tema | Decisión |
| --- | --- |
| Bloque 3 | Se cierra. VIC-29 y VIC-32 son condición de entrada del bloque 5, no del 4 |
| VIC-34, runner propio | A *Backlog*, con la condición «si un repo vuelve a privado» |
| VIC-28, cabos sueltos | Se parte como se propone: lo teórico, como límite aceptado; lo demás, en PR pequeños |
| VIC-23, repos anidados | No se cierra: pasa al bloque 5 |
| Poda de `AGENTS.md` | Una issue pequeña antes del bloque 4 |
| Entregas de los bloques 4 a 7 | Se aceptan las cinco reglas; en la 4, el tiempo de espera de la CI en vez de los minutos facturados |
| Rama de esta retrospectiva | Se queda con VIC-33 |

## Pendientes que salen de aquí

- **En Linear:** mover VIC-34 a *Backlog*, partir VIC-28, asignar VIC-23 al bloque 5 y crear la issue de la poda de `AGENTS.md`.
- **En el plan:** la condición de entrada del bloque 5 y las reglas de entrega de los bloques 4 a 7 pasan a `docs/plan-v1.1.md` en este mismo PR.
- **Inbox restante:** VIC-30 (three 0.187, el #43 de Dependabot sigue abierto) y VIC-35 (ya en *Ready*).
- **Poner al día** el baseline de la calculadora (`picomatch`). La nota de `docs/herramientas.md` sobre el repo privado se corrige en este mismo PR.
- **Etiqueta v1.1.0:** cuando Víctor lo decida; esta retrospectiva no la crea.

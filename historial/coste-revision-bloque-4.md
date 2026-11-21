# Coste de la revisión en el bloque 4 (VIC-43)

Cuánto cuesta cada ronda de G4 y qué encuentra, con los PR del bloque 4. Sirve para decidir si el revisor de código en R1 sigue aportando ahora que hay controles fijos del bloque 3: mutaciones, duplicados, semgrep, osv-scanner y gitleaks (mejora #2 del primer recorrido). La decisión es de Víctor.

## 1. De dónde salen los datos

- **Hallazgos por ronda:** las líneas `Métricas G4` de `sdd-metricas`, resumidas con `entorno/resumen-metricas.py` desde el 2026-11-19. La gravedad, el revisor y la resolución de cada hallazgo salen de las líneas de la reconciliación de cada PR (`G4-<ronda>-<letra>-NN · gravedad · … · resolución`). En los PR anteriores a ese formato, de la descripción del revisor. *Mejora* (la escala de antes de VIC-38) cuenta como *menor*.
- **Tokens, tiempo y modelo de cada revisor:** del transcript de cada subagente (`~/.claude/projects/<repo>/<sesión>/subagents/`). `sdd-metricas` no los guarda.
  - Tokens: la suma de entrada, caché y salida de todas sus llamadas.
  - Tiempo: del primer al último mensaje del subagente.
  - Coste estimado: a precio de API (Opus 5.5: 4 $/20 $ por millón de tokens de entrada y salida y 0,20 $ la lectura de caché; Sonnet 5.5: 2 $/10 $ y 0,10 $; escritura de caché a 1,25 veces la entrada). Con la suscripción no se paga por token: se gasta cuota.
- **Sesiones:** coste y minutos de la tabla de `resumen-metricas.py`, también a precio de API.
- **Evaluaciones:** las cifras son de Víctor, de las salidas de `claude plugin eval` en local. La CI no ha corrido `evals` durante el bloque 4: la última ejecución es del 15-11.
- **Defectos escapados:** `historial/defectos-escapados.csv`, vacío.

PR medidos:
- **sdd-workflow:** #52 a #60.
- **calculadora-discos:** #74, más los R1 de los mismos días (#67 a #71), porque son los que permiten responder a la pregunta: en el workflow solo hay cuatro PR de código R1.

## 2. Revisor de código R1 (un revisor, Sonnet 5.5)

| PR | Ronda | Tokens | Salida | Min | Coste est. | Confirmados (imp. / men.) | Descartados |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| sdd #57 (M13, encargo y caso) | 1 | 196 k | 8,1 k | 1,0 | 0,17 $ | 0 / 1 | 1 |
| sdd #58 (M15) | 1 | 114 k | 4,3 k | 0,5 | 0,13 $ | 0 / 1 | 0 |
| sdd #59 (M1) | 1 | 159 k | 6,5 k | 0,8 | 0,16 $ | 2 / 0 | 1 |
| sdd #59 | 2 | 131 k | 6,6 k | 0,8 | 0,16 $ | 0 / 1 | 0 |
| sdd #60 (M23) | 1 | 456 k | 12,1 k | 1,4 | 0,32 $ | 1 / 2 | 0 |
| calc #67 (tests) | 1 | 42 k | 2,8 k | 0,3 | 0,07 $ | 0 / 0 | 1 |
| calc #68 (tests E2E) | 1 | 143 k | 4,6 k | 0,6 | 0,14 $ | 0 / 0 | 2 |
| calc #69 (tests E2E) | 1 | 93 k | 4,5 k | 0,5 | 0,12 $ | 0 / 0 | 2 |
| calc #70 (tests E2E) | 1 | 48 k | 2,5 k | 0,3 | 0,07 $ | 0 / 1 | 1 |
| calc #71 (baseline) | 1 | 153 k | 5,7 k | 0,7 | 0,14 $ | 1 / 3 | 0 |
| **Total (10 rondas)** | | **1,5 M** | | **6,9** | **1,48 $** | **4 / 9** | **8** |

- Ningún *debe corregirse*. Los 8 descartados son menores o mejoras.
- Los cuatro *importantes* confirmados no los podía ver ningún control fijo:
  - **sdd #59, G4-1-A-01:** el texto nuevo contradecía el ADR-0001 («dos revisores en las specs R1 y en todo R2»).
  - **sdd #59, G4-1-A-02:** la condición del camino corto no admitía el cambio de `estado` que hace toda aclaración.
  - **sdd #60, G4-1-A-01:** con los pesos de los evaluadores, el caso nuevo pasaba de 0,8 aunque fallase lo que debía probar.
  - **calc #71:** el baseline daba por hecho que Dependabot ya no proponía `three`, y `dependabot.yml` de `main` aún lo proponía.
- **Evaluadores:** tres de los nueve menores son de los evaluadores o los tests del propio caso (#57, #58 y #59 r2), además del *importante* de #60. La evaluación no comprueba a sus evaluadores; el revisor sí lo hizo.
- **calc #67 a #69:** en los PR que solo reorganizan tests, el revisor no confirmó nada (5 descartados). Ahí los controles fijos ya cubren lo que mira: los tests, las mutaciones y jscpd.
- **Tiempo:** el revisor tarda de 0,3 a 1,4 minutos por ronda. Lo que más tarda no es el revisor: preparar el encargo, reconciliar y esperar a la CI. Eso no se mide aparte.

## 3. Revisores de R2, para comparar (Sonnet A y Opus B, seguridad)

| PR | Rondas | Coste A + B | Confirmados de A | Confirmados de B |
| --- | ---: | ---: | --- | --- |
| sdd #52 (formato y check) | 3 | 0,73 $ + 2,03 $ | señaló 4 imp. y 8 men. | señaló 5 imp. y 8 men., muchos los mismos que A |
| sdd #53 | 1 | 0,19 $ + 0,79 $ | ninguno | 1 menor (1 descartado) |
| sdd #54 | 1 | 0,17 $ + 0,50 $ | ninguno | 1 importante |
| sdd #55 | 1 | 0,22 $ + 0,52 $ | 1 menor | 1 importante (1 menor descartado) |
| sdd #56 | 1 | 0,13 $ + 0,37 $ | 1 importante | 1 importante y 2 menores |
| calc #74 | 1 | 0,20 $ + 0,44 $ | 3 menores | 2 importantes (1 menor repetido) |
| **Total** | **8** | **1,64 $ + 4,65 $** | | |

En #52, las `Métricas G4` dicen 11, 8 y 5 confirmados en las tres rondas (1 descartado). El reparto por revisor sale de la reconciliación, que antes de la ronda 3 no llevaba líneas por hallazgo.

El revisor Opus de seguridad es el 74 % del coste de la revisión en R2. Encontró algún *importante* en cinco de los seis PR; en tres de ellos (#54, #55 y #74), A no encontró ninguno.

## 4. Proporción con el resto

- **Revisores:** los de los PR de las tablas cuestan unos 7,8 $. Las sesiones del bloque 4 (del 19-11 a las 21:08 al 21-11) suman unos 71 $ en `sdd-metricas`. La revisión es el 10–11 % del coste: no he comprobado si la cifra de Claude Code incluye a los subagentes, y con ellos o sin ellos sale lo mismo.
- **Revisor R1:** 0,15 $ de media por ronda. Las 10 rondas son el 2 % del coste de las sesiones del bloque.
- **Evaluaciones:** unos 2 $ por PR de skills, según Víctor, con 3 ejecuciones por caso y umbral 0,8 sobre la media (`runsPerCase: 3` en los resultados locales de noviembre, `plugin-sdd/evals/results/*/aggregate-result.json`, que Git no guarda). En el bloque 4, cinco PR traen un caso nuevo (#53, #57, #58, #59 y #60): unos 10 $. Una evaluación cuesta lo que unas 13 rondas de revisor R1.

## 5. Las comprobaciones menores que fallan una de cada tres veces

- **Qué pasa:** Víctor ve en sus salidas que algunos evaluadores de poco peso fallan en una de las tres ejecuciones, sin que cambie nada. No tengo el detalle por caso: no está ni en el repo ni en la CI.
- **Lo que pesan:** poco. En `g4-mantenibilidad` los pesos son 11, 4, 2 y 1. Si el de peso 1 falla en una de las tres ejecuciones, esa ejecución saca 17/18 y la media baja a 0,98 y el caso sigue en verde. Lo que molesta es el ruido al leer la salida, no el resultado.
- **Si una comprobación falla de verdad con probabilidad 1/3 (p = 1/3):**
  - **Con 3 ejecuciones:** la salida enseña al menos un fallo el 70 % de las veces. Falla en las tres solo el 4 %. Si se rompe del todo, falla en las tres siempre.
  - **Con 5 ejecuciones (+67 % de coste, unos 3,3 $ por PR):** sirve para ver una regresión a medias, que pase de fallar 1 de cada 3 a 2 de cada 3. Con 3 ejecuciones y la regla «falla las tres», eso se ve el 30 % de las veces. Con 5 y la regla «falla 4 o más», el 46 %.
  - **Con 2 ejecuciones (−33 %):** falla en las dos el 11 % de las veces, aunque no haya cambiado nada. Distingue peor el ruido de una rotura.

## 6. Propuesta para Víctor

**Revisor de código R1: mantenerlo (recomendado).**
- **Lo que cuesta:** unos 0,15 $ y menos de un minuto y medio por ronda.
- **Lo que encuentra:** en 10 rondas, 4 *importantes* confirmados que ningún control fijo podía ver: contradicciones con un ADR o con la configuración, y pesos de evaluación que dejaban pasar el fallo.
- **Dónde los encuentra:** los cuatro son de PR de texto de skills, de evaluadores o de documentación (#59, #60 y calc #71), donde los controles del bloque 3 no llegan. En el código con controles fijos (calc #67 a #70, solo tests) lleva 0 *importantes* en 4 rondas: para esa parte, la muestra no dice que aporte. Mantenerlo se apoya en que la mayoría de los PR R1 del workflow son de texto.
- **Sin él:** esos cuatro habrían quedado para Víctor en G6, si los veía.
- **Alternativas:**
  - *Reducir:* quitarlo en los PR que solo reorganizan tests, con mutaciones y duplicados en verde. Ahorraría unos 0,33 $ en tres PR. Además, el ADR-0001 pide un revisor con contexto limpio en todo el código R1: quitarlo ahí pide otro ADR.
  - *Quitar:* ahorraría 1,48 $ en el bloque, a cambio de esos cuatro *importantes*.
  - Ninguna de las dos compensa.

**Evaluaciones: seguir con 3 ejecuciones por caso.**
- **Más ejecuciones:** cuestan más que todo el revisor R1 y apenas mejoran la detección.
- **Menos:** confunden ruido con rotura.
- **Para leer el ruido:** si un evaluador de peso bajo falla en una de las tres, es ruido conocido; en dos, se mira; en las tres, es una rotura.
- **Si el ruido molesta:** mejor corregir el evaluador que falla (casi siempre una expresión demasiado estricta) que pagar más ejecuciones.

**Si se quiere ahorrar, el dinero está en otro sitio:**
- el revisor Opus de seguridad (74 % del coste de R2);
- las evaluaciones (unos 2 $ por PR de skills).
Cambiar el modelo de un revisor es una decisión del ADR-0002 y del bloque 7 (M29), no de aquí.

## 7. Límites y huecos

- **Muestra pequeña:** 10 rondas R1 y 8 de R2, en cuatro días. Los defectos escapados aún no han tenido tiempo de aparecer.
- **Lo que no registra `sdd-metricas`:** la línea `Métricas G4` no lleva revisor, modelo, gravedad, tokens ni tiempo. El punto 1 del alcance de VIC-43 lo pide, y aquí se ha sacado a mano de los transcripts.
  - **Propuesta:** una issue aparte para que `sdd-review` escriba una línea por revisor y `sdd-metricas` la lea. No va en este PR, para que siga pequeño.
- **Datos que no cuadran:**
  - **#53:** `Métricas G4` dice 2 confirmados y 0 descartados; la reconciliación descarta uno.
  - **#59:** hay dos líneas de la ronda 1. La segunda (2 corregidos) corrige a la primera, y `resumen-metricas.py` se queda con la última.
- **Evaluaciones:** el coste y el patrón de fallos son de Víctor, sin el detalle por caso.

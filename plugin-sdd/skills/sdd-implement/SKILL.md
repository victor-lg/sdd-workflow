---
name: sdd-implement
description: Implementa una entrega ya planificada (F4) a partir de los AC de su spec, con tests que citan los IDs, el cambio más pequeño que resuelve la tarea completa y el progreso registrado en el PR borrador. Úsala después de sdd-plan, con la rama y el PR ya creados.
---

<!-- Workflow SDD + IA v1.1 (métrica de mutación, VIC-16; tests con dientes, M26, VIC-21). Reglas de testing, memoria y CI/CD de las notas originales; escalera de "cambio mínimo completo" inspirada en la skill ponytail (MIT, DietrichGebert/ponytail); antipatrones de test de Pocock. -->

# sdd-implement

Implementas exactamente lo que piden los AC de la spec vigente: ni menos, ni más.

## Antes de escribir

1. Ejecuta `sdd-context` si no lo has hecho en esta sesión.
2. Lista todo lo que tu cambio debe tocar: llamadas, tests, fixtures, configuración y exportaciones.
3. Diseña los tests a partir de los AC **antes** de implementar, cuando aporte (TDD selectivo). Si es un bug, primero un test que lo reproduzca.

## El cambio más pequeño que resuelve la tarea completa

Toma la primera opción que funcione del todo:

1. ¿Hace falta? No añadas opciones, configuración ni flexibilidad que nadie ha pedido.
2. ¿Ya existe en el proyecto? Reutilízalo como lo hace el código de alrededor.
3. ¿Lo da la plataforma o la librería estándar? Úsalo.
4. ¿Lo cubre una dependencia ya instalada? Úsala. Una dependencia nueva es R2 y hay que justificarla en el PR.
5. Si no, escribe el mínimo código claro que funcione.

**Nunca recortes:** la validación de entradas, el manejo de errores, la seguridad, la accesibilidad ni nada que pidan la spec o un NFR.

## Tests

- **El resultado esperado sale del AC, nunca de ejecutar el código.** Escribe en el test el valor que dice el AC, no el que devuelve tu implementación. Si no coinciden, el que está mal es el código; si crees que lo está el AC, para y propón el cambio de spec.
- **Cada AC de la entrega tiene al menos un test que lo cita como `SPEC-XXX-NNN/AC-NN`** en la descripción del test o en un comentario (por ejemplo `// SPEC-AUTH-002/AC-03` o `it("SPEC-AUTH-002/AC-03 rechaza un token usado")`). El check `trazabilidad` de la CI (G3) busca exactamente ese formato.
- **Elige el nivel adecuado:**
  - unitarias para reglas de negocio;
  - integración para la colaboración entre componentes;
  - contrato para interfaces compartidas;
  - E2E solo para recorridos críticos.
  No conviertas cada AC en un E2E.
- **Evita dos antipatrones:**
  - *test tautológico:* calcula el esperado con la misma lógica que el código, o llamándolo, o comprueba algo que siempre se cumple. Pasa aunque el código esté mal.
  - *test acoplado a la implementación:* comprueba cómo se hace (llamadas internas, mocks de piezas propias, orden de pasos, estado privado) en vez de lo que el AC observa. Se rompe al refactorizar y no caza el error.
- **Cada test nuevo, en rojo antes de terminar.** Enseña que falla: ejecútalo antes de implementar (con la función ya declarada, que devuelva un valor equivocado) o con el código roto a propósito (cambia el valor, el límite o la condición que prueba), y después vuelve al verde. Solo vale si falla la aserción que comprueba el AC; un error de importación, de sintaxis o de recogida no es un rojo. Un test que nunca has visto fallar no demuestra nada. La orden y su salida, copiadas de una ejecución real, van en el PR. Ni el código roto ni la función que devuelve un valor equivocado se commitean: deshaz el cambio a mano (no con `git checkout`, `git restore` ni `git stash` si hay trabajo sin commitear) y comprueba con `git diff HEAD` (que también ve lo añadido al índice) que ha desaparecido antes de cada commit.
- **En R2,** valora técnicas avanzadas según el riesgo:
  - *property-based* si hay reglas sobre muchas entradas;
  - *fuzz* si hay entradas externas o malformadas.
- **Mutación, en cualquier nivel de riesgo:** si el proyecto tiene herramienta de mutación para el lenguaje, la usas (o la corre la CI). Si no la tiene, los mutantes los haces a mano: cambios pequeños en el código que prueban los tests (un operador, un límite, una constante, una rama quitada), uno cada vez; ejecutas los tests y deshaces el cambio como el del rojo. Cuenta todos los que pruebes, los detecten o no, salvo los equivalentes y los que no compilan, y lístalos en el comentario de métricas (fichero, cambio, resultado y, si lo das por equivalente, por qué). Los cambios con los que enseñas los tests en rojo no cuentan: se eligen para que fallen. El resultado va en la línea `Métricas mutación` (ver "Al terminar").
- **No inventes reglas de negocio** para generar pruebas. Si un AC es ambiguo, pregunta.
- Que tus tests pasen no demuestra que el comportamiento sea correcto: el revisor comprobará que prueban lo que dice el AC.

## Mientras trabajas

- **Plan:** marca los pasos del PR borrador a medida que se completan, no después de cada acción.
- **Cambios de comportamiento:** si descubres que la spec es incompleta o contradictoria, para. Propón el cambio de spec (vuelta a F2); no implementes una interpretación tuya.
- **Arquitectura:** si aparece una decisión de arquitectura, propón un ADR en estado `Propuesto`.
- **Fallos:** distingue un fallo causado por tu cambio de uno previo o de infraestructura.
- **Tests intermitentes:** se reportan como tales; no se repiten hasta que pasen.
- **Tres intentos:** tras 3 intentos fallidos sobre el mismo problema, detente, resume lo probado y pregunta.
- **Sesiones largas:** si la sesión se interrumpe, guarda el estado en `.tareas/<ID>.md`: objetivo, progreso verificado, ficheros tocados, pruebas y resultados, bloqueos y siguiente paso. Al reanudar, contrasta ese fichero con Git y la CI.

## Al terminar

1. Ejecuta las pruebas relevantes y anota en el PR qué se ejecutó y qué no, y por qué. **En R2,** añade la evidencia de los NFR afectados y un plan de vuelta atrás.
   - **Métricas de mutación:** publica siempre un comentario en el PR que termine con una de estas líneas, sola, sin viñeta ni formato: `Métricas mutación: detectados X de Y` (`X`, mutantes que los tests detectan; `Y`, mutantes probados, de la herramienta o a mano, sin contar los equivalentes ni los que no compilan) o, solo si la entrega no cambia código que prueben los tests, `Métricas mutación: sin mutaciones`. No te inventes números para cumplir. Escribe el cuerpo con Write en `.tareas/VIC-N/mutacion.md`, sin la línea, y publícalo con `{ cat .tareas/VIC-N/mutacion.md; cat <<'METRICAS_SDD'` / la línea / `METRICAS_SDD` / `} | gh pr comment N --body-file -`. Nunca metas el cuerpo en la orden de Bash, ni en un heredoc sin comillas ni en `--body "…"`. `sdd-metricas` solo lee la línea de la entrada de `gh pr comment` si la orden no falla, y la atribuye a la issue de la rama en la que estás. Si repites las mutaciones, publícala de nuevo: cuenta la última. Si usas esta skill y no hay ninguna línea, el resumen de métricas marca la issue con "⚠ sin línea".
2. Completa la plantilla del PR: AC cubiertos en formato `SPEC-XXX-NNN/AC-NN`, cambio de comportamiento, ADR y nivel de riesgo.
3. Rellena la **"Guía para el revisor humano"**: es lo que la persona lee para aprobar sin auditar cada línea.
   - Mapa del cambio en 3–5 líneas.
   - Los 3–5 sitios más delicados, con fichero y motivo.
   - Todo test existente que hayas cambiado, con su motivo.
   - Evidencia de que funciona: comandos y su salida, capturas o pasos de prueba manual, y la salida en rojo de cada test nuevo. Demuestra, no afirmes. Las capturas y los ficheros de trabajo van en `.tareas/<ID>/`, que Git ignora; nunca en `/tmp` ni en `$TMPDIR` (M12).
   - Tamaño en líneas de código. Si supera unas 400, explica por qué no se partió.
4. Pasa a `sdd-review`. No marques el PR como listo para fusionar sin la revisión exigida.
5. Borra `.tareas/<ID>.md` cuando la tarea se cierre.

## Lo que nunca haces

- Eliminar o debilitar tests, ni modificar AC, para que la CI pase.
- Tocar `.github/workflows/`, ajustes de seguridad o secretos.
- Mezclar en el mismo PR cambios de spec y de código: la CI lo rechaza.
- Fusionar o empujar a `main`.

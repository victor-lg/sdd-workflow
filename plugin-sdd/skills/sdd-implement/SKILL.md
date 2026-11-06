---
name: sdd-implement
description: Implementa una entrega ya planificada (F4) a partir de los AC de su spec, con tests que citan los IDs, el cambio más pequeño que resuelve la tarea completa y el progreso registrado en el PR borrador. Úsala después de sdd-plan, con la rama y el PR ya creados.
---

<!-- Workflow SDD + IA v1.1 (métrica de mutación, VIC-16). Reglas de testing, memoria y CI/CD de las notas originales; escalera de "cambio mínimo completo" inspirada en la skill ponytail (MIT, DietrichGebert/ponytail). -->

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

- **Cada AC de la entrega tiene al menos un test que lo cita como `SPEC-XXX-NNN/AC-NN`** en la descripción del test o en un comentario (por ejemplo `// SPEC-AUTH-002/AC-03` o `it("SPEC-AUTH-002/AC-03 rechaza un token usado")`). El check `trazabilidad` de la CI (G3) busca exactamente ese formato.
- **Elige el nivel adecuado:**
  - unitarias para reglas de negocio;
  - integración para la colaboración entre componentes;
  - contrato para interfaces compartidas;
  - E2E solo para recorridos críticos.
  No conviertas cada AC en un E2E.
- **En R2,** valora técnicas avanzadas según el riesgo:
  - *property-based* si hay reglas sobre muchas entradas;
  - *fuzz* si hay entradas externas o malformadas;
  - *mutation* si dudas de si los tests detectan errores.
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
   - **Si hiciste mutaciones,** escribe en tu respuesta, no solo en el PR, esta línea sola, sin viñeta ni formato y con números: `Métricas mutación: detectados X de Y` (`X`, mutantes que los tests detectan; `Y`, mutantes probados, sin contar los equivalentes ni los que no compilan). La lee `sdd-metricas` en el transcript y la atribuye a la issue de la rama en la que estás; si repites las mutaciones, escríbela de nuevo: cuenta la última.
2. Completa la plantilla del PR: AC cubiertos en formato `SPEC-XXX-NNN/AC-NN`, cambio de comportamiento, ADR y nivel de riesgo.
3. Rellena la **"Guía para el revisor humano"**: es lo que la persona lee para aprobar sin auditar cada línea.
   - Mapa del cambio en 3–5 líneas.
   - Los 3–5 sitios más delicados, con fichero y motivo.
   - Todo test existente que hayas cambiado, con su motivo.
   - Evidencia de que funciona: comandos y su salida, capturas o pasos de prueba manual. Demuestra, no afirmes.
   - Tamaño en líneas de código. Si supera unas 400, explica por qué no se partió.
4. Pasa a `sdd-review`. No marques el PR como listo para fusionar sin la revisión exigida.
5. Borra `.tareas/<ID>.md` cuando la tarea se cierre.

## Lo que nunca haces

- Eliminar o debilitar tests, ni modificar AC, para que la CI pase.
- Tocar `.github/workflows/`, ajustes de seguridad o secretos.
- Mezclar en el mismo PR cambios de spec y de código: la CI lo rechaza.
- Fusionar o empujar a `main`.

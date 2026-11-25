# Glosario del workflow SDD + IA

Qué significa cada código y cada paso. La norma completa está en `docs/linea-base-v1.md`; esto es la chuleta.

## El camino de un cambio

```
Idea → Descubrir → Spec (PR) → Issue en Ready → Implementar (PR) → Revisión IA + CI → Fusionar → Publicar → Probar en el iPhone
 F0       F1         F2   G1       F3     G2         F4      G3        F5   G4  G5      F6  G6      (D25)
```

1. **F0 Idea:** sale de una conversación, una nota o una issue.
2. **F1 Descubrir:** entrevista guiada para aclarar qué se quiere (skill `sdd-discover`).
3. **F2 Especificar:** se escribe o cambia la spec en su propio PR (`sdd-spec`). **G1:** la spec solo vale cuando está fusionada en `main`.
4. **F3 Planificar:** la issue de Linear pasa a *Ready* con el enlace a la spec (**G2**). El agente comprueba que está y que la spec está en `main` (`sdd-plan`).
5. **F4 Implementar:** el agente escribe tests desde los AC y el código, en un PR de código (`sdd-implement`). **G3:** cada AC que el PR dice cubrir tiene un test que lo cita.
6. **F5 Revisar:** revisores IA independientes (**G4**, `sdd-review`) y la CI en verde (**G5**).
7. **F6 Integrar:** la persona aprueba y fusiona (**G6**).
8. **Publicar:** paso aparte y manual (*Actions → deploy*). Fusionar no es publicar (D25).
9. **Prueba en el iPhone:** la persona prueba lo publicado y cierra la issue.

## Códigos de identificación

| Código | Qué es | Ejemplo |
| --- | --- | --- |
| `VIC-N` | Issue de Linear (team "Desarrollo", clave `VIC`) | VIC-12, "Dibujo 3D y movimiento" |
| `#N` | Pull request (PR) de GitHub | #33 |
| `SPEC-AREA-NNN` | Especificación: qué debe hacer la app | SPEC-CALC-003, presentación |
| `FR-NN` | Requisito funcional dentro de una spec: una regla de comportamiento | FR-08, borrar una serie |
| `NFR-NN` | Requisito no funcional: rendimiento, privacidad, accesibilidad… | NFR-02, contraste |
| `AC-NN` | Criterio de aceptación: comprobación concreta que demuestra un FR o NFR. Se cita como `SPEC-CALC-003/AC-13` y cada uno necesita un test | AC-13, Deshacer dura 5 s |
| `SPEC-XCUT-*` | Spec transversal, compartida por varias | — |
| `ADR-NNNN` | Registro de una decisión de arquitectura y su porqué | ADR-0003, three.js |
| `vX.Y` | Versión de una spec, del workflow o de la app | SPEC-CALC-003 v0.5, workflow v0.23 |
| `M-NN` | Mejora del workflow | M42, convenciones (`docs/convenciones.md`) |

Hay dos series de ADR: los del **proyecto** (`calculadora-discos/docs/adr/`, por ejemplo ADR-0003 three.js) y los del **workflow** (`sdd-workflow/docs/adr/`, por ejemplo ADR-0006 lo que puede hacer Claude con el navegador). Comparten numeración, pero no son los mismos.

## Gates (controles) G1–G6

| Gate | Qué asegura | Quién o qué lo aplica |
| --- | --- | --- |
| G1 | La spec está aprobada: fusionada en `main` | Tú, al fusionar el PR de spec |
| G2 | La issue está en *Ready* y enlaza una spec de `main` | Tú en Linear; el agente lo comprueba |
| G3 | Cada AC declarado tiene un test que lo cita | La CI (check `trazabilidad`) |
| G4 | Ha revisado alguien que no hizo el cambio | Subagentes revisores (IA) |
| G5 | La CI está en verde sobre el último commit | GitHub (checks obligatorios) |
| G6 | La integración la hace una persona | GitHub (1 aprobación tuya) |

**DoR** (Definition of Ready): la spec está lista para construir. **DoD** (Definition of Done): el cambio está integrado (G6).

## Niveles de riesgo R0–R2

| Nivel | Ejemplos | Revisores IA (spec / código) |
| --- | --- | --- |
| R0 trivial | Erratas, documentación | — / opcional |
| R1 normal | Una funcionalidad o una corrección | 2 / 1 |
| R2 sensible | Dependencias, CI, permisos, rutas sensibles (en la calculadora: `app/sw.js`, la CSP de `app/index.html`, el test de sin conexión) | 2 / 2, uno de seguridad con Opus |

El agente propone el nivel; la CI puede subirlo, nunca bajarlo. Una aclaración de spec (un PR que solo pasa a la spec una lectura que la persona ya decidió) va por el camino corto: los dos revisores de una spec y una sola ronda, en R1 y R2; lo que deba corregirse se corrige sin otra y la persona lo revisa al aprobar (`sdd-review`).

## Revisión (G4)

- **Revisor:** subagente `reviewer`, de solo lectura. Recibe la spec de `main`, el diff, la CI y los ADR; nunca el razonamiento del autor ni la descripción del PR. En el código R1, y en R2 el que no lleva seguridad, añade el foco de mantenibilidad: los olores de Fowler y la rúbrica de calidad de thermos, copiadas en `sdd-review`, sin subir la gravedad por ellas.
- **Ronda:** una pasada de revisión. Hasta 3; después decide la persona.
- **Clasificación de hallazgos:** *debe corregirse* (bloquea), *importante* (se corrige o se descarta con prueba) y *menor* (opcional). Cada hallazgo lleva un ID (`G4-<ronda>-<revisor>-NN`) y una prueba: un test, una línea o una cita.
- **Reconciliación:** el agente contrasta los hallazgos con el código, corrige y lo explica en el PR, con una línea por hallazgo y su resolución: corregido en un commit, descartado con prueba o pregunta a la persona. El check `hallazgos` de la CI comprueba que ninguno queda sin resolver. Las respuestas de los revisores van en comentarios del PR, y el check solo lee los de las cuentas autorizadas (`CUENTAS_G4` en `checks.py`).
- **Aclaración:** la lectura de un requisito que decide la persona cuando dos revisores lo leen de forma distinta y la spec no lo zanja. Se anota en el PR («Revisión IA») y pasa a la spec en un PR de spec antes de cerrar la issue.
- **Cambios tras la última ronda:** lo que entra después sin otro revisor. Lo calcula el check `cambios` de la CI desde el commit que vio cada revisor (`Commit revisado:` en su comentario) y lo publica en el resumen de `checks-sdd`, para que lo leas. Escrita a mano en la descripción del PR, el check falla. En R0 y R1 solo puede ser documentación (`.md` normales que no son specs, ADR ni instrucciones de agentes, fuera de carpetas que empiezan por punto): si no, el check falla y hace falta otra ronda o tu aprobación sobre la cabeza, pensada para cuando no cabe otra ronda (VIC-56). En R2 siempre la frena tu aprobación.

## La CI (`checks-sdd` y `tests`)

- **`checks-sdd`:** comprueba la estructura de las specs, que un PR no mezcle spec y código (`mezcla`), la trazabilidad AC ↔ tests (`trazabilidad`) y el nivel de riesgo mínimo (`riesgo`).
- **`tests`:** unitarios y E2E (pruebas de extremo a extremo con Playwright, en Chromium y WebKit). Desde el #34, los E2E van en tres **trozos** en paralelo.

## Casos negativos N1–N8

Pruebas de que el sistema frena lo que debe:

| Caso | Qué se intenta | Qué debe pasar |
| --- | --- | --- |
| N1 | Implementar una spec que no está en `main` | El agente para y la CI falla |
| N2 | Cambiar una spec aprobada en el PR de código | Hace falta un PR de spec aparte |
| N3 | Un commit nuevo tras la aprobación | La aprobación se invalida |
| N4 | El agente fusiona o hace push a `main` | GitHub lo rechaza |
| N5 | El agente toca `.github/workflows/` | Su token no tiene permiso |
| N6 | Un texto externo pide leer `~/.ssh` y sacarlo fuera | El sandbox lo impide |
| N7 | Un AC sin test | La CI falla |
| N8 | El revisor recibe el razonamiento del autor | La revisión se repite |

## Linear

- **Estados:** *Inbox* (recién creada), *Discovery*, *Ready* (lista para implementar, G2), *In Progress*, *In Review*, *Done*, *Canceled*.
- **"Fixes VIC-N"** en el PR cierra la issue al fusionar. **"Refs VIC-N"** la enlaza sin cerrarla: es lo habitual cuando la entrega tiene una prueba manual (en el iPhone, tras publicar…) o no consta si la tiene, y la cierras tú después de probar (M4).

## Herramientas y piezas

- **Agente:** Claude Code en WSL, con la cuenta de máquina `victor-lg-bot`. Trabaja dentro de un **sandbox** que limita qué ficheros lee y a qué red sale.
- **Skills `sdd-*`:** procedimientos del workflow, en el plugin `sdd`: `sdd-discover`, `sdd-spec`, `sdd-plan`, `sdd-context`, `sdd-implement` y `sdd-review`.
- **`AGENTS.md` y `CLAUDE.md`:** instrucciones del agente en cada repo.
- **Ruleset y CODEOWNERS:** reglas de GitHub sobre `main`: PR obligatorio, checks y aprobación del dueño del código.
- **`.tareas/VIC-N.md`:** estado de una tarea larga, fuera de Git.
- **Perfil Claude / perfil Go:** con qué modelos corre el agente. Claude, el principal; Go (OpenCode Go), modelos ligeros, aplazado.
- **Claude en la app:** este asistente. Diseña contigo, revisa los PR antes de que los apruebes y hace en Linear y GitHub lo que permite ADR-0006.

## Códigos del historial

Sirven para rastrear de dónde sale cada regla. No hace falta recordarlos.

| Código | Qué es | Dónde |
| --- | --- | --- |
| D00–D59 | Las 60 decisiones de diseño iniciales | `historial/registro-D00-D59.md` |
| H01–H24 | Hallazgos de la auditoría del diseño | `historial/auditoria-H01-H24.md` |
| P01–P10 | Principios de la línea base (por ejemplo, P03 "aprobar = fusionar") | `docs/linea-base-v1.md` §4 |
| Q01–Q09 | Preguntas que se cerraron al montar el workflow | ADR-0001 a ADR-0005 del workflow |
| C1–C22 | Hallazgos de la revisión independiente | `historial/revision-independiente-1.md` |
| V1–V7 | Hallazgos de esa revisión que pasan a la v1.1 | ídem |
| #1–#10 | Mejoras candidatas del primer recorrido | `historial/retrospectiva-1.md` |
| M1–M24 | Mejoras candidatas del segundo recorrido | `historial/recorrido-2.md` y `retrospectiva-2.md` |
| obs. N | Observación numerada de un recorrido | `historial/recorrido-N.md` |

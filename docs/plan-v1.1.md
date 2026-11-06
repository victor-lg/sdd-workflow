# Plan de la v1.1 del workflow

**Estado:** propuesta para revisar con Víctor (2026-11-04). Recoge las mejoras aceptadas en `historial/retrospectiva-2.md` (con su evidencia) y el análisis de `historial/analisis-herramientas-1.md`. Se trabaja por bloques, en orden, porque cada bloque se apoya en el anterior.

## Principios del plan

- **Primero la red de seguridad, después los cambios.** Antes de tocar skills y reglas, el repo del workflow pasa a trabajar por PR, con CI y con pruebas del propio workflow. Así, cada cambio posterior se comprueba solo.
- **Primero lo que no es opinión, después la autonomía.** El agente solo fusionará sin ti cuando existan controles fijos: mutaciones, regresión visual, seguridad estática. Es la "escalera de confianza" de Kem.
- **Cada regla de fondo que cambia lleva su ADR** en `docs/adr/` del workflow. Lo demás entra directamente por PR, con su línea en el CHANGELOG.
- **Requisitos de todos los bloques:**
  - **Medir:** lo que cambie se mide con `sdd-metricas` para evaluarlo en el próximo proyecto.
  - **Inyección:** cada pieza nueva se evalúa con la trifecta letal. Las skills de terceros se copian fijadas y revisadas, sin hooks ajenos, y se repite N1–N8 en cada configuración nueva.
  - **Sin burocracia:** si una mejora no se puede comprobar o medir, se simplifica o se descarta.

## Bloque 0 — Cerrar la v1.0

**Por qué primero:** la v1.1 parte de una v1.0 declarada. Lo pendiente es poco y está definido desde la revisión independiente.

- Pruebas C18–C20 (las hace Víctor; los pasos ya están dados):
  - C18: la CI rechaza una spec que no está en `main` y la mezcla de spec y código;
  - C19: el ruleset rechaza un push directo del agente a `main`;
  - C20: el sandbox corta la red sin proxy y oculta `~/.ssh`.
- Quitar las marcas "BORRADOR" y las referencias desfasadas (C22), subir el plugin a 1.0.0 y escribir la entrada v1.0 en el CHANGELOG.

**Hecho cuando:** v1.0 declarada en el CHANGELOG, con la evidencia de C18–C20 en `historial/recorrido-1.md`. ✔ Hecho el 2026-11-05.

## Bloque 1 — Base para cambiar el workflow sin romperlo

**Por qué ahora:** todos los bloques siguientes modifican skills, plantillas y reglas. Sin PR, CI ni pruebas del workflow, cada cambio es una apuesta, y ya ha habido copias que llegaron con contenido viejo sin avisar.

| Mejora | Qué se hace |
| --- | --- |
| **M36** | El repo `sdd-workflow` se trabaja como un proyecto más: el agente en WSL abre PR, la CI valida y tú fusionas. Se acaba copiar desde este chat a la carpeta de Windows |
| **M35** | Evaluaciones del propio workflow (`claude plugin eval`). Los casos negativos que dependen del plugin (N1, N2, N6 como inyección, N7 y N8; N3–N5 son barreras de GitHub y del token, y la barrera de N6, el sandbox, no se evalúa aquí) y el comportamiento clave de cada skill (`sdd-plan` se para si la issue no está en *Ready*, `sdd-review` no pasa contexto de más…) se ejecutan en la CI del workflow de madrugada (02:17 UTC) si `plugin-sdd/` cambió en el último día, o a mano; nunca en un PR. En una evaluación los hooks del plugin se ejecutan fuera del sandbox, y el token no debe llegar a código sin revisar. Además, las evaluaciones consumen del mismo plan que el trabajo diario y, de día, chocan con su límite de uso |
| **Autoría** | ADR-0007. `"attribution": {"commit": "", "pr": "", "sessionUrl": false}` en los ajustes de usuario (las cadenas vacías ocultan la mención). Se quitan de `AGENTS.md` y de la plantilla de PR el `Co-Authored-By`, el pie "Generated with" y el apartado "Perfil y modelo". Los commits y el squash quedan a nombre de la cuenta de máquina del agente, que abre el PR; la autoría de Víctor se descarta (ADR-0007, §2) |
| **M42** | Convenciones de nombres y mensajes en `docs/convenciones.md`, adoptadas por el ADR-0007 junto con la autoría (ramas `tipo/vic-N-…`, Conventional Commits con `Refs: VIC-N` en el pie, títulos de issue y PR, versiones). `AGENTS.md`, plantillas y skills remiten a ese documento. Linear ya está preparado (team "Desarrollo", etiquetas Tipo, Riesgo y Origen, plantillas, proyecto del workflow) |
| **Medición** | `sdd-metricas` amplía lo que guarda: rondas de G4, hallazgos (confirmados y descartados), puntuación de mutación cuando exista, defectos escapados (M10) e intervenciones humanas. `resumen-metricas.py` los resume por issue |

**Hecho cuando:** un primer PR del workflow, abierto por el agente, pasa la CI, sus commits no mencionan a Claude y la siguiente evaluación nocturna pasa.

## Bloque 2 — Controles en vez de instrucciones

**Por qué ahora:** es la base de todo lo demás (Kem: "un hook siempre se ejecuta; una skill, solo si el modelo quiere"). Además, poda el contexto que el agente lee en cada sesión, lo que abarata cada llamada por la caché de prompts.

| Mejora | Qué se hace |
| --- | --- |
| **M25** | Inventario de cada regla de `AGENTS.md`, `CLAUDE.md` y las skills: instrucción o control, si se ha incumplido y si es mecánica. Las mecánicas o incumplidas pasan a **hooks de Claude Code** o a la **CI**. Referencia para diseñarlos: los 27 hooks de baseline (friedbot studio), leídos en `historial/analisis-herramientas-1.md` §16. Primeros candidatos: consentimiento con caducidad que el agente no puede falsificar (base de M24), guarda de `.env`, `deny` de `git add -A`/`git add .`, guarda de fugas por `.gitignore` y no escribir PASS sin un test en verde. Cada guarda de ficheros lleva su pareja en Bash |
| **M16** | Primer hook: bloquear `git push -u`, `git branch --set-upstream-to` y `git config` |
| **M12** | Hook: escrituras de capturas fuera del repo (`/tmp`) |
| **M5** | Script que comprueba que `checks-sdd` no quedó cancelado antes de dar el PR por listo |
| **M11** | El ID de la issue en todas las ramas, comprobado por la CI |
| **M17** | `.gitignore` de la plantilla con los ficheros del sandbox y `capturas-*/` |
| **M39** | Las specs dejan de llevar historial en la cabecera; `checks.py` avisa si reaparece |
| **M7** | Comillas en las referencias de la cabecera YAML de los ADR, comprobado por `checks.py` |
| **Poda** | `AGENTS.md` queda como mapa corto (Jake, Pocock `writing-for-agents`); los procedimientos van a las skills y los controles a hooks y CI. Se desactiva lo que no se usa (MCP, plugins). Se mide el contexto fijo antes y después (mejora #9 del primer recorrido) |

**Hecho cuando:** cada regla del inventario tiene su destino, los hooks pasan sus evaluaciones (M35) y el contexto fijo baja de forma medible.

## Bloque 3 — Calidad y seguridad sin opinión

**Por qué ahora:** son los controles fijos que permiten, en el bloque 5, que el agente fusione sin ti. También son la condición para el "empieza barato" de los modelos (bloque 6).

| Mejora | Qué se hace |
| --- | --- |
| **M26** | Tests con dientes. En `sdd-implement`: el resultado esperado sale del AC, no del código; antes de terminar se enseña el test en rojo; y los antipatrones de Pocock (tautológico, acoplado). En la CI, mutaciones con la herramienta de cada lenguaje (Stryker en JS/TS), o mutantes del agente si no la hay |
| **M27** | Regresión visual con capturas de referencia aprobadas una vez, y accesibilidad automática (axe) en los E2E |
| **M19** | La regla de los E2E: lo que no trata de una capacidad cara corre sin ella, y esa capacidad tiene sus ficheros y un recorrido completo |
| **M33** | Seguridad estática: Semgrep más el escáner del lenguaje, gitleaks y osv-scanner. Antes del commit con lefthook; en la CI como autoridad. Un hook bloquea `--no-verify`, `LEFTHOOK=0` y `LEFTHOOK_EXCLUDE` |
| **M23** (parte fija) | knip en JS/TS y jscpd con baseline: avisan de código que sobra y de duplicación nueva |
| **M38** | Bot de dependencias (Renovate o Dependabot) y tarea mensual con osv-scanner |
| **M6** | El ejemplo de workflow de tests con el contenedor de Playwright por digest y el reparto en trozos del #34 |
| Piloto | AgentShield una vez, en un contenedor, sobre la configuración del workflow |

**Hecho cuando:** la plantilla de proyecto trae los checks de este bloque y la calculadora los pasa (o tiene un baseline explícito de lo heredado).

## Bloque 4 — Revisión y reconciliación

**Por qué ahora:** con los controles fijos funcionando, los revisores IA se centran en lo que el código no puede comprobar (Kem: el juez solo donde el código no llega).

| Mejora | Qué se hace |
| --- | --- |
| **Reconciliación** | Cada revisor cierra sus propios hallazgos en la ronda siguiente. Para descartar un *debe corregirse* o un *importante* hace falta una prueba concreta (test, línea o cita), y si no la hay, se pregunta. Los hallazgos tienen formato fijo y la CI comprueba que todos tienen resolución. Se aplica el filtro "¿puede un usuario real llegar aquí?" y se exige una prueba por hallazgo (reglas del adversarial de Kem) |
| **M8** | La lista de "cambios tras la última ronda" la calcula la CI (diff desde el commit que vio el último revisor), no el agente. Cada revisión queda atada al SHA que vio (idea de la revisión con recibo de Gentle-AI) |
| **M13** | Encargo del revisor de spec: cruzar cada FR con los AC que lo citan |
| **M15** | Si dos revisores leen la spec de forma distinta, el agente pregunta; la respuesta se anota como aclaración y se pasa a la spec al cerrar la issue |
| **M1** | Camino corto para aclaraciones: un PR de spec, un revisor, una ronda |
| **M23** (rúbrica) | Un revisor con foco de mantenibilidad: los olores de Fowler (Pocock) y la rúbrica de calidad de thermos (sin leer la discusión del PR ni sus flujos de fusión), con la regla de no exagerar la gravedad |
| **M34** | Revisor en la CI con modelo configurable (compatible con OpenAI, por ejemplo DeepSeek de OpenCode Go): la clave como secreto de GitHub y permiso solo para comentar |
| Coste | Se mide cuánto cuesta cada revisión y se decide si el revisor de código R1 sigue aportando con los controles del bloque 3 (mejora #2 del primer recorrido) |

**Hecho cuando:** un PR de la calculadora pasa por la reconciliación nueva con el revisor de la CI, y la métrica de hallazgos confirmados queda registrada.

## Bloque 5 — Tu papel, la autonomía del agente y dejar este chat

**Por qué ahora:** es lo que más cambia tu día a día. Depende de los controles (bloques 2–3) y de la revisión fiable (bloque 4).

**ADR-0008 del workflow (modifica P03, G6, N4 y ADR-0006):**
- **Tu papel:**
  - la entrevista y la spec (G1);
  - las decisiones de producto y las lecturas de la spec (M15);
  - la prueba final del producto donde hace falta una persona;
  - publicar.
- **El agente:**
  - crea issues, planifica, implementa, revisa y reconcilia;
  - **fusiona lo que no es sensible** (M24) cuando la CI y G4 están en verde.
  - Tú apruebas solo specs, ADR, dependencias, CI, configuración del agente y rutas sensibles, con CODEOWNERS limitado a esas rutas y 0 aprobaciones generales en el ruleset.
- **Escalera de confianza (M24):**
  1. Primero, R0 y R1 que no toquen lo sensible.
  2. Después, R2 que no toque rutas sensibles, si en las entregas medidas no se escapa ningún defecto.
- **Dejar el chat:** el agente de WSL es el único sitio de trabajo.
  - **Linear:** escritura por MCP, salvo *Ready* y *Done*, si así lo decides.
  - **GitHub:** con `gh`, como ahora.
  - **Fuente de verdad:** el repo, no el Project.
  - **La app:** queda para el diseño visual y la exploración.
- **M18:** lo que puede hacer Claude con el navegador, si se sigue usando, queda recogido en el mismo ADR.
- **M4 y M20:** "Refs" por defecto con prueba manual; una sesión por PR también en entregas partidas, con el estado en `.tareas/`. Los subagentes se lanzan solo por un motivo explícito: explorar, verificar de forma independiente o relevar una sesión larga ("delegar por un motivo", de Gentle-AI).
- **M28:** la plantilla de la issue de Linear lleva el contrato: alcance, fuera de alcance, cuándo está hecho, ficheros permitidos y qué hacer si se bloquea.

**Hecho cuando:** el ADR-0008 está aceptado, el ruleset y CODEOWNERS de la calculadora están ajustados (eso lo haces tú) y una entrega completa pasa sin copiar nada desde este chat.

## Bloque 6 — Skills de producto y plantilla

**Por qué ahora:** con el papel definido, se afinan las herramientas de tu parte (la entrevista) y de la verificación.

| Mejora | Qué se hace |
| --- | --- |
| **M31** | `sdd-discover` adapta `grilling` y `domain-modeling` de Pocock: rondas sobre un árbol de decisiones, respuesta recomendada en cada pregunta, hechos buscados por el agente, glosario del dominio y fin cuando no queda nada sin decidir. La plantilla de spec recomienda escribir FR y AC con notación EARS ("Cuando…, la app deberá…") |
| **M41** | `sdd-status`: un comando que lee Linear y GitHub y dice en qué fase está cada issue (F0–F6), qué espera y cuál es el siguiente paso. Idea de la plantilla SDD de Juan Carlos Lagos |
| **M40** | Plantilla con `architecture.md` corto, `vision.md` como PRD ligero (salida de la entrevista) y modelo de amenazas solo en R2, con los requisitos de seguridad como NFR y AC |
| **M32** | Paquete de diseño (`design-system.md` con referencias visuales): fundamentos, componentes con todos sus estados y comportamiento |
| **M21 y M14** | `sdd-verify`, adaptada de pstack (`create`/`maintain-verification-skill`) con el paso de Kem: genera para cada proyecto el guion que arranca la app, la maneja como un usuario, guarda pruebas y compara con la referencia visual; se prueba rompiendo una función |
| **M22** | `sdd-bugfix`, adaptada de `diagnosing-bugs` de Pocock: primero un bucle que se pone en rojo con ese fallo |
| **M2** | `sdd-plan` parte las entregas de interfaz en PR que se prueban usándolos |

**Hecho cuando:** las skills nuevas pasan sus evaluaciones (M35) y la plantilla genera un proyecto nuevo con estos documentos.

## Bloque 7 — Modelos y portabilidad

**Por qué al final:** depende de tener tests con dientes (para "subir si falla") y de las evaluaciones del workflow (para comprobar otro ejecutor).

**ADR-0009 del workflow (modifica ADR-0002):**
- **M29:** una tabla en un solo fichero con qué modelo y qué esfuerzo para cada tarea, y la regla de empezar barato y subir si fallan los tests. Cambiar de modelo es cambiar una línea.
- **M30:** piloto de portabilidad con OpenCode y un modelo de Go, en contenedor, con los mismos ficheros y repitiendo N1–N8.
- **Perfil Go** (mejora #10 del primer recorrido): se retoma dentro de este bloque.
- **Medición fuera de Claude Code:** un medidor equivalente a `sdd-metricas` para OpenCode.
- **Evaluaciones con el modelo de Go:** si se adopta el perfil Go, el plugin se evalúa (M35) también con ese modelo, porque será el que lo use. Hasta entonces se evalúa solo con Claude.

**Hecho cuando:** el piloto de OpenCode completa una entrega pequeña pasando N1–N8, y la tabla de modelos tiene datos de coste y defectos de al menos dos modelos.

## Pilotos para el próximo proyecto

Se deciden con datos del próximo proyecto, no antes:
- **OpenSpec** como formato de spec, con nuestros controles encima.
- **Ponytail** (solo el texto de la skill) en una entrega, comparando con y sin.
- **Jev** cuando haya acceso, como juez de la reconciliación o para elegir modelo.
- **rtk** (edición completa, sin su proxy) en una entrega de implementación, midiendo el pico de contexto; nunca en la revisión.
- **Herdr y Sheprd** para ver qué hace el agente, después del bloque 5: Herdr en la terminal de WSL y Sheprd como interfaz gráfica en Windows (revisión de diffs con notas, anotaciones en el navegador). Desde el móvil, por SSH con Moshi. Cezar queda como alternativa web.
- **Headroom** en modo MCP, sin proxy, solo si el piloto de rtk no baja lo suficiente los picos de contexto.
- **Moshi** como terminal del móvil (por Tailscale, nunca SSH abierto a internet), junto con Herdr; imprescindible si se adopta OpenCode en el bloque 7, porque Remote Control solo funciona con modelos de Anthropic.

## Siguen en observación

- **M3:** tests primero, visibles en el historial.
- **Las estimaciones de tamaño.**
- **Del primer recorrido:** N6 con una inyección inocua (#8) y los hallazgos V1–V7 de la revisión independiente. Se revisan al cerrar el bloque 4.

## Cómo se trabaja cada bloque

1. Se abre una issue en Linear, en un proyecto nuevo para el workflow, con el contrato de la M28.
2. Si cambia una regla de fondo, primero su ADR, en su propio PR.
3. Los cambios, en PR pequeños, con las evaluaciones (M35) en verde.
4. Una línea en el CHANGELOG por versión (v1.1.0, v1.1.1…) y una nota en el historial con lo medido.
5. Al cerrar el bloque, una retrospectiva corta: ¿se cumplió el "hecho cuando"? ¿Hay algo que quitar?

# Trazabilidad D00–D59 → línea base

**Estado:** BORRADOR · **Última revisión:** 2026-10-19 (lagunas L1–L9 cerradas)
**Para qué sirve:** comprobar, decisión por decisión, que adoptar la línea base (Q01, opción A) no pierde nada del registro `historial/registro-D00-D59.md`.

## Cómo leerlo

Cada decisión tiene un estado:

- **CONSERVADA:** se mantiene igual; la línea base solo la resume o la concreta.
- **CONDENSADA:** se mantiene la intención con menos mecanismo. Es la reducción de sobreingeniería.
- **MODIFICADA:** cambia algo de fondo. Hay que aceptarla de forma consciente.
- **APLAZADA:** no entra en v1; tiene un disparador en la sección 10 de la línea base.
- **DESCARTADA:** se ha decidido conscientemente que no aporta, con una línea de motivo. Puede aplicarse a una decisión entera o a una parte de ella.

El objetivo de esta trazabilidad es que nada se pierda *sin querer*, no conservarlo todo: el criterio para mantener algo es que tenga sentido, no que estuviera en el registro (ADR-0001).

**LAGUNA** marca algo de la decisión que la línea base no recogía. Las nueve detectadas (L1–L9) se aceptaron y cerraron el 2026-10-19; su resolución ya está aplicada en la línea base y en la plantilla.

## Resumen

- 60 de 60 decisiones tienen destino; ninguna queda sin sitio.
- **Conservadas:** 30 · **Condensadas:** 20 · **Modificadas:** 8 · **Aplazadas:** 2.
- **Lagunas detectadas:** 9, todas cerradas (L1–L9). Son las que se habrían perdido adoptando la opción A sin esta comprobación.

## 01. Visión, descubrimiento y especificación

- **D00 Finalidad y ámbito** — CONSERVADA. *Dónde:* README, §1, §15. v1 es solo la vía personal; la adaptación al entorno profesional (GitLab, CI/CD propia) y la versión reducida quedan aplazadas en §10 (ADR-0004).
- **D01 Descubrimiento guiado por IA** — CONSERVADA. *Dónde:* F1 y la futura skill `sdd-discover`.
- **D02 Descubrimiento progresivo** — CONSERVADA. *Dónde:* F1 y `discovery/`.
- **D03 Especificación por capacidades** — CONSERVADA. *Dónde:* P01 y F2.
- **D04 Visión global y specs de capacidad** — CONSERVADA. ✔ LAGUNA L1 (cerrada): la estructura del repo no tiene sitio para la visión global ligera del producto. *Resolución aceptada:* añadir `docs/vision.md` a la plantilla.
- **D05 Plantilla de spec adaptable** — CONSERVADA. *Dónde:* plantilla de spec, con núcleo obligatorio y secciones opcionales.
- **D06 Sintaxis e identificadores** — CONSERVADA. *Dónde:* P01 y plantilla de spec (EARS y Given/When/Then).

## 02. Gobierno documental, aprobación y evolución

- **D07 Revisión independiente de specs** — MODIFICADA (aceptada, M1). Se mantienen dos jueces ciegos en todas las specs R1 y R2; en el código, dos en R2 y uno en R1. ✔ LAGUNA L2 (cerrada): los gates no dicen que G4 se aplique también a los PRs de spec, solo a los de código. *Resolución aceptada:* G4 se aplica a todo PR de spec R1/R2, con la rúbrica de `sdd-spec`.
- **D08 Aprobación humana verificable de specs** — MODIFICADA (aceptada, M2). *Dónde:* P03 y §8. El mecanismo es el merge humano en rama protegida, no un registro propio.
- **D09 Cambios normales, triviales y urgentes** — MODIFICADA (aceptada, M3). *Dónde:* R0–R2 (§6). La urgencia deja de ser una vía aparte y solo cambia la prioridad; la justificación de una excepción va en una línea del PR. La corrección urgente (hotfix) se diseña con la primera publicación (§10).
- **D10 ADRs selectivos** — CONSERVADA. *Dónde:* plantilla de ADR y `AGENTS.md`.
- **D11 Selección progresiva de tecnologías** — CONDENSADA. *Dónde:* `sdd-spec` (no inventar tecnologías) y ADR.
- **D12 Inicialización en dos etapas** — CONDENSADA. ✔ LAGUNA L3 (cerrada): no está escrito que un proyecto pueda empezar solo con documentación, sin stack ni CI de código. *Resolución aceptada:* la plantilla tiene una etapa documental (`discovery/` y `docs/`, que incluye las specs) y una técnica (`src/`, `tests/`, CI) que se añade al elegir tecnología.
- **D13 Fuentes de verdad y papel de Notion** — CONDENSADA (ADR-0003). *Dónde:* P02. Git sigue siendo la autoridad. La captura de ideas pasa al Inbox de Linear; Notion queda aplazado para investigación larga (§10). Obsidian sigue siendo compatible porque edita los mismos Markdown.
- **D14 Estado temporal de descubrimiento** — CONSERVADA. *Dónde:* `discovery/` y P10.
- **D15 Requisitos transversales sin duplicación** — CONSERVADA. ✔ LAGUNA L4 (cerrada): no hay convención para los requisitos compartidos entre specs. *Resolución aceptada:* specs transversales en `docs/specs/` con área `XCUT` (por ejemplo `SPEC-XCUT-001`), citadas por ID desde las demás.
- **D16 Trazabilidad documental y de entrega** — CONSERVADA. *Dónde:* G3 (check AC ↔ tests), plantilla de PR y revisión semántica en G4.
- **D17 Evolución spec-first y control del desvío** — CONSERVADA. *Dónde:* P01, `AGENTS.md` y plantilla de PR.

## 03. Entregas, Git e integración

- **D18 Linear y planificación de entregas** — CONSERVADA (ADR-0003). Linear es la fuente del estado de las entregas y de sus dependencias; las specs viven en Git. El principio "planes persistentes solo para tareas complejas" sigue en Q09.
- **D19 Estructura inicial de Linear** — CONSERVADA (ADR-0003). Un team, un proyecto por producto, issue por entrega; ciclos opcionales.
- **D20 Autonomía controlada sobre Linear** — CONDENSADA (ADR-0003). En v1 el agente solo lee Linear: las escrituras se bloquean con reglas de permisos, y los estados de ejecución los mueve la integración nativa. Las escrituras del agente quedan aplazadas (§10).
- **D21 Estados de entrega en Linear** — CONSERVADA (ADR-0003). Inbox → Discovery → Ready → In Progress → In Review → Done, más Canceled. Los tres primeros los mueve la persona; los de ejecución, la integración con GitHub. Ready es G2 y Done llega con G6.
- **D22 Ramas, PR y worktrees** — CONSERVADA. *Dónde:* §7 y §8. Los worktrees quedan aplazados junto con el paralelismo.
- **D23 Revisión independiente de código** — MODIFICADA (aceptada, M1). Dos revisores ciegos en R2; uno con contexto limpio en R1. El segundo revisor en R1 se reactiva si la métrica de defectos escapados lo justifica.
- **D24 Controles obligatorios de CI y merge** — CONSERVADA. *Dónde:* G5 y reglas de rama.
- **D25 Separar integración, publicación y recuperación** — CONSERVADA. *Dónde:* §7 ("fusionar no es desplegar"). El proceso de publicación se diseña cuando el primer proyecto publique.

## 04. Seguridad, permisos y herramientas

- **D26 Roles y permisos efectivos** — CONSERVADA. *Dónde:* P04, §8 (identidades) y §9.
- **D27 Protección frente a prompt injection** — CONSERVADA. *Dónde:* `AGENTS.md`, sandbox y caso N6.
- **D28 Gestión de secretos** — CONDENSADA. *Dónde:* §9, capa 4. Revocación = revocar el token del agente. Las credenciales temporales quedan para cuando haya acceso a servicios externos.
- **D29 Perfiles de aislamiento** — CONDENSADA. Un solo perfil en v1 (sandbox estricto en WSL2); el dev container es el siguiente escalón.
- **D30 Catálogo gobernado de herramientas y MCP** — CONDENSADA. *Dónde:* §9 ("solo MCP auditados"; `ask` si escriben). ✔ LAGUNA L5 (cerrada): no hay un sitio donde anotar qué MCP o herramientas están aprobados. *Resolución aceptada:* una lista breve en `docs/herramientas.md` del workflow, que se crea con el primer MCP.

## 05. Agentes, coordinación y ejecución

- **D31 Catálogo modular de roles** — CONDENSADA. En v1, implementador y revisor; el resto de roles son skills.
- **D32 Orquestación híbrida bajo demanda** — CONSERVADA. *Dónde:* P09 (un agente más un subagente revisor).
- **D33 Contratos de delegación** — CONDENSADA. *Dónde:* `CLAUDE.md` (qué recibe el revisor). El contrato general queda aplazado con el multiagente.
- **D34 Persistencia y reanudación** — CONSERVADA (ADR-0004, Q09). *Dónde:* P10 y `AGENTS.md`. La entrega vive en la issue de Linear; el plan y el progreso, en la descripción del PR borrador; las sesiones interrumpidas, en `.tareas/<ID>.md` fuera de Git, que se borra al cerrar.
- **D35 Paralelismo acotado** — APLAZADA (§10).
- **D36 Selección y sustitución de modelos** — MODIFICADA (aceptada, ADR-0002). Routing estático con dos perfiles en Claude Code: Claude por suscripción (principal) y Go para modelos ligeros. El reparto de tareas, las reglas de datos y el registro del modelo usado están en §5.
- **D37 Presupuestos y límites de ejecución** — CONDENSADA. *Dónde:* métricas de coste (§11). ✔ LAGUNA L6 (cerrada): no hay límite de reintentos o iteraciones antes de parar y avisar. *Resolución aceptada:* una línea en `AGENTS.md`: tras 3 intentos fallidos sobre el mismo problema, detenerse, resumir y preguntar.
- **D38 Observabilidad y supervisión remota** — CONDENSADA. *Dónde:* §8 (Remote Control y GitHub). La observabilidad propia queda aplazada.
- **D39 Contrato verificable de aprobación** — MODIFICADA (aceptada, M2). *Dónde:* §8. La caducidad es la invalidación de aprobaciones con cada push; la revocación, cerrar el PR o retirar la aprobación. Sin aprobaciones por lotes en v1. Las operaciones que no son un merge (despliegue, producción, escrituras externas) quedan deshabilitadas hasta que un ADR diseñe su aprobación; la evolución prevista está en §10.
- **D40 Orquestación y controles portables** — CONSERVADA. *Dónde:* P08.

## 06. Verificación, calidad y evals

- **D41 Verificación a partir de specs** — CONSERVADA. *Dónde:* G3 y `AGENTS.md`.
- **D42 Pirámide de pruebas adaptable** — CONDENSADA. *Dónde:* futura guía de testing de `sdd-implement` (pendiente en la hoja de ruta).
- **D43 Entornos y datos de prueba fiables** — CONDENSADA. ✔ LAGUNA L7 (cerrada): no hay regla para tests intermitentes (flaky). *Resolución aceptada:* una línea en `AGENTS.md`: un test intermitente se reporta como tal y no se da por bueno repitiéndolo hasta que pase.
- **D44 Calidad no funcional** — CONSERVADA. *Dónde:* plantilla de spec (NFR) y evidencia de NFR exigida en R2.
- **D45 Evaluaciones del workflow y agentes** — CONDENSADA. *Dónde:* casos N1–N8 y métricas (§11). Las evals versionadas quedan aplazadas.
- **D46 Evolución controlada del workflow** — CONSERVADA. *Dónde:* §15, ADR y `CHANGELOG.md`.

## 07. Arquitectura reusable e interfaces

- **D47 Núcleo modular y reutilizable** — CONSERVADA (ADR-0004, Q05). *Dónde:* `plantilla-proyecto/`, que aporta los ficheros del proyecto, y `plugin-sdd/`, que aporta las skills y los subagentes.
- **D48 Configuración declarativa por capas** — CONDENSADA. *Dónde:* §9: lo crítico va en ajustes de usuario, que el repo no puede relajar.
- **D49 Inicializador progresivo y repetible** — CONDENSADA. En v1, plantilla más guía de instalación. El inicializador asistido (una skill `sdd-init`) queda aplazado.
- **D50 Interfaz orientada a comandos** — CONSERVADA. *Dónde:* skills `sdd-*`, invocables como comandos. Invocar un comando no aprueba nada (P03).
- **D51 Catálogo pequeño de comandos y skills** — CONSERVADA. Seis skills en v1.
- **D52 Independencia de OpenCode y Claude Code** — MODIFICADA (aceptada, ADR-0002). Claude Code es el único harness en v1. El núcleo sigue siendo portable (P08), y el harness de OpenCode queda aplazado (§10). DESCARTADA la evaluación comparativa de harness: el usuario decidió no probar OpenCode como agente.

## 08. Adopción, cobertura y sostenibilidad

- **D53 Construcción incremental por recorridos completos** — CONSERVADA. *Dónde:* §11 y §15.
- **D54 Inventario vivo y auditoría de cobertura** — CONDENSADA. *Dónde:* este documento y `clasificacion-notas.md`. ✔ LAGUNA L8 (cerrada): falta la auditoría independiente en hitos. *Resolución aceptada:* antes de declarar v1.0, una revisión con contexto limpio (otra sesión o subagente) de esta trazabilidad y del resultado del primer recorrido.
- **D55 Continuidad ante fallos externos** — CONDENSADA. *Dónde:* P10. Con un solo sistema externo (GitHub), la reconciliación se reduce a mirar su estado real antes de reintentar.
- **D56 Clasificación y circulación de datos** — CONDENSADA. *Dónde:* P07 y §5 (modelos de Go permitidos salvo los "Contributor"). ✔ LAGUNA L9 (cerrada y después retirada): el campo `datos:` por proyecto se retiró en ADR-0004. Hay una sola vía, con Remote Control y la web siempre permitidos. DESCARTADA en v1 la clasificación por proyecto; vuelve con la adaptación al entorno profesional (§10).
- **D57 Protección y recuperación de información** — APLAZADA (§10). GitHub actúa como copia mientras tanto.
- **D58 Dependencias y código de terceros** — CONDENSADA. *Dónde:* una dependencia nueva es R2 y se instala dentro del sandbox. SBOM y firmas quedan aplazados.
- **D59 Evaluación híbrida del riesgo** — MODIFICADA (aceptada, M3). *Dónde:* R0–R2 para el cambio y `allow`/`ask`/`deny` para cada operación (§6, §9). El agente propone el nivel y la CI solo puede subirlo. DESCARTADA en parte: el riesgo inherente del proyecto como dimensión propia. Se expresa con las rutas sensibles que declara cada proyecto, porque un nivel mínimo obligaría a especificar hasta una errata.

## Lo que esta comprobación no cubre

Verifica que nada de D00–D59 se pierde, pero no que D00–D59 recogiera todas las necesidades reales; la propia auditoría lo advertía. Eso solo se comprueba usando el workflow: el primer recorrido, las retrospectivas y la regla de lagunas de Q01.

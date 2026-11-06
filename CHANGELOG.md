# Registro de cambios del workflow

Formato: una entrada por versión, la más reciente arriba. Las versiones 0.x son de diseño; la 1.0 es la primera usable.

## v1.1 — en curso

- **Autoría y convenciones (ADR-0007, VIC-16):**
  - `entorno/user-settings.json` lleva `"attribution": {"commit": "", "pr": "", "sessionUrl": false}`: ni commits ni PR mencionan a Claude.
  - `docs/convenciones.md` pasa a ser norma. La §7 de la línea base remite a ella y deja la "Autoría transparente" por commits a nombre de la cuenta de máquina sin menciones a Claude.
  - `plantilla-proyecto/AGENTS.md` y la plantilla de PR adoptan las convenciones; la plantilla pierde "Perfil y modelo" y abre con `Fixes VIC-N`.
  - `sdd-plan`, `sdd-spec` y `sdd-review` usan ramas `<tipo>/vic-<N>-…` y títulos con el alcance como zona; `sdd-implement` deja de pedir el perfil y el modelo.
  - `sdd-metricas.py` deduce la issue de las ramas `tipo/vic-N-…` sin perder el formato `vic-N-…`.
  - La guía de instalación cambia el *Default commit message* a "Pull request title and commit details", recoge en el ruleset de `sdd-workflow` el check `validar`, la revisión de Code Owners y la excepción "Allow for pull requests only", y usa ramas con ID en sus pruebas.
  - `README.md`: el repo del workflow se cambia por PR (M36). Cabeceras v1.1 en `plantilla-proyecto/.github/CODEOWNERS` y `sdd.yml` (C22).
  - `docs/convenciones.md` y `docs/linea-base-v1.md` pasan a CODEOWNERS.
  - Primer test de scripts (`tests/test_sdd_metricas.py`, `issue_de()`), que `validar` ejecuta. CODEOWNERS cubre además `plantilla-proyecto/AGENTS.md` y `CLAUDE.md`, `README.md`, `tests/`, `.claude-plugin/` y, si llegan a existir, `.claude/`, `AGENTS.md` y `CLAUDE.md` de la raíz (línea base §8).
- **Plugin `sdd` 1.1.0.** Tras fusionar: `claude plugin marketplace update sdd-workflow && claude plugin update sdd@sdd-workflow`.

## v1.0 — 2026-11-05 (primera versión usable)

El workflow queda declarado tras dos recorridos completos con la calculadora de discos (VIC-5 a VIC-15), los ocho casos negativos y las pruebas de la revisión independiente.

- **Pruebas C18–C20** (`historial/recorrido-1.md`): las barreras del sistema funcionan sin depender del modelo.
  - C18: `checks-sdd` rechaza una spec que no está en `main` y la mezcla de spec y código (PR #38).
  - C19: el ruleset rechaza el push directo del agente a `main` (`GH013`).
  - C20: sin proxy no hay red y `~/.ssh` aparece vacío dentro del sandbox.
- **Marcas "BORRADOR" retiradas** de plantillas, skills y documentos aceptados; versiones y referencias desfasadas corregidas (C22): README, guía de instalación, hoja de ruta y herramientas. Quedan los comentarios de cabecera de los cuatro ficheros de `plantilla-proyecto/.github/`, que solo se pueden cambiar desde Git: van en el primer PR del bloque 1.
- **Documentos nuevos desde la v0.23:**
  - segundo recorrido y su retrospectiva (`historial/recorrido-2.md`, `historial/retrospectiva-2.md`);
  - análisis de herramientas externas (`historial/analisis-herramientas-1.md`);
  - plan de la v1.1 (`docs/plan-v1.1.md`), glosario (`docs/glosario.md`) y convenciones propuestas (`docs/convenciones.md`, M42).
- **Linear:** team "Desarrollo" (clave `VIC`), etiquetas Tipo, Riesgo y Origen, plantillas Bug, Spec y Mejora del workflow, y proyecto "Workflow SDD v1.1" con un hito por bloque.
- **Plugin `sdd` 1.0.0.** Tras el push: `claude plugin marketplace update sdd-workflow && claude plugin update sdd@sdd-workflow`.

## v0.23 — 2026-10-29 (medición del segundo recorrido)

- **Registro del segundo recorrido** (`historial/recorrido-2.md`): lo hecho, métricas, nueve observaciones y diez mejoras candidatas para la v1.1 (M1–M10). La hoja de ruta gana la sección F.
- **Métricas automáticas por sesión (M9):** la línea de estado `entorno/sdd-metricas.py` guarda el coste estimado, las duraciones, los tokens, el pico de contexto, la rama y la issue de cada sesión del agente, sin `/usage` a mano. `entorno/resumen-metricas.py` las resume en tablas. Cambian `user-settings.json` y el bloque B5 de la guía.

## v0.22 — 2026-10-23 (revisión independiente)

Una sesión nueva, sin el historial, revisó el workflow antes de la v1.0: 31 hallazgos (`historial/revision-independiente-1.md`). Se resuelven todos salvo las pruebas que hace Víctor (C18–C20) y los siete de la v1.1 (V1–V7).

- **ADR-0006, "Ajustes del primer recorrido":** reúne las decisiones de la v0.12 a la v0.21 que solo estaban en el CHANGELOG (C3) y resuelve los dos bloqueos.
  - **B1, Claude con el navegador:** ayuda a la persona, pero no es un agente del workflow. Nunca mueve a *Ready*, aprueba, fusiona, publica ni toca ajustes. Registrado en `herramientas.md` como límite aceptado.
  - **B2, perfil Go:** sale de la v1.0 y pasa a §10 con su disparador.
  - Modifica ADR-0002, ADR-0003 y ADR-0005; el índice lo anota.
- **`checks.py`:**
  - un ADR es como mínimo R1 (C7);
  - un PR de código hereda el riesgo de la spec que implementa, y un PR de spec no puede bajar el suyo (C13);
  - `no aplica` exige el motivo entre paréntesis, y un PR de código en R0 o sin AC sale con un aviso ⚠️ (C12);
  - el resumen lista los tests existentes que el PR modifica o borra (C14).
  - Probado en un repo local con seis escenarios.
- **Gates (C10, C11):** la línea base distingue los gates que impone el sistema de los que dependen del agente (*Ready* y G4). G4 deja rastro: el encargo literal de cada revisor y su respuesta, plegados en el PR.
- **Revisión (C6–C8):**
  - lista única de lo que recibe el revisor, en `sdd-review`;
  - la guía del revisor humano la comprueba el orquestador, no el revisor;
  - los PR de ADR llevan 2 revisores;
  - hasta 3 rondas (la inicial y 2 repeticiones).
- **Coherencia (C1, C2, C4, C5, C9, C21):**
  - lista canónica de disparadores de R2 en §6, con `CLAUDE.md`;
  - "Sí, sin actualizar la spec" sale de la plantilla del PR;
  - R2 pide evidencia de NFR y plan de vuelta atrás;
  - nueve entradas desfasadas corregidas en la trazabilidad y la línea base;
  - la retrospectiva separa lo que bloqueó el sistema de lo que bloqueó el agente.
- **PR de la persona (C15):** los R2 pasan `sdd-review` antes del bypass.
- **Repo del workflow (C17):** hasta la v1.1, por commits directos, declarado en el README.
- **Playwright (C16):** los navegadores se instalan desde fuera del repo, con versión fijada, para no ejecutar fuera del sandbox el `node_modules` del agente.
- **Pendiente para la v1.0:** las pruebas C18–C20, y quitar las marcas BORRADOR y las versiones desfasadas (C22).
- **Plugin `sdd` 0.6.0.**

## v0.21 — 2026-10-23 (retrospectiva del primer recorrido)

Retrospectiva en `historial/retrospectiva-1.md`. Entran en la v1.0 las tres mejoras baratas y con evidencia; el resto pasa a la v1.1.

- **Interacciones entre reglas** (`sdd-spec` y `reviewer`): la auditoría y la revisión de specs recorren los estados intermedios y las reglas que actúan a la vez. Es la causa del único defecto escapado (validación más recálculo en vivo).
- **Rondas de revisión** (`sdd-review`): después de la ronda 2, las aclaraciones de la persona se aplican sin otra ronda, salvo reglas nuevas, con la lista exacta de cambios en el PR. Se había decidido a mano en los PR #2, #3 y #6.
- **Cómo diseñar las pruebas de casos negativos** (línea base §11): acciones y no razonamiento, señuelos inocuos, prompts sin pistas, y no esquivar las salvaguardas. Lo motivan tres sesiones bloqueadas.
- **Guía: "Cómo revisar un PR en GitHub"**, dónde está cada cosa que compruebas al aprobar.
- **Primer recorrido:** N1–N8 cerrados. Pendiente para la v1.0: revisión independiente y quitar las marcas "BORRADOR".
- **Plugin `sdd` 0.5.0.**

## v0.20 — 2026-10-22 (fase D en curso)

- **Revisores con Sonnet:** el subagente `reviewer` usa `model: sonnet`. En R2, el revisor de seguridad se lanza con Opus (`sdd-review`). Motivo: `/usage` atribuía un 90 % del consumo de las últimas 24 h a los subagentes de revisión, y Sonnet ya había encontrado defectos reales en el PR #5. Se revierte si la métrica de defectos escapados lo justifica.
- **Plugin `sdd` 0.4.0.** Tras el push: `claude plugin marketplace update sdd-workflow && claude plugin update sdd@sdd-workflow`.
- **Primer recorrido:** N1 verificado (VIC-7: el agente se negó a implementar una spec "aprobada" que no estaba en `main`).

## v0.19 — 2026-10-22 (fase D en curso)

Ajustes que salieron al adoptar la v0.18 en `calculadora-discos` (PR #9).

- **`AGENTS.md`:** los ADR tienen autoridad si están `Aceptado` **y fusionados en `main`**. Con la v0.17, `Aceptado` se escribe antes del merge.
- **Ramas `chore-…`** para mantenimiento (`AGENTS.md`, línea base §7).
- **Plantilla de README:** "Etapa" no habla de `src/`, y avisa de que la CI no la lee.
- **Corrección:** la entrada v0.18 decía que `checks.py` lee "Etapa". No es así: solo lee "Rutas sensibles".
- **Pendiente para la v1.0:** quitar las marcas "BORRADOR" de plantillas y skills al declararla.

## v0.18 — 2026-10-22 (fase D: camino feliz completo)

Criterio nuevo: **profesional y coherente, sin burocracia** (línea base §1). Ningún check nuevo en la CI.

- **Convenciones de GitHub** (línea base §7, `AGENTS.md`, plantilla del PR):
  - títulos de PR en Conventional Commits, con el ID como alcance;
  - solo squash, con el título como mensaje;
  - ramas `vic-N-…`, `spec-…`, `adr-…` y `ci-…`, borradas al fusionar;
  - releases semver con notas generadas;
  - `Co-Authored-By` del agente.
- **PR pequeños:** unas 400 líneas de código por PR, orientativas. `sdd-plan` parte las entregas grandes y usa "Part of <ID>" en los PR intermedios.
- **Qué afirma tu aprobación** (línea base §8): no certifica cada línea; certifica la evidencia y acepta el riesgo restante. Hay una lista de cinco minutos con casillas en la plantilla del PR, y una lectura completa de specs, ADR y todo test existente que cambie. Es un límite aceptado.
- **"Guía para el revisor humano"** en la plantilla del PR: mapa, dónde mirar, tests que cambian, evidencia y tamaño. La rellena `sdd-implement`, `sdd-review` pide a los revisores que busquen tests debilitados, y `sdd-review` comprueba el título y la guía antes de quitar el borrador.
- **Plugin `sdd` 0.3.0.** Tras el push: `claude plugin marketplace update sdd-workflow && claude plugin update sdd@sdd-workflow`.
- **Plantilla de README:** portada profesional con insignia de CI, funcionalidad enlazada a specs, arquitectura enlazada a ADR, desarrollo y "Cómo se trabaja aquí". `checks.py` sigue leyendo "Etapa" y "Rutas sensibles".
- **Una sesión por PR,** y nunca dos sesiones sobre la misma copia del repo (`AGENTS.md`).
- **Guía:**
  - B2: interop de WSL desactivado (seguridad) y Node con nvm;
  - A4: ajustes de PR del repo (solo squash, borrar ramas);
  - nuevo bloque G con los tests, los navegadores de Playwright fuera del sandbox, Pages con dominio verificado, la publicación manual y las releases;
  - desviaciones de la fase D.
- **Ejemplos probados** en `docs/ejemplos/workflows/`: `tests-node-playwright.yml` y `deploy-pages.yml`, los de `calculadora-discos`.
- **Primer recorrido:** camino feliz completo, de la spec al iPhone (iOS 27.0.1), con N3 y N7 verificados. Faltan N1, N2, N6 completo y N8. Ver `historial/recorrido-1.md`.

## v0.17 — 2026-10-21 (fase D en curso)

- **Estado del ADR:** `AGENTS.md` y la plantilla de ADR. El agente pasa el ADR a `Aceptado` en el último commit de su PR, cuando la revisión termina, como ya hace con `aprobada` en las specs (v0.16). Lo detectó el agente: ADR-0001 llegó a `main` como `Propuesto`, y `AGENTS.md` solo reconoce los `Aceptado`. En `calculadora-discos` se corrige dentro del PR de spec que enlaza el ADR.
- **Tamaño del ADR:** la plantilla pide solo decisiones y su porqué, en una o dos páginas. El cómo va al plan o al PR. Es la lección de ADR-0001 (de 306 líneas a unas dos páginas).
- **Pendiente:** llevar el `AGENTS.md` nuevo a `calculadora-discos` (PR R2), porque los proyectos tienen una copia de la plantilla.

## v0.16 — 2026-10-21 (fase D en curso)

- **Estado de la spec:** `sdd-spec` y la plantilla de spec. El agente escribe `estado: aprobada` en el último commit del PR de spec, cuando la revisión termina sin nada que corregir. Antes nadie lo cambiaba y la spec llegaba a `main` como `en-revision`. Sigue sin autorizar nada sin el merge (N1). Plugin `sdd` 0.2.0: tras el push, en WSL `claude plugin marketplace update sdd-workflow` y `claude plugin update sdd@sdd-workflow`.
- **Métricas del primer recorrido:** nuevo `historial/recorrido-1.md`, con las cuatro métricas de §11, las desviaciones del camino feliz (idea fuera del Inbox de Linear, nombre de las notas) y el estado de N1–N8.
- **Guía:** notas de entorno de la fase D (permisos al copiar desde `/mnt/c`, `gh pr edit` y Projects classic, puntos de montaje en `git status`).

## v0.15 — 2026-10-21 (fase C en curso)

- **Bloque D hecho.** Claude configuró Linear desde tu Chrome, porque el navegador integrado no podía iniciar sesión:
  - team VIC con los estados de D21;
  - automatizaciones de PR: borrador o abierto → In Progress, revisión pedida → In Review, fusionado → Done;
  - plantilla "Entrega SDD" y proyecto "Calculadora de discos";
  - ramas con el formato `vic-123-titulo`;
  - la app Linear Code solo ve `calculadora-discos`;
  - issues de ejemplo canceladas.
- **MCP de Linear verificado:** el agente lee las issues y no puede moverlas. El endpoint solo tiene herramientas de lectura, `AGENTS.md` también lo prohíbe, y el agente no buscó otra vía.
- **Bloque E hecho:** Remote Control con `/remote-control`. Un permiso `ask` llegó como notificación al iPhone y se denegó desde allí. La prueba de GitHub Mobile se hará con el PR de la spec.
- **Bloque F (perfil Go) aplazado** a después del primer recorrido: no lo bloquea.
- **Límite aceptado:** la app de Linear tiene escritura en código y workflows del repo que se le da (app oficial, repos elegidos y ruleset de `main`).

## v0.14 — 2026-10-20 (fase C en curso)

- **Corrección de seguridad, R2:** se quita `Read(~/.config/gh/**)` de los ajustes gestionados.
  - Claude Code aplica las reglas `Read` también al sandbox y ocultaba el token de `victor-lg-bot`: el agente no podía empujar ni abrir PR.
  - La protección de ese token es la de GitHub (ADR-0005).
- **B5 verificado:**
  - escritura fuera del proyecto, bloqueada;
  - red con lista blanca: `example.com`, 403; `github.com`, sí;
  - lectura de credenciales, bloqueada por la regla y por el sandbox, comprobado con un fichero señuelo;
  - salida directa sin proxy: documentada, no medida.
- **B6 verificado:** el plugin se instala desde `victor-lg/sdd-workflow` con 6 skills, 1 agente y ~760 tokens fijos.
- **Aprendido y anotado** en la línea base (§9, límites) y en la guía:
  - el modo `!` también va por el sandbox;
  - el sandbox oculta las carpetas protegidas ("no existe");
  - las pruebas formuladas como sondas activan las salvaguardas del modelo.
- **Primer recorrido:** descubrimiento cerrado y spec `SPEC-CALC-001` lista para revisión, en el proyecto (desde el móvil).
- **Bloque C hecho:**
  - PR #1 de `calculadora-discos` abierto por `victor-lg-bot` desde el sandbox;
  - `checks-sdd` en verde en 6 s y ya obligatorio en el ruleset;
  - fusionado por `victor-lg` tras aprobarlo.
- **Casos negativos adelantados:**
  - N4: `gh pr merge` rechazado por el ruleset;
  - N5: push de `.github/workflows/x.yml` rechazado por falta de `workflow`.
- **Límite conocido:** el sandbox protege `.git/config`, así que el agente no puede fijar el seguimiento de la rama (`set-upstream`). No afecta al push ni al PR.

## v0.13 — 2026-10-20 (fase C en curso)

- **Bloque A hecho**, a medias entre Claude (navegador integrado) y Fork:
  - repos `sdd-workflow` y `sdd-template` (plantilla), privados;
  - repo `calculadora-discos` creado desde la plantilla;
  - `checkout` fijado a v7.0.1 por SHA;
  - ruleset `main-protegida` en `calculadora-discos`, con excepción del admin solo para PR y aprobación obligatoria del último push.
- **Cuenta de máquina `victor-lg-bot` invitada a los dos repos.**
  - Hecho: en los repos de una cuenta personal no hay rol "Read", todo colaborador escribe.
  - Decisión: el `main` de `sdd-workflow` se protege con un ruleset; el agente solo abre PR y tu excepción es "Always allow" para seguir usando Fork.
  - Precisa lo que v0.11 anotó sobre ADR-0005 (rol Read).
- **Token de la cuenta de máquina:** `repo` + `read:org`, porque `gh auth login` lo exige. `read:org` solo lee la pertenencia a organizaciones. Sigue sin `workflow` (N5 intacto). Precisa ADR-0005, que decía solo `repo`.

## v0.12 — 2026-10-19 (diseño)

- **Guía de instalación reordenada en bloques A–F.** Primero Windows con tu cuenta: ficheros, repos y cuenta de máquina. Después WSL con la cuenta del agente, que clona el workflow desde GitHub. Corrige un hueco de la v0.11: no explicaba cómo llegaban los ficheros a WSL.
- **Bloque C nuevo, la prueba de punta a punta del PR:**
  - push desde el sandbox;
  - `checks-sdd`;
  - N4 (el agente no puede fusionar);
  - N5 opcional (el token no puede tocar `workflows`).
  - El check requerido se añade cuando GitHub ya lo conoce.
- Sección "Desviaciones encontradas" en la guía, para registrar lo que no funcione como dice.
- El perfil Go (bloque F) se marca como no bloqueante para el primer recorrido.
- Cliente Git en Windows: **Fork** en lugar de GitHub Desktop (A2, A3). Como Fork no crea repos en GitHub, el repo vacío se crea en la web y después se añade el remoto.

## v0.11 — 2026-10-19 (diseño)

- **Fase B terminada.** Ajustes de Claude Code, perfil Go, marketplace y guía de instalación.
- **`entorno/managed-settings.json`** (va en `/etc/claude-code/`):
  - sandbox estricto y obligatorio;
  - red con lista blanca estricta (GitHub, npm, PyPI);
  - credenciales ocultas a los comandos y a la herramienta Read;
  - `ask` al añadir dependencias;
  - el modo "saltarse permisos" desactivado.
  - Validado con `claude doctor`.
- **Corrección de §9 y H16:** las claves de seguridad van en ajustes **gestionados**, no de usuario. Según la documentación, solo los gestionados (o `--settings`) impiden que un repo relaje el sandbox.
- **`entorno/user-settings.json`:** Remote Control en todas las sesiones y canal `stable`.
- **Perfil Go:** función `claude-go` en `entorno/claude-go.sh`.
  - Hecho nuevo (§3.4): desde Claude Code solo sirven los modelos de Go compatibles con la API de Anthropic. **DeepSeek V4.1 Flash no lo es.** Modelo por defecto: Qwen3.8 Flash.
  - Remote Control no funciona contra Go: el perfil Go queda solo para el PC, como preveía ADR-0002.
  - La URL base se confirma en la fase C.
- **Linear:** el MCP se conecta al endpoint oficial de solo lectura (`https://mcp.linear.app/mcp/readonly`). Sustituye a las reglas `deny` sobre herramientas de escritura.
- **Plugin:**
  - el repo del workflow es el marketplace (`.claude-plugin/marketplace.json`);
  - `claude plugin validate` pasa;
  - instalado en local: 6 skills, 1 agente, ~760 tokens fijos.
  - La cuenta de máquina necesita rol Read en este repo para instalarlo. Es una ampliación menor del alcance de ADR-0005, que solo la preveía en los repos del proyecto.
- **Documentación nueva:**
  - `docs/guia-instalacion.md`: fase C paso a paso, con comprobaciones y fuentes;
  - `docs/herramientas.md`: registro de lo aprobado y lo descartado (ponytail).

## v0.10 — 2026-10-19 (diseño)

- **Fase B: CI de la plantilla.** `.github/workflows/sdd.yml` + `.github/sdd/checks.py` (Python estándar, sin dependencias), un único check requerido `checks-sdd`:
  - *specs:* frontmatter, ID, nombre de fichero `<ID>-<nombre>.md`, secciones 1–6, IDs únicos, cada AC → FR/NFR existente.
  - *mezcla:* un PR no cambia spec y código a la vez (N2).
  - *trazabilidad (G3):* los AC declarados en el PR existen en la spec de `main` (N1) y algún test los cita (N7); publica la matriz AC ↔ tests.
  - *riesgo:* nivel mínimo por rutas, manifiestos, rutas sensibles del README y `riesgo` de la spec; falla si el PR marca menos.
  - La CI ejecuta el script y lee las rutas sensibles **desde `main`**, para que un PR no pueda debilitar sus propios checks.
  - Probado con 12 escenarios (camino feliz y negativos) en un repo local.
- **Formato canónico de cita de AC:** `SPEC-XXX-NNN/AC-NN`, en tests y en el PR. Actualizados `AGENTS.md`, la plantilla de PR, `sdd-plan`, `sdd-implement` y `sdd-spec`.
- **G3 precisado** en la línea base: se exige cobertura de los AC que el PR declara; los de entregas futuras salen en la matriz sin bloquear.
- `CODEOWNERS` en la plantilla. Plantilla de issue para Linear en `docs/plantilla-issue-linear.md` (las issues no viven en GitHub).
- Pendiente de verificar en la fase C: fijar `actions/checkout` por SHA.

## v0.9 — 2026-10-19 (diseño)

- **Fase B: skills del plugin escritas (borrador).** `sdd-context`, `sdd-discover`, `sdd-plan`, `sdd-implement` y `sdd-review`, más el subagente `reviewer` (solo lectura: Read, Grep, Glob). Con `sdd-spec`, el plugin cubre de F1 a G4.
- `sdd-implement` incorpora la escalera de "cambio mínimo completo" inspirada en la skill ponytail (MIT), sin instalar el plugin.
- Ponytail evaluado y **no instalado** en v1: instala hooks y una statusline que corren fuera del sandbox (sería R2 y requeriría `docs/herramientas.md`) y se solapa con `sdd-implement` y `sdd-review`. Candidato a prueba medida en v1.x.

## v0.8 — 2026-10-19 (diseño)

- **Q04 cerrada → ADR-0005.** El agente usa una cuenta de máquina colaboradora con token clásico (`repo`, sin `workflow`, 90 días). Con esto, **todas las decisiones abiertas Q01–Q09 quedan cerradas**.
- Confirmado: se excluyen los modelos "Contributor" de OpenCode Go.
- Primer recorrido: sin Mac y sin App Store; la PWA es la candidata natural para el ADR técnico.

## v0.7 — 2026-10-19 (diseño)

- **Q05–Q09 cerradas → ADR-0004.**
  - Q05: núcleo híbrido, con repo plantilla (`plantilla-proyecto/`) y plugin de Claude Code (`plugin-sdd/`).
  - Q06: el primer recorrido es una calculadora de discos para series de calentamiento, en iOS.
  - Q07: una sola vía de datos; se retira el campo `datos:`; el entorno profesional (GitLab) se aplaza.
  - Q08: rutas `docs/specs/` y `docs/adr/`.
  - Q09: progreso en la issue de Linear y el PR borrador, y `.tareas/` fuera de Git.
- Hecho verificado 3.7: límites de GitHub (protección de ramas en privados con Pro; tokens de grano fino; cuentas de máquina). Q04 se reformula.
- La plantilla se reorganiza: specs en `docs/specs/`, `.gitignore` nuevo, sección de datos retirada del README y PR con "Plan y progreso". La skill `sdd-spec` se mueve a `plugin-sdd/`.

## v0.6 — 2026-10-19 (diseño)

- **Q03 cerrada → ADR-0003.** GitHub es la autoridad (código, specs, aprobación) y Linear se usa para planificar (Inbox, backlog, dependencias, estados de D21). La integración nativa mueve los estados de ejecución, y el agente solo lee Linear. D18–D21 se recuperan.
- Uso del móvil: el trabajo principal es en el PC; el iPhone, para continuar cuando estás fuera.
- Notion: aplazado (no descartado); la captura de ideas pasa al Inbox de Linear.
- Línea base: §5, §7 (G2 y Done), §8, §10, §11 (preparación con Linear, N1 ampliado) y §12–§13 actualizados. Plantillas: `AGENTS.md` y PR con el ID de Linear.

## v0.5 — 2026-10-19 (diseño)

- **Q02 cerrada → ADR-0002.** Claude Code es el único harness, con dos perfiles de modelo: Claude por suscripción (principal) y OpenCode Go para modelos ligeros. Reglas de datos por perfil. Sin experimento comparativo con OpenCode.
- Línea base: hechos verificados 3.4 (OpenCode Go desde Claude Code), 3.5 (OpenCode sin sandbox) y 3.6 (sin comparación objetiva de harness); nueva subsección "Ejecutor y perfiles de modelo" en §5; §9 y §10 actualizadas.
- Plantilla de PR: sección "Perfil y modelo".

## v0.4 — 2026-10-19 (diseño)

- **Q01 cerrada → ADR-0001.** La línea base es la capa normativa: §4, §6 y §7 quedan ACEPTADAS y el resto sigue como PROPUESTA. D00–D59 pasa a historial, con la regla de lagunas.
- Modificación M3 aceptada (D09/D59): rutas sensibles declaradas por proyecto en su README; se descarta el nivel mínimo por proyecto; la corrección urgente se añade a la §10.
- Nuevo estado DESCARTADA en la trazabilidad. El criterio para conservar algo es que tenga sentido, no que estuviera en el registro.
- Plantilla de README del proyecto: sección "Rutas sensibles".

## v0.3 — 2026-10-19 (diseño)

- Trazabilidad decisión a decisión de D00–D59 a la línea base (`docs/trazabilidad-D00-D59.md`): 27 conservadas, 19 condensadas, 9 modificadas y 5 aplazadas.
- Nueve lagunas detectadas y cerradas, con las resoluciones aceptadas por el usuario:
  - L1 (D04): `docs/vision.md` en cada proyecto.
  - L2 (D07): G4 también en los PRs de spec R1/R2.
  - L3 (D12): etapas documental y técnica del proyecto.
  - L4 (D15): specs transversales `SPEC-XCUT-*`, citadas por ID.
  - L5 (D30): registro `docs/herramientas.md`, creado con el primer MCP; añadir uno es R2.
  - L6 (D37): detenerse y preguntar tras 3 intentos fallidos.
  - L7 (D43): los tests intermitentes se reportan; no se repiten hasta que pasen.
  - L8 (D54): revisión independiente antes de v1.0 y de cada versión mayor.
  - L9 (D56): campo `datos:` (personal | confidencial) en el README del proyecto.
- Nuevas plantillas: `README.md` y `docs/vision.md` del proyecto.
- Modificación M1 aceptada (D07/D23, opción B): 2 revisores ciegos en specs R1 y en todo R2; 1 en el código R1. Actualizados la línea base (§6, §7, §10, §12, §13), la trazabilidad, `CLAUDE.md` y la plantilla de PR.
- Modificación M2 aceptada (D08/D39, opción A): GitHub es el único mecanismo de aprobación en v1; las operaciones que no se pueden aprobar ahí quedan deshabilitadas hasta tener ADR. Evolución prevista añadida a §10.
- Q01 sigue abierta: falta M3 (riesgo, D09/D59).

## v0.2 — 2026-10-19 (diseño)

- Estructura del repositorio del workflow (`README.md`, `docs/`, `plantilla-proyecto/`, `historial/`).
- Clasificación de las notas originales por destino (`docs/clasificacion-notas.md`).
- Hoja de ruta y ciclo de versiones (`docs/hoja-de-ruta.md`).
- Borradores de plantilla de proyecto a partir de las notas: `AGENTS.md`, `CLAUDE.md`, plantilla y ejemplo de spec, plantilla de ADR, plantilla de PR y skill `sdd-spec`.
- Línea base: nuevas decisiones abiertas Q08 (rutas de documentos) y Q09 (dónde vive el progreso de una tarea); nueva sección 15 sobre el ciclo de versiones.

## v0.1 — 2026-10-18 (diseño)

- Línea base v1 (propuesta) a partir del registro D00–D59 y la auditoría H01–H24.
- El registro D00–D59 y la auditoría pasan a historial.

# Registro de cambios del workflow

Formato: una entrada por versión, la más reciente arriba. Las versiones 0.x son de diseño; la 1.0 es la primera usable.

## v0.15 — 2026-10-21 (fase C en curso)

- **Bloque D hecho.** Claude configuró Linear desde tu Chrome, porque el navegador integrado no podía iniciar sesión:
  - team VIC con los estados de D21;
  - automatizaciones de PR: borrador o abierto → In Progress, revisión pedida → In Review, fusionado → Done;
  - plantilla "Entrega SDD" y proyecto "Calculadora de discos";
  - ramas con el formato `vic-123-titulo`;
  - la app Linear Code solo ve `calculadora-discos`;
  - issues de ejemplo canceladas.
- **MCP de Linear verificado:** el agente lee las issues y no puede moverlas. El endpoint solo tiene herramientas de lectura, `AGENTS.md` también lo prohíbe, y el agente no buscó otra vía.
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

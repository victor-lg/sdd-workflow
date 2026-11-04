# Análisis de herramientas externas para la v1.1

Fecha: 2026-11-04. Fuente: los repos clonados en `C:\Users\victor\Documents\herramientas` (leídos, nada ejecutado) y, para Jev, su documentación pública. Es historial, no norma: lo que se acepte entra por la v1.1.

## Criterios

Para cada herramienta:
- qué problema nuestro resuelve, con evidencia de los recorridos;
- qué instala y qué ejecuta;
- licencia y mantenimiento;
- riesgo de inyección y de cadena de suministro;
- portabilidad (Claude Code, OpenCode u otros);
- recomendación: **adoptar** (tal cual), **adaptar** (copiar y ajustar a nuestro workflow), **inspirarse** (tomar ideas), **piloto** (probar con métrica) o **descartar**.

## Reglas comunes que salen del análisis

1. **Una skill de terceros es un conjunto de instrucciones.** No se instala desde fuera ni se actualiza sola. Se copia una versión fijada dentro del plugin `sdd`, se revisa el texto y se cita la fuente. Todas las que interesan tienen licencia MIT, que permite copiar si se conserva el aviso de licencia.
2. **No se abre Claude Code dentro de un repo de terceros.** Los ajustes y hooks del proyecto se cargan al abrirlo. Hubo dos vulnerabilidades en 2026: CVE-2025-59536 (ejecución antes del diálogo de confianza) y CVE-2026-21852 (desvío de `ANTHROPIC_BASE_URL` y fuga de la clave). La carpeta `herramientas` se lee desde fuera.
3. **Sin hooks de terceros.** Se toma el texto de la skill y, si hace falta un hook, lo escribimos nosotros (M25).
4. **La "trifecta letal"** (Simon Willison, citada en la guía de seguridad de ECC) sirve para evaluar cada pieza nueva. Si una misma ejecución tiene **datos privados + contenido no fiable + salida al exterior**, una inyección puede sacar datos. Hay que romper al menos una de las tres.

---

## 1. Skills de Matt Pocock (`mattpocock/skills`)

- **Qué es:** 39 skills pequeñas y combinables. Las mantiene con un criterio estricto: solo cambia una skill si hay un fallo observado en una sesión real, el mismo criterio que nuestra regla de "una mejora entra solo si responde a algo observado".
- **Licencia y mantenimiento:** MIT; último commit el 2026-10-31.
- **Instalación propuesta por él:** un plugin que se actualiza solo. **No** lo usaríamos así (regla 1).
- **Riesgo:** bajo. Son textos cortos, y los únicos scripts son plantillas de shell opcionales.

| Skill | Qué hace | Encaja con | Recomendación |
| --- | --- | --- | --- |
| `grilling` (y `grill-me`, `grill-with-docs`) | Entrevista por rondas sobre un "árbol de decisiones". En cada ronda pregunta todo lo que ya se puede decidir, numerado y con su respuesta recomendada. Los hechos los busca el agente con subagentes; las decisiones son de la persona. Termina cuando no queda ninguna rama sin decidir | **M31**, la entrevista, que pasa a ser tu trabajo principal | **Adaptar** como núcleo de `sdd-discover` |
| `domain-modeling` | Glosario del dominio (`GLOSSARY.md`) que se actualiza durante la conversación. Contrasta con el código lo que dice la persona y solo propone un ADR si la decisión es difícil de revertir, sorprendente sin contexto y fruto de un compromiso real | M31, y nuestro criterio de ADR (lo confirma) | **Adaptar** el glosario del dominio en la plantilla |
| `tdd` | Tests en las fronteras públicas acordadas. Antipatrones: el test acoplado a la implementación, el **tautológico** (recalcula lo esperado igual que el código, así que nunca falla) y escribir todos los tests de golpe | **M26** (tests con dientes) y M3 | **Adaptar** los antipatrones en `sdd-implement` |
| `diagnosing-bugs` | Primero construir un bucle que se ponga en rojo con *ese* fallo; luego reproducir y minimizar, 3–5 hipótesis ordenadas y el arreglo. Prohíbe teorizar antes de tener el bucle | **M22** | **Adaptar** como base de `sdd-bugfix` |
| `code-review` | Dos revisores en paralelo y separados: **estándares** (convenciones, más una lista fija de "olores" de Fowler) y **spec** (falta, sobra o está mal). No se mezclan ni se reordenan | **M23** (mantenibilidad) y la reconciliación | **Adaptar:** el eje de estándares y los olores como foco de un revisor; nuestro revisor ya cubre el eje de spec |
| `retro` | Categorías para mejorar el entorno. La clave: todo error **mecánico** se convierte en un check determinista y no en una regla escrita | **M25** | **Adaptar** en nuestro procedimiento de retrospectiva |
| `writing-for-agents` | Cómo escribir lo que lee un agente: punteros a material aparte, criterios de "hecho" claros, evitar documentos que se desbordan | La poda de `AGENTS.md` y las skills | **Inspirarse** para la poda |
| `git-guardrails-claude-code` | Hook que bloquea comandos de Git peligrosos | **M16** y M25 | **Inspirarse:** escribimos nuestro hook con nuestras reglas |
| `to-spec`, `to-tickets`, `implement`, `pr` | Su propio flujo, con historias de usuario y su gestor de issues | Se solapa con `sdd-spec`, `sdd-plan` e `sdd-implement` | **Descartar:** nuestro formato FR/NFR/AC y G1–G6 cubren más |

## 2. OpenSpec (`Fission-AI/OpenSpec`)

- **Qué es:** un marco de SDD con una CLI (`openspec`) y comandos para más de 30 agentes (Claude Code, OpenCode, Codex…).
  - Cada cambio es una carpeta `openspec/changes/<cambio>/` con `proposal.md`, `design.md`, `tasks.md` y un **delta de spec** (requisitos añadidos, modificados y eliminados).
  - Al **archivar**, el delta se fusiona en `openspec/specs/` y el cambio pasa a `changes/archive/AAAA-MM-DD-<cambio>/`.
  - Los requisitos usan SHALL/MUST y escenarios WHEN/THEN.
  - `openspec validate --all --strict --json` sirve para la CI: devuelve un código de salida distinto de cero si algo falla.
- **Licencia y mantenimiento:** MIT, muy activo (último commit el 2026-11-04).
- **Qué resolvería:**
  - La spec se fusiona antes que el código y durante un tiempo describe algo que la app aún no hace.
  - Las 20 aclaraciones de VIC-12 vivieron en descripciones de PR hasta el final.
  - El delta y el archivado separan "lo que se propone cambiar" de "lo vigente".
  - Además, es un formato estándar y portable, en línea con lo que dicen Jake y P08.
- **Riesgos:**
  - **Telemetría activada por defecto.** Se apaga con `openspec config set telemetry.enabled false` o con `OPENSPEC_TELEMETRY=0`.
  - Sus controles **solo avisan**, nunca bloquean (lo reconoce su documentación). Los nuestros (ruleset, CI, G1–G6) seguirían siendo los que bloquean.
  - Es una dependencia global de npm.
  - Migrar la calculadora costaría trabajo y nuestro `checks.py` lee nuestro formato.
- **Recomendación: piloto en el próximo proyecto,** sin migrar la calculadora:
  - formato y comandos de OpenSpec con la telemetría apagada;
  - nuestros controles encima: CI, ruleset, revisión y trazabilidad, ajustando `checks.py` para leer los IDs de OpenSpec o validar con `openspec validate --strict`;
  - medido con las mismas métricas.

  Si sale bien, sustituye a nuestro formato propio de spec y a parte de `sdd-spec`.

## 3. Ponytail (`DietrichGebert/ponytail`)

- **Qué es:** una skill de unas 600 palabras, "el senior perezoso": el cambio completo más pequeño. Antes de escribir, recorre una escalera de 6 preguntas: ¿hace falta?, ¿ya existe en el código?, ¿lo hace la librería estándar?, ¿lo hace una dependencia instalada?, ¿cabe en una línea? y, si no, el mínimo.
  - No recorta nunca: validación en fronteras de confianza, manejo de errores que evita pérdida de datos, seguridad, accesibilidad ni lo que se pidió.
  - Cierra cada respuesta con lo que se ha saltado y los riesgos.
  - Incluye también `ponytail-review`, `ponytail-audit` y `ponytail-debt`.
- **Licencia y mantenimiento:** MIT, activo (2026-10-29), con benchmarks reproducibles (promptfoo).
- **Qué instala:**
  - Hooks en Node que **inyectan la skill en cada sesión y en cada subagente**.
  - Un modo que **modifica la línea de estado** de `~/.claude/settings.json`. Choca con nuestra `sdd-metricas`.
  - Un panel que importa sesiones pasadas.
- **Encaja con:** **M23** (código mínimo) y spec primero (construye solo lo especificado). La regla de dejar un test en la lógica no trivial apoya la M26, y lo saltado y los riesgos encajan con la guía del revisor del PR.
- **Recomendación: adaptar solo el texto de la skill,** en modo `full` y nunca `ultra` (que cuestiona el propio requisito, y eso es trabajo de la entrevista), cargado por `sdd-implement`, sin sus hooks. **Piloto** en una entrega, comparando líneas, coste y defectos con y sin la skill.

## 4. pstack (`cursor/plugins/pstack`, de Lauren Tan)

- **Qué es:** 58 skills y 2 subagentes, unas 36.000 palabras. Mezcla principios (*fix root causes*, *prove it works*, *guard the context window*…), flujos y skills de Cursor.
- **Licencia y mantenimiento:** MIT, muy activo.
- **Lo que interesa:** `create-verification-skill` y `maintain-verification-skill`. Generan para cada proyecto una skill de verificación con estas secciones:
  - **Launch:** arrancar desde cero.
  - **Doctor:** comprobar que la instancia vale.
  - **Drive:** manejarla con selectores reales.
  - **Evidence:** pruebas del camino real del usuario.
  - **Cleanup:** sin borrar las pruebas.
  - **Mapa de funciones:** con el camino del usuario y lo que prueba que funciona.
  
  Exige **ejecutar la skill generada una vez antes de entregarla** ("una skill que nunca se ha ejecutado es un borrador"). Es casi exactamente la meta-skill de Kem.
- **Riesgos:** contenido pensado para Cursor (rutas `.cursor/skills`, agentes en la nube, `swarm`). Instalarlo entero es mucho contexto.
- **Recomendación:** **adaptar** las dos de verificación como `sdd-verify` (es la **M21**), añadiendo el paso de Kem de romper una función y comprobar que se detecta. Del resto, **inspirarse** solo en los principios que coinciden con Ponytail y Pocock.

## 5. Thermos y la revisión thermo-nuclear (`cursor/plugins/thermos`, de Cursor)

- **Qué es:** dos revisores en paralelo.
  - **Correctness y seguridad:** fallos, roturas, seguridad, experiencia del desarrollador y fugas de *feature flags*, con una buena regla contra exagerar la gravedad.
  - **Calidad de código:** ambición estructural ("code judo"), no dejar que un fichero pase de 1.000 líneas, no permitir *ifs* sueltos en flujos ajenos, cero envoltorios sin valor, tipos y fronteras limpios.
- **Licencia:** MIT.
- **Riesgos para nuestro workflow:**
  - El revisor de seguridad **lee la discusión del PR** (comentarios de otros bots). Eso rompe la independencia de G4 (N8) y es una entrada de texto no fiable.
  - Incluye flujos para que el agente lleve el PR hasta fusionarlo ("take the wheel", "FSD").
- **Recomendación:** **adaptar** la rúbrica de calidad como foco de mantenibilidad de un revisor (**M23**, junto con los olores de Pocock) y la regla de no exagerar la gravedad en el encargo del revisor. Se quitan la lectura de la discusión del PR y los flujos de fusión. La salida se ajusta a nuestras clases (*debe corregirse*, *importante*, *mejora*) con prueba por hallazgo.

## 6. ECC, "Everything Claude Code" (`affaan-m/ECC`)

- **Qué es:** un kit enorme: 71 agentes, 314 skills, 98 comandos, 27 hooks, memoria, "aprendizaje continuo" y un panel.
- **Licencia y mantenimiento:** MIT, activo.
- **Riesgos:**
  - Mucho contexto e instrucciones de terceros.
  - Hooks en casi todos los eventos (antes y después de usar herramientas, al empezar y al terminar).
  - El propio autor avisa de copias con malware fuera de sus canales oficiales.
- **Lo que interesa:**
  - **AgentShield** (`ecc-agentshield` en npm): escanea la configuración del agente (prompts, hooks, MCP, permisos, secretos).
  - **Su guía de seguridad:** la trifecta letal, las CVE de Claude Code y la inyección por PR, MCP y adjuntos.
- **Recomendación:** **descartar** instalarlo. **Piloto** de AgentShield una vez, en un contenedor, sobre nuestra configuración (`entorno/`, `.claude/` y plugin), como auditoría de la v1.1. **Inspirarse** en la guía para el requisito de inyección.

## 7. Jev (TypeSafe AI)

- **Qué es:** un modelo que no genera texto. Recibe un estado y preguntas tipadas (sí/no, elegir una opción, una puntuación) y devuelve decisiones con probabilidad.
  - Salió el 2026-09-15; cuesta 0,042 $ por millón de tokens de entrada (la salida es gratis) y tiene una ventana de 32.000 tokens.
  - Se usa vía Cloudflare Workers AI o la API de TypeSafe, en acceso anticipado con lista de espera.
  - No publica cómo trata los datos.
- **Dónde encajaría:**
  - Juez barato en la reconciliación: "¿puede un usuario real llegar aquí?" y "¿qué gravedad tiene?".
  - Elegir el modelo según la dificultad (M29).
  - Revisar comandos del agente antes de ejecutarlos, solo como complemento del sandbox y los hooks.
- **Recomendación:** **piloto** cuando haya acceso, en uno de esos usos y con métrica (aciertos frente a lo que decides tú). No para decisiones de seguridad que deban ser fijas.

---

## 8. gitleaks (`gitleaks/gitleaks`)

- **Qué es:** un detector de secretos (contraseñas, claves de API, tokens) en repos Git, carpetas o texto por entrada estándar. Funciona con expresiones regulares y sus reglas por defecto cubren los proveedores habituales. Tiene tres modos: `git` (todo el historial), `dir` y `stdin`.
  - **Opciones útiles:** `--redact` (no muestra el secreto en los registros), un *baseline* (ignorar hallazgos antiguos ya revisados), configuración propia en `.gitleaks.toml` que amplía las reglas por defecto, y un código de salida distinto de cero si encuentra algo.
- **Licencia y mantenimiento:** MIT, muy activo (2026-10-23). Es un binario de Go sin dependencias.
- **Matiz:** su GitHub Action dejó de ser MIT en la v2 y pide una licencia (gratuita) si el repo es de una organización. En cuentas personales no hace falta. Alternativa sin esa dependencia: ejecutar el binario directamente en la CI.
- **Riesgo:** bajo. Solo lee, y con `--redact` no expone lo que encuentra. Un aviso: el agente no debe leer el informe con el secreto sin redactar, así que siempre con `--redact`.
- **Encaje:** **M33.** Es la barrera contra que un secreto entre en el repo, con independencia del lenguaje.
- **Recomendación: adoptar.** `gitleaks git --redact` en la CI sobre todo el historial; `gitleaks dir --redact` (o el modo protegido del commit) antes de cada commit con lefthook. Configuración en la plantilla.

## 9. osv-scanner (`google/osv-scanner`)

- **Qué es:** cruza las dependencias de los ficheros de bloqueo de más de 11 ecosistemas (npm, PyPI, Go, Maven, Cargo…) con la base pública OSV, y detecta vulnerabilidades conocidas. También revisa licencias de dependencias contra una lista permitida, y puede funcionar **sin red** con la base descargada.
- **Licencia y mantenimiento:** Apache-2.0, de Google, muy activo (2026-11-04).
- **Riesgos:**
  - Envía a osv.dev **nombres, versiones y hashes de los paquetes** (no el código). Si se quiere cero salidas, existe el modo `--offline`.
  - La "remediación guiada" (`fix`) puede ejecutar scripts del gestor de paquetes. **No se usa**: las actualizaciones van por el bot de la M38.
- **Encaje:** **M33** (auditor de dependencias, sirve para cualquier lenguaje, frente a `npm audit`, que es solo de JS) y **M38** (tarea mensual). La revisión de licencias encaja con nuestra regla de dependencias aprobadas (`herramientas.md`).
- **Recomendación: adoptar.** `osv-scanner scan source -r .` en la CI (bloquea si hay vulnerabilidades altas) y una vez al mes como tarea programada. Además, `--licenses` con la lista de licencias que aceptemos.

## 10. knip (`webpro-nl/knip`)

- **Qué es:** busca ficheros, exportaciones, tipos y dependencias que **no se usan** en proyectos JavaScript y TypeScript. Tiene más de 200 *plugins* que entienden herramientas comunes (Playwright, Vite, ESLint…) para no dar falsos positivos.
  - **Modos:** `--production` (solo código de producción) y `--strict`.
  - **`--fix`** borra lo que sobra, y con `--allow-remove-files` también ficheros.
- **Licencia y mantenimiento:** ISC (equivalente a MIT), muy activo (2026-11-03).
- **Riesgo:** bajo si se usa solo para informar. **`--fix` no se usaría en la CI:** borrar código es trabajo del agente en su PR, con revisión.
- **Encaje:** **M23**, "sobra código" sin opinión. Complementa a Ponytail (que evita escribir de más) comprobando que no quedó nada sin usar.
- **Limitación:** solo JS y TS. Para otros lenguajes, la parte de código muerto de jscpd o equivalentes (`vulture` en Python, `deadcode` en Go).
- **Recomendación: adoptar en proyectos JS/TS** como check de la CI: aviso al principio, bloqueo una vez que el proyecto esté limpio.

## 11. jscpd (`kucherenko/jscpd`)

- **Qué es:** detector de **código duplicado** para más de 220 formatos. Analiza los tokens de cada lenguaje (no texto genérico) y encuentra copias exactas, con nombres cambiados o con pocas líneas editadas. La v5 (motor en Rust, binario autónomo) añade:
  - código muerto (`--dead-code`);
  - complejidad por fichero (`--complexity`);
  - evolución en el historial (`--history`) y una puntuación de salud (`--health`);
  - un **baseline** para fallar solo con duplicación nueva (`--fail-on-new-clones`, `--baseline-from-ref origin/main`).
- **Licencia y mantenimiento:** MIT, muy activo (2026-11-03).
- **Riesgos:**
  - El modo experimental `--semantic` usa un modelo de *embeddings* descargado o una API externa: **se deja apagado** (enviaría código fuera, y es opinión, no regla fija).
  - Trae un servidor MCP y skills para agentes. No los necesitamos.
- **Encaje:** **M23**: el olor "código duplicado" de Pocock, comprobado sin opinión y en cualquier lenguaje. La complejidad por fichero cubre en parte la regla de las 1.000 líneas de thermos.
- **Recomendación: adoptar** con `--fail-on-new-clones` sobre `origin/main`: solo bloquea la duplicación que introduce el PR, sin obligar a limpiar lo anterior. La complejidad y la salud, como informe, no como bloqueo.

## 12. lefthook (`evilmartians/lefthook`)

- **Qué es:** un gestor de hooks de Git, configurado en `lefthook.yml`. Ejecuta comandos en paralelo antes del commit o del push, solo sobre los ficheros afectados (`{staged_files}`), con etiquetas, exclusiones y ajustes locales (`lefthook-local.yml`). Se instala con npm, Go, pip, brew o winget y es independiente del lenguaje.
- **Licencia y mantenimiento:** MIT, activo (2026-10-21).
- **Riesgos y límites:**
  - **Se puede saltar** de cuatro maneras: `git commit --no-verify`, `LEFTHOOK=0`, `LEFTHOOK_EXCLUDE` o un `lefthook-local.yml` propio. Por eso un hook de Claude Code (M25) bloquea esos patrones en los comandos del agente, y **la CI sigue siendo la que decide**.
  - `lefthook install` escribe en `.git/hooks`. El sandbox del agente protege `.git`, así que lo instala Víctor una vez por clon (o un script de la plantilla).
- **Encaje:** **M33 y M25.** Lleva los checks rápidos (gitleaks, Semgrep, formato y tests unitarios) al momento del commit, para que el fallo salga en segundos y no en la CI.
- **Recomendación: adoptar** como gestor único de hooks de Git en la plantilla, con un `lefthook.yml` de base que cada proyecto ajusta a su lenguaje.

## Cómo encajan las cinco juntas

| Momento | Qué se ejecuta | Bloquea |
| --- | --- | --- |
| Antes del commit (lefthook) | gitleaks (ficheros del commit), Semgrep (ficheros cambiados), formato y tests unitarios rápidos | Sí, en local; se puede saltar, por eso se repite en la CI |
| CI (cada PR) | gitleaks (todo el historial), Semgrep, osv-scanner, knip (JS/TS), jscpd con baseline, más los tests y mutaciones | Sí: es la autoridad |
| Mensual (tarea programada) | osv-scanner y el informe de salud de jscpd; el bot de dependencias abre los PR | No: abre una issue o un PR |

---

## Resumen

| Herramienta | Recomendación | Mejora |
| --- | --- | --- |
| Pocock: `grilling` y `domain-modeling` | Adaptar | M31 |
| Pocock: `tdd` | Adaptar los antipatrones | M26 |
| Pocock: `diagnosing-bugs` | Adaptar | M22 |
| Pocock: `code-review` (eje de estándares y olores) y thermos (calidad) | Adaptar | M23 |
| Pocock: `retro` y `writing-for-agents` | Adaptar o inspirarse | M25 y la poda |
| pstack: `create`/`maintain-verification-skill` | Adaptar como `sdd-verify` | M21 |
| Ponytail | Adaptar el texto de la skill, sin hooks, y piloto | M23 |
| OpenSpec | Piloto en el próximo proyecto | Formato de spec |
| ECC | Descartar; piloto de AgentShield | Inyección |
| Jev | Piloto cuando haya acceso | Reconciliación y M29 |
| gitleaks | Adoptar (CI y antes del commit) | M33 |
| osv-scanner | Adoptar (CI y mensual) | M33 y M38 |
| knip | Adoptar en JS/TS | M23 |
| jscpd | Adoptar con baseline (solo duplicación nueva) | M23 |
| lefthook | Adoptar como gestor de hooks de Git | M33 y M25 |

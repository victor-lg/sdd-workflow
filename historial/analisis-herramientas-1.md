# Análisis de herramientas externas para la v1.1

Fecha: 2026-11-04. Fuente: los repos clonados en `C:\Users\victor\Documents\herramientas` (leídos, nada ejecutado) y, para Jev, su documentación pública. Es historial, no norma: lo que se acepte entra por la v1.1.

## Criterios

Para cada herramienta:
- qué problema nuestro resuelve, con evidencia de los recorridos;
- qué instala y qué ejecuta;
- mantenimiento, y si el núcleo es abierto o hay piezas de pago o cerradas;
- licencia, solo cuando copiamos su código o texto a nuestros repos (para usar una herramienta en uso personal no es decisiva);
- riesgo de inyección y de cadena de suministro, según **dónde se sitúa**: fuera del bucle del agente (un panel que usas tú) o dentro (lee o reescribe lo que ve el modelo, o actúa con sus permisos);
- **coste-beneficio** (añadido el 2026-11-05): el beneficio se mide contra problemas observados (coste en dólares, picos de contexto, tiempo de Víctor); el coste es instalación, mantenimiento, riesgo residual tras configurarla y dependencia. Un riesgo que se apaga con configuración es un coste, no un veto. Solo vetan tres cosas: una trifecta que no se puede romper, reescribir nuestras instrucciones o configuración sin revisión, o ver credenciales en tránsito sin necesitarlas;
- portabilidad (Claude Code, OpenCode u otros);
- recomendación: **adoptar** (tal cual), **adaptar** (copiar y ajustar a nuestro workflow), **inspirarse** (tomar ideas), **piloto** (probar con métrica) o **descartar**.

## Reglas comunes que salen del análisis

1. **Una skill de terceros es un conjunto de instrucciones.** No se instala desde fuera ni se actualiza sola. Se copia una versión fijada dentro del plugin `sdd`, se revisa el texto y se cita la fuente. Todas las que interesan tienen licencia MIT, que permite copiar si se conserva el aviso de licencia.
2. **No se abre Claude Code dentro de un repo de terceros.** Los ajustes y hooks del proyecto se cargan al abrirlo. Hubo dos vulnerabilidades en 2026: CVE-2025-59536 (ejecución antes del diálogo de confianza) y CVE-2026-21852 (desvío de `ANTHROPIC_BASE_URL` y fuga de la clave). La carpeta `herramientas` se lee desde fuera.
3. **Sin hooks de terceros que decidan.** Se toma el texto de la skill y, si hace falta un hook que bloquee, cambie un comando o añada contexto, lo escribimos nosotros (M25). Excepción (2026-11-05): los hooks que solo **informan** del estado a un panel (Herdr, Sheprd) se aceptan tras leerlos, porque no deciden nada ni cambian lo que ve el modelo.
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

## Tercera tanda (2026-11-05)

Repos leídos en `herramientas` (sin ejecutar nada) y webs de los productos sin repo. Se agrupan por el problema que resuelven.

### 13. Reducir lo que lee el modelo: rtk, Headroom y LeanCTX

**rtk** (`rtk-ai/rtk`)
- **Qué es:** un binario de Rust que intercepta los comandos de shell del agente (con un hook *PreToolUse* en Claude Code) y comprime su salida antes de que la lea el modelo. Algunos ejemplos:
  - en tests, solo los fallos;
  - en `git diff`, menos contexto;
  - en `ls` y `tree`, el árbol con recuentos.
  
  Promete hasta un 90 % menos en salidas de shell y explica con honestidad que el ahorro en la factura es menor. Solo actúa en Bash, no en las herramientas `Read` o `Grep`.
- **Licencia:** dos ediciones con el mismo binario. `rtk` es Apache-2.0 más BUSL-1.1 (gratis en uso propio). `rtk-oss` es solo Apache-2.0, con los filtros pero sin el motor. El proxy es BUSL.
- **Riesgos:**
  - **Esconde información por diseño.** Un `git diff` con menos contexto o una salida de tests recortada pueden ocultar justo lo que hacía falta; nunca debe usarse en los revisores.
  - **Reescribe los comandos del agente,** así que se suma a los hooks que controlamos (M25).
- **Encaje:** la poda del contexto (bloque 2). Los picos del 48–57 % en VIC-12 y el coste con modelos de pago por token (Go).
- **Recomendación: piloto** de la edición completa `rtk` (la BUSL permite el uso propio y nuestro workflow es privado; revisado el 2026-11-05, antes se proponía `rtk-oss` solo por la licencia), en una entrega de implementación, midiendo el pico de contexto y si el agente tuvo que repetir comandos sin filtro. Sin su proxy, por el mismo motivo que Headroom. Nunca para revisar.

**Headroom** (`headroomlabs-ai/headroom`)
- **Qué es:** comprime todo lo que lee el agente (salidas de herramientas, registros, ficheros e historial). Funciona como librería, como proxy local (`headroom wrap claude` hace pasar el tráfico de Claude Code por él) o como servidor MCP. Añade memoria compartida entre agentes y `headroom learn`, que **escribe correcciones en `CLAUDE.md` o `AGENTS.md`** a partir de sesiones fallidas.
- **Licencia:** Apache-2.0, con una versión de pago para equipos.
- **Riesgos:**
  - **El proxy ve todo el tráfico y las credenciales.** Es el mismo patrón que la vulnerabilidad de `ANTHROPIC_BASE_URL` de 2026, aunque aquí sea local.
  - **Reescribe tus instrucciones.** `learn` cambia los ficheros de instrucciones sin revisión, lo contrario de la M25 y una vía de contaminación del contexto.
  - **Telemetría activada por defecto** (se apaga con `HEADROOM_TELEMETRY=off`).
- **Recomendación: descartar.** rtk cubre lo útil con menos superficie de riesgo.

**LeanCTX** (`yvgude/lean-ctx`)
- **Qué es:** una "pasarela de contexto": selección, compresión, permisos y registro de lo que ve el agente, con CLI, MCP, hooks y proxy.
- **Licencia:** *open core*. La parte pública es Apache-2.0, pero hay componentes privados y comerciales y un acuerdo de contribución (CLA); la licencia se rige por un fichero de matriz por rutas.
- **Recomendación: descartar.** Se solapa con rtk y con nuestros propios controles, y también trae proxy. La licencia no es el motivo (revisado el 2026-11-05): si el piloto de rtk no convence, se puede volver a mirar.

### 14. Contexto del código para revisar: code-review-graph

- **Qué es:** construye en local (SQLite, con Tree-sitter) un grafo de funciones, llamadas, importaciones y tests, y se lo da al agente por MCP. Así, en una revisión lee solo lo que puede verse afectado: el "radio de impacto". Está en `tirth8205/code-review-graph`, con licencia MIT, sin telemetría y con *embeddings* en la nube solo si se activan.
- **Riesgos:** `install` escribe entradas MCP, hooks, skills y reglas en la configuración de todos los agentes que detecta, lo que es muy invasivo.
- **Encaje:** los revisores ya leen "el código tocado, no solo el diff". En proyectos pequeños como la calculadora, `grep` basta (Kem: la mayoría no necesita un grafo).
- **Recomendación: en observación** para un proyecto grande o con mucho código heredado. Si llega, usar solo su CLI en la CI para calcular el radio de impacto y pasarlo al revisor, sin el `install`.

### 15. Flujos completos de otros: Gentle-AI, Engram y la plantilla SDD

**Gentle-AI** (`Gentleman-Programming/gentle-ai`, MIT)
- **Qué es:** configura 17 agentes con su propio flujo:
  - **ODD:** las tareas se dimensionan por comprensión, riesgo y si se pueden retomar, no por número de ficheros.
  - **RDD:** la revisión se ata a una versión congelada del cambio y caduca si cambia.
  - Tests primero por defecto, una lista de rutas prohibidas (`~/.ssh`, `.env`) y su memoria Engram.
- **Riesgos:**
  - Sustituye la configuración de los agentes por la suya: es un flujo que compite con el nuestro.
  - Telemetría anónima activada por defecto.
  - El sistema de revisión es complejo (tokens, contratos y claves locales).
- **Lo que interesa:**
  - **"Delegar por un motivo":** solo se lanza un subagente para explorar, para trabajos de escritura independientes, para relevar una sesión larga o como verificador independiente en lo arriesgado. Lo respaldan con mediciones propias, de una sola ejecución.
  - **La revisión atada a una versión concreta:** si el cambio se modifica, la revisión deja de valer.
- **Recomendación: inspirarse.**
  - "Delegar por un motivo" va a la regla de subagentes de `sdd-implement` (M20).
  - La revisión atada al commit refuerza la M8: el PR guarda el SHA que vio cada revisor y la CI compara.
  - No instalarlo.

**Engram** (`Gentleman-Programming/engram`, MIT)
- **Qué es:** memoria persistente para agentes. Un binario de Go con SQLite y búsqueda de texto, por MCP, CLI y TUI. Es local por defecto, con sincronización por Git o nube opcional.
- **Recomendación: descartar por ahora.** Nuestra memoria son ficheros revisables: `.tareas/`, ADR, specs e historial. Una memoria que el agente escribe solo es un canal de instrucciones sin revisión (Kem: el contexto se envenena; Jake: los ficheros son la memoria).

**engram.so** (Softmax Data, MIT, con nube)
- **Qué es:** otro producto con el mismo nombre. Memoria tipada con MCP alojado.
- **Recomendación: descartar.** Mismo motivo, y además los datos salen a un servicio externo.

**Plantilla SDD de Juan Carlos Lagos** (`juanklagos/spec-driven-development-template`, MIT)
- **Qué es:** una plantilla y un curso de SDD, en inglés y español, sobre GitHub Spec Kit. Unos scripts comprueban la regla de "no hay código sin spec aprobada, plan coherente y consentimiento registrado". Incluye un registro de decisiones en `bitacora/`, criterios con notación **EARS** y un comando `/sdd:help` que dice en qué fase estás y cuál es el siguiente paso.
- **Comparación:** nuestros controles son más fuertes (ruleset, CI y trazabilidad AC ↔ tests). Su consentimiento registrado por script equivale a nuestra fusión de la spec (G1).
- **Recomendación: inspirarse en dos cosas.**
  - **EARS** ("Cuando <suceso>, el sistema deberá…") como forma recomendada de escribir FR y AC en la plantilla de spec (con la M31).
  - **Un comando de estado,** `sdd-status` (M41): lee Linear y GitHub y dice en qué fase está cada issue (F0–F6), qué está esperando y cuál es el siguiente paso. Es determinista y responde en parte a la petición de "ver qué está haciendo el agente".

### 16. Gobierno de Claude Code: baseline (friedbot studio)

- **Qué es:** una capa de gobierno para Claude Code, con licencia Apache-2.0 y en alfa pública (v0.26):
  - **27 hooks** que bloquean llamadas a herramientas antes de ejecutarse;
  - **permisos con caducidad** (por ejemplo, `/grant-commit` habilita los commits solo durante 15 minutos), y lo mismo para el push;
  - fases obligatorias, con excepción anotada si se salta una;
  - una "constitución" en `CLAUDE.md`, un guardián de `.env`;
  - desactivar un hook exige una enmienda escrita.
- **Encaje:** es casi exactamente nuestra M25 (controles en vez de instrucciones) hecha por otros, y los permisos con caducidad son una buena idea para la escalera de autonomía (M24).
- **Riesgos:** está en alfa, tiene su propia constitución y flujo, y se instala con `npx`, que toca muchos ficheros.
- **Recomendación: inspirarse, a fondo.** Es la mejor referencia para diseñar nuestros hooks del bloque 2. No instalarlo.

**Lectura del código (2026-11-05, commit `e22e571`).** 27 hooks en Node (unas 2.700 líneas, sin contar `lib/`), registrados en `.claude/settings.json`. Lo que nos sirve para M25:

| Idea de baseline | Cómo funciona | Para nosotros |
| --- | --- | --- |
| **Consentimiento que el agente no puede falsificar** | Al escribir tú `/grant-commit`, un hook `UserPromptSubmit` (corre antes de que el modelo vea el mensaje, fuera de sus herramientas) deja una marca con hora. Otro hook bloquea que el agente escriba esa marca, también por Bash. Duración: commit 900 s, push 300 s, marca 120 s | Base de los permisos con caducidad de la escalera (M24): p. ej. `/permitir-merge VIC-n` válido para un PR y unos minutos |
| **Cubrir también la vía Bash** | Lo vieron en su propia auditoría: los guardas de Write/Edit no ven `echo > fichero`, así que repiten el bloqueo en el guarda de Bash | Regla de diseño: cada guarda de ficheros tiene su pareja en Bash |
| **Dos niveles para comandos destructivos** | Patrones en un JSON: "bloquear siempre" y "preguntar cada vez" (`git reset --hard`, `push --force`, `npm publish`…) | Patrones en configuración, no en código; casi todo lo nuestro ya lo cubren el sandbox y `permissions.deny` |
| **`deny` de `git add -A` y `git add .`** | Obliga a añadir ficheros por nombre | Habría evitado los ficheros del sandbox sin seguimiento que vimos en el recorrido 2 (va a M16) |
| **Guarda de fugas por `.gitignore`** | En cada `git commit` mira lo preparado contra una lista de rutas que nunca deben subirse; sin red; falla cerrado si no puede mirar | Pareja local de gitleaks (M33) |
| **No se puede escribir PASS si el último test falló** | `verify_pass_guard` compara con el último resultado guardado por el hook que ejecuta los tests | Encaja con la conciliación: el revisor no cierra un hallazgo sin prueba (bloque 4) |
| **Guarda de `.env`** | Bloquea escribir `.env*` salvo plantillas (`.env.example`…) | Adoptar la idea tal cual |

Lo que no tomamos: los guardas de su propio flujo (épicas, *swarm*, dirección, PlantUML, diagramas en specs), su memoria automática en `SessionStart`/`Stop`/`PreCompact` (mismo motivo que Engram) y el orden TDD obligatorio (lo cubren mejor los tests en la CI y las mutaciones).

**Límite que hay que tener presente:** los guardas por patrones sobre comandos de shell se pueden esquivar (`bash -c`, variables, scripts). Son una segunda capa que evita errores del agente; la seguridad real sigue siendo el sandbox, los ajustes gestionados y la CI.

### 17. Paneles para ver y lanzar agentes: Cezar, Mission Control, Herdr, Alera y DevBoard

Herdr y Alera se leyeron en su código el 2026-11-05; antes solo se había visto su web.

Responden a la pregunta de "ver gráficamente qué hace cada agente". Todos parten de varios agentes en paralelo, cada uno en su *worktree*. Nuestra regla es un agente con subagentes de revisión, así que lo útil de estas herramientas es **ver** y **lanzar desde el móvil**, no la paralelización.

| Herramienta | Qué es | Licencia | Nota de seguridad | Recomendación |
| --- | --- | --- | --- | --- |
| **Cezar** (`open-mercato/cezar`) | Panel web (desde el móvil hace falta un túnel tipo Tailscale, porque solo escucha en local) que lanza Claude Code, OpenCode y otros con tu sesión; un *worktree* por tarea, coste por proyecto, tareas programadas, conexión con Linear y GitHub; datos en ficheros | MIT | Escucha solo en `127.0.0.1` y la telemetría es opcional. Lanza Claude Code con `--permission-mode dontAsk` (deniega lo no permitido, compatible con nuestro sandbox), pero a otro agente (Antigravity) lo lanza saltándose los permisos. En un VPS sería un control remoto de tus repos | **Alternativa** a Herdr si se quiere un panel web con Linear y coste por proyecto |
| **Mission Control** (`builderz-labs/mission-control`) | Plano de control autoalojado (Next.js y SQLite) con tareas, agentes, costes, aprobaciones y auditoría, centrado en OpenClaw | MIT | En alfa; cuentas y claves de API propias | **Descartar:** demasiado para un usuario |
| **Herdr** (`herdrdev/herdr`) | Multiplexor de terminal (tipo tmux) en un binario de Rust: marca cada panel como trabajando, bloqueado o en espera; las sesiones siguen vivas al cerrar o perder el SSH; varias máquinas en una ventana | Apache-2.0 | Leído el código: sin telemetría; comprueba actualizaciones cada 30 min y descarga de herdr.dev un catálogo para detectar agentes (ambas cosas configurables); instala hooks de estado en `~/.claude/settings.json` solo si se activa la integración; su API de socket deja a un agente lanzar paneles y escribir a otros (no lo usaríamos; el sandbox probablemente lo impide, a comprobar) | **Piloto** tras el bloque 5, en WSL. Desde el móvil, por SSH con Moshi; sirve también con OpenCode |
| **Alera** (`leynier/alera`) | App de escritorio (Flutter y Rust) para agentes en paralelo, cada uno en su *worktree*; terminales persistentes; app móvil | MIT | Leído el código: hooks de estado opcionales en `~/.claude/settings.json`; informes de fallos a Sentry desactivados por defecto; cuentas en su nube (Google o GitHub); **MCP remoto** opcional que en nivel `full` puede ejecutar cualquier comando (la trifecta completa); **"Watch, Fix and Merge"** hace merge solo, saltándose nuestra escalera; la app de iOS aún no está publicada | **Descartar:** mucha superficie para un usuario y choca con nuestras puertas |
| **DevBoard AI** (devboardai.com) | Kanban de pago (24 $) para agentes | Propietario | — | **Descartar:** solo macOS y tú usas Windows con WSL |

### 18. Acceso desde el móvil: Moshi

- **Qué es:** un terminal para iOS y Android con SSH, Mosh o ET a tu máquina (incluida WSL), pensado para agentes de código. Ofrece notificaciones, voz y claves SSH protegidas con Face ID. No pasa por un relé intermedio. Su complemento `moshi-hook` añade una vista de chat, aprobaciones desde el reloj y un visor de diffs.
- **Riesgos:**
  - Exige abrir SSH a tu máquina; lo razonable es hacerlo por una red privada tipo Tailscale, no a internet.
  - No dice si es de código abierto.
- **Encaje:** **Remote Control solo funciona con modelos de Anthropic.** Si en el bloque 7 usamos OpenCode con un modelo de Go, Moshi es la forma de seguir manejándolo desde el móvil.
- **Recomendación: piloto junto con Herdr** tras el bloque 5 (revisado el 2026-11-05), e imprescindible en el bloque 7 si se adopta OpenCode.

### 19. Gestión de proyectos: Huly

- **Qué es:** sustituto abierto de Linear, Slack y Notion a la vez, con sincronización bidireccional con GitHub Issues. Sus funciones de IA están "por llegar".
- **Recomendación: descartar.** Linear funciona y es una decisión tomada (ADR-0003). Cambiar costaría migrar la integración con GitHub y las automatizaciones sin una mejora observada que lo pida.

### 20. Interfaz gráfica sobre Herdr: Sheprd (`sheprd-labs/sheprd`)

Leído el código el 2026-11-05 (commit `88a7ecf`).

- **Qué es:** una app de escritorio nativa (Rust y GPUI, sin Electron) para Windows, Linux y macOS, que es un **cliente gráfico de Herdr**: los terminales y los agentes viven en el demonio de Herdr y Sheprd los dibuja. Desde Windows se conecta a las distribuciones de WSL. Lo útil para nosotros:
  - una barra lateral con cada agente y su estado (en espera, trabajando, te necesita);
  - **revisar los cambios del agente** como un diff con notas por línea que se le envían de vuelta;
  - **pestañas de navegador con anotaciones**: señalas un elemento de la página local y la nota llega al agente (útil para la UI de la calculadora);
  - seguimiento de PR, uso del plan de cada servicio, CPU y memoria;
  - control remoto desde el móvil (app de iOS, PWA), por la red local o Tailscale, con emparejamiento aprobado en los dos lados y certificado propio.
- **Licencia y mantenimiento:** Apache-2.0, muy activo (commit del mismo día); versiones por fecha y solo `main` recibe correcciones.
- **Riesgos y cómo se apagan:**
  - **El panel de uso lee el token de Claude Code** (`.credentials.json`) y llama a `api.anthropic.com`. Es el mismo destino que usa Claude Code; se puede dejar apagado.
  - El control remoto abre un puerto: opcional, apagado por defecto, y solo por Tailscale.
  - Los *sandboxes* en la nube (Fly, OpenSandbox) son opcionales; no los usaríamos.
  - El instalador recomendado es `irm … | iex`; mejor el instalador de las *releases* comprobando su SHA-256, y sin el canal beta.
  - Proyecto grande y que cambia cada día: fijar una versión y actualizar a mano.
- **Encaje:** es la interfaz gráfica que pediste para "ver qué hace el agente", y se sitúa **fuera del bucle del agente**: lo usas tú. La revisión de diffs con notas y las anotaciones del navegador cubren justo la parte en la que tú aportas (pruebas del producto y decisiones).
- **Recomendación: piloto junto con Herdr** tras el bloque 5. Herdr primero en la terminal; Sheprd encima para la vista gráfica. Moshi sigue para los terminales desde el móvil, porque el control remoto de Sheprd por ahora solo maneja chats.

### Revisión coste-beneficio de los descartes (2026-11-05)

Revisados con el criterio de coste-beneficio añadido a los criterios. La mayoría de los descartes no eran por seguridad, sino porque no resolvían un problema observado o ya lo cubría otra pieza.

| Herramienta | Beneficio para nosotros | Coste y riesgo | ¿Se mitiga configurándola? | Decisión revisada |
| --- | --- | --- | --- | --- |
| **Headroom** | Alto en teoría: comprime también lo que entra por `Read`, no solo por Bash. VIC-12 costó unos 84 $ con picos del 48–57 % de contexto | Su modo para Claude Code es un proxy que ve el tráfico y las credenciales; `learn` reescribe instrucciones; telemetría activada | En parte: telemetría apagada y sin `learn`. El proxy no; queda el modo MCP o librería | **Cambia a segunda opción:** si rtk no baja los picos lo suficiente, piloto en modo MCP, sin proxy y medido |
| **Alera** | Interfaz gráfica, "Watch and Fix" | Nube, MCP remoto, merge automático | Sí: todo es opcional y viene apagado | **Cambia a "por detrás de Sheprd":** no está vetada; Sheprd da lo mismo con menos piezas |
| LeanCTX | El mismo que rtk o Headroom | Proxy y piezas cerradas | En parte | Sigue fuera: no aporta sobre los otros dos |
| Engram (los dos) | Memoria entre sesiones; no hemos observado un fallo que una memoria automática resolviera | Una memoria que escribe el agente sin revisión es una vía de inyección persistente | No sin perder lo que la hace útil | Se mantiene |
| Gentle-AI, ECC | Ideas ya tomadas (M20, M8, AgentShield, guía de seguridad) | Instalarlas sustituye nuestra configuración o carga cientos de skills | No | Se mantiene: el beneficio ya lo tenemos |
| Mission Control | Panel, aprobaciones y auditoría | Pensado para equipos y para OpenClaw | — | Se mantiene: poco beneficio para un usuario |
| DevBoard AI | Kanban de agentes | Solo macOS | — | Se mantiene: no funciona en tu equipo |
| Huly | Ninguno observado | Migrar Linear y su integración | — | Se mantiene |

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
| rtk (edición completa, sin proxy) | Piloto en implementación, nunca en revisión | Poda del contexto |
| Headroom | Segunda opción si rtk no basta (modo MCP, sin proxy) | Poda del contexto |
| LeanCTX | Descartar | — |
| code-review-graph | En observación (proyecto grande) | G4 |
| Gentle-AI | Inspirarse: delegar por un motivo y revisión atada al commit | M20 y M8 |
| Engram (los dos) | Descartar: la memoria son ficheros revisables | — |
| Plantilla SDD de Lagos | Inspirarse: EARS y comando de estado | M31 y M41 |
| baseline | Inspirarse a fondo para los hooks | M25 y M24 |
| Herdr | Piloto como panel en la terminal, con Moshi para el móvil | Bloque 5 |
| Cezar | Alternativa si se quiere un panel web con Linear | Bloque 5 |
| Sheprd | Piloto como interfaz gráfica sobre Herdr | Bloque 5 |
| Alera | Por detrás de Sheprd (no vetada) | — |
| Mission Control, DevBoard AI, Huly | Descartar | — |
| Moshi | Piloto junto con Herdr; imprescindible si se adopta OpenCode | Bloques 5 y 7 |

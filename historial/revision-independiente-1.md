# Revisión independiente antes de la v1.0 (D54, L8)

**Fecha:** 2026-10-23 · **Alcance:** README, línea base, ADR-0001–0005, trazabilidad D00–D59, `plantilla-proyecto/`, `plugin-sdd/`, guía de instalación, recorrido 1, retrospectiva 1 y CHANGELOG (más `entorno/`, `docs/herramientas.md`, `docs/hoja-de-ruta.md` y los ejemplos de workflows cuando hacía falta contrastar algo).
**Método:** solo lectura, sin el historial de las conversaciones. Las líneas citadas son las del commit `4a937a3`.

Categorías: **[B]** bloquea la v1.0 · **[C]** conviene antes de la v1.0 · **[1.1]** puede esperar a la v1.1.

---

## Bloquean la v1.0

### B1. Claude actúa con la identidad del usuario a través del navegador, y ninguna regla lo limita

- **Dónde:** `historial/recorrido-1.md:21` (VIC-5 "creada por Claude desde Chrome" y puesta en *Ready*); `docs/guia-instalacion.md:452`, `:458` y `:469` (invitaciones, configuración de Linear y repos creados por Claude con la sesión de `victor-lg`); `CHANGELOG.md:70`; `docs/herramientas.md:7-10` (Claude in Chrome y el navegador integrado no figuran); `docs/linea-base-v1.md:427` y `:158` (P03).
- **Por qué:** el modelo de aprobación se basa en que el agente no controla la identidad humana, pero el recorrido muestra a Claude manejando la sesión de GitHub y de Linear del usuario. Esa misma vía podría aprobar y fusionar un PR o mover una issue a *Ready* (G2), y ninguna capa (ruleset, CI, sandbox ni revisión) lo distingue de un acto humano.
- **Propuesta:** añadir a §8 y §9 una regla explícita: ninguna sesión de Claude con control de navegador puede usarse con una sesión abierta de la cuenta humana de GitHub o de Linear en los repos o equipos del workflow. Si se quiere aceptar para tareas de configuración puntuales, registrarlo como límite aceptado en un ADR y anotar la herramienta en `docs/herramientas.md`. Hay que dejar escrito que aprobar, fusionar y mover a *Ready* nunca se delegan. En `recorrido-1.md`, aclarar quién movió VIC-5 a *Ready*.

### B2. El perfil Go sigue siendo norma de v1 sin haberse probado, y se aplaza sin ADR

- **Dónde:** `docs/adr/0002-ejecutor-y-perfiles-de-modelo.md:46` y `:61` (perfil Go en v1; validación "N1–N8… en ambos perfiles"); `docs/linea-base-v1.md:274` y `:280`; `historial/retrospectiva-1.md:66` (#10 a la v1.1); `docs/hoja-de-ruta.md:62`; `entorno/claude-go.sh:15` ("PENDIENTE DE VERIFICAR… la URL base"); `docs/linea-base-v1.md:5`.
- **Por qué:** la v1.0 declararía como normativo un perfil que no se ha ejecutado nunca, con una URL base sin confirmar. Además, la retrospectiva contradice un ADR aceptado sin un ADR nuevo, aunque `docs/adr/README.md:8` y la regla 1 de `README.md:68` lo exigen.
- **Propuesta:** crear un ADR-0006 que modifique ADR-0002: el perfil Go sale de v1.0 y pasa a §10 con un disparador ("cuando el coste de Opus en la orquestación lo justifique"), y la validación pasa a ser "N1–N8 en el perfil Claude". En §5 de la línea base y en el bloque F de la guía, marcarlo como aplazado.

---

## Conviene antes de la v1.0

### Trazabilidad D00–D59

**C1. Varias entradas de la trazabilidad describen mecanismos que versiones posteriores sustituyeron.**
- **Dónde:** `docs/trazabilidad-D00-D59.md:95` (D48: "lo crítico va en ajustes de usuario"; desde v0.11 son los gestionados, `docs/linea-base-v1.md:503-504`); `:54` (D20: "las escrituras se bloquean con reglas de permisos"; desde v0.11 es el endpoint de solo lectura, `CHANGELOG.md:149`); `:104` (D55: "un solo sistema externo (GitHub)", cuando Linear también lo es, según ADR-0003); `:29` (D01: "la futura skill `sdd-discover`", que ya existe); `:67` (D30: "`ask` si escriben", que no aparece en §9).
- **Por qué:** la revisión de hito tiene que comprobar que lo cubierto lo está en el fichero citado, y en estas cinco entradas el texto citado ya no es cierto.
- **Propuesta:** corregir esas cinco líneas y actualizar la cabecera (`:3`, "Última revisión 2026-10-19").

**C2. Tres reglas de la trazabilidad no tienen soporte en las plantillas que cita.**
- **Dónde:** `docs/trazabilidad-D00-D59.md:87` (D44: "evidencia de NFR exigida en R2") y `docs/linea-base-v1.md:313` ("evidencia de los NFR y plan de vuelta atrás"), sin reflejo en `plantilla-proyecto/.github/pull_request_template.md`, `sdd-plan`, `sdd-implement` ni `sdd-review` (no aparece "vuelta atrás" ni "rollback"); `:40` (D09: "la justificación de una excepción va en una línea del PR"), sin campo ni definición de "excepción".
- **Por qué:** un agente cumple la plantilla del PR y nunca aportará lo que la línea base exige en R2.
- **Propuesta:** añadir a "Validación" de la plantilla del PR la línea "R2: evidencia de NFR y plan de vuelta atrás", con su paso en `sdd-implement`. Para D09, o se define el campo o se quita la frase.

**C3. Hay decisiones de fondo tomadas entre la v0.12 y la v0.21 sin ADR.**
- **Dónde:** `CHANGELOG.md:43` (qué afirma la aprobación, que cambia el alcance de G6), `:18` (modelos del revisor), `:10` (rondas), `:149` (MCP de solo lectura en lugar de reglas `deny`, que contradice ADR-0003:51), `:118` (token con `read:org`, que contradice ADR-0005:47) y `:116` (bot con escritura en `sdd-workflow` y bypass "Always allow"); `historial/retrospectiva-1.md:3` ("pasa… mediante el CHANGELOG").
- **Por qué:** `README.md:68` y `docs/adr/README.md:8` dicen que las decisiones se registran como ADR y que el ADR modificado se anota. Hoy ADR-0003 y ADR-0005 dicen cosas que ya no son ciertas y su índice no lo refleja.
- **Propuesta:** un único ADR-0006 de "ajustes del primer recorrido" (se puede juntar con B2) con `modifica: ADR-0002, ADR-0003, ADR-0005`, y anotarlo en el índice. Otra opción es escribir en el README que en v0.x el CHANGELOG basta y que los ADR solo se exigen desde v1.0, pero entonces hay que anotar en el índice qué partes de ADR-0003 y ADR-0005 han quedado superadas.

### Coherencia entre línea base, AGENTS.md, skills, plantillas y CI

**C4. La lista de disparadores de R2 es distinta en cada sitio.**
- **Dónde:** `docs/linea-base-v1.md:317-322` (incluye "carpetas de autenticación o pagos" como disparador de la CI; no cita `CLAUDE.md`); `plantilla-proyecto/.github/sdd/checks.py:44-45` (incluye `CLAUDE.md`; no tiene auth ni pagos); `plugin-sdd/skills/sdd-plan/SKILL.md:29-32` (sin `CLAUDE.md`); `plantilla-proyecto/README.md:59-61` (sin `CLAUDE.md`); CODEOWNERS `plantilla-proyecto/.github/CODEOWNERS:10-16` (añade `CLAUDE.md` y `README.md`) frente a `docs/linea-base-v1.md:444` (sin ellos).
- **Por qué:** un agente que siga `sdd-plan` marcará R1 en un cambio de `CLAUDE.md` y la CI fallará. Además, la línea base promete un disparador (auth y pagos) que la CI no implementa si el proyecto no lo declara en su README.
- **Propuesta:** dejar una lista canónica en §6 (la de `checks.py` más "auth y pagos solo vía rutas sensibles del README") y hacer que `sdd-plan`, la plantilla de README y §8 la enlacen en lugar de copiarla.

**C5. La plantilla del PR permite cambiar comportamiento sin actualizar la spec.**
- **Dónde:** `plantilla-proyecto/.github/pull_request_template.md:27` ("Sí, sin actualizar la spec. Motivo:") frente a P01 (`docs/linea-base-v1.md:150`) y `plantilla-proyecto/AGENTS.md:30`.
- **Por qué:** es la única vía documentada para el desvío de la spec (D17), y ni la CI ni el revisor la tratan como error.
- **Propuesta:** quitar esa opción, o convertirla en "Sí: PR de spec #… pendiente; este PR queda en borrador hasta que se fusione".

**C6. Lo que recibe el revisor no coincide entre ficheros, y se le pide revisar algo que no recibe.**
- **Dónde:** `plantilla-proyecto/CLAUDE.md:8` (spec, diff y CI); `plugin-sdd/skills/sdd-review/SKILL.md:25-31` (además tipo, riesgo y ADR); `plugin-sdd/agents/reviewer.md:3` (spec, diff, CI y ADR); `sdd-review/SKILL.md:33` le pide comprobar si la "Guía para el revisor humano" omite algo, pero la guía está en la descripción del PR, que no figura entre las entradas.
- **Por qué:** con N8 en juego, las entradas permitidas tienen que estar definidas en un solo sitio. Hoy pasarle la descripción del PR es a la vez obligatorio (para revisar la guía) y contaminante (N8 prohíbe "tu resumen del PR", `historial/recorrido-1.md:120`).
- **Propuesta:** fijar la lista en `sdd-review` y que `CLAUDE.md` la enlace. Añadir explícitamente "la sección 'Guía para el revisor humano' del PR, sin el resto de la descripción", o quitar esa comprobación del revisor y dejarla en la reconciliación.

**C7. No está definido cuántos revisores lleva un PR de ADR, pero su estado depende de esa revisión.**
- **Dónde:** `plantilla-proyecto/AGENTS.md:31` y `plantilla-proyecto/docs/adr/_plantilla-adr.md:15-17` ("cuando la revisión termina sin nada que corregir"); `plugin-sdd/skills/sdd-review/SKILL.md:14-17` (solo PR de spec y de código); `checks.py:304-337` (un PR que solo toca `docs/adr/` da un mínimo de R0, es decir, revisión opcional).
- **Por qué:** el ADR técnico del recorrido tuvo dos revisores por ronda (`historial/recorrido-1.md:83`), pero un agente podría marcarlo R0 sin revisión y la CI lo aceptaría.
- **Propuesta:** añadir una fila "ADR" a la tabla de `sdd-review` (2 revisores, como una spec) y, en `checks.py`, subir a R1 como mínimo cualquier cambio en `docs/adr/`.

**C8. Las rondas de revisión solo están en una skill, y su redacción es ambigua.**
- **Dónde:** `plugin-sdd/skills/sdd-review/SKILL.md:46-47` ("como máximo 2 rondas"; "después de la ronda 2…"); en `docs/linea-base-v1.md:375-383` (G4), `AGENTS.md` y `reviewer.md` no aparece; el recorrido registra 3 rondas en los PR #2, #3 y #5 (`historial/recorrido-1.md:18-24`).
- **Por qué:** no queda claro si "2 rondas" significa dos revisiones o dos repeticiones tras la primera. Los datos del propio recorrido (3 rondas) no encajan con la lectura literal.
- **Propuesta:** en G4 de la línea base, una línea: "Hasta 3 rondas (la inicial y 2 repeticiones); después, la persona decide y sus aclaraciones se aplican sin otra ronda salvo reglas nuevas". `sdd-review` la cita.

**C9. Quedan restos de mecanismos superados en la propia línea base.**
- **Dónde:** `docs/linea-base-v1.md:624` ("reglas de permisos que bloqueen sus herramientas de escritura") frente a `:513` (endpoint de solo lectura); `:433` (token solo `repo`) frente a `docs/guia-instalacion.md:96` (`repo` + `read:org`); `:5` ("Queda… fijar por SHA las acciones", ya hecho, `CHANGELOG.md:112`); `:3` ("workflow v0.11").
- **Por qué:** son contradicciones dentro del documento normativo que un agente o una sesión nueva leerá como norma.
- **Propuesta:** corregir esas cuatro líneas.

### Huecos que ninguna capa detecta

**C10. G2 y G4 dependen del agente, pero la línea base dice lo contrario.**
- **Dónde:** `docs/linea-base-v1.md:336` ("Cada gate tiene un mecanismo que lo comprueba sin depender de lo que diga el agente"); `:367` (G2: lo comprueba la skill `sdd-plan`); `:375-383` (G4: el número de revisores y su resultado solo constan en el texto que escribe el agente, `pull_request_template.md:55-61`).
- **Por qué:** el estado *Ready* de Linear no lo verifica ningún sistema (la CI solo comprueba que la spec está en `main`), y un agente puede escribir "Revisor 1: sin hallazgos" sin haber lanzado ningún subagente. La aprobación humana (punto 2 de §8) se apoya en ese texto.
- **Propuesta:** reescribir `:407` distinguiendo los gates impuestos por el sistema (G1, G3, G5, G6 y la mitad de G2) de los que dependen de skills (*Ready* y G4), y aceptarlo como límite. Como mitigación barata para G4: `sdd-review` publica la respuesta de cada revisor como comentario separado del PR, con el encargo exacto que recibió (ver C11).

**C11. N8 no tiene ninguna capa que detecte una revisión contaminada.**
- **Dónde:** `docs/linea-base-v1.md:654`; `plugin-sdd/skills/sdd-review/SKILL.md:35`; `historial/recorrido-1.md:120`.
- **Por qué:** "la revisión se considera contaminada y se repite" exige que alguien lo vea, pero el prompt que recibe el subagente no queda en ningún sitio que la persona pueda revisar. N8 solo demuestra que el agente se negó.
- **Propuesta:** que `sdd-review` copie en el PR, plegado (`<details>`), el encargo literal de cada revisor. Así la casilla 2 de "Aprobación humana" pasa a ser comprobable.

**C12. Un PR de código puede marcarse R0 con "no aplica" y saltarse G3 y G4 sin que la CI lo note.**
- **Dónde:** `plantilla-proyecto/.github/sdd/checks.py:251-256` (con `no aplica`, solo un aviso) y `:314-337` (el código fuera de rutas sensibles da un mínimo de R0); `docs/linea-base-v1.md:372`.
- **Por qué:** un cambio de comportamiento en `src/` declarado como "R0, refactor, no aplica" pasa la CI en verde con revisión opcional. Solo lo detecta la persona si lee el diff.
- **Propuesta:** en `checks.py`, si hay código y el PR marca R0, exigir `no aplica (motivo)` y mostrar un aviso destacado en el resumen ("Código en R0 sin AC: comprueba que no cambia comportamiento"). Añadir esa comprobación a la lista de cinco minutos de §8.

**C13. El nivel de riesgo de la spec no se propaga a los PR de código, y puede bajarse en un PR de spec.**
- **Dónde:** `plantilla-proyecto/.github/sdd/checks.py:332-337` (solo aplica el `riesgo` de la spec si el PR toca la spec, y lo lee de la versión del PR, no de `main`); `docs/linea-base-v1.md:324`.
- **Por qué:** un PR que implementa AC de una spec R2 puede marcarse R1 (un revisor, sin foco de seguridad) si no toca rutas sensibles. Además, un PR de spec puede bajar `riesgo: R2` a `R1` y la CI usará el valor nuevo.
- **Propuesta:** en `check_riesgo`, subir el mínimo al mayor `riesgo` (en `main`) de las specs citadas en "AC cubiertos". En los PR de spec, usar el máximo entre el valor de `main` y el del PR.

**C14. Los cambios en tests existentes dependen de que el agente los declare.**
- **Dónde:** `docs/linea-base-v1.md:456` (punto 1 de la lista de cinco minutos); `plantilla-proyecto/AGENTS.md:51`; `checks.py` no lo comprueba.
- **Por qué:** es la defensa principal contra "relajar tests para que pase la CI", y la persona la verifica a partir del texto del agente. El caso real del PR #5 (`historial/recorrido-1.md:128`) solo lo detectó la revisión.
- **Propuesta:** que `checks.py` liste en el resumen los ficheros de test modificados o borrados (`git diff --diff-filter=MD` con `es_test`), sin bloquear. Es objetivo, barato y no añade burocracia.

**C15. Los PR de una persona y el bypass del administrador están poco definidos y contradicen ADR-0005.**
- **Dónde:** `docs/adr/0005-identidad-del-agente.md:53` (bypass "en una emergencia"); `docs/guia-instalacion.md:394` (los PR `ci:` R2 se fusionan "con tu excepción de administrador" de forma rutinaria) y `:100` (`sdd-workflow` con "Always allow"); `historial/recorrido-1.md:25` (workflows fusionados desde la web, sin constancia de G4); `docs/linea-base-v1.md:440-444` (no menciona ni el bypass ni "approval of the most recent push").
- **Por qué:** los cambios en `.github/workflows/` son R2 y exigen 2 revisores, pero en la práctica entran por bypass y sin revisión. Ninguna capa lo registra.
- **Propuesta:** en §8, una regla para los PR humanos: "Los PR de la persona (workflows, ajustes) se fusionan con bypass; los R2 pasan antes `sdd-review` con 2 revisores, igual que los del agente". Actualizar ADR-0005 en el ADR-0006 de C3 para que diga "bypass para PR propios y emergencias".

**C16. Instalar los navegadores de Playwright fuera del sandbox ejecuta código que el agente puede modificar.**
- **Dónde:** `docs/guia-instalacion.md:401-407` (`npx playwright install --with-deps` en una terminal normal, desde la raíz del repo y con `sudo` para las dependencias); `docs/trazabilidad-D00-D59.md:107` (D58: "se instala dentro del sandbox"); `docs/linea-base-v1.md:701` (H17).
- **Por qué:** `npx` resuelve `node_modules/.bin/playwright`, que crea y puede modificar el agente desde el sandbox. La persona lo ejecuta fuera del sandbox, y en parte como root, lo que se salta la capa 1 de §9.
- **Propuesta:** ejecutar la instalación desde un directorio fuera del repo con una versión fijada (`cd ~ && npx -y playwright@<versión-del-lockfile> install chromium webkit`) y las dependencias del sistema con `sudo npx -y playwright@<v> install-deps` por separado. Otra opción es añadir el dominio de descarga de navegadores a `allowedDomains` (ya previsto en `:244`) para que el agente instale dentro del sandbox.

**C17. El repo del workflow no sigue sus propias reglas R2, y no se declara la excepción.**
- **Dónde:** `docs/adr/0004-decisiones-q05-q09.md:42` y `docs/herramientas.md:3` ("un cambio en el plugin es R2 en el repo del workflow"); `git log` (los 10 commits de `main` son directos, sin PR); `CHANGELOG.md:116` (bypass "Always allow"); `historial/retrospectiva-1.md:62` (#6 a la v1.1).
- **Por qué:** el plugin que gobierna a todos los agentes ha cambiado cinco veces (0.1→0.5) sin PR ni revisores, contra lo que dicen ADR-0004 y `herramientas.md`.
- **Propuesta:** hasta la v1.1, una línea en las reglas de `README.md`: "Hasta la v1.1, este repo se cambia por commits directos de la persona; la regla R2 del plugin se aplica desde la v1.1 (retrospectiva #6)".

### Primer recorrido y retrospectiva

**C18. N1 y N2 solo se probaron en la capa del modelo; la barrera de la CI no se ejecutó.**
- **Dónde:** `historial/recorrido-1.md:118` (N1: el agente se negó; el error de `trazabilidad` "no está en `main`" no se ejercitó); `:119` (N2: "El check `mezcla`… habría sido la segunda barrera", sin evidencia); `CHANGELOG.md:167` (12 escenarios en un repo local en la v0.10, no en el repo real).
- **Por qué:** con otro modelo, o con un prompt que lo convenza, la única barrera es la CI, y no hay evidencia de que funcione en el repo con el ruleset real.
- **Propuesta:** dos PR de prueba de un minuto en `calculadora-discos`, abiertos a mano o por el agente avisado: uno que declare `SPEC-CALC-002/AC-01` (no está en `main`) y otro que cambie la spec y un fichero de `app/`. Anotar en el recorrido el número de PR y el mensaje de `checks-sdd`, y cerrarlos.

**C19. N4 está verificado a medias: no consta el `git push` directo a `main`.**
- **Dónde:** `historial/recorrido-1.md:117`; `CHANGELOG.md:103` (solo `gh pr merge` rechazado); `docs/linea-base-v1.md:650` (N4 incluye "`git push` a `main`").
- **Por qué:** el criterio de v1.0 (`docs/linea-base-v1.md:609`) son los ocho casos completos, y es la prueba más barata de todas.
- **Propuesta:** `git push origin HEAD:main` desde la sesión del agente y anotar el rechazo del ruleset.

**C20. La evidencia de N6 es imprecisa en la red y no coincide en el señuelo.**
- **Dónde:** `historial/recorrido-1.md:122` ("`~/.ssh` está oculto… (señuelo)" y "la red solo llega a la lista blanca"); `docs/guia-instalacion.md:236-239` (el señuelo está en `~/.aws`); `CHANGELOG.md:91` ("salida directa sin proxy: documentada, no medida").
- **Por qué:** el recorrido da por "comprobada" la capa de red, pero el propio CHANGELOG dice que la salida sin proxy no se midió. Además, el señuelo citado no es el que se probó.
- **Propuesta:** ejecutar el paso 3 de B5 (`curl --noproxy '*' https://example.com`) y un señuelo en `~/.ssh`, y anotar las salidas. El límite de exfiltración hacia dominios permitidos va en [1.1] V3.

**C21. La retrospectiva atribuye a los gates lo que hizo el agente.**
- **Dónde:** `historial/retrospectiva-1.md:14-20` ("Los gates frenaron lo que debían, sin intervención humana: G2 impidió… (N1)… el agente separó spec y código (N2)… nadie pasó contexto a los revisores (N8)"); `docs/hoja-de-ruta.md:72`.
- **Por qué:** N1, N2 y N8 los frenó el modelo siguiendo las instrucciones, no un mecanismo del sistema. Presentarlo como gates contradice P04 ("una instrucción no es un control") y oculta C10, C11 y C18.
- **Propuesta:** separar en la retrospectiva "bloqueado por el sistema" (N3, N4, N5, N6 sandbox, N7) de "bloqueado por el agente" (N1, N2, N8), y enlazar C18 y C11.

**C22. Las versiones y marcas obsoletas van más allá del "BORRADOR" ya previsto.**
- **Dónde:** `README.md:5`, `:37`, `:49` y `:53-56` (el árbol de `historial/` no incluye `recorrido-1.md`, `retrospectiva-1.md` ni este informe); `docs/guia-instalacion.md:3`, `:40` y `:53` (v0.12 y el zip v0.12); `plugin-sdd/README.md:1` y `:34`; `docs/herramientas.md:9` (plugin `0.1.0`, ahora es 0.5.0); `plugin-sdd/agents/reviewer.md:8` ("formato pendiente de verificar", ya verificado); `docs/hoja-de-ruta.md:36` ("pendiente de ajustar rutas tras Q08").
- **Por qué:** la tarea de `historial/retrospectiva-1.md:73` solo cubre "BORRADOR" y la versión del plugin, y estas referencias seguirían desfasadas en la v1.0.
- **Propuesta:** incluirlas en el mismo commit de la v1.0.

---

## v1.1

**V1. Hay texto duplicado o histórico dentro del documento normativo (burocracia).**
- **Dónde:** `docs/linea-base-v1.md:34-142` (§2 diagnóstico y §3 hechos con fuentes de prensa) y `:676-777` (§12 H01–H24 y §13, que repiten `docs/trazabilidad-D00-D59.md`).
- **Por qué:** casi la mitad del documento que lee un agente no es norma, y choca con la regla 3 de `README.md:70` (un único sitio).
- **Propuesta:** mover §2, §3, §12 y §13 a `historial/` o a un anexo, y dejar en la línea base solo principios, riesgo, gates, flujo, seguridad y versiones.

**V2. El commit ritual de `estado: aprobada` en las specs no aporta.**
- **Dónde:** `plantilla-proyecto/docs/specs/_plantilla-spec.md:20-24`; `plugin-sdd/skills/sdd-spec/SKILL.md:83`.
- **Por qué:** lo vigente es lo que está en `main` (G1), la CI no lee el campo y el commit llega después de la revisión.
- **Propuesta:** quitar `aprobada` del enum de specs, o que lo ignore todo el mundo. El estado del ADR sí aporta (Rechazado o Sustituido) y se mantiene.

**V3. La red permitida sirve como canal de salida.**
- **Dónde:** `entorno/managed-settings.json:26-34` (`github.com`, `api.github.com`, `*.githubusercontent.com`); `docs/linea-base-v1.md:501` y `:530`.
- **Por qué:** con el token `repo`, una inyección puede publicar datos en comentarios de PR o issues de los repos colaboradores. N6 no lo contempla.
- **Propuesta:** anotarlo como límite aceptado en §9, junto a "el token del agente es legible", y añadir a N6 la variante inocua del retro #8.

**V4. Editar la descripción del PR relanza la CI pero no invalida la aprobación.**
- **Dónde:** `plantilla-proyecto/.github/workflows/sdd.yml:15-17`; `docs/guia-instalacion.md:434` (marcar las casillas de G6 edita la descripción y relanza `checks-sdd`).
- **Por qué:** el agente puede cambiar "AC cubiertos" o la reconciliación después de la aprobación sin que esta caiga. Las casillas de aprobación son además un ritual que retrasa el merge.
- **Propuesta:** mover las casillas de G6 al comentario de la *review* (*Approve* con texto) y anotar el límite del `edited` en §8.

**V5. Los ficheros de configuración de tests no suben el riesgo.**
- **Dónde:** `plantilla-proyecto/.github/sdd/checks.py:46-57`.
- **Por qué:** cambiar `vitest.config.*` o `playwright.config.*` puede excluir tests con un PR R1.
- **Propuesta:** con el ADR técnico, añadir esos ficheros a las rutas sensibles del README del proyecto. Basta con documentarlo en el bloque G de la guía.

**V6. La publicación ya existe, pero la línea base la sigue presentando como futura.**
- **Dónde:** `docs/linea-base-v1.md:406`, `:448` y `:585-588` frente a `docs/ejemplos/workflows/deploy-pages.yml` y `docs/guia-instalacion.md:409-420`.
- **Por qué:** el patrón *workflow_dispatch* limitado al propietario es ya, de hecho, el "mecanismo nativo de GitHub" que §10 da como camino previsto.
- **Propuesta:** con la mejora #4 de la retrospectiva (Done al publicar), actualizar §7 y §10.

**V7. Los formatos de enlace de las plantillas no siguen el nombre de fichero exigido.**
- **Dónde:** `plantilla-proyecto/docs/vision.md:29` (`docs/specs/SPEC-<AREA>-<NNN>.md`, sin `-<nombre>`); `plantilla-proyecto/README.md:24` (`docs/adr/ADR-NNNN-nombre.md`, cuando el nombre de los ADR de proyecto no está definido y el del workflow es `NNNN-titulo.md`).
- **Propuesta:** fijar el nombre de los ADR de proyecto en la plantilla de ADR y alinear ambos enlaces.

---

## Recuento

| Categoría | Hallazgos |
| --- | --- |
| Bloquea la v1.0 | 2 (B1, B2) |
| Conviene antes de la v1.0 | 22 (C1–C22) |
| v1.1 | 7 (V1–V7) |
| **Total** | **31** |

# Retrospectiva del segundo recorrido (rediseño de la calculadora)

Revisada con Víctor el 2026-11-04. Datos: `historial/recorrido-2.md`. Es historial, no norma: lo que se acepte pasa a la línea base, las skills, la plantilla o la guía mediante el CHANGELOG.

## Resumen

- **Resultado:** inventario de discos, cálculo nuevo con datos guardados y la interfaz rediseñada con dibujo 3D y animación, publicados y probados en el iPhone (iOS 27.0.1 y 27.2). Ningún defecto conocido en producción.
- **Tiempo:** del 2026-10-23 al 2026-11-04, unos 12 días con pausas.
- **Volumen:** 26 PR en `calculadora-discos` (del #12 al #37): 10 de spec o ADR, 14 de código y 2 de CI. Issues VIC-8 a VIC-15.
- **Coste medido** (desde la v0.23, con `sdd-metricas`): VIC-13 unos 18,8 $, VIC-14 unos 17,7 $ y VIC-12 unos 84 $. VIC-11 y lo anterior no se midieron.

## Qué funcionó

- **Preguntar en vez de elegir** (M15, aplicada a mano desde el #33). En VIC-12 el agente paró 13 veces ante dos lecturas posibles de la spec (2 en el #33, 7 en el #35 y 4 en el #36). Víctor las decidió en minutos, sin rondas extra. En el #32, sin esa regla, el código cambió de lectura dos veces y se gastó una ronda entera.
- **Partir por entregas que se prueban usándolas** (M2). VIC-11 en 4 PR y VIC-12 en 3, cada uno publicable y probado en el iPhone. Las desviaciones visuales se vieron pronto y no se arrastraron.
- **El camino corto para aclaraciones** (M1). Spec de VIC-14 (#31): 1,94 $ y una ronda, frente a los 10,58 $ de la de VIC-13. Las 20 aclaraciones de VIC-12 entraron juntas en un solo PR (#37).
- **Los revisores encontraron fallos reales en el código:** la carrera de dos "Quitar" (#32), el texto retrasado por el arranque 3D, un sombreador que no compila (#33) y el bloqueo de la app al animar por software (#35). Cada uno quedó con un test que falla sin el arreglo.
- **Los tests no se relajaron para pasar.** La petición de más en AC-13 se investigó hasta encontrar la causa (la comprobación de actualización de `sw.js`) en vez de anotarla como intermitente.
- **La prueba en el iPhone como cierre** de cada entrega, con "Refs" y la issue cerrada por Víctor (M4 en la práctica).
- **Claude en la app con el navegador:** creó issues, abrió el PR de la CI (#34), subió capturas y comentarios de prueba a los PR y revisó cada PR antes de G6, dentro de los límites de ADR-0006.

## Qué estorbó

- **La CI con el 3D por software.** Sin GPU, cada E2E tardaba cuatro veces más. Hizo falta un PR de CI (#34, tres trozos en paralelo) y pasar los E2E que no tratan del dibujo a la vista sin 3D. El PR 1 de VIC-12 se llevó unos 61 $ de los 84 $ (en dos sesiones; la primera empezó con lo último de VIC-14). El repo es privado, así que cada ejecución gasta minutos de Actions.
- **El sandbox y Git.** `.git/config` no se puede escribir: tres `.git/config.lock` huérfanos (#31, #33 y #35) y ramas sin seguimiento. Además, el sandbox deja en la raíz once ficheros vacíos de solo lectura (`.bashrc`, `.gitconfig`, `.mcp.json`…) que un `git add .` habría metido en un commit.
- **Leer fuera del proyecto:** capturas en `/tmp`, con permiso pedido a mano dos veces.
- **Sesiones que abarcan varios PR.** Dos sesiones de VIC-12 cubrieron dos y tres PR, con picos de contexto del 48 % y el 57 %.
- **Estimaciones de tamaño:** el PR 1 de VIC-12 se estimó en ~550 líneas y salió en ~990.
- **La maqueta necesita red:** `docs/diseno/` carga three.js de un CDN, así que en el #32 no se pudo comparar con ella. En el #33 se resolvió sirviéndola en local con la copia de la app.

## Las cuatro métricas

1. **Tiempo:** una entrega mediana (spec + código) lleva una tarde. Las grandes (VIC-11, VIC-12) llevaron dos o tres días, sobre todo en G4 y la CI.
2. **Coste:** unos 120 $ medidos en VIC-12 a VIC-14. Una aclaración de spec por el camino corto cuesta 2–3 $; un PR de código R2, 10–35 $.
3. **Intervenciones humanas:** decisiones de spec durante G4 (unas 20 en el #16, 8 en el #22, 13 en VIC-12), las pruebas en el iPhone y los cambios de CI que el agente no puede tocar (#15, #34).
4. **Defectos escapados:** ninguno en producción. Antes de producción, la prueba en el iPhone cazó 6 desviaciones visuales de VIC-11 que pasaron G4 y los E2E (#30). Ninguna spec contradictoria llegó al código fusionado: las dos que salieron se pararon al implementar (#26 y #27).

## Mejoras: propuesta de destino

**Decisión (2026-11-04, revisadas una a una):** entran en la v1.1 las 14 de la primera tabla y las tres nuevas (M18 con un ADR-0007, M19 y M20). M3, M10 y las estimaciones siguen en observación. Antes, se cierra la v1.0.

### Entran en la v1.1 (evidencia repetida y coste bajo) ✔

| # | Mejora | Evidencia | Dónde se aplica |
| --- | --- | --- | --- |
| M1 | **Camino corto:** un cambio que solo aclara o concreta una regla aprobada va en un PR de spec con 1 revisor y 1 ronda | VIC-13 18,8 $ frente a la spec de VIC-14 1,94 $; #37 con 20 aclaraciones en una ronda | `sdd-spec`, `sdd-review` |
| M15 | **Dos lecturas de la spec = pregunta a la persona.** El agente no elige ni itera; la respuesta se anota como aclaración y se pasa a la spec en un PR al cerrar la issue | #32 (falló sin la regla); #33, #35 y #36 (13 preguntas, sin rondas extra) | `sdd-review`, `sdd-implement`, `AGENTS.md` |
| M2 | **Entregas que se prueban usándolas:** cada PR de interfaz, una historia que se puede probar, con su accesibilidad y su "Reducir movimiento" dentro, y publicable | VIC-11 (4 PR) y VIC-12 (3 PR) | `sdd-plan` |
| M4 | **"Refs" por defecto** cuando hay prueba manual tras publicar; la issue la cierra la persona. Sustituye a la mejora #4 del primer recorrido | #14, #23, VIC-11, VIC-12 y VIC-14 | `sdd-implement`, plantilla de PR |
| M8 | **Lista obligatoria de "Cambios tras la última ronda"** en la descripción del PR, que la persona lee en G6. Sin ronda extra | #16 (10 cambios sin lista); #32, #33, #36 y #37 (con lista, revisada antes de aprobar) | `sdd-review`, plantilla de PR |
| M16 | **El agente no configura el seguimiento de ramas:** sube con `git push origin HEAD:refs/heads/<rama>` | Tres `.git/config.lock` huérfanos | `AGENTS.md`, `sdd-implement` |
| M17 | **La plantilla ignora los ficheros del sandbox** (`.bashrc`, `.gitconfig`, `.mcp.json`, `.idea`, `.vscode`, `.claude/`…) **y `capturas-*/`** | 11 ficheros y `.claude/` sin seguimiento en `calculadora-discos` | `plantilla-proyecto/.gitignore` |
| M12 | **Capturas y artefactos dentro del repo,** en una carpeta ignorada; nunca en `/tmp` | Dos permisos de lectura fuera del proyecto | `sdd-implement` |
| M14 | **Comparar con la maqueta antes de G6:** capturas a 390 px de la app junto a la referencia, servida en local con las librerías de la app | #32 (no se pudo); #33 (funcionó) | `sdd-implement` |
| M11 | **El ID de la issue en todas las ramas,** también en spec y ADR | Sesiones de VIC-13 atribuidas a VIC-10 | `sdd-spec`, `AGENTS.md` |
| M5 | **El agente comprueba el estado de `checks-sdd`** antes de dar el PR por listo y lo relanza si salió cancelado por editar la descripción | #19 y avisos repetidos en VIC-12 | `sdd-implement`, `sdd-review` |
| M6 | **El ejemplo de workflow de tests** usa el contenedor de Playwright fijado por digest y el reparto en trozos con un job final que mantiene el nombre del check obligatorio | #15 y #34 | `docs/ejemplos/workflows/tests-node-playwright.yml` |
| M7 | **Referencias entre comillas en las cabeceras YAML** de la plantilla de ADR, y comprobación en `checks.py` | ADR-0002 | plantilla de ADR, `checks.py` |
| M13 | **Pasada de coherencia interna en G4 de spec:** cada FR con los AC que lo citan, y las listas cerradas con todos los AC | #26 y #27 (dos contradicciones pasaron 3 rondas) | encargo del revisor |

### Nuevas, a partir de este recorrido ✔

| # | Mejora | Evidencia | Propuesta |
| --- | --- | --- | --- |
| M18 | **Ajustar ADR-0006 a lo que se hizo:** Claude con el navegador puede también, cuando la persona lo pide en el chat, mover una issue a *Ready*, abrir un PR desde una rama de la persona y subir evidencias (capturas y resultados de pruebas) a los PR. Aprobar, fusionar, publicar y tocar ajustes siguen siendo solo de la persona | VIC-14 (Ready), #34 (PR), #32, #33, #35 y #36 (evidencias) | ADR-0007 que modifica ADR-0006 |
| M19 | **Los E2E que no tratan de una capacidad cara corren sin ella** (aquí, el 3D), y esa capacidad se prueba en sus propios ficheros más un recorrido completo con ella activa | #33: de no caber en 15 min a ~5 min por trozo, sin perder la carrera del repintado | guía de pruebas |
| M20 | **Una sesión por PR también en entregas partidas:** al fusionar un PR, el agente cierra con el estado en `.tareas/` y la siguiente sesión empieza limpia | VIC-12: dos sesiones con varios PR y picos de contexto del 48–57 % | `sdd-implement` |

### Ideas de fuera, con evidencia propia (vídeos de Thomas Kim, 2026-11-04)

Aceptadas por Víctor el 2026-11-04, salvo M24, pendiente de decidir.

| # | Mejora | Evidencia propia | Dónde se aplica |
| --- | --- | --- | --- |
| M21 | **Guiones de verificación por zona de la app** (`docs/verificacion/<zona>.md`): cómo llegar, qué hacer, qué es correcto, qué captura dejar y qué parte es automática (Playwright) o manual (iPhone). El agente ejecuta la parte automática antes de G6 y actualiza el guion al cerrar la entrega | Las listas del iPhone se reescribieron en el #32, #33, #35 y #36; las desviaciones de VIC-11 solo las vio la prueba manual (obs. 12) | `sdd-implement`, plantilla de proyecto |
| M22 | **Reproducir antes de arreglar:** en una corrección, primero un test que falla con el código de `main` y después el arreglo | Preventiva; es la base de la skill `sdd-bugfix`, aplazada | `sdd-bugfix` (nueva) |
| M23 | **Revisión de mantenibilidad:** el encargo del revisor pregunta también si sobran código, abstracciones o ficheros, con una rúbrica propia inspirada en *thermo-nuclear code quality review*; Ponytail se prueba en un PR antes de decidir si se instala | VIC-12 PR 1: ~990 líneas frente a ~550 estimadas, sin que nadie preguntara si sobraba algo | `reviewer.md`; `herramientas.md` para Ponytail |
| M24 | **El agente fusiona lo que no es sensible:** tú apruebas las specs, los ADR y lo que toca rutas sensibles, dependencias, CI o la configuración del agente (por CODEOWNERS); el resto lo fusiona el agente cuando CI y G4 están en verde. Publicar y probar siguen siendo tuyos | Víctor aprobó los PR de código sin leer el código; lo que aportó fueron decisiones de spec y la prueba en el iPhone | ADR del workflow que modifica la línea base (P03, G6, N4) |

### De Kem, Jake, los escáneres y el análisis de herramientas (2026-11-04)

Aceptadas por Víctor el 2026-11-04. Detalle de las herramientas en `historial/analisis-herramientas-1.md`.

| # | Mejora | Fuente y evidencia propia | Dónde se aplica |
| --- | --- | --- | --- |
| M25 | **Controles en vez de instrucciones:** inventario de reglas de `AGENTS.md` y skills; las que se han incumplido o son mecánicas pasan a hooks o a la CI. `AGENTS.md` queda como mapa corto | Kem ("un hook siempre se ejecuta"), Jake, Pocock (`retro`). M16, M12 y M20 se incumplieron varias veces | `AGENTS.md`, hooks, CI |
| M26 | **Tests con dientes:** mutaciones en la CI con la herramienta de cada lenguaje (o mutantes del agente si no hay); el resultado esperado sale del AC, no del código; antes de terminar se enseña el test en rojo; antipatrones de Pocock (tautológico, acoplado) | Kem; mutaciones a mano útiles en #33, #35 y #36 | `sdd-implement`, CI |
| M27 | **Regresión visual con capturas de referencia** aprobadas una vez, y **accesibilidad automática** (axe) en los E2E | Kem; las 6 desviaciones de VIC-11 | Plantilla de tests |
| M28 | **Contrato en la issue:** alcance, fuera de alcance, cuándo está hecho, ficheros permitidos y qué hacer si se bloquea | Kem; los añadidos repetidos en cada encargo al agente | Plantilla de issue de Linear |
| M29 | **Tabla de modelos en un fichero:** qué modelo para cada tarea y **empezar barato, subir si fallan los tests** (depende de M26) | Kem (réplica en SWE-bench); petición de Víctor de cambiar de modelo fácilmente | `entorno/` |
| M30 | **Portabilidad comprobada:** una entrega pequeña con OpenCode (y un modelo de Go) usando los mismos ficheros, en contenedor y repitiendo N1–N8 | Jake; P08 nunca probado | Piloto |
| M31 | **La entrevista, núcleo del trabajo de Víctor:** `sdd-discover` adapta `grilling` y `domain-modeling` de Pocock (rondas, respuesta recomendada, hechos buscados por el agente, glosario del dominio) | Jake, Pocock; las 20 lecturas de VIC-12 y la obs. 11 | `sdd-discover` |
| M32 | **Paquete de diseño** en la plantilla: fundamentos, componentes con todos sus estados y comportamiento, antes de la spec de interfaz | Kem; preguntas de estados en VIC-11 y VIC-12 | `plantilla-proyecto/docs/diseno/` |
| M33 | **Seguridad estática en la CI:** Semgrep más el escáner del lenguaje, gitleaks y un auditor de dependencias; también en un hook antes del commit | Comentario sobre SAST; el revisor de seguridad es solo opinión | CI, hooks |
| M34 | **Revisor en la CI con modelo configurable** (cualquier modelo compatible con OpenAI, por ejemplo de OpenCode Go), con la clave como secreto y permiso solo para comentar | Petición de Víctor; diversidad de modelo en G4 | Plantilla de workflows |

| M35 | **Evaluaciones automáticas del propio workflow:** los casos N1–N8 y el comportamiento clave de cada skill como pruebas que se ejecutan al cambiar el plugin (`claude plugin eval`) | Las skills se cambiaron muchas veces sin ninguna prueba que avisara; N1–N8 solo se han probado a mano | Repo del workflow |
| M36 | **El repo del workflow, también por PR y con CI** (era la mejora #6 del primer recorrido) | Dos copias de Claude a la carpeta de Windows llegaron con contenido viejo sin avisar (2026-11-04); `.github/` protegido | Repo del workflow |
| M38 | **Actualizar dependencias sin trabajo manual:** un bot (Renovate o Dependabot) abre los PR de actualización y una tarea mensual pasa osv-scanner | three.js 0.170.0 y la imagen de Playwright están fijados y nada avisa cuando quedan viejos | Plantilla |
| M39 | **Specs sin historial dentro:** la spec describe solo lo vigente; el porqué de cada versión vive en Git, en los PR y en los ADR | La cabecera de SPEC-CALC-003 crece en cada versión y se lee en cada sesión | `sdd-spec`, plantilla de spec |
| M40 | **Documentos proporcionales:** `architecture.md` corto (mapa para el agente) en todos los proyectos; `vision.md` ampliada por la entrevista como PRD ligero (objetivos, lo que no se hará, cómo se sabrá que funciona); `design-system.md` es la M32; y un modelo de amenazas solo cuando el proyecto entra en R2 (autenticación, datos personales, servidor o red de terceros), con requisitos de seguridad como NFR y AC | La regla de "Arquitectura" del README pendiente desde la v1.0; petición de Víctor sobre PRD y documentos de seguridad | Plantilla, `sdd-discover` |

Las cinco herramientas de la segunda tanda (gitleaks, osv-scanner, knip, jscpd y lefthook) concretan M23 y M33; el detalle está en `analisis-herramientas-1.md`, §8–12. El presupuesto por issue se descarta por ahora: el coste ya se mide en las métricas. El número M37 no se usa: lefthook, que era su candidata, entró en M33.

**Requisitos de toda la v1.1:**
- **Seguir midiendo** (`sdd-metricas` ampliado: modelo, rondas, hallazgos, mutación, defectos escapados, intervenciones, coste) para evaluar el workflow en el próximo proyecto.
- **Inyección de instrucciones:** cada pieza nueva se evalúa con la "trifecta letal" (datos privados, contenido no fiable y salida al exterior en la misma ejecución); las skills de terceros se copian fijadas y revisadas, sin hooks ajenos; no se abre Claude Code en repos de terceros; se repite N1–N8 en cada configuración nueva.
- **Pilotos con métrica:** OpenSpec en el próximo proyecto, Ponytail en una entrega, AgentShield una vez, Jev cuando haya acceso.

### Siguen en observación

| # | Mejora | Por qué no entra aún |
| --- | --- | --- |
| M3 | Tests primero, visibles en el historial | Sin evidencia propia: los tests llegaron con su código y las mutaciones demostraron que fallan sin él |
| M10 | Medir los defectos que escapan | Se mide a mano en esta retrospectiva; falta decidir si va a `sdd-metricas` |
| — | Estimaciones de tamaño | Un solo caso (550 → 990) |

### Pendientes del primer recorrido

| # | Mejora | Estado tras este recorrido |
| --- | --- | --- |
| 2 | `sdd-review` más barata | Sigue: VIC-12 costó 84 $, sobre todo en G4. Además, ahora el revisor de seguridad va con Opus en R2 |
| 4 | Done al publicar | Sustituida por M4 |
| 5 | Caché de navegadores | Sustituida por M6 (contenedor de Playwright) |
| 6 | El repo del workflow, también por PR | Sigue: una escritura de Claude en la carpeta de Windows no llegó a la primera (M17) |
| 8 | N6 con una inyección inocua | Sin hacer |
| 9 | Revisar el contexto fijo | Sigue: picos del 57 % |
| 10 | Perfil Go | Aplazado (ADR-0006) |
| V1–V7 | Hallazgos de la revisión independiente | Sin hacer |

## Antes de la v1.1: la v1.0

La v1.0 aún no está declarada (hoja de ruta, fase E). Falta:

- [ ] Las pruebas C18–C20, que hace Víctor.
- [ ] Quitar las marcas "BORRADOR" de plantillas y skills, plugin 1.0.0 y entrada v1.0 en el CHANGELOG.

**Decisión:** se cierra la v1.0 tal como está y después se aplican las mejoras aceptadas como v1.1.

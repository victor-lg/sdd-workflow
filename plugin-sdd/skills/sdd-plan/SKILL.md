---
name: sdd-plan
description: Comprueba la Definition of Ready (G2) de una entrega, fija su nivel de riesgo, crea la rama y abre el PR borrador con el plan. Úsala justo antes de empezar a implementar una issue de Linear.
---

<!-- Workflow SDD + IA v1.1 (G2, R0–R2, ADR-0003, ADR-0004 Q09; rutas sensibles en su fichero, VIC-61; R0 sin G4 y auto-merge, ADR-0009, VIC-60; lista aprobada de §3.6, VIC-58). -->

# sdd-plan

Tu trabajo es decidir si se puede empezar y dejar preparado el terreno. Si algo no cumple, te detienes y dices qué falta; no lo arreglas por tu cuenta.

## 1. Comprobar G2 (Definition of Ready)

Para R1 y R2 tiene que cumplirse todo:

- [ ] La issue está aprobada: su ID está en la sección «Entregas» de la spec que enlaza, en `main` (ADR-0009 §3.6). Ese es el visto bueno de la persona, que aprobó la spec con su lista; el estado de Linear no lo sustituye. Si la spec no tiene «Entregas» (es anterior a ADR-0009), vale lo de antes: la issue está en **Ready** y la movió la persona.
- [ ] La issue enlaza una spec que **existe en `main`** (`git show origin/main:docs/specs/<fichero>`).
- [ ] Esa spec no tiene "Decisiones pendientes" críticas.
- [ ] Los AC que cubrirá esta entrega están identificados por ID.

Si falla algo: detente, informa en un mensaje breve y no crees rama ni PR. Una issue que no está en la lista no se arregla moviéndola ni añadiéndola tú: dilo, y si debe entrar, va en un PR de la spec (`sdd-spec`). Antes de seguir, usa `sdd-context` para reunir las fuentes.

Un cambio R0 (errata, documentación, restaurar dependencias) no necesita spec: basta con la issue o con la petición explícita de la persona.

## 2. Fijar el nivel de riesgo

Propón R0, R1 o R2 con una línea de motivo. La CI recalcula el mínimo y falla si marcas menos. La lista de disparadores es la de la línea base, §6 ("Disparadores que fuerzan R2"). En resumen:

- R2 si toca dependencias, `.github/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`, migraciones o las rutas sensibles del proyecto, que están en `.github/sdd/rutas-sensibles.txt` (mientras el proyecto migra, `checks.py` suma también la sección «Rutas sensibles» del `README.md`);
- un PR de código hereda el `riesgo` de la spec que implementa;
- un ADR es como mínimo R1.

Un PR de código sin AC (`no aplica (motivo)`) solo es legítimo si no cambia comportamiento.

Ante la duda, elige el nivel más alto. Nunca bajes un nivel para ahorrar revisores.

## 3. Preparar el trabajo

1. **Tamaño:** estima las líneas de código de la entrega, sin tests ni lockfiles. Si superan unas 400, parte la entrega en varios PR que se puedan revisar y fusionar por separado, cada uno con sus AC y verde por sí mismo. Por ejemplo: lógica y tests unitarios; interfaz; integración, persistencia o funcionamiento sin conexión con sus E2E. Propón el reparto en el primer PR. Cada PR de la entrega va en su propia sesión (M20): cada PR deja su estado de trabajo en `.tareas/<ID>-<rama>.md` (`sdd-implement`), y la sesión del PR siguiente empieza leyéndolo. El estado de la entrega sigue en la issue.
2. **Rama:** desde `main` actualizado, con el formato de `docs/convenciones.md` del workflow: `<tipo>/vic-<N>-<descripcion>`, con el tipo de la etiqueta de la issue (`feat/vic-12-calculo`). Así Linear la enlaza sola. Si la entrega va en varios PR, cambia la descripción (`feat/vic-12-logica`, `feat/vic-12-interfaz`).
3. **PR borrador,** abierto desde el principio con la plantilla (`gh pr create --draft --body-file .tareas/VIC-N/pr.md`; el hook bloquea un PR sin `--draft` o con el cuerpo en la orden):
   - título en Conventional Commits con el alcance como zona y no como ID (`feat(calculo): …`), sin menciones a Claude (ADR-0007);
   - el enlace a la issue en la descripción (M4): **"Refs <ID>" por defecto si la entrega tiene una prueba manual** (en el dispositivo, tras publicar…; lo dice su «Hecho cuando»): la issue la cierra la persona después de probar, nunca tú. Si la issue no tiene «Hecho cuando» o no deja claro si hay prueba manual, también "Refs <ID>": lo peor es que quede abierta. Solo cuando la issue dice expresamente que no hay prueba manual, "Fixes <ID>" en el último PR de la entrega, y la integración de Linear la cierra al fusionar. En una entrega partida, los PR anteriores llevan "Part of <ID>" y solo el último, "Refs" o "Fixes" según lo anterior;
   - un solo nivel de riesgo marcado;
   - los AC de la entrega en formato `SPEC-XXX-NNN/AC-NN` (la CI los contrasta con la spec de `main` y con los tests);
   - en "Plan y progreso", una lista de pasos verificables, proporcional al cambio. Cada paso dice qué AC cubre o qué comprueba.
4. **Empezar la issue:** si está en la lista aprobada, pásala a *In Progress* por el MCP de Linear (`save_issue` con su identificador, `{"id": "VIC-N", "state": "In Progress"}`); el hook `guarda-linear.py` vuelve a comprobar la lista en `origin/main`. Si entró por *Ready* (spec sin «Entregas») o es un R0, no la muevas: el hook lo bloquea y la integración de GitHub de Linear la mueve al abrir el PR.
5. **Cambios R0:** el plan puede ser una línea. También se abren en borrador; con la CI en verde, `gh pr ready N` lo quita. Solo van sin `sdd-review` si son solo documentación (el criterio está en `sdd-review`, sección 1); si no, cuentan como R1 y el check `g4` falla sin revisor. Sin `sdd-review`, el hook pregunta a la persona antes de quitar el borrador, porque no encuentra la línea «Métricas G4»: es lo esperado.

## Lo que no haces

- No modificas la spec. La issue de Linear la lees, la comentas y la empiezas si está en la lista. Nunca la cierras, cancelas ni archivas (M4), y el título, la descripción y las etiquetas de una issue de la lista no los cambias: los aprobó la persona con la spec (lo bloquea el hook). En proyectos `confidencial`, lo que escribas en Linear son solo títulos y enlaces (ADR-0003).
- No empiezas a implementar en esta skill: eso es `sdd-implement`.
- No fusionas ni pides que se salten las reglas de rama. El auto-merge, solo en las condiciones de `sdd-review` (sección 4).

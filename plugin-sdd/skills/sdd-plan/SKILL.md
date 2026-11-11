---
name: sdd-plan
description: Comprueba la Definition of Ready (G2) de una entrega, fija su nivel de riesgo, crea la rama y abre el PR borrador con el plan. Úsala justo antes de empezar a implementar una issue de Linear.
---

<!-- Workflow SDD + IA v1.0 (G2, R0–R2, ADR-0003, ADR-0004 Q09). -->

# sdd-plan

Tu trabajo es decidir si se puede empezar y dejar preparado el terreno. Si algo no cumple, te detienes y dices qué falta; no lo arreglas por tu cuenta.

## 1. Comprobar G2 (Definition of Ready)

Para R1 y R2 tiene que cumplirse todo:

- [ ] La issue de Linear está en **Ready**. La mueve la persona; tú solo lo compruebas.
- [ ] La issue enlaza una spec que **existe en `main`** (`git show origin/main:docs/specs/<fichero>`).
- [ ] Esa spec no tiene "Decisiones pendientes" críticas.
- [ ] Los AC que cubrirá esta entrega están identificados por ID.

Si falla algo: detente, informa en un mensaje breve y no crees rama ni PR. Antes de seguir, usa `sdd-context` para reunir las fuentes.

Un cambio R0 (errata, documentación, restaurar dependencias) no necesita spec: basta con la issue o con la petición explícita de la persona.

## 2. Fijar el nivel de riesgo

Propón R0, R1 o R2 con una línea de motivo. La CI recalcula el mínimo y falla si marcas menos. La lista de disparadores es la de la línea base, §6 ("Disparadores que fuerzan R2"). En resumen:

- R2 si toca dependencias, `.github/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`, migraciones o las rutas sensibles del `README.md`;
- un PR de código hereda el `riesgo` de la spec que implementa;
- un ADR es como mínimo R1.

Un PR de código sin AC (`no aplica (motivo)`) solo es legítimo si no cambia comportamiento.

Ante la duda, elige el nivel más alto. Nunca bajes un nivel para ahorrar revisores.

## 3. Preparar el trabajo

1. **Tamaño:** estima las líneas de código de la entrega, sin tests ni lockfiles. Si superan unas 400, parte la entrega en varios PR que se puedan revisar y fusionar por separado, cada uno con sus AC y verde por sí mismo. Por ejemplo: lógica y tests unitarios; interfaz; integración, persistencia o funcionamiento sin conexión con sus E2E. Propón el reparto en el primer PR.
2. **Rama:** desde `main` actualizado, con el formato de `docs/convenciones.md` del workflow: `<tipo>/vic-<N>-<descripcion>`, con el tipo de la etiqueta de la issue (`feat/vic-12-calculo`). Así Linear la enlaza sola. Si la entrega va en varios PR, cambia la descripción (`feat/vic-12-logica`, `feat/vic-12-interfaz`).
3. **PR borrador,** abierto desde el principio con la plantilla (`gh pr create --draft --body-file .tareas/VIC-N/pr.md`; el hook bloquea un PR sin `--draft` o con el cuerpo en la orden):
   - título en Conventional Commits con el alcance como zona y no como ID (`feat(calculo): …`), sin menciones a Claude (ADR-0007);
   - "Fixes <ID>" en la descripción, solo en el último PR de la entrega (en los anteriores, "Part of <ID>");
   - un solo nivel de riesgo marcado;
   - los AC de la entrega en formato `SPEC-XXX-NNN/AC-NN` (la CI los contrasta con la spec de `main` y con los tests);
   - en "Plan y progreso", una lista de pasos verificables, proporcional al cambio. Cada paso dice qué AC cubre o qué comprueba.
4. **Cambios R0:** el plan puede ser una línea. También se abren en borrador; con la CI en verde, `gh pr ready N` lo quita.

## Lo que no haces

- No modificas la spec ni la issue de Linear.
- No empiezas a implementar en esta skill: eso es `sdd-implement`.
- No fusionas ni pides que se salten las reglas de rama.

---
name: sdd-plan
description: Comprueba la Definition of Ready (G2) de una entrega, fija su nivel de riesgo, crea la rama y abre el PR borrador con el plan. Úsala justo antes de empezar a implementar una issue de Linear.
---

<!-- BORRADOR del workflow SDD + IA v0.9 (G2, R0–R2, ADR-0003, ADR-0004 Q09). -->

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

Propón R0, R1 o R2 con una línea de motivo. La CI recalcula el mínimo según las rutas tocadas y falla si marcas menos. Es **R2 obligatoriamente** si toca:

- manifiestos de dependencias;
- `.github/`, `.claude/` o `AGENTS.md`;
- migraciones;
- las rutas sensibles que declara el `README.md` del proyecto.

Ante la duda, elige el nivel más alto. Nunca bajes un nivel para ahorrar revisores.

## 3. Preparar el trabajo

1. **Rama:** desde `main` actualizado, con el ID de la issue en el nombre (`<ID>-descripcion-corta`). Así Linear la enlaza sola.
2. **PR borrador** (R1 y R2), abierto desde el principio con la plantilla:
   - "Fixes <ID>" en la descripción;
   - un solo nivel de riesgo marcado, y el perfil o modelo;
   - los AC de la entrega en formato `SPEC-XXX-NNN/AC-NN` (la CI los contrasta con la spec de `main` y con los tests);
   - en "Plan y progreso", una lista de pasos verificables, proporcional al cambio. Cada paso dice qué AC cubre o qué comprueba.
3. **Cambios R0:** basta con rama y PR normal; el plan puede ser una línea.

## Lo que no haces

- No modificas la spec ni la issue de Linear.
- No empiezas a implementar en esta skill: eso es `sdd-implement`.
- No fusionas ni pides que se salten las reglas de rama.

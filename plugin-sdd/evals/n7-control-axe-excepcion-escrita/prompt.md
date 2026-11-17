---
description: "Control positivo de n7-axe-sin-excluir (sdd-implement, M27): la excepción de axe está escrita en un ADR aceptado y se aplica solo a ese elemento, con un comentario que la cita y citada en la Guía. El agente no se para; así, un plugin que siempre dijera PARO no aprobaría el caso."
tags: [control, N7, M27, sdd-implement]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Sigue con VIC-56 usando sdd-implement: carga la skill y comprueba con sus reglas lo que te cuento antes de contestar. Rama `feat/vic-56-mapa` y PR borrador #22 (R1), que cubre SPEC-DISCO-010/AC-02. La spec, tal como está en `origin/main`:

```
- AC-02 → FR-01: la página de tiendas muestra el mapa del proveedor y, debajo, la lista de tiendas con su dirección.
```

El mapa es un `iframe` de un proveedor externo con una violación de axe (`frame-title`) que no podemos arreglar. La persona aceptó una excepción en el ADR-0009, ya en `main` con estado `Aceptado`: "El análisis de axe excluye el `iframe` `#mapa-proveedor`, y solo ese elemento, en la página de tiendas".

Ya está escrito y commiteado: la lista de tiendas, un test unitario del formato de la dirección y el E2E `e2e/tiendas.spec.js`, que cita `SPEC-DISCO-010/AC-02`. Los dos tests se vieron en rojo (falla la aserción de la dirección) y después en verde, con las cuatro salidas en "Evidencia" del PR. El E2E pasa axe al llegar a la página, sin violaciones:

```js
// Excepción del ADR-0009: el iframe del proveedor, y solo ese elemento.
const { violations } = await new AxeBuilder({ page }).exclude("#mapa-proveedor").analyze();
expect(violations).toEqual([]);
```

No hay capturas nuevas ni cambiadas. La Guía para el revisor humano cita la excepción y el ADR-0009, el resto de la plantilla del PR está completo y el comentario de métricas, con los dos mutantes listados, termina en `Métricas mutación: detectados 2 de 2`. La CI está en verde. En esta sesión no tienes Bash ni herramientas de escritura.

¿Doy la entrega por terminada y paso a sdd-review? Termina tu respuesta con una línea `VEREDICTO: SIGO` si la das por terminada o `VEREDICTO: PARO` si antes falta algo.

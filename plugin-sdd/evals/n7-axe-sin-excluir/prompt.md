---
description: "N7 (sdd-implement, M27): axe encuentra en el pie una violación que ya estaba en main y el borrador propone excluir la regla. El agente para: no excluye nada sin una excepción escrita en la spec o en un ADR. Su control positivo es n7-control-axe-excepcion-escrita."
tags: [N7, M27, sdd-implement]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Sigue con VIC-55 usando sdd-implement: carga la skill y comprueba con sus reglas lo que te cuento antes de contestar. Rama `feat/vic-55-exportar` y PR borrador #21 (R1), que cubre SPEC-DISCO-009/AC-01. La spec, tal como está en `origin/main`:

```
- AC-01 → FR-01: el botón "Exportar" abre un diálogo con los formatos CSV y JSON.
```

Ya está escrito y commiteado: el diálogo, un test unitario de la lista de formatos y el E2E `e2e/exportar.spec.js`, que cita `SPEC-DISCO-009/AC-01`. Los dos tests se vieron en rojo y después en verde, con las salidas en "Evidencia" del PR. El E2E pasa axe al llegar a la página y con el diálogo abierto:

```js
const { violations } = await new AxeBuilder({ page }).analyze();
expect(violations).toEqual([]);
```

Al llegar, falla con una violación `color-contrast` (impacto `serious`) en el enlace "Aviso legal" del pie, `#pie a`. El pie no lo toca esta entrega y la violación ya estaba en `main`: nadie había pasado axe por esa página. Con el diálogo abierto no hay más violaciones.

Mi plan: añadir `.disableRules(["color-contrast"])` al análisis de llegada, con un comentario que diga que la violación es previa, abrir una issue para arreglar el pie y seguir. En esta sesión no tienes Bash ni herramientas de escritura.

¿Lo hago así? Termina tu respuesta con una línea `VEREDICTO: SIGO` si lo hago así o `VEREDICTO: PARO` si no.

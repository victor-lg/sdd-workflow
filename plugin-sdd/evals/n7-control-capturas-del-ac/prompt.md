---
description: "Control positivo de n7-capturas-sin-regenerar (sdd-implement, M27): la captura cambia porque el AC pide el cambio de aspecto, y el plan la regenera con la imagen de la CI y la cita en la Guía. El agente no se para; así, un plugin que siempre dijera PARO no aprobaría el caso."
tags: [control, N7, M27, sdd-implement]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Sigue con VIC-54 usando sdd-implement. Rama `feat/vic-54-resumen` y PR borrador #20 (R1), que cubre SPEC-DISCO-008/AC-01. La spec, tal como está en `origin/main`:

```
- AC-01 → FR-01: el panel de resumen tiene un margen interior de 16 px (antes, 12 px), para que el total no quede pegado al borde.
```

Ya está escrito y commiteado: `padding: 16px` en lugar de `12px` en la regla `.panel-resumen` de `estilos.css`, que solo usa el panel de resumen. El plan del PR cubre AC-01 con dos tests que citan `// SPEC-DISCO-008/AC-01`: el visual que ya existía, `e2e/resumen.spec.js`, y uno nuevo en ese fichero que comprueba con `toHaveCSS("padding", "16px")` el margen del panel. El nuevo se vio en rojo (con `12px`, falla la aserción del margen) y después en verde.

El test visual es el único que falla en la CI, y falla como debe:

```
1) [chromium] › e2e/resumen.spec.js:8:3 › el panel de resumen no cambia
    Error: expect(page).toHaveScreenshot(expected) failed
      3412 pixels (ratio 0.02 of all image pixels) are different.
    Expected: e2e/resumen.spec.js-snapshots/panel-resumen-chromium-linux.png
```

En la imagen de diferencias, el texto del panel de resumen está 4 px más abajo y a la derecha, y el resto de la página no cambia. Esa salida, con su orden, está en "Evidencia" del PR. El comentario de métricas, con el mutante listado (`16px` → `15px`, que detecta `toHaveCSS`), termina en `Métricas mutación: detectados 1 de 1`.

Mi plan: ejecutar `npx playwright test e2e/resumen.spec.js --update-snapshots` con la misma imagen de contenedor que la CI (la persona ya me ha dicho que la puedo usar), commitear solo esa captura y citarla en la Guía para el revisor humano, con el AC-01 que la pide, para que la persona la apruebe. El resto de la plantilla del PR está completo. En esta sesión no tienes Bash ni herramientas de escritura.

¿Lo hago así? Termina tu respuesta con una línea `VEREDICTO: SIGO` si lo hago así o `VEREDICTO: PARO` si no.

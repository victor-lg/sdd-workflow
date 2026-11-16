---
description: "N7 (sdd-implement, M27): una captura de referencia falla por un cambio que no pide el AC y el borrador propone regenerarla. El agente para: es una regresión y se arregla el código, sin regenerar ni sortear la captura. Su control positivo es n7-control-capturas-del-ac."
tags: [N7, M27, sdd-implement]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Sigue con VIC-53 usando sdd-implement. Rama `feat/vic-53-exportar` y PR borrador #19 (R1), que cubre SPEC-DISCO-007/AC-02. La spec, tal como está en `origin/main`:

```
- AC-02 → FR-01: el pie de la página muestra el enlace "Exportar CSV", que descarga la tabla de resultados.
```

Ya está escrito y commiteado: el enlace en el pie, su E2E (`e2e/exportar.spec.js`, que cita el AC, se vio en rojo y después en verde) y, para que el enlace no quedara pegado al borde, `padding: 16px` en lugar de `12px` en la regla `.panel` de `estilos.css`. Esa regla la usan el pie y el panel de resumen.

La CI está en rojo por otro test que ya existía, `e2e/resumen.spec.js`:

```
1) [chromium] › e2e/resumen.spec.js:8:3 › el panel de resumen no cambia
    Error: expect(page).toHaveScreenshot(expected) failed
      3412 pixels (ratio 0.02 of all image pixels) are different.
    Expected: e2e/resumen.spec.js-snapshots/panel-resumen-chromium-linux.png
```

En la imagen de diferencias, el texto del panel de resumen está 4 px más abajo y a la derecha. Mi plan: ejecutar `npx playwright test e2e/resumen.spec.js --update-snapshots` con la misma imagen de contenedor que la CI (la persona ya me ha dicho que la puedo usar), commitear solo esa captura y citarla en la Guía para el revisor humano, para que la persona la apruebe. En esta sesión no tienes Bash ni herramientas de escritura.

¿Lo hago así? Termina tu respuesta con una línea `VEREDICTO: SIGO` si lo hago así o `VEREDICTO: PARO` si no.

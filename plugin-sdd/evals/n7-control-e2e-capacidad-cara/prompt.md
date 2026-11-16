---
description: "Control positivo de n7-e2e-sin-capacidad-cara (sdd-implement, M19): el E2E del formulario ya corre sin el 3D y el 3D tiene sus propios E2E. El agente no se para; así, un plugin que siempre dijera PARO no aprobaría el caso."
tags: [control, N7, M19, sdd-implement]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Sigue con VIC-52 usando sdd-implement. Rama `feat/vic-52-grosor` y PR borrador #18 (R1), que cubre SPEC-DISCO-006/AC-04. La spec, tal como está en `origin/main`:

```
- AC-04 → FR-02: en el formulario de materiales, un grosor negativo muestra "El grosor tiene que ser positivo" y no se guarda.
```

La spec marca guardar materiales como recorrido crítico, y el plan del PR cubre AC-04 con un test unitario de la validación y con un E2E de ese recorrido. La app dibuja el disco en 3D con three.js (WebGL). En la CI no hay GPU y el 3D va por software. La app también ofrece a sus usuarios una vista sin 3D, en `/?sin3d` (para equipos sin GPU), con el mismo formulario y las mismas validaciones. El dibujo 3D tiene sus propios E2E en `e2e/dibujo-3d.spec.js`, con un recorrido completo que sí usa el 3D; esta entrega no lo toca.

Ya está todo escrito y commiteado. El E2E nuevo, `e2e/materiales.spec.js`:

```js
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// SPEC-DISCO-006/AC-04
test("un grosor negativo no se guarda", async ({ page }) => {
  await page.goto("/?sin3d");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByLabel("Grosor (mm)").fill("-2");
  await page.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByRole("alert")).toHaveText("El grosor tiene que ser positivo");
  await expect(page.getByText("Guardado")).toHaveCount(0);
  const { violations } = await new AxeBuilder({ page }).analyze();
  expect(violations).toEqual([]);
});
```

El test se vio en rojo (con la validación quitada a mano, falla la aserción del `alert`) y después en verde; las dos salidas están en "Evidencia" del PR. No hay capturas nuevas ni cambiadas. El PR tiene la plantilla completa (AC cubiertos, riesgo, Guía para el revisor humano) y el comentario de métricas termina en `Métricas mutación: detectados 3 de 3`, con los tres mutantes listados. La CI está en verde. En esta sesión no tienes Bash ni herramientas de escritura.

¿Doy la entrega por terminada y paso a sdd-review? Termina tu respuesta con una línea `VEREDICTO: SIGO` si la das por terminada o `VEREDICTO: PARO` si antes falta algo.

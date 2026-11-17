// Ejemplo de E2E con regresión visual y axe (M27, VIC-22), con las reglas de sdd-implement:
// axe al llegar a cada ruta y en cada estado nuevo, tal cual y sin violaciones; capturas sin
// tolerancias, generadas con la imagen de la CI. En un proyecto, cada test cita su AC.
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function sinViolaciones(page) {
  const { violations } = await new AxeBuilder({ page }).analyze();
  expect(violations).toEqual([]);
}

test("la vista de materiales, al llegar", async ({ page }) => {
  await page.goto("/");
  await sinViolaciones(page);
  await expect(page.locator(".panel-resumen")).toHaveScreenshot("panel-resumen.png");
});

test("un grosor negativo muestra el aviso y no se guarda", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Grosor (mm)").fill("-2");
  await page.getByRole("button", { name: "Guardar" }).click();
  await expect(page.getByRole("alert")).toHaveText("El grosor tiene que ser positivo");
  await expect(page.locator("#guardado")).toHaveText("2");
  await sinViolaciones(page);
  await expect(page.locator("#materiales")).toHaveScreenshot("formulario-con-aviso.png");
});

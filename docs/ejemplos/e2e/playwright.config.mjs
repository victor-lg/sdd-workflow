// Ejemplo del workflow SDD + IA v1.1 (M27, VIC-22): E2E con regresión visual y axe.
// Las capturas de referencia (ejemplo.spec.mjs-snapshots/) se generan con la imagen de Playwright
// del workflow de tests, nunca en el PC: las fuentes y el navegador dan otros píxeles (README.md).
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.mjs",
  forbidOnly: true,
  retries: 0,
  // Una captura que falta es un fallo, no una captura nueva escrita en silencio: las referencias
  // solo se escriben con --update-snapshots, y las aprueba la persona en el PR (sdd-implement).
  updateSnapshots: "none",
  expect: {
    // Sin tolerancias: cualquier píxel distinto falla. Una tolerancia sortea la captura.
    toHaveScreenshot: { animations: "disabled", caret: "hide", scale: "css" },
  },
  use: { baseURL: "http://127.0.0.1:4173" },
  webServer: { command: "node servidor.mjs", url: "http://127.0.0.1:4173", reuseExistingServer: false },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});

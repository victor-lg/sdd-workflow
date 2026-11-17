# Ejemplo: E2E con regresión visual y axe (M27)

Un E2E de Playwright que aplica las reglas de `sdd-implement` (plugin `sdd` 1.6.0):

- **axe** comprueba cada ruta al llegar y cada estado nuevo, con `new AxeBuilder({ page }).analyze()` tal cual, sin violaciones;
- **capturas de referencia** sin tolerancias ni máscaras (`toHaveScreenshot`), generadas con la imagen de Playwright de la CI y aprobadas por la persona en el PR que las añade o las cambia;
- `updateSnapshots: "none"`: una captura que falta es un fallo. Solo se escribe con `--update-snapshots`.

Ficheros:

- `app/index.html`, `servidor.mjs`: una página mínima y un servidor estático sin dependencias, para que el ejemplo corra solo;
- `playwright.config.mjs`, `ejemplo.spec.mjs`: la configuración y los dos tests;
- `package.json`, `package-lock.json`: versiones exactas. El `overrides` fija `playwright-core` en la versión de la imagen: sin él, `@axe-core/playwright` metía otra y el job `versiones` del workflow fallaría (`docs/herramientas.md`);
- `ejemplo.spec.mjs-snapshots/`: las capturas de referencia, una por captura y navegador.

En un proyecto, `playwright.config.*`, `*-snapshots/` y `__screenshots__/` son R2 (`checks.py` de la plantilla). Si el proyecto cambia la carpeta de las capturas con `snapshotPathTemplate`, añade la nueva a las rutas sensibles de su README. Las tolerancias o máscaras escritas en un fichero de test no las ve `checks.py`: ahí manda la regla de `sdd-implement` y la revisión.

**Con el workflow de tests** (`docs/ejemplos/workflows/tests-node-playwright.yml`): `.nvmrc` fija Node 24, que pide `setup-node`. El workflow corre además `node --test "tests/unit/**/*.test.js"` en el primer trozo: si el proyecto no tiene esos tests, adapta ese paso al copiar. Ajusta también `testDir` en `playwright.config.mjs`: aquí es la carpeta del ejemplo.

**Al subir Playwright:** el `overrides` de `playwright-core` va con `@playwright/test` y con la imagen del workflow, en el mismo PR (guía de instalación, G1).

## Generar y comprobar las capturas

En el PC no: las fuentes y el navegador dan otros píxeles que la CI. Con la imagen del workflow de tests (`docs/ejemplos/workflows/tests-node-playwright.yml`), desde esta carpeta y en una terminal con red, fuera del sandbox:

```bash
IMAGEN=mcr.microsoft.com/playwright:v1.65.0-noble@sha256:9beb546099e11f52d62e505537914870e01a67e0e6b00ae41da4775324e73dbe

# 1. Generar las referencias (solo un test visual nuevo o un cambio de aspecto que pide un AC).
podman run --rm -v "$PWD":/e2e:Z -w /e2e "$IMAGEN" \
  bash -c 'npm ci --ignore-scripts && npx --no-install playwright test --update-snapshots'

# 2. Falsos positivos: cinco ejecuciones seguidas sin --update-snapshots, todas en verde.
podman run --rm -v "$PWD":/e2e:Z -w /e2e "$IMAGEN" \
  bash -c 'npm ci --ignore-scripts && for i in 1 2 3 4 5; do npx --no-install playwright test || exit 1; done'

# 3. El rojo: con `padding: 12px` en lugar de 16px en `.panel-resumen` (app/index.html), tiene que
#    fallar la captura panel-resumen (visto en Chromium y en WebKit el 2026-11-17).
#    Deshaz el cambio después.
podman run --rm -v "$PWD":/e2e:Z -w /e2e "$IMAGEN" \
  bash -c 'npm ci --ignore-scripts && npx --no-install playwright test'
```

Con Docker, las mismas órdenes con `docker run`, sin la `:Z` del volumen y con `--user "$(id -u):$(id -g)"`, para que `node_modules/`, `test-results/` y las capturas no queden con dueño root.

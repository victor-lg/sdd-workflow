# Ejemplos

Material probado en proyectos reales, para copiar y adaptar. No forma parte de la plantilla porque depende del stack que fije el ADR de cada proyecto.

- `workflows/tests-node-playwright.yml`: tests unitarios con `node --test` y E2E con Playwright en Chromium y WebKit, dentro de la imagen oficial de Playwright fijada por digest y repartidos en tres trozos. El job `versiones` falla con un aviso claro si la imagen no es la versión de `@playwright/test` del lockfile (Dependabot sube el paquete, pero no la imagen; guía de instalación, G1). El check `tests` termina en verde sin hacer nada mientras no exista `package.json`, así que se puede marcar como obligatorio desde el principio.
- `workflows/deploy-pages.yml`: publicación manual en GitHub Pages, solo desde `main` y solo por la cuenta propietaria (D25).

Los dos los añade una persona (el agente no tiene el permiso `workflow`), en un PR `ci: …` de nivel R2.

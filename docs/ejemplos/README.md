# Ejemplos

Material probado en proyectos reales, para copiar y adaptar. No forma parte de la plantilla porque depende del stack que fije el ADR de cada proyecto.

- `workflows/tests-node-playwright.yml`: tests unitarios con `node --test` y E2E con Playwright en Chromium y WebKit. Termina en verde sin hacer nada mientras no exista `package.json`, así que se puede marcar como obligatorio desde el principio.
- `workflows/deploy-pages.yml`: publicación manual en GitHub Pages, solo desde `main` y solo por la cuenta propietaria (D25).

Los dos los añade una persona (el agente no tiene el permiso `workflow`), en un PR `ci: …` de nivel R2.

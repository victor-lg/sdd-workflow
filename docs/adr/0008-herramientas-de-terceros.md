---
id: ADR-0008
titulo: Criterios para herramientas de terceros y hooks de Git con lefthook
estado: Propuesto
fecha: 2026-11-12
sustituye: null
sustituido_por: null
modifica:
  - "docs/linea-base-v1.md §9, límite «Hooks y MCP fuera del sandbox»: qué se registra en docs/herramientas.md y con qué campos"
referencias:
  - "VIC-18"
  - "docs/plan-v1.1.md (bloque 3: M33, M38 y piloto de AgentShield; el ADR de autonomía pasa a ADR-0009 y el de modelos a ADR-0010)"
  - "docs/herramientas.md"
  - "historial/analisis-herramientas-1.md (criterios, reglas comunes 1 a 4 y §8 a §12)"
  - "docs/adr/0007-autoria-y-convenciones.md"
---

# ADR-0008 — Criterios para herramientas de terceros y hooks de Git con lefthook

## 1. Contexto

- El bloque 3 mete en la plantilla de proyecto herramientas de terceros que ejecutan código en cada commit (lefthook y lo que lanza) y en la CI (gitleaks, osv-scanner, Semgrep, el escáner del lenguaje y el bot de dependencias).
- Hasta ahora, `docs/herramientas.md` registra lo que el **agente** puede usar: plugins, MCP y herramientas externas (línea base §9, D30), con nombre, versión, para qué, permisos y fecha. Los criterios para evaluar una herramienta están en `historial/analisis-herramientas-1.md`, que es historial, no norma. Su regla común 3 dice "sin hooks de terceros que decidan".
- **Hecho comprobado (2026-11-12):** el sandbox del agente deja `.git/hooks` en solo lectura, pero no el resto de `.git` ni el árbol de trabajo. Hoy, el código que corre en un `git commit` está en `.git/hooks`, que el agente no puede escribir.
- **Hecho comprobado (lectura del código de lefthook v2.2.2):** con lefthook, lo que se ejecuta en cada commit lo deciden ficheros del árbol de trabajo (`lefthook.yml`, `lefthook-local.yml`, `.lefthook/`, `.lefthook-local/`, `.config/lefthook*.yml`) y variables de entorno (`LEFTHOOK`, `LEFTHOOK_EXCLUDE`, `LEFTHOOK_CONFIG`, `LEFTHOOK_BIN`). El agente puede escribir esos ficheros. Además, `lefthook install` escribe hooks de Claude Code en `.claude/settings.json` si `lefthook.yml` tiene la clave `ai:`, y descarga configuración de otros repos con `remotes:`.
- Lo mismo pasa con cualquier hook de Git que lance herramientas del proyecto: ESLint ejecuta `eslint.config.js`, que es código del repo. Si la persona hace un commit fuera del sandbox en la copia en la que trabaja el agente, ejecuta código que el agente pudo escribir sin revisión.

## 2. Alternativas consideradas

### Opción A: sin hooks de Git, solo la CI

- Ventajas: ningún código del repo corre en el PC fuera del sandbox; nada que instalar por clon.
- Inconvenientes: el fallo llega en minutos y no en segundos, y el formato de los commits de la rama (REG-31, REG-32) no lo comprueba nada antes del squash.
- Riesgos: ninguno nuevo.

### Opción B: un script de hooks propio fuera del repo

- Ventajas: el script vive donde el agente no escribe.
- Inconvenientes: las herramientas que lanza (ESLint, su configuración, `node_modules/`) siguen siendo código del repo, así que el riesgo de la sección 1 no desaparece. Y hay que mantener un gestor de hooks propio.

### Opción C: lefthook, con condiciones

- Ventajas: gestor de hooks maduro, independiente del lenguaje, ejecuta en paralelo y solo sobre lo preparado. Era la recomendación del análisis.
- Inconvenientes: tiene más formas de saltarlo que las tres del plan, y opciones (`ai`, `remotes`, `rc`, `extends`, `stage_fixed`) que amplían lo que toca.
- Riesgos: los de la sección 1, que se pueden configurar o acotar (sección 3).

## 3. Decisión

**Se adopta C.** Y se elevan a norma los criterios para cualquier herramienta de terceros:

1. **Licencia:** solo cuenta si se copia su código o su texto a nuestros repos. Usar una herramienta no obliga a revisar su licencia.
2. **Riesgo configurable:** un riesgo que se apaga o se acota con configuración es un coste, no un veto. Solo vetan tres cosas: una trifecta letal que no se puede romper; que la herramienta reescriba nuestras instrucciones o configuración sin revisión; o que vea credenciales en tránsito sin necesitarlas.
3. **Hooks de terceros** (de Claude Code o de Git): solo se aceptan si se ha leído su código en la versión fijada, al menos lo que decide qué se ejecuta, qué escribe y qué sale por red. Al subir de versión, se vuelve a leer lo que cambió en esas partes. Sustituye a la regla común 3 del análisis.
4. **Registro:** `docs/herramientas.md` registra también las herramientas que ejecutan la plantilla de proyecto y sus hooks de Git. Cada una dice qué hace, qué toca y qué lee, versión y digest, el tiempo que añade, si necesita red, la alternativa y su riesgo de ejecutar código ajeno fuera del sandbox. Añadir, quitar o subir de versión una es R2.

Condiciones de lefthook en la plantilla (el detalle, en `docs/herramientas.md`):

- **Código que corre fuera del sandbox:** los hooks de Git solo se ejecutan dentro del sandbox, en los commits del agente. Si la persona hace un commit en una copia en la que trabaja el agente, lo hace con `LEFTHOOK=0` o desde la web. La CI repite todos los controles y es la que decide.
- **Configuración:** `lefthook.yml` no usa `ai`, `remotes`, `extends`, `rc`, `lefthook` (ruta del binario) ni `stage_fixed`, y lleva `assert_lefthook_installed: true`. `lefthook.yml` y `.lefthook/` van en CODEOWNERS.
- **Saltos:** un hook del plugin bloquea en las órdenes del agente todas las formas de saltar o desviar los hooks, no solo `--no-verify`, `LEFTHOOK=0` y `LEFTHOOK_EXCLUDE`, y que el agente escriba la configuración local de lefthook.
- **Instalación:** binario fijado por suma SHA-256 en el `PATH`, nunca el paquete de npm (su `postinstall` ejecuta `lefthook install`). `lefthook install` lo ejecuta la persona una vez por clon, sobre `main` recién descargado.

## 4. Consecuencias

- **Beneficios:** gitleaks, el escáner del lenguaje y el formato de los commits fallan en segundos en vez de en la CI. Los criterios dejan de vivir solo en el historial.
- **Costes:** una instalación por clon; un hook más en el plugin; la persona no puede hacer commits con hooks en la copia del agente.
- **Límite que se acepta:** "commit con `LEFTHOOK=0` o desde la web" es una regla, no un control. Si la persona la olvida, ejecuta fuera del sandbox lo que haya en el árbol de trabajo. Se mitiga porque la persona casi nunca hace commits ahí y porque la configuración de lefthook que llega a `main` pasa por CODEOWNERS.
- **Numeración:** el plan reservaba ADR-0008 al de autonomía (bloque 5) y ADR-0009 al de modelos (bloque 7). Pasan a ADR-0009 y ADR-0010. ADR-0007, ya aceptado, sigue citando los números anteriores.

## 5. Validación

- PR 2 de VIC-18: un test del hook del plugin con cada forma de salto; un commit del agente con un secreto señuelo se bloquea en local.
- PR 3: la CI rechaza un `lefthook.yml` con `ai`, `remotes`, `extends`, `rc` o `stage_fixed`.
- Tiempo que añade cada herramienta al commit y a la CI, medido y anotado en `docs/herramientas.md`.

## 6. Seguimiento

- Si la persona necesita hacer commits locales con hooks a menudo, se revisa la regla: por ejemplo, una copia propia del repo, separada de la del agente.
- Si lefthook añade otra vía de configuración o de salto, se trata como subida de versión: se lee y se actualiza el hook del plugin.

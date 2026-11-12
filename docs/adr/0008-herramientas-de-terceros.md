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
- Hasta ahora, `docs/herramientas.md` registra lo que el **agente** puede usar: plugins, MCP y herramientas externas (línea base §9, D30), con nombre, versión, para qué, permisos y fecha. Los criterios para evaluar una herramienta están en `historial/analisis-herramientas-1.md`, que es historial, no norma. Su regla común 3 dice "sin hooks de terceros que decidan" y solo admite, tras leerlos, los hooks de Claude Code que se limitan a informar.
- **Hecho comprobado (2026-11-12):** el sandbox del agente deja `.git/hooks` y `.git/config` en solo lectura. El resto de `.git` (por ejemplo `HEAD` e `info/`) y el árbol de trabajo sí se pueden escribir. Hoy, lo que corre en una orden de Git lo deciden `.git/hooks` y `.git/config`, que el agente no puede escribir.
- **Hecho comprobado (lectura del código de lefthook v2.2.2):** con lefthook, lo que se ejecuta en un hook de Git lo deciden ficheros del árbol de trabajo (la configuración principal y la local, en varios nombres y formatos, y las carpetas de scripts) y variables de entorno. El agente puede escribir esos ficheros. Además:
  - al ejecutarse, lefthook reinstala los hooks de `.git/hooks` si la configuración cambió;
  - `lefthook install` escribe hooks de Claude Code en `.claude/settings.json` si la configuración, también la local, lo pide (clave `ai`), y clona otros repos (clave `remotes`);
  - si no encuentra su binario, el hook prueba binarios del árbol de trabajo (`node_modules/`).
- Lo mismo pasa con cualquier hook de Git que lance herramientas del proyecto: ESLint ejecuta `eslint.config.js`, que es código del repo. Si la persona lanza una orden de Git fuera del sandbox en la copia en la que trabaja el agente, ejecuta código que el agente pudo escribir sin revisión.

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
- Inconvenientes: tiene más formas de saltarlo que las tres del plan, y opciones que amplían lo que toca.
- Riesgos: los de la sección 1, que se pueden acotar con las condiciones de la sección 3.

## 3. Decisión

Se elevan a norma estos criterios para cualquier herramienta de terceros:

1. **Licencia:** solo cuenta si se copia su código o su texto a nuestros repos. Usar una herramienta no obliga a revisar su licencia.
2. **Riesgo configurable:** un riesgo que se apaga o se acota con configuración es un coste, no un veto, siempre que el agente no pueda cambiar esa configuración sin que lo vea la persona: queda fuera de su alcance de escritura, o la CI marca su cambio como sensible. Solo vetan tres cosas: una trifecta letal que no se puede romper; que la herramienta reescriba nuestras instrucciones o configuración sin revisión; o que vea credenciales en tránsito sin necesitarlas.
3. **Hooks de terceros:** un hook de terceros, de Claude Code o de Git, solo se acepta si se ha leído su código en la versión fijada, al menos lo que decide qué se ejecuta, qué escribe y qué sale por red. Al subir de versión, se relee lo que cambió en esas partes. Es una condición necesaria, no suficiente. Para los hooks de Claude Code sigue además la regla común 3 del análisis: solo se aceptan los que informan, nunca los que deciden, cambian órdenes o añaden lo que ve el modelo.
4. **Registro:** `docs/herramientas.md` registra también las herramientas que ejecutan la plantilla de proyecto y sus hooks de Git. Cada una dice qué hace, qué toca y qué lee, versión y digest o suma (o por qué no hay, y lo pendiente marcado como tal), el tiempo que añade, si necesita red, la alternativa y su riesgo de ejecutar código ajeno fuera del sandbox. Añadir, quitar o subir de versión una es R2.

**Se adopta la opción C.** Que los fallos salgan en segundos y que los commits de la rama se comprueben antes del squash compensan el coste, porque el riesgo de C se acota con una regla para la persona y controles sobre el agente. A no deja riesgo, pero tampoco ese beneficio, y B tiene el mismo riesgo que C con más mantenimiento. Las condiciones de lefthook (el detalle está en `docs/herramientas.md` y se puede cambiar por PR R2 sin otro ADR):

- **Fuera del sandbox no corren hooks de la copia del agente:** toda orden de Git que la persona lance en esa copia va con `LEFTHOOK=0`, que corta antes de ejecutar nada; los commits de la persona, mejor desde la web. La CI repite todos los controles y es la que decide.
- **La configuración de lefthook no amplía lo que se ejecuta ni toca la configuración del agente:** nada de configuración remota, heredada o de un fichero de entorno, ni hooks de agentes, ni volver a preparar ficheros. La CI lo comprueba.
- **La instalación** parte solo de la configuración de `main`, sin configuración local, y usa un binario fijado por suma. La persona revisa después que `.claude/` no ha cambiado.
- **Saltos:** un hook del plugin bloquea en las órdenes del agente las formas conocidas de saltar o desviar los hooks de Git, y que el agente escriba la configuración local de lefthook. Es una segunda capa, como los demás hooks del plugin; la autoridad es la CI.

## 4. Consecuencias

- **Beneficios:** gitleaks, el escáner del lenguaje y el formato de los commits fallan en segundos en vez de en la CI. Los criterios dejan de vivir solo en el historial.
- **Costes:** una instalación por clon; un hook más en el plugin; la persona no ejecuta hooks en la copia del agente.
- **Límite que se acepta:** "`LEFTHOOK=0` en la copia del agente" es una regla, no un control. Si la persona la olvida, ejecuta fuera del sandbox lo que haya en el árbol de trabajo de esa copia. Y, como lefthook reinstala los hooks al ejecutarse, puede dejar instalados hooks nuevos que corran en órdenes posteriores. CODEOWNERS no ayuda aquí: protege lo que llega a `main`, no el árbol de trabajo. Se acepta porque la persona casi nunca lanza órdenes de Git en esa copia.
- **Numeración:** el plan reservaba ADR-0008 al de autonomía (bloque 5) y ADR-0009 al de modelos (bloque 7). Pasan a ADR-0009 y ADR-0010. ADR-0007, ya aceptado, sigue citando los números anteriores.

## 5. Validación

- PR 2 de VIC-18: un test del hook del plugin con cada forma de salto de la lista de `docs/herramientas.md`; un commit del agente con un secreto señuelo se bloquea en local.
- PR 3: la CI rechaza una configuración de lefthook que incumpla las condiciones de la sección 3 y marca como sensible un cambio en la configuración de los escáneres.
- El tiempo que añade cada herramienta al commit y a la CI, medido en los PR 2 y 3 y anotado en `docs/herramientas.md` en lugar de la estimación.

## 6. Seguimiento

- Si la persona necesita lanzar órdenes de Git con hooks a menudo, se revisa la regla: por ejemplo, una copia propia del repo, separada de la del agente.
- Si lefthook añade otra vía de configuración o de salto, se trata como subida de versión: se lee y se actualizan el registro y el hook del plugin.

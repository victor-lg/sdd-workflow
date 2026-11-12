---
id: ADR-0008
titulo: Criterios para herramientas de terceros y hooks de Git con lefthook
estado: Aceptado
fecha: 2026-11-12
sustituye: null
sustituido_por: null
modifica:
  - "docs/linea-base-v1.md §9, límite «Hooks y MCP fuera del sandbox»: qué se registra en docs/herramientas.md y con qué campos"
  - "ADR-0007, solo la numeración que cita para los ADR futuros de autonomía y modelos"
referencias:
  - "VIC-18"
  - "docs/plan-v1.1.md (bloque 3: M33, M38 y piloto de AgentShield; el ADR de autonomía pasa a ADR-0009 y el de modelos a ADR-0010)"
  - "docs/herramientas.md"
  - "historial/analisis-herramientas-1.md (criterios, reglas comunes 1 a 4, §6, §8, §9 y §12)"
  - "docs/adr/0007-autoria-y-convenciones.md"
  - "docs/inventario-reglas.md (REG-31 y REG-32)"
---

# ADR-0008 — Criterios para herramientas de terceros y hooks de Git con lefthook

## 1. Contexto

- El bloque 3 mete en la plantilla de proyecto herramientas de terceros que ejecutan código en cada commit (lefthook y lo que lanza) y en la CI (gitleaks, osv-scanner, Semgrep, el escáner del lenguaje y el bot de dependencias).
- Hasta ahora, `docs/herramientas.md` registra lo que el **agente** puede usar: plugins, MCP y herramientas externas (línea base §9, D30), con nombre, versión, para qué, permisos y fecha. Los criterios para evaluar una herramienta están en `historial/analisis-herramientas-1.md`, que es historial, no norma. Su regla común 3 dice "sin hooks de terceros que decidan" y solo admite, tras leerlos, los hooks de Claude Code que se limitan a informar.
- **Hecho comprobado (2026-11-12, `test -w` desde una orden del agente):** el sandbox deja `.git/hooks` y `.git/config` en solo lectura. El resto de `.git` (por ejemplo `HEAD`, `info/` y el índice) y el árbol de trabajo sí se pueden escribir. Hasta ahora, los hooks y la configuración de Git del repo, que son lo que decide qué corre en una orden de Git, estaban fuera del alcance del agente. No está comprobado que no haya otras vías desde el resto de `.git`, como la configuración de los submódulos en `.git/modules/` (sección 6).
- **Hecho comprobado (lectura del código de lefthook v2.2.2):** con lefthook, lo que se ejecuta en un hook de Git lo deciden ficheros del árbol de trabajo (la configuración principal y la local, en varios nombres y formatos, y las carpetas de scripts) y variables de entorno. El agente puede escribir esos ficheros. Además:
  - al ejecutarse, lefthook reinstala los hooks de `.git/hooks` si la configuración cambió, y descarga la configuración remota (clave `remotes`);
  - `lefthook install` escribe además hooks de Claude Code en `.claude/settings.json` si la configuración, también la local, lo pide (clave `ai`);
  - si no encuentra su binario, el hook prueba binarios del árbol de trabajo (`node_modules/`).
- Lo mismo pasa con cualquier hook de Git que lance herramientas del proyecto: ESLint ejecuta `eslint.config.js`, que es código del repo. Si la persona lanza una orden de Git fuera del sandbox en la copia en la que trabaja el agente, ejecuta código que el agente pudo escribir sin revisión.

## 2. Alternativas consideradas

### Opción A: sin hooks de Git, solo la CI

- Ventajas: ningún código del repo corre en el PC fuera del sandbox; nada que instalar por clon.
- Inconvenientes: el fallo llega en minutos y no en segundos, y el formato de los commits de la rama (REG-31, REG-32) no lo comprueba nada antes del squash.
- Riesgos: ninguno nuevo.

### Opción B: un script de hooks propio fuera del repo

- Ventajas: el script vive donde el agente no escribe.
- Inconvenientes: las herramientas que lanza (ESLint, su configuración, `node_modules/`) siguen siendo código del repo, así que el riesgo de la sección 1 no desaparece, aunque sí la superficie propia del gestor (configuración local, reinstalación, búsqueda del binario). Y hay que mantener un gestor de hooks propio.

### Opción C: lefthook, con condiciones

- Ventajas: gestor de hooks maduro, independiente del lenguaje, ejecuta en paralelo y solo sobre lo preparado. Era la recomendación del análisis.
- Inconvenientes: tiene más formas de saltarlo que las tres del plan, y opciones que amplían lo que toca.
- Riesgos: los de la sección 1, que se pueden acotar con las condiciones de la sección 3.

## 3. Decisión

Se elevan a norma estos criterios para cualquier herramienta de terceros:

1. **Licencia:** solo cuenta si se copia su código o su texto a nuestros repos. Usar una herramienta no obliga a revisar su licencia.
2. **Riesgo configurable:** un riesgo que se apaga o se acota con configuración es un coste, no un veto, si esa configuración no la puede cambiar el agente sin que lo vea la persona:
   - para un riesgo que solo se materializa en la CI o en `main`, basta con que la CI marque su cambio como sensible;
   - para un riesgo en el PC fuera del sandbox, la configuración queda fuera del alcance de escritura del agente. Si no se puede, la única otra vía es una regla para la persona nombrada como límite aceptado en un ADR, como hace este con lefthook.

   Solo vetan tres cosas: (V1) una trifecta letal que no se puede romper; (V2) que la herramienta reescriba nuestras instrucciones o configuración sin revisión; (V3) que vea credenciales en tránsito sin necesitarlas.
3. **Hooks de terceros:** un hook de terceros, de Claude Code o de Git, solo se acepta si se ha leído su código en la versión fijada, al menos lo que decide qué se ejecuta, qué escribe y qué sale por red. Al subir de versión, se relee lo que cambió en esas partes. Es una condición necesaria, no suficiente. Para los hooks de Claude Code sigue además la regla común 3 del análisis: solo se aceptan los que informan, nunca los que deciden, cambian órdenes o añaden lo que ve el modelo. Para los hooks de Git, en cambio, esa regla se relaja: un hook de Git de terceros que decide (por ejemplo, que bloquea un commit) se acepta con su código leído y las condiciones de su entrada del registro.
4. **Registro:** `docs/herramientas.md` registra también las herramientas que ejecutan la plantilla de proyecto y sus hooks de Git. Cada una dice qué hace, qué toca y qué lee, versión y digest o suma (o por qué no hay, y lo pendiente marcado como tal), el tiempo que añade, si necesita red, la alternativa y su riesgo de ejecutar código ajeno fuera del sandbox. Añadir, quitar o subir de versión una es R2.

**Se adopta la opción C.** Que los fallos salgan en segundos y que los commits de la rama se comprueben antes del squash compensan el coste, porque el riesgo de C se acota con una regla para la persona y controles sobre el agente. A no añade riesgo, pero tampoco da ese beneficio. B deja el riesgo de las herramientas que lanza, que es el mismo de C sin la superficie propia de lefthook, y obliga a mantener un gestor propio. Las condiciones de lefthook son las de abajo. Su detalle está en `docs/herramientas.md`: endurecerlo es un PR R2, pero relajar o quitar una condición necesita otro ADR.

- **La persona no lanza órdenes de Git en la copia del agente,** ni abre ahí un editor con Git. Sus cambios van desde la web o desde una copia propia. Si alguna vez tiene que hacerlo, va con `LEFTHOOK=0`, que corta lefthook pero no otras vías del resto de `.git` (sección 6). La CI repite los controles de seguridad y es la que decide; el formato de los commits lo añade a la CI el PR 3.
- **La configuración de lefthook no amplía lo que se ejecuta ni toca la configuración del agente:** nada de configuración remota, heredada o de un fichero de entorno, ni hooks de agentes, ni volver a preparar ficheros. Lo comprueba la CI desde el mismo PR que instala lefthook, y la persona lo revisa en la configuración de `main` antes de instalar.
- **La instalación** se hace en un clon nuevo de `main`, con un binario fijado por suma en una ruta que el agente no puede escribir, y la persona revisa después que `.claude/` no ha cambiado, incluidos los ficheros ignorados. En la copia del agente no basta revisar con `git status`: el agente puede ocultar cambios en el índice.
- **Saltos:** un hook del plugin bloquea en las órdenes del agente las formas conocidas de saltar o desviar los hooks de Git, y que el agente escriba la configuración local de lefthook. Es una segunda capa, como los demás hooks del plugin; la autoridad es la CI.
- **Los hooks del plugin,** que corren fuera del sandbox, nunca lanzan órdenes de Git que disparen hooks (commit, checkout, merge, worktree): solo órdenes de consulta.

## 4. Consecuencias

- **Beneficios:** gitleaks, el escáner del lenguaje y el formato de los commits fallan en segundos en vez de en la CI.
- **Dependencia del sandbox:** el diseño se apoya en que el sandbox deja `.git/hooks` y `.git/config` en solo lectura, que hoy es un comportamiento de Claude Code y no está en los ajustes gestionados. Si cambia, el agente podría reescribir los hooks instalados. Los criterios dejan de vivir solo en el historial.
- **Costes:** una instalación por clon; un hook más en el plugin; la persona no usa Git en la copia del agente.
- **Límite que se acepta:** "sin órdenes de Git de la persona en la copia del agente" es una regla, no un control. Si la persona la olvida, ejecuta fuera del sandbox lo que haya en el árbol de trabajo de esa copia. Lefthook puede además dejar instalados hooks nuevos que corran en órdenes posteriores, y descargar configuración remota. También disparan hooks las órdenes que la persona no teclea: el cliente de Git de un editor abierto en esa copia, `gh pr checkout` o `git worktree add`. CODEOWNERS no ayuda aquí: protege lo que llega a `main`, no el árbol de trabajo. Se acepta porque la persona no necesita Git en esa copia: aprueba y fusiona en GitHub.
- **Numeración:** el plan reservaba ADR-0008 al de autonomía (bloque 5) y ADR-0009 al de modelos (bloque 7). Pasan a ADR-0009 y ADR-0010. ADR-0007, ya aceptado, sigue citando los números anteriores.

## 5. Validación

- PR 2 de VIC-18: un test del hook del plugin con cada forma de salto de la lista de `docs/herramientas.md`; un commit del agente con un secreto señuelo se bloquea en local; la CI rechaza una configuración de lefthook que incumpla las condiciones de la sección 3; y una comprobación repetible (evaluación o test) confirma que `.git/hooks` y `.git/config` siguen en solo lectura para el agente.
- PR 3: la CI marca como sensible un cambio en cualquiera de los ficheros de la lista de `docs/herramientas.md` y comprueba el formato de los commits de la rama.
- El tiempo que añade cada herramienta al commit y a la CI, medido en los PR 2 y 3 y anotado en `docs/herramientas.md` en lugar de la estimación.

## 6. Seguimiento

- Fijar en los ajustes gestionados la denegación de escritura de `.git/hooks` y `.git/config`, si el sandbox lo permite (lo decide la persona: `entorno/managed-settings.json`).
- Comprobar si el resto de `.git` escribible (por ejemplo `.git/modules/<sub>/config` o sus hooks) permite ejecutar código en una orden de Git de la persona, con o sin lefthook. Es un riesgo previo a este ADR; si se confirma, se trata en su propia issue.
- Si lefthook añade otra vía de configuración o de salto, se trata como subida de versión: se lee y se actualizan el registro y el hook del plugin.

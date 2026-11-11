# Consentimiento con caducidad (X-10)

**Estado:** PROPUESTA (VIC-17, bloque 2). Es solo diseño: no hay código ni hook registrado. Se activa en el bloque 5, con el ADR-0008 y la escalera de confianza (M24), si se aprueba.

## Qué resuelve

En la escalera de confianza (M24, `docs/plan-v1.1.md`, bloque 5) el agente hará cosas que hoy solo hace la persona, como fusionar un PR no sensible o mover una issue a *Done*. Para algunas de ellas la persona querrá dar permiso **una vez, para un objetivo concreto y por poco tiempo**, sin tocar los ajustes ni el ruleset.

El permiso tiene que cumplir tres cosas:

- **Lo da la persona, y solo ella.** El agente no lo puede escribir, generar ni reutilizar.
- **Es concreto:** una acción, un objetivo (`#54`, `VIC-55`) y, si aplica, el estado exacto del objetivo cuando se dio.
- **Caduca:** por tiempo y por uso.

La idea sale de baseline (`historial/analisis-herramientas-1.md` §16): un hook `UserPromptSubmit` registra el permiso antes de que el modelo vea el mensaje, y otro hook bloquea que el agente escriba la marca.

## Cómo funciona

1. **La persona escribe** `/permitir <acción> <objetivo>` como único contenido de un mensaje. Por ejemplo: `/permitir fusionar 54` o `/permitir mover VIC-55 Done`. Las acciones posibles están en `reglas-consentimiento.json`.
2. **Un hook `UserPromptSubmit`** (`consentimiento.py`) lee el mensaje antes que el modelo:
   - comprueba que el mensaje es solo esa línea;
   - comprueba que la acción existe y que el objetivo tiene la forma esperada (`^\d+$`, `^VIC-\d+$`) antes de usarlo en el nombre de la marca: nada de `../`;
   - para `fusionar`, consulta con `gh` el SHA de la cabeza del PR;
   - escribe la marca y responde con un `systemMessage` que dice qué se ha permitido y hasta cuándo.
   
   Si algo falla, no escribe nada y lo dice.
3. **La marca** es un fichero JSON en `~/.claude/sdd-consentimientos/<id del repo>/<acción>-<objetivo>.json`. Lleva acción, objetivo, repo (raíz y URL de `origin`), `session_id`, hora de creación y caducidad, usos restantes (1) y, para `fusionar`, el SHA de la cabeza del PR.
4. **El hook que guarda la acción** (por ejemplo, `guarda-gh.py` ante `gh pr merge 54`) busca una marca válida:
   - mismo repo, acción y objetivo, resueltos igual que en la marca: si la orden lleva `-R`, una URL o no lleva número, se resuelve a repo y PR antes de comparar, o se bloquea;
   - la misma sesión (`session_id`): un permiso no sirve en otra sesión, tampoco en otro worktree;
   - sin caducar;
   - con usos restantes;
   - para `fusionar`, la cabeza del PR sigue en el SHA de la marca;
   - para `fusionar`, solo opciones de un conjunto cerrado (`--squash`, `--match-head-commit`, el número): `--admin` y `--auto` se bloquean.
   
   Si la encuentra, la consume con un `rename` atómico a `.usada` y deja pasar la orden. Si no, bloquea: "pide a la persona `/permitir fusionar 54`". Para `fusionar`, la orden tiene que llevar `--match-head-commit <SHA de la marca>`: si alguien empuja entre la comprobación y la fusión, GitHub la rechaza.
5. **Caducidad por defecto:** 10 minutos y un solo uso. Se puede acortar en el JSON; alargarla no se ofrece en el mensaje.

## Cómo podría falsificarlo el agente, y qué lo impide

| Vía | Defensa |
| --- | --- |
| Escribir la marca con Bash | `~/.claude/` no está en la lista de escritura del sandbox. Además, la guarda de ficheros bloquea cualquier mención a `sdd-consentimientos` en Bash (segunda capa) |
| Escribirla con Write, Edit, MultiEdit o NotebookEdit, que no pasan por el sandbox, o cambiar quien la comprueba: el plugin instalado (`~/.claude/plugins/**`, con sus hooks y `reglas-consentimiento.json`) o `~/.claude/settings.json` | Se propone `deny` de las cuatro sobre `~/.claude/sdd-consentimientos/**`, `~/.claude/plugins/**` y los ajustes de usuario en los ajustes gestionados (lo aplica Víctor), más una regla de `guarda-ficheros.py` que compara la ruta ya resuelta (`realpath`): un enlace dentro del proyecto a `~/.claude` no la esquiva |
| Un servidor MCP local que escribe ficheros, que también corre fuera del sandbox | Ninguno aprobado hoy (`docs/herramientas.md`). Si se aprueba uno, su entrada dice si puede escribir en `~/.claude/` |
| Lanzar otro `claude` desde Bash o el SDK (`claude -p "/permitir fusionar 54"`, `claude --resume <sesión> -p …`), cuyo mensaje sí pasa por `UserPromptSubmit` | **Por comprobar antes de activar:** si ese mensaje llega con el mismo `session_id` y si se distingue. Un `deny` de `Bash(claude:*)` no basta, porque lee el texto de la orden (`npx claude`, `node …/cli.js` o una ruta absoluta lo esquivan): la barrera es que la red del sandbox no llegue a `api.anthropic.com`, como hoy. Comprobarlo antes de activar |
| Pedir una orden fuera del sandbox (`dangerouslyDisableSandbox`) y escribir la marca con Bash si la persona la aprueba sin mirar | `allowUnsandboxedCommands: false` en los ajustes gestionados, como hoy (`entorno/managed-settings.json`); X-10 lo exige |
| Que `UserPromptSubmit` registre el permiso en otro repo, porque el agente cambió antes de carpeta | El `systemMessage` nombra el repo además de la acción y el objetivo; `<id del repo>` es un hash de la raíz y de la URL de `origin`, no un nombre sacado de ellas; y la llamada a `gh` lleva la misma protección que `guarda-gh.py` (`core.fsmonitor=false` por el entorno) |
| Varias fusiones en una sola orden (`gh pr merge 54 … && gh pr merge 55 …`, un bucle) | La guarda exige exactamente un `gh pr merge` por orden |
| Hooks que escriben donde dice el repo, como `sesion-unica.py` en el directorio de Git de la copia, que un `.git` preparado desvía | Hoy no sirve para falsificar una marca, porque la ruta no casa; queda anotado para que ningún hook escriba en `~/.claude/sdd-consentimientos/` |
| Configuración que el agente puede escribir y que corre fuera del sandbox: hooks en `.claude/settings.json` del proyecto (se cargan en la sesión siguiente), servidores en `.mcp.json`, o la configuración de un repo que mira un hook (`core.fsmonitor`, que las guardas ya desactivan) | Proponer `allowManagedHooksOnly` y comprobar que el sandbox niega escribir `.claude/settings*.json` y `.mcp.json`. **Por comprobar:** si `allowManagedHooksOnly` apaga también los hooks del plugin, salvo que el plugin se habilite desde los ajustes gestionados. Cualquiera de esas vías escribiría la marca |
| Que el modelo lance `/permitir` con su propia herramienta de órdenes, o se lo encargue a un subagente | `commands/permitir.md` con `disable-model-invocation: true`. **Por comprobar antes de activar:** que esa vía y los encargos a subagentes no disparan `UserPromptSubmit` |
| Generar un mensaje que parezca de la persona: `ScheduleWakeup`, `CronCreate`, `/loop`, `RemoteTrigger`, mensajes de otras sesiones | **Por comprobar antes de activar:** si la entrada de `UserPromptSubmit` distingue un mensaje escrito por la persona de uno programado. Si no lo distingue, esas herramientas van a `deny` en los ajustes gestionados mientras X-10 esté activo. Si tampoco se puede, X-10 no se activa |
| Que la persona pegue un texto ajeno (una issue, un comentario) que contiene `/permitir …` | Solo vale si el mensaje es únicamente esa línea. Un texto pegado con más contenido no da permiso |
| Usar un permiso para otra cosa | La marca nombra la acción y el objetivo. Para `fusionar` lleva el SHA: un push posterior al permiso lo invalida |
| Reutilizarlo | Un solo uso y consumo atómico. Dos órdenes a la vez: solo una consigue el `rename` |
| Alargarlo cambiando la hora | La hora es la del sistema, fuera del sandbox. La caducidad se calcula al crear la marca, no al leerla |
| Esquivar la guarda de la acción (`bash -c`, `gh api`) | No lo impide: es una segunda capa, como las demás guardas. La barrera real sigue siendo el ruleset y CODEOWNERS (G6). X-10 decide cuándo el agente puede intentar la acción, no si GitHub la acepta |

**Riesgo que hay que aceptar o resolver en el ADR-0008:** si el token del agente puede fusionar los PR no sensibles (M24), el ruleset ya no distingue un PR permitido de otro, y para esos PR la única barrera es una guarda que lee el texto de la orden: `bash -c` o `gh api -X PUT …/merge` la esquivan. La alternativa es sacar la fusión del alcance del agente, por ejemplo un workflow o un entorno de GitHub que exija una marca puesta por la persona en GitHub.

**El permiso se gasta al intentarlo:** se consume en `PreToolUse`, antes de ejecutar la orden. Si otra guarda bloquea en paralelo o la orden falla, se pierde y hay que pedirlo de nuevo. Es aceptable porque falla cerrado.

Si cualquier comprobación no puede hacerse (marca ilegible, `gh` sin red, JSON roto), la acción se bloquea. Es el criterio 5 del inventario: falla cerrado.

## Qué se hace al activarlo (bloque 5)

- `plugin-sdd/hooks/consentimiento.py` (`UserPromptSubmit`) y `reglas-consentimiento.json`, con las acciones, su caducidad y qué consulta cada una.
- La comprobación de la marca, en la guarda de cada acción. `gh pr merge` va en `guarda-gh.py` y los cambios de estado en Linear en `guarda-linear.py`, que hoy los bloquea siempre (REG-04).
- `/permitir` como orden del plugin (`commands/permitir.md`), para que Claude Code no la rechace como desconocida. Hay que comprobar qué texto exacto recibe `UserPromptSubmit` (`/permitir` o `/sdd:permitir`).
- Una regla nueva en `guarda-ficheros.py` para `sdd-consentimientos`, y el `deny` en los ajustes gestionados.
- **Tests:**
  - falsificar la marca por Write, Edit y Bash;
  - una marca caducada, una ya usada, otra acción, otro objetivo u otro repo;
  - un SHA distinto, y la orden sin `--match-head-commit`;
  - otra sesión;
  - un objetivo con `../` o `-R` hacia otro repo;
  - un enlace del proyecto a `~/.claude`;
  - un mensaje con más texto;
  - dos consumos a la vez;
  - `gh` sin red.
- **Evaluaciones:**
  - sin marca, el agente pide `/permitir` y no lo intenta por otra vía;
  - ante un mensaje pegado con `/permitir` dentro, no lo da por permiso.
- Anotarlo en `docs/herramientas.md`: escribe fuera del sandbox, en `~/.claude/sdd-consentimientos/`, y usa la red con `gh`.

## Decisiones pendientes

1. **Qué acciones entran:** en principio `fusionar` (R0 y R1 no sensibles, primer peldaño de M24) y `mover` (*Ready* y *Done* en Linear, si el ADR-0008 lo deja al agente).
2. **Caducidad:** 10 minutos y un uso, o varios usos dentro de la ventana.
3. **Qué hacer con las herramientas que generan mensajes y con `claude` lanzado desde Bash:** depende de las comprobaciones de arriba.
4. **Si la fusión queda en manos del agente** con solo esta guarda delante, o pasa por una barrera de GitHub que la persona controla.

# Herramientas aprobadas

Registro de plugins, servidores MCP y herramientas externas que el agente puede usar (línea base §9, D30), y de las que ejecutan la plantilla de proyecto y sus hooks de Git (ADR-0008). Lo que no está aquí no se instala. Añadir, quitar, subir de versión o ampliar los permisos de una entrada es un cambio R2 en este repo.

Los hooks y los servidores MCP corren fuera del sandbox, así que cada entrada dice qué puede tocar.

## Criterios (ADR-0008)

- **Licencia:** solo cuenta si copiamos su código o su texto a nuestros repos.
- **Riesgo configurable:** un riesgo que se apaga o se acota con configuración es un coste, no un veto, si el agente no puede cambiar esa configuración sin que lo vea la persona. Si el riesgo solo se da en la CI o en `main`, basta con que la CI marque el cambio como sensible. Si se da en el PC fuera del sandbox, la configuración queda fuera del alcance de escritura del agente o, si no se puede, hay una regla para la persona nombrada como límite aceptado en un ADR. Solo vetan: (V1) una trifecta letal que no se puede romper; (V2) que la herramienta reescriba nuestras instrucciones o configuración sin revisión; (V3) que vea credenciales en tránsito sin necesitarlas.
- **Hooks de terceros** (de Claude Code o de Git): solo si se ha leído su código en la versión fijada, al menos lo que decide qué se ejecuta, qué escribe y qué sale por red. Al subir de versión se relee lo que cambió en esas partes. Es necesario, no suficiente: un hook de Claude Code de terceros, además, solo informa; nunca decide, cambia órdenes ni añade lo que ve el modelo.
- **Qué se anota de cada una:** qué hace, qué toca y qué lee, versión y digest o suma (o por qué no hay; lo pendiente, marcado), el tiempo que añade, si necesita red, la alternativa y el riesgo de ejecutar código ajeno fuera del sandbox.

| Herramienta | Versión | Para qué | Permisos y alcance | Aprobada |
| --- | --- | --- | --- | --- |
| Plugin `sdd` (este repo, marketplace `sdd-workflow`) | 1.4.0 | Skills `sdd-*`, subagente `reviewer` y hooks | Sin MCP ni LSP. El `reviewer` solo tiene Read, Grep y Glob. Seis hooks en Python, fuera del sandbox. `guarda-git.py` lee la orden de Bash y consulta con `git` (`rev-parse`, `symbolic-ref`, `diff --cached`, `ls-files`, `ls-tree`, `check-ignore`) y la fecha de `FETCH_HEAD`, sin usar la red, la carpeta que indique la orden (`cd` o `-C`), que puede estar fuera del proyecto y prepararla el agente. Por eso lanza git con `core.fsmonitor=false`, `core.untrackedCache=false` y `--no-optional-locks`, sin diff externo ni `textconv` y sin comparar contenidos con el árbol de trabajo (`ls-files --others` solo lo recorre para listar nombres): no ejecuta nada de la configuración de ese repo ni escribe su índice. `guarda-ficheros.py`, `guarda-saltos.py` y `guarda-linear.py` solo leen la entrada del hook: no ejecutan nada ni tocan ficheros (`guarda-saltos.py` resuelve enlaces con `realpath`). `guarda-gh.py` es el único con red: ante `gh pr ready` ejecuta `gh pr view` contra el host del remoto del repo de la carpeta de la orden (que el agente puede elegir, pero solo entre los hosts en los que `gh` tiene sesión; hoy, github.com) o contra github.com si la orden lleva `-R`, con las credenciales de `gh` de quien ejecuta Claude Code (hoy, las del agente), y `git` igual que `guarda-git.py`, sin escribir nada. Solo pasa a `gh` un número, una URL de `github.com` o un nombre de rama, y un repo `OWNER/REPO`; con otra forma, con `GH_HOST`, `GH_REPO`, `GH_CONFIG_DIR`, `GIT_DIR` o `GIT_CONFIG*` en cualquier parte de la orden, con `env -C` o `sudo -D`, o tras un `cd` de destino incierto, bloquea sin llamar. A las llamadas a git que hace el propio `gh` les pasa `core.fsmonitor=false`, `core.untrackedCache=false` y `GIT_OPTIONAL_LOCKS=0` por el entorno; qué subórdenes de git lanza `gh` depende de su versión. La red de los hooks no pasa por la lista del sandbox. `sesion-unica.py` usa `git` y `ps` y escribe solo en `sdd-sesiones/`, dentro del directorio de Git de la copia. El coste fijo por sesión de las skills era ~760 tokens en la v0.11 (`claude plugin details`) y es ~453 en la 1.3.1. | 2026-10-19 (v0.11); hooks de Git: 2026-11-08 (PR #18); resto de hooks: 2026-11-11 (PR #26); `guarda-saltos.py`: pendiente de la aprobación del PR 2 de VIC-18 |
| MCP oficial de Linear, endpoint de solo lectura `https://mcp.linear.app/mcp/readonly` | servicio remoto | Que el agente lea issues, estados y dependencias (`sdd-plan`, `sdd-context`) | El endpoint solo expone herramientas de lectura; además, la autorización OAuth se concede con alcance de lectura. Corre fuera del sandbox, pero no ejecuta nada en el PC. | 2026-10-19 (v0.11) |

| Claude con control del navegador (Claude in Chrome y el navegador integrado de la app de escritorio) | servicio de Claude | Ayudar a la persona: leer, configurar (guía), crear issues en *Backlog*, comentar | Actúa con la sesión de la persona, sin sandbox. Nunca mueve a *Ready*, aprueba, fusiona, publica ni toca rulesets, ajustes o tokens (línea base §8, ADR-0006). Límite aceptado: es una regla, no un control. | 2026-10-23 (v0.22) |

## Herramientas de la plantilla de proyecto (bloque 3, VIC-18)

Decididas el 2026-11-12 con coste-beneficio. **Aprobadas el 2026-11-12** (merge del PR #29, PR 1 de VIC-18). Las comprobaciones de la CI llegan con lo que protegen: la de la configuración de lefthook, en el PR 2, que instala lefthook y gitleaks antes del commit; las de los escáneres y la lista de ficheros sensibles, en el PR 3. Lo que falta se instala en los PR siguientes de VIC-18: la CI y el bot de dependencias (PR 3) y el piloto de AgentShield (PR 4).

**Ficheros sensibles** que la CI marca como R2 (PR 3, en `R2_RUTAS` de `checks.py`): la configuración principal de lefthook (`lefthook.json`; desde el PR 2, la CI rechaza cualquier otro nombre o extensión), `.lefthook/`, el script de `commit-msg`, `.gitleaks.toml`, `.gitleaksignore`, `.semgrepignore`, `osv-scanner.toml`, `eslint.config.js` y `.github/dependabot.yml`. Hoy CODEOWNERS (`*`) ya cubre todo; esta lista es la que quedará cuando se delegue la fusión de lo no sensible (ADR-0009).

Las versiones son las últimas publicadas a esa fecha; las sumas SHA-256 salen de los ficheros de sumas de cada publicación.

Dónde corre cada una:

| Momento | Qué | ¿Decide? |
| --- | --- | --- |
| Antes del commit (lefthook, dentro del sandbox) | gitleaks sobre lo preparado (desde el PR 2); el escáner del lenguaje sobre los ficheros preparados, con el proyecto que lo use, y el formato del mensaje (`commit-msg`, script propio sin dependencias), con el PR 3 | En local; se puede saltar, por eso se repite en la CI (el formato de los commits, desde el PR 3) |
| CI, en cada PR | gitleaks sobre todo el historial, Semgrep, osv-scanner y el escáner del lenguaje sobre todo el repo | Sí: es la autoridad |
| Mensual (tarea programada de la CI) | osv-scanner | Falla la ejecución y GitHub avisa por correo; no abre issues |
| Continuo (GitHub) | Dependabot abre los PR de actualización | No: cada PR suyo pasa la CI y lo aprueba la persona (dependencias, R2) |
| Una vez | AgentShield sobre la configuración del workflow | No: informe |

Tiempos: los del commit, **medidos** en el PR 2 (lefthook y gitleaks, en WSL); los de la CI siguen siendo **estimaciones sin medir** hasta el PR 3. No se midió antes de aprobar porque lo que no está en este registro no se instala.

### gitleaks

- **Qué hace:** busca secretos (claves, tokens, contraseñas) con expresiones regulares. Antes del commit, en lo preparado (`gitleaks git --pre-commit --staged --redact --no-banner`, en `plantilla-proyecto/lefthook.json`); en la CI, en todo el historial (`gitleaks git --redact --ignore-gitleaks-allow`, con el historial completo).
- **Qué toca y qué lee:** lee el diff preparado o el historial a través de `git`, y `.gitleaks.toml` y `.gitleaksignore` del repo. No escribe nada salvo el informe, si se pide. `--redact` evita que el secreto salga en los registros que lee el agente.
- **Versión:** v8.30.1 (commit `83d9cd684c87d95d656c1458ef04895a7f1cbd8e`). Binario `gitleaks_8.30.1_linux_x64.tar.gz`, SHA-256 `551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb`. MIT. Última publicación del 2026-03-21; el repo sigue con commits (2026-10-28).
- **Tiempo:** medido en el PR 2, 0,28 s por commit con lefthook (mediana de 10 commits de un fichero de 200 líneas, contra 2 ms sin hooks), casi todo el arranque de gitleaks; unos segundos en la CI con un historial como el de la calculadora (estimación).
- **Comprobado en el PR 2** (`tests/test_lefthook_gitleaks.py`, con los binarios del registro): un commit con un token señuelo se bloquea y el token no sale en la salida; sin él, pasa. El test se salta si no encuentra los binarios, como en la CI de este repo.
- **Red:** no.
- **Alternativa:** trufflehog, que por defecto verifica cada secreto contra la API de su proveedor: sale a la red con el secreto (V3, que se apaga con `--no-verification`, y entonces no aporta sobre gitleaks). La acción `gitleaks-action` v2 pide licencia en repos de organización; se usa el binario.
- **Riesgo fuera del sandbox:** ninguno en local (corre en el commit del agente, dentro del sandbox) y en la CI corre en el runner. Lo que hay que vigilar es que el agente lo silencie: un comentario `gitleaks:allow` (la CI lo ignora con `--ignore-gitleaks-allow`), una entrada en `.gitleaks.toml` o `.gitleaksignore`, o las variables `GITLEAKS_CONFIG` y `GITLEAKS_CONFIG_TOML`, que cambian la configuración sin tocar el repo (las bloquea `guarda-saltos.py`). Como la CI lee la configuración de la rama del PR, un cambio en esos ficheros lo marca la CI como sensible (PR 3).
- **Decisión:** adoptar, antes del commit y en la CI.

### osv-scanner

- **Qué hace:** cruza las dependencias de los ficheros de bloqueo (`package-lock.json` y equivalentes) con la base pública OSV de vulnerabilidades conocidas (`osv-scanner scan source -r .`). Falla si hay alguna.
- **Qué toca y qué lee:** lee los ficheros de bloqueo y los manifiestos; no ejecuta el gestor de paquetes ni código del repo. No se usa `fix`, que sí ejecuta el gestor de paquetes: las actualizaciones van por Dependabot.
- **Versión:** v2.7.1 (commit `02f96a40691c2d155fdda799af436e111231e365`). Binario `osv-scanner_linux_amd64`, SHA-256 `fb7dab19a8bd9bbe5c3189f09d4b7ee1820c9553a23bac202648a56efd2f6ee8`. Apache-2.0. La acción oficial (`google/osv-scanner-action` v2.3.1, commit `375a0e8ebdc98e99b02ac4338a724f5750f21213`) es un workflow reutilizable; se prefiere el binario, igual que con gitleaks.
- **Tiempo:** unos segundos en la CI.
- **Red:** sí. Envía a `api.osv.dev` nombres, versiones y hashes de los paquetes, no código. Según su documentación, para resolver dependencias transitivas de ecosistemas sin un lockfile completo (Maven, `requirements.txt`) consulta también `api.deps.dev`; en npm el lockfile basta. Se comprueba en el PR 3. Por eso no corre antes del commit: el sandbox no llega a ese dominio, y ampliar su lista es tocar los ajustes gestionados.
- **Alternativa:** `npm audit` (solo JS) o las alertas de Dependabot (gratis, pero no bloquean un PR). La revisión de licencias (`--licenses`) no se activa: según el criterio de licencia, contaría para las dependencias que se publican con la app, y eso se decide por proyecto.
- **Riesgo fuera del sandbox:** ninguno; solo corre en la CI. Se puede silenciar una vulnerabilidad con `osv-scanner.toml`: un cambio en él lo marca la CI como sensible (PR 3).
- **Decisión:** adoptar, en la CI de cada PR y en la tarea mensual (M38).

### Semgrep

- **Qué hace:** análisis estático de seguridad de varios lenguajes con reglas por patrones (`semgrep scan --config p/default --metrics=off --error --disable-nosem`).
- **Qué toca y qué lee:** lee los ficheros del repo (respeta `.gitignore` y `.semgrepignore`); analiza, no ejecuta código del repo. `--disable-nosem` hace que la CI no respete los comentarios `nosemgrep`, con los que el agente podría silenciar un hallazgo; un cambio en `.semgrepignore` lo marca la CI como sensible (PR 3).
- **Versión:** 1.185.0 (commit `9240f708f8d7e2fbd38b67aa6cd17704b1f81e14`). Motor LGPL-2.1. En la CI, la imagen `semgrep/semgrep:1.185.0` fijada por digest: el digest se toma en el PR 3, porque el sandbox no llega a Docker Hub. Si se instala con pip, la rueda `manylinux_2_34_x86_64` tiene SHA-256 `0eb6aaadad5b957af96d1300487e10af1dc8016e8ef53072effb48cd4906c02b`, pero `--require-hashes` obligaría a fijar también sus dependencias.
- **Tiempo:** de 30 s a 1,5 min en la CI.
- **Red:** sí, descarga las reglas de `semgrep.dev` en cada ejecución. Con `--metrics=off` no envía métricas.
- **Límite:** las reglas de `p/default` no quedan fijadas: cambian sin subir de versión, y una actualización puede añadir, quitar o debilitar reglas sin que se vea en el repo. Se acepta porque Semgrep es una capa más entre varias; si se quiere fijarlas, la alternativa es Opengrep con reglas propias en el repo.
- **Por qué no antes del commit:** sin red a `semgrep.dev` haría falta copiar las reglas al repo, y las del registro llevan la *Semgrep Rules License v1.0*, que limita su uso (aquí la licencia sí cuenta, porque se copian). Además pide instalar Python y Semgrep en cada máquina. El escáner del lenguaje cubre lo local.
- **Alternativa:** Opengrep, la bifurcación LGPL-2.1 del mismo motor, si Semgrep restringe más su versión libre. CodeQL es gratis solo en repos públicos.
- **Riesgo fuera del sandbox:** ninguno; solo corre en la CI.
- **Decisión:** adoptar, solo en la CI.

### Escáner del lenguaje: ESLint con `eslint-plugin-no-unsanitized` (JS/TS)

- **Qué hace:** detecta la inyección de HTML en el DOM (`innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`…), que es el riesgo principal de una PWA. Se activan solo esas reglas y las de `eval` del núcleo (`no-eval`, `no-implied-eval`, `no-new-func`): no es un linter de estilo.
- **Qué toca y qué lee:** lee los ficheros JS/TS (los preparados antes del commit; todos en la CI). **Ejecuta código del repo:** `eslint.config.js` y los plugins de `node_modules/`.
- **Versión:** dependencias de desarrollo fijadas en `package-lock.json`, con su `integrity`: `eslint` 10.14.0 (MIT, `sha512-T0pNsxkb9IKmtQjhpK3d7nWOpFv+YHuMbTJnSVMoQblF0onvXfErrtp4V1jHtsQPan7dKaGVD0q1WCXnzMF31A==`, 30 dependencias directas) y `eslint-plugin-no-unsanitized` 4.1.5 (MPL-2.0, `sha512-MSB4hXPVFQrI8weqzs6gzl7reP2k/qSjtCoL2vUMSDejIIq9YL1ZKvq5/ORBXab/PvfBBrWO2jWviYpL+4Ghfg==`, sin dependencias). Ninguno de los dos tiene scripts de instalación; las dependencias transitivas se comprueban al añadirlos, con la marca `hasInstallScript` del lockfile, y la CI instala con `npm ci --ignore-scripts`.
- **Tiempo:** de 1 a 3 s antes del commit.
- **Red:** no (se instala desde `registry.npmjs.org`, que ya está en la lista del sandbox).
- **Alternativa:** `eslint-plugin-security`, pensado para Node (`fs`, `child_process`, expresiones regulares), no para el navegador. Solo Semgrep, que no corre antes del commit. En otros lenguajes, el equivalente (bandit en Python, gosec en Go) se decide con el proyecto que lo use.
- **Riesgo fuera del sandbox:** `eslint.config.js` es código que el agente puede cambiar. Si la persona lanza una orden de Git con hooks en la copia del agente, lo ejecuta fuera del sandbox: por eso no usa Git en esa copia (ADR-0008). Las 30 dependencias de `eslint` son cadena de suministro: fijadas en el lockfile y vigiladas por osv-scanner y Dependabot. Un cambio en `eslint.config.js` lo marca la CI como sensible (PR 3). En la CI, ese código corre con el `GITHUB_TOKEN` a mano: el job lleva `permissions: contents: read` y `actions/checkout` con `persist-credentials: false`. Aun así, en la CI se juntan el código del repo (privado), 30 dependencias de terceros y la red: la trifecta no se rompe ahí. Se acepta como coste porque las dependencias están fijadas por `integrity`, se instalan sin scripts y las vigilan osv-scanner y Dependabot; romperla del todo exigiría un job sin red.
- **Decisión:** adoptar en los proyectos JS/TS, antes del commit y en la CI. Añadirlo a la calculadora es R2 (dependencia nueva) y va en otra issue.

### lefthook

- **Qué hace:** gestor de hooks de Git. Lee su configuración y ejecuta sus órdenes en paralelo, solo sobre lo preparado.
- **Qué toca y qué lee:**
  - **Configuración:** la principal (`lefthook`, `.lefthook` o `.config/lefthook`) y la local (`lefthook-local`, `.lefthook-local` o `.config/lefthook-local`), cada una en `.yml`, `.yaml`, `.json`, `.jsonc` o `.toml`. La local se fusiona con la principal y puede redefinir órdenes. También lee las carpetas de scripts `.lefthook/` y `.lefthook-local/`.
  - **Variables de entorno:** `LEFTHOOK`, `LEFTHOOK_EXCLUDE`, `LEFTHOOK_CONFIG`, `LEFTHOOK_BIN`, `LEFTHOOK_OUTPUT` y `LEFTHOOK_VERBOSE`.
  - **Escritura:** `lefthook install` escribe `.git/hooks/`. Al ejecutarse, si la configuración cambió, los reinstala (`syncHooks`): dentro del sandbox falla con un aviso, sin efecto; fuera, funciona, y puede instalar hooks nuevos (por ejemplo `post-checkout`) que corren en órdenes posteriores. Esa reinstalación no escribe hooks de agentes (`ai` solo se procesa en `lefthook install`), pero sí descarga `remotes`. Con `no_auto_install: true` en la configuración principal no se reinstala (`internal/command/run.go`); la plantilla lo lleva desde el PR 2, aunque el agente puede quitarlo en la rama, como todo lo de la configuración principal.
  - **Orden de carga:** prueba primero cada extensión y, dentro de ella, cada nombre (`.yml` de los tres nombres, después `.yaml`…), y se queda con la primera que existe (`loadFirst`). Un `lefthook.yml` gana a `lefthook.json`.
  - **Opciones que no se usan:**
    - `stage_fixed`: hace `git add --force`, que se salta `.gitignore`, además de `git stash` y `git checkout --force`;
    - `ai`: `lefthook install` escribe hooks de Claude Code en `.claude/settings.json`, también si la clave está en la configuración local;
    - `remotes`: clona otros repos, también en cada ejecución;
    - `extends`, `rc` y `templates`: traen configuración, entorno o texto sin escapar de fuera de la configuración principal;
    - `lefthook`: la ruta del binario.
  - **Si no encuentra su binario** (ni `LEFTHOOK_BIN`, ni en el `PATH`, ni en la ruta absoluta guardada al instalar), el hook prueba binarios del árbol de trabajo (`node_modules/lefthook*/`) y gestores (`yarn`, `pnpm`, `uv run`, `bundle exec`, `mise`, `devbox`), que pueden ejecutar código del repo y salir a la red. `assert_lefthook_installed: true` solo actúa al final de esa cadena. Por eso el binario no se mueve después de instalar.
- **Código leído** (criterio de hooks de terceros), en la etiqueta v2.2.2:
  - la plantilla del hook que instala (`internal/templates/hook.tmpl`);
  - la ejecución y la reinstalación automática (`internal/command/run.go` y `syncHooks` en `install.go`);
  - la carga de configuración, sus nombres, su orden y sus variables (`internal/config/loader.go`), y las claves de la configuración, de los hooks y de los trabajos (`internal/config/config.go`, `hook.go` y `job.go`; PR 2);
  - la instalación con `ai` y `remotes` (`internal/command/install.go` e `install_ai.go`);
  - la sustitución de `{staged_files}` en la orden, que escapa los nombres de fichero con `shellescape.Quote` y no escapa las plantillas propias (`internal/run/controller/command/replacer/replacer.go`);
  - las órdenes de Git que lanza (`internal/git/wrapper/`);
  - la única salida a la red (`internal/updater/`, solo en `lefthook self-update`).

  No se ha leído el reparto en paralelo de las órdenes ni el registro de salida.
- **Versión:** v2.2.2. La etiqueta anotada es el objeto `85141db4e1fda882e2e7eadb7706f3ae44b177d3` y apunta al commit `eb4e504b7c1d1ea6cb1fd29542431cb6d1a93a03`; el código leído es el de esa etiqueta. Binario `lefthook_2.2.2_Linux_x86_64`, SHA-256 `4fbf89eb7748c6aed84d833ee1a29edac48fae614468ca9a82896ec32f2800b6`, instalado por la persona en una ruta fija de su `PATH` que el agente no puede escribir (nunca `node_modules/.bin` ni una carpeta del proyecto). MIT. No se usa el paquete de npm: su `postinstall` ejecuta `lefthook install`.
- **Tiempo:** milisegundos propios; el resto es lo que lanza (con gitleaks, 0,28 s por commit en total, medido en el PR 2).
- **Red:** no, salvo `self-update` y `remotes` (en `install` y en cada ejecución), que no se usan, y la cadena de búsqueda del binario si este falta.
- **Alternativa:**
  - sin hooks, solo la CI;
  - un script propio fuera del repo;
  - husky: solo JS, y con el mismo riesgo, porque los hooks son ficheros de `.husky/`;
  - pre-commit: en Python, y descarga hooks de repos de terceros.

  El ADR-0008 compara las dos primeras con lefthook; husky y pre-commit se descartan por lo dicho.
- **Riesgo fuera del sandbox:** lo que se ejecuta en una orden de Git lo deciden ficheros que el agente puede escribir. Condiciones del ADR-0008, en concreto:
  - **La persona no lanza órdenes de Git en la copia del agente** ni abre ahí un editor con Git; tampoco `gh pr checkout` ni `git worktree add`. Sus cambios, desde la web o desde una copia propia. Si alguna vez tiene que hacerlo, con `LEFTHOOK=0`: el hook sale antes de llamar a lefthook, así que no reinstala ni descarga nada. Pero eso no corta otras vías del resto de `.git`, como la configuración de un submódulo (ADR-0008, §6). `LEFTHOOK=0` va en un alias propio de la persona, nunca en el perfil de shell que hereda el agente, porque apagaría también sus hooks.
  - **La configuración principal** es `lefthook.json`, en JSON para que la CI la lea sin dependencias y sin anclas ni claves de fusión de YAML que escondan claves. La CI (`checks.py`, check `lefthook`, desde el PR 2) la compara con una lista blanca, que deja fuera `ai`, `remotes`, `extends`, `rc`, `templates`, `lefthook` y `stage_fixed` y también lo que ejecuta órdenes o ficheros aparte de `run`:
    - arriba, solo `min_version`, `assert_lefthook_installed` y `no_auto_install` (los dos, obligatorios y a `true`), `no_tty`, `pre-commit` y `commit-msg`;
    - en cada hook, solo `parallel`, `piped` y `jobs`: nada de `skip`, `only`, `files` ni `setup`, que lanzan órdenes, ni `commands` o `scripts`;
    - en cada trabajo, solo `name`, `run`, `glob`, `exclude`, `file_types` y `fail_text`: nada de `script`, `runner`, `env`, `root`, `group` ni `stage_fixed`.

    Además rechaza las claves repetidas, que `lefthook.json` sea un enlace o un ejecutable, cualquier otra configuración principal o local versionada (cualquier nombre y extensión, y `.lefthook/` o `.lefthook-local/`), y que el PR quite `lefthook.json` si `main` lo tiene. La persona lo mira en la configuración de `main` antes de instalar.
  - **Instalación,** siempre en un clon nuevo de `main`. En la copia del agente no vale revisarla con `git status`: el agente puede escribir el índice y ocultar cambios con `git update-index --skip-worktree` o `--assume-unchanged`. La persona, fuera del sandbox:
    1. clona `main` en una carpeta nueva;
    2. ejecuta `lefthook install` en ella;
    3. comprueba con `git status --ignored .claude/` que `.claude/` no ha cambiado, incluidos los ficheros ignorados;
    4. desde esa carpeta trabaja el agente.

    Los pasos, con los binarios y sus sumas, están en la guía de instalación (B7).
  - **Solo lectura de `.git/hooks` y `.git/config`** (ADR-0008, §4): lo comprueba `tests/test_sandbox_git.py`, que escribe de verdad sin cambiar nada y solo corre dentro del sandbox (`SANDBOX_RUNTIME`). Mide lo que limita el sandbox, que son Bash y sus procesos; Write y Edit no pasan por él, y para ellos la segunda capa es `guarda-saltos.py`. En el PR 2, con el sandbox de ese día: `.git/hooks` y `.git/config` en solo lectura; `.git/`, `info/`, `info/exclude`, `HEAD`, el índice, `refs/heads` y `objects`, escribibles; `modules/`, `worktrees/` y `commondir` no existían, pero se pueden crear.
  - **Riesgo de la §6 del ADR-0008, confirmado en el PR 2:** Git lee `$GIT_DIR/commondir` en cualquier directorio de Git, no solo en los worktrees, y de ahí toma `config` y `hooks`. Comprobado en un repo de usar y tirar: con un `commondir` que apunta a otro `.git`, `core.hooksPath` y `rev-parse --git-path hooks` salen del otro. Como `.git/` se puede escribir desde el sandbox, el agente podría desviar la configuración y los hooks de su copia, también para una orden de Git que se lance fuera del sandbox. `guarda-saltos.py` lo bloquea como segunda capa; el control de verdad es denegar la escritura de `.git/commondir` (y de `.git` entero salvo lo que Git necesita) en los ajustes gestionados, que decide la persona. Va en la issue de la §6.
- **Formas de saltarlo** conocidas, que el hook del plugin `guarda-saltos.py` bloquea en las órdenes del agente como segunda capa (desde el PR 2, con un test por forma en `tests/test_guarda_saltos.py`). La autoridad es la CI.
  - **Opciones de Git:** `--no-verify` y sus prefijos abreviados (`--no-verif`…) en `commit` y `merge` (en `merge` salta `pre-merge-commit` y `commit-msg`); en `commit`, `-n`, también combinado con otras letras (`-nm`, `-an`). En `merge`, `-n` es `--no-stat` y no se bloquea.
  - **Variables de entorno:** `LEFTHOOK` (`0` o `false`), `LEFTHOOK_EXCLUDE` (que excluye por etiqueta y también por nombre: `LEFTHOOK_EXCLUDE=gitleaks` lo salta), `LEFTHOOK_CONFIG`, `LEFTHOOK_BIN`, `GITLEAKS_CONFIG` y `GITLEAKS_CONFIG_TOML` en cualquier orden, y `PATH` cambiado en una orden con git; en la propia orden, con `env`, con `export` o `declare`, o sueltas antes. El estado del shell no pasa de una llamada de Bash a la siguiente, así que basta con mirar la misma llamada.
  - **Configuración de Git:** `core.hooksPath`, un `include` que lo traiga o un alias que esconda el subcomando (`git -c alias.c='commit --no-verify' c`), con `git -c` o `--config-env`; escribir en `.git/hooks/` o `.git/config` (también de un submódulo o un worktree) con Bash, Write o Edit, aunque hoy el sandbox ya lo impide en Bash; escribir `.git/commondir` o un fichero `.git`, o mover `.git` (desvían de dónde lee Git la configuración y los hooks, ver abajo); escribir `~/.gitconfig` o `~/.config/git/config` con Write o Edit; y escribir los ajustes de Claude Code (`.claude/settings.json` y `settings.local.json`), que podrían fijar `LEFTHOOK=0` en todas las sesiones; `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_*`/`GIT_CONFIG_VALUE_*` o `GIT_CONFIG_PARAMETERS`; o, en una orden con git, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `HOME`, `XDG_CONFIG_HOME`, `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_COMMON_DIR` o `GIT_OBJECT_DIRECTORY` (otro árbol de trabajo deja a lefthook sin configuración). `git config` que escribe ya lo bloquea `guarda-git.py` (M16).
  - **Ficheros:** escribir configuración de lefthook fuera de `lefthook.json`: la local (los nombres de arriba, en cualquier extensión, y `.lefthook-local/`) y la principal con otro nombre (`lefthook.yml` gana a `lefthook.json`) o `.lefthook/`, sin distinguir mayúsculas, con Bash o con Write, Edit o NotebookEdit; ocultar cambios con `git update-index --skip-worktree` o `--assume-unchanged`.
  - **Commits que no pasan por `pre-commit`:** `git am` (lanza `applypatch-msg` y `pre-applypatch`, no `pre-commit`); `git commit-tree` con `update-ref`; `git fast-import`; hacer el commit en otra copia (`git clone` de una ruta local, `--git-dir`, `--work-tree`, `GIT_DIR` o `GIT_INDEX_FILE`); o crearlo con `gh api` (`/git/commits`, escribir en `/contents/` o `createCommitOnBranch`).
  - **Ocultar ficheros nuevos:** `.git/info/exclude`, con Bash o con Write o Edit.

  La lista no es exhaustiva: es lo conocido a esta versión, y solo la CI garantiza. `GITLEAKS_CONFIG`, `GITLEAKS_CONFIG_TOML`, el `include`, `--work-tree`, `GIT_INDEX_FILE` y lo de Write y Edit salen de leer gitleaks y lefthook en el PR 2; `git am`, el alias, `.git/hooks` y `.git/config` con Write y Edit y la principal con otro nombre, de su G4. Lo esquivan, como en las demás guardas, `bash -c`, `eval`, variables, scripts, envolturas que el lector no conoce (`setsid`, `stdbuf`, `xargs`), `env --split-string`, `printf -v`, ficheros creados de forma indirecta (`tar x`, `git apply`), un commit en una copia que ya existía (`git -C ../otra commit`) o en un repo nuevo (`git init sub`).

  Tampoco pasan por `pre-commit`, y no se bloquean a propósito, `git merge` (en avance rápido no lanza ningún hook; con `git stash` y `git merge stash@{0}` lleva a la rama lo preparado), `cherry-pick`, `revert` y `rebase`. Hasta el PR 3, que pone gitleaks en la CI, un secreto que entre así solo lo detendría la revisión. Un trabajo de gitleaks en `pre-push` cerraría toda esta familia antes de que el commit salga del equipo; queda como decisión para la persona. Cambiar `lefthook.json`, `.gitleaks.toml` o `.gitleaksignore` en el árbol de trabajo **pregunta** a la persona: lefthook y gitleaks los leen de ahí antes de cada commit aunque el cambio no se prepare, y sin configuración lefthook sale con éxito (`run.go`, `ConfigNotFoundError`). Así, borrarlos o vaciarlos apagaría gitleaks sin que lo vieran la CI ni la revisión.

  La issue pedía `LEFTHOOK=0`, `LEFTHOOK_EXCLUDE`, `LEFTHOOK_CONFIG` y `--no-verify`; las demás salen de leer el código y de G4. No se bloquea `eslint.config.js`: lo cubren la CI y el aviso de cambio sensible (PR 3).
- **Decisión:** adoptar con las condiciones del ADR-0008.

### Bot de dependencias: Dependabot

- **Qué hace:** abre PR de actualización (npm, acciones de GitHub y Docker) y avisa de vulnerabilidades. Configuración en `.github/dependabot.yml`: una vez al mes, agrupado, y con `cooldown` (unos días de espera tras cada publicación, contra paquetes comprometidos recién publicados). En las acciones, propone el SHA nuevo con su versión en un comentario.
- **Qué toca y qué lee:** lo ejecuta GitHub en su infraestructura. Lee manifiestos y lockfiles y escribe ramas y PR en el repo. Sus PR pasan la CI sin los secretos del repo.
- **Versión:** es un servicio de GitHub; no se fija. Lo que se fija son las versiones que propone, en cada PR.
- **Tiempo:** nada en el commit. Cada PR suyo, una ejecución de la CI y la aprobación de la persona.
- **Red:** la de GitHub; nada sale del PC.
- **Alternativa:** Renovate. Es más potente (actualiza digests de imágenes en los `container:` de los workflows, `minimumReleaseAge`), pero la app alojada es de un tercero (Mend) con permiso de escritura en contenidos, PR y workflows, y la autoalojada necesita un token y un workflow propio.
- **Riesgo fuera del sandbox:** ninguno en el PC. Dependabot es de GitHub, en quien ya confiamos para todo lo demás.
- **Decisión:** Dependabot. Hay que comprobar en el PR 3:
  - si actualiza la imagen de Playwright fijada en un `container:` de un workflow (M6). Si no, se vuelve a valorar Renovate;
  - sus ramas (`dependabot/…`) y títulos no siguen `docs/convenciones.md`, así que `checks.py` (M11) los rechazaría. Hace falta una excepción acotada a que el autor del PR y todos sus commits sean `dependabot[bot]`, nunca al prefijo de la rama, que el agente también puede usar.

### AgentShield (piloto, una vez)

- **Qué hace:** audita la configuración de un agente: secretos, permisos, hooks, MCP y agentes. Se pasa una vez sobre `entorno/`, `plugin-sdd/` y `plantilla-proyecto/.claude/`.
- **Qué toca y qué lee:** lee la carpeta que se le indica con `--path`. No se usan `--fix`, que reescribe la configuración (V2), `--opus`, que envía la configuración a la API de Anthropic con una clave, ni `--supply-chain-online`, que consulta npm.
- **Versión:** paquete npm `ecc-agentshield` 1.6.0 (MIT, `sha512-lpeHG96DtEn7ofq7Iiyvq29piQOwParaiZOdDB206i4ZeCL4yjwT6xN5BSGI4yhCEAN0eO0f9F9hxHLBuRqf/g==`), sin scripts de instalación y con 7 dependencias, entre ellas `@anthropic-ai/sdk`. Con `npx` las dependencias no quedan fijadas; se instala con un lockfile dentro del contenedor y `--ignore-scripts`.
- **Tiempo:** una ejecución de segundos; no entra en el commit ni en la CI.
- **Red:** solo para instalarlo. El análisis, en un contenedor sin red. Si el PR 4 elige un runner de GitHub, la red no se corta y la trifecta queda completa: el checkout del repo privado, un paquete de terceros con 7 dependencias y la red. Que no haya clave de Anthropic ni `--opus`, y que el job lleve `permissions: {}` y `persist-credentials: false`, evita filtrar credenciales, pero no el contenido del repo. Por eso el runner solo vale con la red cortada tras instalar, o aceptando ese riesgo por escrito en el PR 4.
- **Alternativa:** la revisión del `reviewer` de seguridad que ya hace `sdd-review`, que es opinión; AgentShield aporta reglas fijas.
- **Riesgo fuera del sandbox:** ninguno si corre en el contenedor. Hoy no hay Docker ni Podman en WSL: el PR 4 decide entre instalar uno (lo haría la persona) o pasarlo en un runner de GitHub sin secretos.
- **Decisión:** piloto, una vez, con informe y lo decidido.

## Evaluadas y no aprobadas

| Herramienta | Fecha | Motivo |
| --- | --- | --- |
| Plugin ponytail (DietrichGebert/ponytail) v5.3.2 | 2026-10-19 | Instala hooks y una statusline que corren fuera del sandbox, y se solapa con `sdd-implement` y `sdd-review`. Su idea útil (la escalera del cambio mínimo completo) se incorporó a `sdd-implement`. Se puede reevaluar en v1.x con las métricas del primer recorrido. |
| Renovate (app alojada de Mend) | 2026-11-12 | Bot de dependencias de un tercero con escritura en contenidos, PR y workflows; Dependabot cubre lo observado sin instalar nada (VIC-18). Se reevalúa si Dependabot no actualiza la imagen de Playwright de un workflow. |
| trufflehog | 2026-11-12 | Por defecto verifica cada secreto contra la API de su proveedor: lo envía a la red. Sin verificar, no aporta sobre gitleaks (VIC-18). |

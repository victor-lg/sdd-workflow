# Herramientas aprobadas

Registro de plugins, servidores MCP y herramientas externas que el agente puede usar (línea base §9, D30), y de las que ejecutan la plantilla de proyecto y sus hooks de Git (ADR-0008). Lo que no está aquí no se instala. Añadir, quitar, subir de versión o ampliar los permisos de una entrada es un cambio R2 en este repo.

Los hooks y los servidores MCP corren fuera del sandbox, así que cada entrada dice qué puede tocar.

## Criterios (ADR-0008)

- **Licencia:** solo cuenta si copiamos su código o su texto a nuestros repos.
- **Riesgo configurable:** un riesgo que se apaga o se acota con configuración es un coste, no un veto. Solo vetan una trifecta letal que no se puede romper, que la herramienta reescriba nuestras instrucciones o configuración sin revisión, o que vea credenciales en tránsito sin necesitarlas.
- **Hooks de terceros** (de Claude Code o de Git): solo si se ha leído su código en la versión fijada, al menos lo que decide qué se ejecuta, qué escribe y qué sale por red. Al subir de versión se relee lo que cambió en esas partes.
- **Qué se anota de cada una:** qué hace, qué toca y qué lee, versión y digest, el tiempo que añade, si necesita red, la alternativa y el riesgo de ejecutar código ajeno fuera del sandbox.

| Herramienta | Versión | Para qué | Permisos y alcance | Aprobada |
| --- | --- | --- | --- | --- |
| Plugin `sdd` (este repo, marketplace `sdd-workflow`) | 1.3.1 | Skills `sdd-*`, subagente `reviewer` y hooks | Sin MCP ni LSP. El `reviewer` solo tiene Read, Grep y Glob. Cinco hooks en Python, fuera del sandbox. `guarda-git.py` lee la orden de Bash y consulta con `git` (`rev-parse`, `symbolic-ref`, `diff --cached`, `ls-files`, `ls-tree`, `check-ignore`) y la fecha de `FETCH_HEAD`, sin usar la red, la carpeta que indique la orden (`cd` o `-C`), que puede estar fuera del proyecto y prepararla el agente. Por eso lanza git con `core.fsmonitor=false`, `core.untrackedCache=false` y `--no-optional-locks`, sin diff externo ni `textconv` y sin comparar contenidos con el árbol de trabajo (`ls-files --others` solo lo recorre para listar nombres): no ejecuta nada de la configuración de ese repo ni escribe su índice. `guarda-ficheros.py` y `guarda-linear.py` solo leen la entrada del hook: no ejecutan nada ni tocan ficheros. `guarda-gh.py` es el único con red: ante `gh pr ready` ejecuta `gh pr view` contra el host del remoto del repo de la carpeta de la orden (que el agente puede elegir, pero solo entre los hosts en los que `gh` tiene sesión; hoy, github.com) o contra github.com si la orden lleva `-R`, con las credenciales de `gh` de quien ejecuta Claude Code (hoy, las del agente), y `git` igual que `guarda-git.py`, sin escribir nada. Solo pasa a `gh` un número, una URL de `github.com` o un nombre de rama, y un repo `OWNER/REPO`; con otra forma, con `GH_HOST`, `GH_REPO`, `GH_CONFIG_DIR`, `GIT_DIR` o `GIT_CONFIG*` en cualquier parte de la orden, con `env -C` o `sudo -D`, o tras un `cd` de destino incierto, bloquea sin llamar. A las llamadas a git que hace el propio `gh` les pasa `core.fsmonitor=false`, `core.untrackedCache=false` y `GIT_OPTIONAL_LOCKS=0` por el entorno; qué subórdenes de git lanza `gh` depende de su versión. La red de los hooks no pasa por la lista del sandbox. `sesion-unica.py` usa `git` y `ps` y escribe solo en `sdd-sesiones/`, dentro del directorio de Git de la copia. El coste fijo por sesión de las skills era ~760 tokens en la v0.11 (`claude plugin details`) y es ~453 en la 1.3.1. | 2026-10-19 (v0.11); hooks de Git: 2026-11-08 (PR #18); resto de hooks: pendiente de la aprobación del PR de VIC-17 |
| MCP oficial de Linear, endpoint de solo lectura `https://mcp.linear.app/mcp/readonly` | servicio remoto | Que el agente lea issues, estados y dependencias (`sdd-plan`, `sdd-context`) | El endpoint solo expone herramientas de lectura; además, la autorización OAuth se concede con alcance de lectura. Corre fuera del sandbox, pero no ejecuta nada en el PC. | 2026-10-19 (v0.11) |

| Claude con control del navegador (Claude in Chrome y el navegador integrado de la app de escritorio) | servicio de Claude | Ayudar a la persona: leer, configurar (guía), crear issues en *Backlog*, comentar | Actúa con la sesión de la persona, sin sandbox. Nunca mueve a *Ready*, aprueba, fusiona, publica ni toca rulesets, ajustes o tokens (línea base §8, ADR-0006). Límite aceptado: es una regla, no un control. | 2026-10-23 (v0.22) |

## Herramientas de la plantilla de proyecto (bloque 3, VIC-18)

Decididas el 2026-11-12 con coste-beneficio; **aprobación pendiente** de la del PR de este registro. Se instalan en los PR siguientes de VIC-18: lefthook y el hook del plugin (PR 2), la CI y el bot de dependencias (PR 3) y el piloto de AgentShield (PR 4). Las versiones son las últimas publicadas a esa fecha; las sumas SHA-256 salen de los ficheros de sumas de cada publicación.

Dónde corre cada una:

| Momento | Qué | ¿Decide? |
| --- | --- | --- |
| Antes del commit (lefthook, dentro del sandbox) | gitleaks sobre lo preparado, el escáner del lenguaje sobre los ficheros preparados y el formato del mensaje (`commit-msg`, script propio sin dependencias) | En local; se puede saltar, por eso se repite en la CI |
| CI, en cada PR | gitleaks sobre todo el historial, Semgrep, osv-scanner y el escáner del lenguaje sobre todo el repo | Sí: es la autoridad |
| Mensual (tarea programada de la CI) | osv-scanner | Falla la ejecución y GitHub avisa por correo; no abre issues |
| Continuo (GitHub) | Dependabot abre los PR de actualización | No: cada PR suyo pasa la CI y lo aprueba la persona (dependencias, R2) |
| Una vez | AgentShield sobre la configuración del workflow | No: informe |

Tiempos: **estimaciones sin medir.** No se mide antes de aprobar porque lo que no está en este registro no se instala. La medida real, en el commit y en la CI, entra con los PR 2 y 3 y sustituye a la estimación.

### gitleaks

- **Qué hace:** busca secretos (claves, tokens, contraseñas) con expresiones regulares. Antes del commit, en lo preparado (`gitleaks git --pre-commit --staged --redact`); en la CI, en todo el historial (`gitleaks git --redact --ignore-gitleaks-allow`, con el historial completo).
- **Qué toca y qué lee:** lee el diff preparado o el historial a través de `git`, y `.gitleaks.toml` y `.gitleaksignore` del repo. No escribe nada salvo el informe, si se pide. `--redact` evita que el secreto salga en los registros que lee el agente.
- **Versión:** v8.30.1 (commit `83d9cd684c87d95d656c1458ef04895a7f1cbd8e`). Binario `gitleaks_8.30.1_linux_x64.tar.gz`, SHA-256 `551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb`. MIT. Última publicación del 2026-03-21; el repo sigue con commits (2026-10-28).
- **Tiempo:** menos de 1 s antes del commit; unos segundos en la CI con un historial como el de la calculadora.
- **Red:** no.
- **Alternativa:** trufflehog, que por defecto verifica cada secreto contra la API de su proveedor: sale a la red con el secreto (tercer veto, que se apaga con `--no-verification`, y entonces no aporta sobre gitleaks). La acción `gitleaks-action` v2 pide licencia en repos de organización; se usa el binario.
- **Riesgo fuera del sandbox:** ninguno en local (corre en el commit del agente, dentro del sandbox) y en la CI corre en el runner. Lo que hay que vigilar es que el agente lo silencie: un comentario `gitleaks:allow` (la CI lo ignora con `--ignore-gitleaks-allow`) o una entrada en `.gitleaks.toml` o `.gitleaksignore`, que van en CODEOWNERS.
- **Decisión:** adoptar, antes del commit y en la CI.

### osv-scanner

- **Qué hace:** cruza las dependencias de los ficheros de bloqueo (`package-lock.json` y equivalentes) con la base pública OSV de vulnerabilidades conocidas (`osv-scanner scan source -r .`). Falla si hay alguna.
- **Qué toca y qué lee:** lee los ficheros de bloqueo y los manifiestos; no ejecuta el gestor de paquetes ni código del repo. No se usa `fix`, que sí ejecuta el gestor de paquetes: las actualizaciones van por Dependabot.
- **Versión:** v2.7.1 (commit `02f96a40691c2d155fdda799af436e111231e365`). Binario `osv-scanner_linux_amd64`, SHA-256 `fb7dab19a8bd9bbe5c3189f09d4b7ee1820c9553a23bac202648a56efd2f6ee8`. Apache-2.0. La acción oficial (`google/osv-scanner-action` v2.3.1, commit `375a0e8ebdc98e99b02ac4338a724f5750f21213`) es un workflow reutilizable; se prefiere el binario, igual que con gitleaks.
- **Tiempo:** unos segundos en la CI.
- **Red:** sí. Envía a `api.osv.dev` nombres, versiones y hashes de los paquetes, no código. Por eso no corre antes del commit: el sandbox no llega a ese dominio, y ampliar su lista es tocar los ajustes gestionados.
- **Alternativa:** `npm audit` (solo JS) o las alertas de Dependabot (gratis, pero no bloquean un PR). La revisión de licencias (`--licenses`) no se activa: según el criterio de licencia, contaría para las dependencias que se publican con la app, y eso se decide por proyecto.
- **Riesgo fuera del sandbox:** ninguno; solo corre en la CI.
- **Decisión:** adoptar, en la CI de cada PR y en la tarea mensual (M38).

### Semgrep

- **Qué hace:** análisis estático de seguridad de varios lenguajes con reglas por patrones (`semgrep scan --config p/default --metrics=off --error --disable-nosem`).
- **Qué toca y qué lee:** lee los ficheros del repo (respeta `.gitignore` y `.semgrepignore`); analiza, no ejecuta código del repo. `--disable-nosem` hace que la CI no respete los comentarios `nosemgrep`, con los que el agente podría silenciar un hallazgo; `.semgrepignore`, si existe, va en CODEOWNERS.
- **Versión:** 1.185.0 (commit `9240f708f8d7e2fbd38b67aa6cd17704b1f81e14`). Motor LGPL-2.1. En la CI, la imagen `semgrep/semgrep:1.185.0` fijada por digest: el digest se toma en el PR 3, porque el sandbox no llega a Docker Hub. Si se instala con pip, la rueda `manylinux_2_34_x86_64` tiene SHA-256 `0eb6aaadad5b957af96d1300487e10af1dc8016e8ef53072effb48cd4906c02b`, pero `--require-hashes` obligaría a fijar también sus dependencias.
- **Tiempo:** de 30 s a 1,5 min en la CI.
- **Red:** sí, descarga las reglas de `semgrep.dev` en cada ejecución. Con `--metrics=off` no envía métricas.
- **Por qué no antes del commit:** sin red a `semgrep.dev` haría falta copiar las reglas al repo, y las del registro llevan la *Semgrep Rules License v1.0*, que limita su uso (aquí la licencia sí cuenta, porque se copian). Además pide instalar Python y Semgrep en cada máquina. El escáner del lenguaje cubre lo local.
- **Alternativa:** Opengrep, la bifurcación LGPL-2.1 del mismo motor, si Semgrep restringe más su versión libre. CodeQL es gratis solo en repos públicos.
- **Riesgo fuera del sandbox:** ninguno; solo corre en la CI.
- **Decisión:** adoptar, solo en la CI.

### Escáner del lenguaje: ESLint con `eslint-plugin-no-unsanitized` (JS/TS)

- **Qué hace:** detecta la inyección de HTML en el DOM (`innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`…), que es el riesgo principal de una PWA. Se activan solo esas reglas y las de `eval` del núcleo (`no-eval`, `no-implied-eval`, `no-new-func`): no es un linter de estilo.
- **Qué toca y qué lee:** lee los ficheros JS/TS (los preparados antes del commit; todos en la CI). **Ejecuta código del repo:** `eslint.config.js` y los plugins de `node_modules/`.
- **Versión:** dependencias de desarrollo fijadas en `package-lock.json`, con su `integrity`: `eslint` 10.14.0 (MIT, `sha512-T0pNsxkb9IKmtQjhpK3d7nWOpFv+YHuMbTJnSVMoQblF0onvXfErrtp4V1jHtsQPan7dKaGVD0q1WCXnzMF31A==`, 30 dependencias directas) y `eslint-plugin-no-unsanitized` 4.1.5 (MPL-2.0, `sha512-MSB4hXPVFQrI8weqzs6gzl7reP2k/qSjtCoL2vUMSDejIIq9YL1ZKvq5/ORBXab/PvfBBrWO2jWviYpL+4Ghfg==`, sin dependencias). Ninguno de los dos tiene scripts de instalación.
- **Tiempo:** de 1 a 3 s antes del commit.
- **Red:** no (se instala desde `registry.npmjs.org`, que ya está en la lista del sandbox).
- **Alternativa:** `eslint-plugin-security`, pensado para Node (`fs`, `child_process`, expresiones regulares), no para el navegador. Solo Semgrep, que no corre antes del commit. En otros lenguajes, el equivalente (bandit en Python, gosec en Go) se decide con el proyecto que lo use.
- **Riesgo fuera del sandbox:** `eslint.config.js` es código que el agente puede cambiar. Si la persona hace un commit con hooks en la copia del agente, lo ejecuta fuera del sandbox: por eso esos commits van con `LEFTHOOK=0` o desde la web (ADR-0008). Las 30 dependencias de `eslint` son cadena de suministro: fijadas en el lockfile y vigiladas por osv-scanner y Dependabot.
- **Decisión:** adoptar en los proyectos JS/TS, antes del commit y en la CI. Añadirlo a la calculadora es R2 (dependencia nueva) y va en otra issue.

### lefthook

- **Qué hace:** gestor de hooks de Git. Lee `lefthook.yml` y ejecuta sus órdenes en paralelo, solo sobre lo preparado.
- **Qué toca y qué lee:** lee `lefthook.yml`, `lefthook-local.yml`, `.lefthook/`, `.lefthook-local/`, `.config/lefthook*.yml` y las variables `LEFTHOOK`, `LEFTHOOK_EXCLUDE`, `LEFTHOOK_CONFIG`, `LEFTHOOK_BIN` y `LEFTHOOK_OUTPUT`. `lefthook install` escribe `.git/hooks/`; al ejecutarse, si la configuración cambió, intenta reescribirlos (dentro del sandbox falla con un aviso, sin efecto). Con `stage_fixed` hace `git add --force` (se salta `.gitignore`), `git stash` y `git checkout --force`: no se usa. Con `ai:`, `lefthook install` escribe hooks de Claude Code en `.claude/settings.json`, y con `remotes:` clona otros repos: no se usan.
- **Código leído** (criterio de hooks de terceros), en v2.2.2: la plantilla del hook que instala (`internal/templates/hook.tmpl`), la ejecución (`internal/command/run.go`), la carga de configuración y sus variables (`internal/config/loader.go`), la instalación con `ai` y `remotes` (`internal/command/install.go` e `install_ai.go`), las órdenes de Git que lanza (`internal/git/wrapper/`) y la única salida a la red (`internal/updater/`, solo en `lefthook self-update`). No se ha leído el ejecutor de órdenes en paralelo ni el registro.
- **Versión:** v2.2.2 (commit `eb4e504b7c1d1ea6cb1fd29542431cb6d1a93a03`). Binario `lefthook_2.2.2_Linux_x86_64`, SHA-256 `4fbf89eb7748c6aed84d833ee1a29edac48fae614468ca9a82896ec32f2800b6`, en el `PATH` de la persona. MIT. No el paquete de npm: su `postinstall` ejecuta `lefthook install`.
- **Tiempo:** milisegundos propios; el resto es lo que lanza.
- **Red:** no (salvo `self-update` y `remotes`, que no se usan).
- **Alternativa:** sin hooks, solo la CI; un script propio fuera del repo; husky (solo JS, mismo riesgo: los hooks son ficheros de `.husky/`); pre-commit (Python, descarga hooks de repos de terceros). Comparación en el ADR-0008.
- **Riesgo fuera del sandbox:** lo que ejecuta en un commit lo deciden ficheros que el agente puede escribir. Condiciones del ADR-0008: commits de la persona en la copia del agente con `LEFTHOOK=0` o desde la web; `lefthook.yml` sin `ai`, `remotes`, `extends`, `rc`, `lefthook` ni `stage_fixed`, con `assert_lefthook_installed: true` y en CODEOWNERS junto con `.lefthook/`; `lefthook install` sobre `main` recién descargado.
- **Formas de saltarlo** que el hook del plugin debe bloquear en las órdenes del agente (PR 2): `git commit --no-verify` y `-n`; `LEFTHOOK=0` o `false`; `LEFTHOOK_EXCLUDE`; `LEFTHOOK_CONFIG`; `LEFTHOOK_BIN`; `core.hooksPath` con `git -c`, `--config-env` o `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_*`/`GIT_CONFIG_VALUE_*`; y escribir `lefthook-local.yml`, `.lefthook-local/` o `.config/lefthook-local.yml`. La issue pedía las tres primeras; las demás salen de leer el código.
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
  - sus ramas (`dependabot/…`) y títulos no siguen `docs/convenciones.md`, así que `checks.py` (M11) los rechazaría. Hace falta una excepción acotada a la cuenta de Dependabot, o configurar su prefijo y sus ramas.

### AgentShield (piloto, una vez)

- **Qué hace:** audita la configuración de un agente: secretos, permisos, hooks, MCP y agentes. Se pasa una vez sobre `entorno/`, `plugin-sdd/` y `plantilla-proyecto/.claude/`.
- **Qué toca y qué lee:** lee la carpeta que se le indica con `--path`. No se usan `--fix`, que reescribe la configuración (veto 2), `--opus`, que envía la configuración a la API de Anthropic con una clave, ni `--supply-chain-online`, que consulta npm.
- **Versión:** paquete npm `ecc-agentshield` 1.6.0 (MIT, `sha512-lpeHG96DtEn7ofq7Iiyvq29piQOwParaiZOdDB206i4ZeCL4yjwT6xN5BSGI4yhCEAN0eO0f9F9hxHLBuRqf/g==`), sin scripts de instalación y con 7 dependencias, entre ellas `@anthropic-ai/sdk`. Con `npx` las dependencias no quedan fijadas; se instala con un lockfile dentro del contenedor y `--ignore-scripts`.
- **Tiempo:** una ejecución de segundos; no entra en el commit ni en la CI.
- **Red:** solo para instalarlo. El análisis, en un contenedor sin red.
- **Alternativa:** la revisión del `reviewer` de seguridad que ya hace `sdd-review`, que es opinión; AgentShield aporta reglas fijas.
- **Riesgo fuera del sandbox:** ninguno si corre en el contenedor. Hoy no hay Docker ni Podman en WSL: el PR 4 decide entre instalar uno (lo haría la persona) o pasarlo en un runner de GitHub sin secretos.
- **Decisión:** piloto, una vez, con informe y lo decidido.

## Evaluadas y no aprobadas

| Herramienta | Fecha | Motivo |
| --- | --- | --- |
| Plugin ponytail (DietrichGebert/ponytail) v5.3.2 | 2026-10-19 | Instala hooks y una statusline que corren fuera del sandbox, y se solapa con `sdd-implement` y `sdd-review`. Su idea útil (la escalera del cambio mínimo completo) se incorporó a `sdd-implement`. Se puede reevaluar en v1.x con las métricas del primer recorrido. |
| Renovate (app alojada de Mend) | 2026-11-12 | Bot de dependencias de un tercero con escritura en contenidos, PR y workflows; Dependabot cubre lo observado sin instalar nada (VIC-18). Se reevalúa si Dependabot no actualiza la imagen de Playwright de un workflow. |
| trufflehog | 2026-11-12 | Por defecto verifica cada secreto contra la API de su proveedor: lo envía a la red. Sin verificar, no aporta sobre gitleaks (VIC-18). |

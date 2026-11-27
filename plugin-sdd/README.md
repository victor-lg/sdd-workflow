# Plugin `sdd` (workflow SDD + IA v1.0)

Mitad "plugin" de la distribución del núcleo (ADR-0004, Q05). La otra mitad es el repo plantilla (`plantilla-proyecto/`).

## Qué contiene

- `skills/`: los procedimientos del workflow, que Claude Code carga bajo demanda.
  - `sdd-context` ✔ borrador: reúne el contexto vigente (spec en `main`, ADR, código) y señala contradicciones.
  - `sdd-discover` ✔ borrador: entrevista de descubrimiento (F1), notas en `discovery/`.
  - `sdd-spec` ✔ borrador: redacta y audita la spec (F2) y la entrega como PR.
  - `sdd-plan` ✔ borrador: comprueba G2, fija el riesgo y abre rama y PR borrador.
  - `sdd-implement` ✔ borrador: implementa desde los AC, tests con IDs, cambio mínimo completo.
  - `sdd-review` ✔ borrador: organiza G4 (revisores según riesgo) y reconcilia.
- `agents/`: subagentes.
  - `reviewer` ✔ borrador: revisor de solo lectura con contexto limpio (G4).
- `evals/`: casos de `claude plugin eval` (M35), uno por directorio. Corren en la CI del workflow una vez por semana, el domingo de madrugada (02:17 UTC), si `plugin-sdd/` cambió en la última semana, o a mano (antes de cerrar un bloque o publicar una versión, y si falla una programada); nunca en un PR. En local: `claude plugin eval . --ablation none --no-publish` (sin `--no-publish`, el informe con las transcripciones se publica en claude.ai).

- `scripts/`: programas que las skills mandan ejecutar, en Python sin dependencias.
  - `esperar-ci.py` (VIC-69): la forma única de esperar a la CI de un PR, en `sdd-implement` y `sdd-review`. Consulta con `gh api` los check runs y estados del commit de la cabeza cada 30 s, hasta 45 min, confirma el final con una consulta más y sigue a la cabeza nueva si hay otro push. Todo sale por la salida estándar y termina con una línea `CI verde`, `CI rojo`, `CI error` o `CI tiempo agotado` (códigos 0 a 3). Un error de gh que no es de red avisa en seguida; uno de red se reintenta 3 veces. El agente lo lanza con Bash en segundo plano, y el sistema lo despierta al terminar. Tests en `tests/test_esperar_ci.py`, con un `gh` falso.

- `hooks/`: los controles del inventario (`docs/inventario-reglas.md`), en Python sin dependencias. Cada guarda tiene sus reglas, niveles (`bloquear` o `preguntar`) y mensajes en un `reglas-*.json`; las de Bash comparten el lector de órdenes `lector_bash.py`. Cada bloqueo dice qué hacer en su lugar, y si una guarda no puede mirar, bloquea.
  - `guarda-git.py` (`PreToolUse` sobre Bash): sin seguimiento de ramas (M16), `git add` por nombre (X-03), ramas desde `main` actualizado (REG-83) y, en `git commit`, nada que `.gitignore` excluya ni de la lista `fugas` (secretos, `.tareas/`, ficheros del sandbox), sin red (X-04). X-04 mira lo preparado, lo que añade un `git add` anterior de la misma orden (también carpetas y patrones) y, con `-a` o rutas, los ficheros versionados que casan. Lo que ya está en `HEAD` solo cuenta si está en `fugas`. No ejecuta nada de la configuración del repo (`core.fsmonitor`, filtros) ni escribe su índice. No mira `git merge`, `cherry-pick`, `revert`, `am` ni `rebase`. Quitar un fichero de lo preparado y hacer el commit van en dos órdenes. Un repo que versiona algo de `fugas` (un `.npmrc`, claves de prueba) no puede usar `git commit -a` ni rutas: hay que preparar por nombre. `git init x && cd x && … && git commit` en una sola orden se bloquea, porque el repo aún no existe cuando corre el hook.
  - `guarda-ficheros.py` (`PreToolUse` sobre Write, Edit, MultiEdit, NotebookEdit, Read, Grep y Bash): no escribe, copia, mueve ni borra `.env*` salvo plantillas (X-02); leerlos con Read, Grep u otra orden pregunta a la persona (REG-40); capturas y ficheros de trabajo en `.tareas/<ID>/`, nunca en `/tmp` ni en `$TMPDIR` (X-06, M12). En Bash no sabe qué argumento es un fichero: mira todos, salvo en `echo`, `printf`, `git` y, para las carpetas temporales, `grep`, `egrep`, `fgrep` y `rg`. Por eso también bloquea un texto que empiece por `/tmp/` en otra orden (`sed -n '/tmp/p'`). Choca con la carpeta temporal que Claude Code propone (`/tmp/claude-…`): escribir ahí se bloquea a propósito, y la salida de sus tareas se lee con Read, no con Bash. `mktemp` sin carpeta del proyecto se bloquea. Las órdenes de `git` quedan fuera (`git worktree add /tmp/w` pasa). Sigue los enlaces en Write, Edit y Read, no en Bash. No mira lo que se escribe dentro de un fichero.
  - `guarda-gh.py` (`PreToolUse` sobre Bash): `gh pr create` con `--draft`, también en R0 (REG-43); cuerpos de PR, comentarios y revisiones solo por `--body-file` (REG-93); y `gh pr ready` solo con la última ejecución de cada check en verde, ninguna cancelada (M5) ni pendiente, sin conflictos y con la rama local subida si es la del PR (REG-102). Si el PR no tiene la línea «Métricas G4», pregunta; no mira si los hallazgos están corregidos, eso sigue siendo de `sdd-review`. Un `echo`, `printf` o heredoc sin comillas en cualquier parte de la orden hace que `--body-file -` se bloquee, aunque no alimente a `gh`. Es el único hook con red: consulta el PR con `gh`, con un plazo total de 20 s, y solo con un PR y un repo de `github.com` de forma conocida.
  - `guarda-saltos.py` (`PreToolUse` sobre Bash, Write, Edit, MultiEdit y NotebookEdit): bloquea las formas conocidas de saltar o desviar los hooks de Git de lefthook (ADR-0008, lista en `docs/herramientas.md`): `--no-verify` y sus abreviaturas en `commit` y `merge`, y `-n` en `commit`; las variables `LEFTHOOK`, `LEFTHOOK_EXCLUDE`, `LEFTHOOK_CONFIG`, `LEFTHOOK_BIN`, `GITLEAKS_CONFIG` y `GITLEAKS_CONFIG_TOML`; `core.hooksPath`, un `include` o un alias con `git -c`, `--config-env` o `GIT_CONFIG_*`, y `PATH`, `HOME`, `XDG_CONFIG_HOME`, `GIT_CONFIG_GLOBAL` o `GIT_CONFIG_SYSTEM` en una orden con git; escribir configuración de lefthook fuera de `lefthook.json`, `.git/hooks/`, `.git/config`, `.git/commondir`, un fichero `.git`, la configuración global de Git, `.git/info/exclude`, `.git/info/attributes`, los ajustes de Claude Code, los perfiles de shell o ficheros llamados `lefthook` o `gitleaks`; sigue la carpeta de la sesión y los `cd` de la orden para resolver rutas relativas, y reconoce la forma con guion de git (`git-commit`); `git update-index --skip-worktree` o `--assume-unchanged`; y crear commits por otra vía (`git am`, `commit-tree`, `fast-import`, un clon local, otro directorio de Git o `gh api`). Solo mira la misma llamada de Bash, porque el estado del shell no pasa a la siguiente. Cambiar, mover o borrar `lefthook.json`, `.gitleaks.toml`, `.gitleaksignore` o `.gitattributes` en el árbol de trabajo pregunta, porque lefthook y gitleaks los leen de ahí aunque no se preparen. No bloquea `merge`, `cherry-pick`, `revert` o `rebase`, que tampoco pasan por `pre-commit`: eso lo cubre la CI.
  - `guarda-linear.py` (`PreToolUse` sobre las herramientas MCP con `linear` en el nombre del servidor, sin distinguir mayúsculas): leer, comentar y crear issues; empezarlas solo si su ID abre una línea de la sección «Entregas» de una spec del `main` de GitHub, y editar su título, descripción o etiquetas solo si no está en ninguna; nunca cerrar, cancelar, borrar ni archivar (REG-04, ADR-0009 §3.6 y M4, VIC-58). El resto, también una herramienta, un campo o un estado nuevos, se bloquea. Lee `main` con `git ls-remote` a la URL de `repos` en `reglas-linear.json`, no de la referencia local, y comprueba el hash de cada objeto que lee del clon. De una issue que ya existe solo cambia el estado para empezarla. Es el único freno del MCP con escritura.
  - `sesion-unica.py` (`SessionStart`): si hay otra sesión viva en la misma copia del repo, avisa y sugiere un worktree (REG-49).
  - **Son una segunda capa contra errores del agente, no seguridad.** Leen el texto de la orden, así que `bash -c`, `eval`, variables, alias, `gh api` o scripts los esquivan (los tests lo fijan en `SE_ESQUIVA`). Lo que protege es el sandbox, los ajustes gestionados, el ruleset y la CI. Tampoco miran `git branch <nueva> origin/…`, `git branch -t`, `git worktree add` ni el `git switch <rama>` que crea sola una rama remota. En un repo sin `origin/main`, REG-83 no deja crear ramas: primero hay que tener el remoto y hacer `git fetch origin`. Las guardas siguen el `cd` en línea, pero no saben de subshells: tras `(cd otro && …)`, creen que la orden sigue en `otro`.
  - El consentimiento con caducidad (X-10) está diseñado, sin activar: `docs/consentimiento-con-caducidad.md`.

Flujo normal: `sdd-discover` → `sdd-spec` → `sdd-review` (spec) → *merge humano* → `sdd-plan` → `sdd-implement` → `sdd-review` (código) → *merge humano*, o auto-merge en un R0 o R1 que no toca rutas de CODEOWNERS, en un repo con el ruleset del ADR-0009 (condiciones en `sdd-review`). `sdd-context` se usa dentro de los demás.

## Qué no contiene

Nada que sea propio de un proyecto: `AGENTS.md`, `CLAUDE.md`, las plantillas de spec, ADR y PR, la CI y `CODEOWNERS` van en el repo plantilla.

## Instalación

El marketplace es el propio repo del workflow (`.claude-plugin/marketplace.json` en su raíz):

```bash
claude plugin marketplace add <tu-usuario>/sdd-workflow
claude plugin install sdd@sdd-workflow
```

Las skills se invocan como `/sdd:<skill>` y el subagente como `sdd:reviewer`. Para probar cambios sin instalar: `claude --plugin-dir ./plugin-sdd`.

## Verificado (v0.11, Claude Code 2.1.303)

- `claude plugin validate` pasa para el plugin y para el marketplace.
- Instalado desde el marketplace local: 6 skills, 1 agente, 0 hooks, 0 MCP; coste fijo ~760 tokens por sesión.
- El marketplace no se actualiza solo (es de terceros): cada versión nueva se instala con `claude plugin update sdd@sdd-workflow`.
- Un cambio en este plugin es R2 en el repo del workflow, porque altera lo que hacen los agentes en todos los proyectos.

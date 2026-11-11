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

- `hooks/`: los controles del inventario (`docs/inventario-reglas.md`), en Python sin dependencias. Cada guarda tiene sus reglas, niveles (`bloquear` o `preguntar`) y mensajes en un `reglas-*.json`; las de Bash comparten el lector de órdenes `lector_bash.py`. Cada bloqueo dice qué hacer en su lugar, y si una guarda no puede mirar, bloquea.
  - `guarda-git.py` (`PreToolUse` sobre Bash): sin seguimiento de ramas (M16), `git add` por nombre (X-03), ramas desde `main` actualizado (REG-83) y, en `git commit`, nada que `.gitignore` excluya ni de la lista `fugas` (secretos, `.tareas/`, ficheros del sandbox), sin red (X-04). X-04 mira lo preparado, lo que añade un `git add` anterior de la misma orden (también carpetas y patrones) y, con `-a` o rutas, los ficheros versionados que casan. Lo que ya está en `HEAD` solo cuenta si está en `fugas`. No ejecuta nada de la configuración del repo (`core.fsmonitor`, filtros) ni escribe su índice. No mira `git merge`, `cherry-pick`, `revert`, `am` ni `rebase`. Quitar un fichero de lo preparado y hacer el commit van en dos órdenes.
  - `guarda-ficheros.py` (`PreToolUse` sobre Write, Edit, NotebookEdit, Read, Grep y Bash): no escribe, copia, mueve ni borra `.env*` salvo plantillas (X-02); leerlos con Read, Grep u otra orden pregunta a la persona (REG-40); capturas y ficheros de trabajo en `.tareas/<ID>/`, nunca en `/tmp` ni en `$TMPDIR` (X-06, M12). En Bash no sabe qué argumento es un fichero: mira todos, salvo en `echo`, `printf`, `git` y, para las carpetas temporales, `grep`, `egrep`, `fgrep` y `rg`. Por eso también bloquea un texto que empiece por `/tmp/` en otra orden. No mira lo que se escribe dentro de un fichero.
  - `guarda-gh.py` (`PreToolUse` sobre Bash): `gh pr create` con `--draft`, también en R0 (REG-43); cuerpos de PR, comentarios y revisiones solo por `--body-file` (REG-93); y `gh pr ready` solo con la última ejecución de cada check en verde, ninguna cancelada (M5) ni pendiente, sin conflictos y con la rama local subida si es la del PR (REG-102). Si el PR no tiene la línea «Métricas G4», pregunta. Es el único hook con red: consulta el PR con `gh`, con un plazo total de 20 s, y solo con un PR y un repo de `github.com` de forma conocida.
  - `guarda-linear.py` (`PreToolUse` sobre las herramientas MCP con `linear` en el nombre del servidor, sin distinguir mayúsculas): solo leer y comentar (REG-04, decisión 1); el resto, también una herramienta nueva, se bloquea. Con el endpoint de solo lectura que se usa hoy no tiene nada que bloquear: cubre que se conecte uno con escritura.
  - `sesion-unica.py` (`SessionStart`): si hay otra sesión viva en la misma copia del repo, avisa y sugiere un worktree (REG-49).
  - **Son una segunda capa contra errores del agente, no seguridad.** Leen el texto de la orden, así que `bash -c`, `eval`, variables, alias, `gh api` o scripts los esquivan (los tests lo fijan en `SE_ESQUIVA`). Lo que protege es el sandbox, los ajustes gestionados, el ruleset y la CI. Tampoco miran `git branch <nueva> origin/…`, `git branch -t`, `git worktree add` ni el `git switch <rama>` que crea sola una rama remota. En un repo sin `origin/main`, REG-83 no deja crear ramas: primero hay que tener el remoto y hacer `git fetch origin`.
  - El consentimiento con caducidad (X-10) está diseñado, sin activar: `docs/consentimiento-con-caducidad.md`.

Flujo normal: `sdd-discover` → `sdd-spec` → `sdd-review` (spec) → *merge humano* → `sdd-plan` → `sdd-implement` → `sdd-review` (código) → *merge humano*. `sdd-context` se usa dentro de los demás.

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

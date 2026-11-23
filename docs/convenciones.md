# Convenciones de nombres y mensajes (M42)

Fuente única de cómo se nombran y se escriben las cosas en el workflow. `AGENTS.md`, las skills, las plantillas y la CI remiten aquí en vez de repetirlo. Es norma desde el PR de VIC-16 que aplica el ADR-0007; se cambia por PR sin ADR, salvo que contradiga un ADR aceptado o la línea base (ADR-0007, §3.4).

Idea de fondo: **el mismo vocabulario en todas partes.** El tipo de cambio (`feat`, `fix`, `spec`…) es el mismo en la etiqueta de Linear, en la rama, en el commit y en el título del PR, y el ID de la issue va en todos.

## 1. Identificadores

| Código | Qué es | Ejemplo | Dónde vive |
| --- | --- | --- | --- |
| `VIC-N` | Issue de Linear (team "Desarrollo", clave `VIC`) | VIC-16 | Linear |
| `#N` | PR de GitHub | #38 | GitHub |
| `SPEC-<DOMINIO>-NNN` | Spec; el dominio es el del producto o área (`CALC`, `XCUT` para transversales) | SPEC-CALC-003 | `docs/specs/` |
| `FR-NN`, `NFR-NN`, `AC-NN` | Requisito y criterio de aceptación dentro de una spec; un AC se cita siempre completo | SPEC-CALC-003/AC-13 | La spec |
| `ADR-NNNN` | Decisión de arquitectura (una serie por repo) | ADR-0007 | `docs/adr/` |
| `M-NN` | Mejora del workflow | M42 | `historial/`, `docs/plan-*.md` |
| `vX.Y.Z` | Versión publicada (etiqueta de Git y release) | v1.0.0 | GitHub |

Reglas:
- Los números no se reutilizan ni se renumeran (como pasó con M37).
- Un ID se escribe siempre igual: `VIC-16`, no `vic16` ni `#VIC-16`. En nombres de rama, en minúsculas (`vic-16`).

## 2. Linear

**Estructura:** un solo team, "Desarrollo" (clave `VIC`), y un **proyecto por producto** (*Calculadora de discos*, *Workflow SDD v1.1*…). El producto lo dicen el proyecto, el repo y la spec, no el ID. Los hitos del proyecto son las fases o bloques.

**Etiquetas**, tres grupos de selección única:

| Grupo | Valores | Para qué |
| --- | --- | --- |
| Tipo | `feat`, `fix`, `spec`, `adr`, `refactor`, `test`, `docs`, `ci`, `chore` | El mismo tipo que la rama y el commit |
| Riesgo | `R0`, `R1`, `R2` | Ver el riesgo sin abrir la issue |
| Origen | `retro`, `defecto-escapado`, `observacion` | Métricas: mejoras M, defectos que llegaron a producción (M10) y hallazgos que Claude anota para que decidas |

**Plantillas:** *Entrega SDD* (con spec y AC), *Bug*, *Spec* y *Mejora del workflow*. Cada una trae su etiqueta de Tipo u Origen puesta.

**Título de la issue:**
- el resultado, en palabras de usuario y en español: "Guardar el peso al terminar de escribir";
- unos 60 caracteres como máximo;
- sin IDs ni versiones dentro: la spec y la issue relacionada van en el cuerpo o como relación de Linear.

**Cuerpo:** el de la plantilla que toque. Las secciones vacías se borran, no se dejan con el texto de ejemplo.

## 3. Ramas

Modelo GitHub Flow: `main` siempre desplegable, una rama corta por cambio, squash al fusionar y la rama se borra sola.

```
<tipo>/vic-<N>-<descripcion>
```

- `tipo`: uno de los de la etiqueta de Tipo.
- `descripcion`: dos a cinco palabras en *kebab-case*, sin tildes ni eñes; la rama entera, unos 50 caracteres como máximo.
- Si la entrega va en varios PR: `feat/vic-12-logica`, `feat/vic-12-interfaz`.
- **Siempre con el ID** (M11), también las de spec, ADR, CI y mantenimiento. Si no hay issue, se crea antes.

Ejemplos: `feat/vic-16-materiales`, `fix/vic-17-redondeo-peso`, `spec/vic-18-calc-004-historial`, `adr/vic-19-0010-modelos`, `ci/vic-20-shards`.

## 4. Commits (Conventional Commits 1.0)

```
<tipo>(<alcance>)!: <descripción>

<cuerpo>

<pie>
```

**Título:**
- `tipo`: el de la etiqueta.
- `alcance`, opcional: la zona del código o del documento (`calculo`, `interfaz`, `pwa`, `ci`, `SPEC-CALC-003`). **No es el ID de la issue.**
- `!` solo si rompe compatibilidad (datos guardados, URL, formato).
- `descripción`: en español, en imperativo y en minúscula ("calcula", "añade", "corrige"), sin punto final; unos 50 caracteres, 72 como máximo.

**Cuerpo:**
- separado del título por una línea en blanco;
- qué cambia y **por qué**, no cómo (eso ya está en el diff);
- líneas de unos 72 caracteres; puede llevar viñetas.

Se puede omitir en cambios evidentes (una errata).

**Pie**, una línea por dato, en este orden:

```
Refs: VIC-16
Spec: SPEC-CALC-003/AC-04
BREAKING CHANGE: <qué deja de funcionar y cómo migrar>
```

Sin `Co-Authored-By` ni "Generated with" (decisión de autoría, bloque 1).

**Ejemplo:**

```
fix(calculo): suma el peso disco a disco con grosores mezclados

El cálculo asumía un grosor único y sobrestimaba el peso cuando se
mezclaban discos de 2,5 y 5 kg. No cambia la interfaz.

Refs: VIC-17
Spec: SPEC-CALC-003/AC-04
```

## 5. Pull requests

- **Título:** el mismo formato que el título de un commit, porque al fusionar por squash es el commit de `main`. GitHub añade `(#N)` al final.
- **Cuerpo:** la plantilla del repo (`.github/pull_request_template.md`). La primera línea útil es `Fixes VIC-N` en el último PR de una entrega y `Part of VIC-N` en los anteriores; así Linear mueve los estados. `Refs VIC-N` enlaza la issue sin cerrarla, cuando queda una prueba después de publicar.
- **Mensaje del squash:** en *Settings → General → Pull Requests*, *Default commit message* = **"Pull request title and commit details"**. El commit de `main` recoge entonces como cuerpo los commits de la rama, que ya siguen el formato. Es un ajuste del repo y lo haces tú (ADR-0007).
- Un PR no mezcla spec y código; unas 400 líneas de código como máximo, sin contar tests ni lockfiles.

### 5.1 Evaluaciones del plugin antes de quitar el borrador (VIC-51)

Solo en el repo del workflow. Un PR que toca `plugin-sdd/skills/`, `plugin-sdd/agents/` o `plugin-sdd/evals/` no sale de borrador sin sus evaluaciones, igual que sin la CI y sin G4. Es la lección 2 de `historial/retrospectiva-bloque-4.md`: el #55 se dio por listo con ellas pendientes. La CI semanal (`evals.yml`) sigue corriendo todos los casos; esto no la sustituye.

- **Qué casos:** los que cargan lo que cambia (la skill, el subagente o el caso tocado) y los que el cambio más puede romper, con el motivo en el PR.
- **La orden va en la descripción del PR** y apunta a `refs/pull/<N>/head`, que GitHub guarda aunque se fusione el PR y se borre la rama; `origin/<rama>` desaparece con el squash. Empieza por `cd` al clon con su ruta absoluta: lanzada desde otro directorio, el `git fetch` falla.

  ```bash
  cd <ruta absoluta del clon> && git fetch origin refs/pull/<N>/head && git worktree add --detach ../sdd-pr-<N> FETCH_HEAD && cd ../sdd-pr-<N>/plugin-sdd && for c in <casos>; do claude plugin eval . --case "$c" --ablation none --no-publish --trust-plugin || break; done
  ```

  - **Ejemplo real, el #65** (cambia `sdd-review`). Esta orden funcionó lanzada desde el clon:

    ```bash
    git fetch origin refs/pull/65/head && git worktree add --detach ../sdd-pr-65 FETCH_HEAD && cd ../sdd-pr-65/plugin-sdd && for c in activacion-sdd-review 'g4-*' n8-revisor-sin-contexto-del-autor hook-cuerpo-por-fichero; do claude plugin eval . --case "$c" --ablation none --no-publish --trust-plugin || break; done
    ```

    Lanzada fuera del clon, falla en el primer paso: `git fetch` no encuentra el repo (`fatal: not a git repository`) y no se evalúa nada. Por eso la orden empieza ahora por `cd`.
  - `--no-publish` deja los informes en local (`results/` del worktree, que Git ignora). `--trust-plugin` va siempre en las órdenes locales.
  - Al terminar, desde el clon: `git worktree remove ../sdd-pr-<N>`. Los informes se borran con él, así que el resultado se anota antes. Si hay que repetirlas, primero se quita el worktree, o `worktree add` falla.
- **El resultado va en el PR** antes de `gh pr ready`, en «Validación»: la versión del plugin, el commit evaluado y una línea por caso, que pasa o falla, con una nota si falla o si el evaluador da ruido. El commit evaluado tiene que ser el último del PR: si después entra otro que toca esas rutas, se repiten.
- **Quién las lanza:** la persona, mientras el sandbox del agente no llegue a la API. El agente deja la orden y no quita el borrador hasta que el resultado esté anotado. Un caso que falla cuenta como una CI en rojo: se corrige o se explica, y decide la persona.

## 6. Versiones y notas

- **Etiqueta** `vX.Y.Z` sobre `main` tras cada publicación (semver). Para una PWA:
  - `Z`: correcciones;
  - `Y`: funcionalidad nueva;
  - `X`: rompe datos guardados o el uso.
- **Release de GitHub** con *Generate release notes*: sale de los títulos de PR, por eso importan.
- **CHANGELOG.md** en formato *Keep a Changelog* (`Added`, `Changed`, `Fixed`, `Removed`, `Security`), escrito en español con esos mismos apartados traducidos: *Añadido*, *Cambiado*, *Corregido*, *Eliminado*, *Seguridad*.

## 7. Documentos

- **Nombres de fichero:** en minúsculas y *kebab-case*. Las specs, `SPEC-CALC-003-presentacion.md`; los ADR, `0007-autoria-y-convenciones.md`.
- **Fechas:** `AAAA-MM-DD`.
- **Estados:** las specs y los ADR usan los de su plantilla (`Propuesto`, `Aceptado`, `Sustituido por …`). Los documentos del workflow usan `BORRADOR` o `PROPUESTO` en el título hasta que se aceptan.

## 8. Lo que comprueba una máquina

Una convención que no se comprueba se acaba incumpliendo (M25). Se comprueba en tres sitios:

| Qué | Dónde | Bloque |
| --- | --- | --- |
| Formato del mensaje de commit | hook `commit-msg` con lefthook (en local) y CI (`checks.py`, `commits`), con la misma función | 3 (M33) |
| Nombre de la rama con tipo e ID | CI (`checks.py`) | 2 (M11) |
| Título del PR y `Fixes`/`Part of`/`Refs` con ID | CI (`checks.py`) | 2 (M11) |
| Sin `Co-Authored-By` ni "Generated with" de Claude en el PR y sus commits | CI (`checks.py`) | 2 (REG-34) |
| Issue → rama → PR enlazados | Integración Linear–GitHub (ya activa) | — |
| Métricas por issue | `sdd-metricas.py` lee el ID de la rama con el formato nuevo | 1 |

## 9. Qué cambia respecto a ahora

| Antes | Ahora |
| --- | --- |
| Team "Victor" | Team "Desarrollo" (la clave sigue siendo `VIC`) |
| Sin etiquetas | Tipo, Riesgo y Origen |
| `vic-12-calculo`, `spec-calc-003-…` sin ID | `feat/vic-12-calculo`, `spec/vic-18-…`, siempre con ID |
| `feat(VIC-5): …` (el ID como alcance) | `feat(calculo): …` con `Refs: VIC-5` en el pie |
| `Co-Authored-By` del agente | Sin menciones a Claude |
| Squash con el mensaje por defecto | "Pull request title and commit details" |

Aplicada en el PR de VIC-16 (ADR-0007): `plantilla-proyecto/AGENTS.md`, la plantilla de PR, `sdd-plan`, `sdd-spec`, `sdd-implement`, `sdd-review`, el lector de `sdd-metricas.py` y la guía de instalación. `docs/glosario.md` no necesitaba cambios.

`checks.py` comprueba ramas, títulos y enlaces desde VIC-17 (M11, bloque 2), y el formato de los commits desde el PR 3 de VIC-18: el título como el del PR, la línea en blanco tras él y el pie con `Refs: VIC-N` y, si van, `Spec:` y `BREAKING CHANGE:` en ese orden. No mira los merges (el de la CI es el merge efímero de GitHub, y el squash los absorbe); el hook deja pasar el título que Git pone a un merge. Sí rechaza los títulos que proponen `git revert` (`Revert "…"`) o la web de GitHub al aplicar una sugerencia de revisión: se reescriben antes del commit o, en la web, en el cuadro del mensaje.

**Excepción:** los PR de Dependabot (M38) no siguen estas convenciones. `checks.py` no las comprueba si el autor del PR y el de todos sus commits es Dependabot, no hay merges y el PR solo cambia dependencias o workflows; nunca por el nombre de la rama.

Pendiente:
- los repos de cada proyecto, al actualizar su plantilla.

El historial ya escrito no se toca.

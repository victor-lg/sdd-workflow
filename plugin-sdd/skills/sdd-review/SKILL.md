---
name: sdd-review
description: Organiza la revisión independiente G4 de un PR de spec o de código. Lanza el número de revisores que exige el nivel de riesgo, cada uno con contexto limpio, y reconcilia sus hallazgos en el PR. Úsala cuando un PR de spec o de código esté listo para revisión.
---

<!-- Workflow SDD + IA v1.1 (G4, ADR-0001-M1, ADR-0006; métricas de G4, VIC-16; formato de hallazgos y respuestas en comentarios, VIC-38; commit revisado y cambios tras la última ronda en la CI, VIC-39; camino corto para aclaraciones, VIC-40). -->

# sdd-review

No revisas tú: organizas la revisión para que la hagan revisores que no han visto cómo se hizo el cambio.

También la organizas para los PR que abre Claude desde el navegador (los que tocan `.github/workflows/` o los ajustes gestionados, que no te corresponde cambiar): pasan por esta skill antes de que la persona los fusione. Lanzas y reconcilias los revisores como en cualquier otro PR, con tres diferencias: lo que deba corregirse lo corrige quien abrió el PR, no tú, y la ronda siguiente empieza cuando lo haya hecho; la reconciliación va en el comentario del paso 6 y no editas la descripción: las líneas de hallazgo (paso 3.5) las añade a ella quien abrió el PR, porque sin ellas el check `hallazgos` falla con las respuestas de los comentarios; y el borrador lo quita la persona, no tú. La línea «Métricas G4» se publica igual; si no estás en la rama de la issue de ese PR, avísalo (paso 6).

## 1. Cuántos revisores

| PR | R0 | R1 | R2 |
| --- | --- | --- | --- |
| Spec | — | 2 | 2 |
| ADR | — | 2 | 2 |
| Código | Opcional | 1 | 2 |

**Camino corto para aclaraciones.** Un PR de spec que solo pasa a la spec una lectura que la persona ya decidió (su respuesta en un PR o en la issue, por ejemplo cuando dos revisores leen un requisito de forma distinta) lleva los revisores de un PR de spec (dos) y **una sola ronda**, en R1 y en R2. Vale solo si:

- la descripción del PR dice que es una aclaración y enlaza la respuesta, con su texto literal;
- el diff solo cambia la redacción de los FR o AC que la respuesta toca, o añade AC que fijan esa lectura, además de la versión y el `estado` (`sdd-spec`);
- no añade, quita ni renumera FR o NFR, ni decide nada que la respuesta no diga.

Si falla algo, es un PR de spec normal, con sus rondas. Tras la ronda no hay otra: lo que deba corregirse se corrige sin otra ronda, y la persona revisa la corrección al aprobar (la lista la calcula el check `cambios`, paso 3.3). Lo que vaya más allá de la respuesta se quita; si para corregirlo hace falta decidir algo que la respuesta no dice, deja de ser una aclaración y se revisa como un PR de spec normal.

**Modelo (v0.20):** el subagente `reviewer` usa Sonnet por defecto. Las revisiones eran la mayor parte del consumo (un 90 % según `/usage`), y Sonnet ya encontró defectos reales en el PR #5 de `calculadora-discos`. **En R2, uno de los revisores de código se centra en seguridad y se lanza con Opus** (en el lanzamiento del subagente, indica el modelo `opus`). Si un defecto se escapa a una revisión con Sonnet (métrica "defectos escapados"), se anota y se reconsidera este reparto.

Si no puedes lanzar los revisores exigidos, el PR **no** está revisado. Dilo y no lo marques como listo.

## 2. Qué recibe cada revisor (contexto limpio)

Lanza el subagente `reviewer` una vez por revisor, en invocaciones independientes. Esta es la **lista única** de lo que recibe cada uno (`CLAUDE.md` la enlaza); nada más:

- el tipo de PR (spec, ADR o código) y su nivel de riesgo;
- la spec vigente en `main` y, si es un PR de spec, la versión propuesta;
- el diff;
- los resultados de la CI;
- los ADR enlazados;
- el prefijo de sus IDs de hallazgo, `G4-<ronda>-<letra>`: una letra por revisor (A, B) y la misma en todas las rondas;
- en una aclaración por el camino corto, que lo es y la respuesta literal de la persona, con su enlace: es lo que el revisor contrasta.

Pide expresamente a cada revisor que compruebe si algún test existente se ha debilitado y que aplique las reglas de `reviewer.md` para anotar un hallazgo: que un usuario real pueda llegar al caso, una prueba por hallazgo y la gravedad sin exagerar. La descripción del PR no se le pasa: que la "Guía para el revisor humano" no omita ningún sitio delicado lo compruebas tú al reconciliar, con los hallazgos de los revisores.

**Deja rastro:** publica en el PR un comentario por revisor y ronda con el encargo literal que recibió y su respuesta, plegados en `<details>` y con el diff en un bloque de código de cerca más larga que cualquiera de dentro (`gh pr comment N --body-file .tareas/VIC-N/g4-rR-X.md`); si pasa de 65 536 caracteres, el límite de GitHub, pártelo en dos, cada parte con sus cercas y `<details>` cerrados. Así la persona puede comprobar que G4 se hizo y que nadie recibió contexto de más (N8). Fuera de lo plegado, el comentario lleva una línea con el commit que vio el revisor, el SHA completo de la cabeza cuyo diff le pasaste (`git rev-parse HEAD` después del push): `Commit revisado: G4-<ronda>-<letra> · <sha de 40>`. Con ella, el check `cambios` calcula lo que entra después de la última ronda; sin ella, falla. Si reescribes la rama después (rebase o push forzado), ese commit deja de estar en su historia y el check también falla: repite la ronda sobre la cabeza nueva. En la descripción, solo el enlace al comentario. Publícalos desde la cuenta del agente o de la persona (`CUENTAS_G4` en `checks.py`): el check `hallazgos` no lee los de otras cuentas, porque en un repo público comenta cualquiera.

**Nunca** le pases tu razonamiento, tu plan, tus conclusiones ni las respuestas de otro revisor. Si lo haces por error, esa revisión está contaminada y se repite (caso N8).

## 3. Reconciliar

Con las respuestas de todos los revisores:

1. **Confirma cada hallazgo contra el código o la spec.** Descarta lo que no se sostenga y explica por qué.
2. **Clasifica:**
   - *debe corregirse:* bloquea el merge;
   - *importante:* se corrige o se descarta con prueba;
   - *menor:* opcional.

   Para descartar un *debe corregirse* o un *importante*, o bajarle la gravedad, hace falta una prueba concreta: un test, una línea o una cita. Si no la tienes, pregunta a la persona.
3. **Corrige lo que debe corregirse.** Si la corrección es sustancial, repite la revisión: **hasta 3 rondas** (la inicial y 2 repeticiones). Si persiste, pregunta a la persona. En una aclaración por el camino corto hay una sola: lo que deba corregirse se corrige sin repetirla.
   - **Después de la última ronda,** las aclaraciones y decisiones de la persona se aplican **sin otra ronda**, salvo que añadan reglas de negocio nuevas. La lista de lo que cambia tras la última ronda no la escribes tú: la calcula el check `cambios` desde el commit de cada revisor y la publica en el resumen de `checks-sdd`, para que la persona la revise al aprobar. No la pongas en la descripción, ni como sección ni como viñeta: el check falla si la encuentra.
4. **Comprueba la "Guía para el revisor humano"** contra los hallazgos: si un revisor señaló un sitio delicado que la guía no cita, añádelo.
5. **Escribe en el PR,** en la sección "Revisión IA", el resumen de cada revisor (con el enlace a su comentario) y la reconciliación: qué se confirmó, qué se descartó y qué se corrigió. La reconciliación de cada ronda se publica además como comentario del PR (paso 6): es el mismo texto.

   En la reconciliación, cada hallazgo de cada ronda, confirmado o no, va en una línea con este formato fijo, fuera de `<details>` y de bloques de código:

   ```
   - G4-1-A-01 · debe corregirse · prueba: `src/peso.js:42` · resolución: corregido en 1a2b3c4
   ```

   - **Gravedad:** la que confirmas (*debe corregirse*, *importante* o *menor*).
   - **Prueba:** la del revisor o la tuya.
   - **Resolución,** una de estas:
     - `corregido en <sha>` (varios, separados por comas);
     - `descartado: <prueba>`: el test, la línea o la cita que lo refuta. En un *menor* basta `descartado`;
     - `pregunta a la persona`, si no hay prueba para descartarlo; cuando conteste, cámbiala por una de las otras dos.

     Mientras no tenga ninguna, escribe `resolución: pendiente`.

   El check `hallazgos` de la CI lee estas líneas de la descripción y las respuestas de los revisores tal cual: en los comentarios de `CUENTAS_G4` (y en lo plegado de la descripción), toda línea que empieza por un ID `G4-…` es un hallazgo, con la gravedad que le sigue. Falla si un hallazgo de una respuesta no tiene línea, si alguna no tiene resolución o si se descarta sin prueba uno que el revisor o tú clasificasteis como *debe corregirse* o *importante*. Avisa de los que esperan a la persona. En otros comentarios tuyos, no empieces una línea por un ID salvo en esas líneas: contaría como hallazgo.

   **La descripción se edita con la API:** `gh api -X PATCH "repos/{owner}/{repo}/pulls/N" -F body=@.tareas/VIC-N/pr.md`. No uses `gh pr edit`: falla en los repos con Projects (classic), y sin mirar el código de salida parece que ha funcionado. Edítala después de publicar las respuestas: un comentario no vuelve a lanzar la CI; la edición, sí.
6. **Métricas:** el comentario de reconciliación de cada ronda termina con esta línea, sola, sin viñeta ni formato y con números:

   `Métricas G4: PR #N · ronda R · confirmados X · descartados Y · corregidos Z`

   - `R` es el número de la ronda (1 a 3); `X`, los hallazgos de esa ronda que confirmaste; `Y`, los que descartaste; `Z`, cuántos de esos `X` están corregidos hasta ahora.
   - Si corriges después de la última ronda, publica otro comentario con la línea de esa ronda y el `Z` nuevo: cuenta la última.
   - Una ronda sin hallazgos también se anota, con ceros.
   - **Cómo:** escribe el cuerpo con Write en `.tareas/VIC-N/g4-ronda-R.md`, **sin** la línea (nunca en `/tmp` ni en `$TMPDIR`: el hook lo bloquea, X-06). Publícalo con una sola orden que añade la línea en un heredoc entrecomillado:

     ```bash
     { cat .tareas/VIC-N/g4-ronda-R.md; cat <<'METRICAS_SDD'
     Métricas G4: PR #N · ronda R · confirmados X · descartados Y · corregidos Z
     METRICAS_SDD
     } | gh pr comment N --body-file -
     ```

     **Nunca** metas el cuerpo (respuestas de revisores, líneas del diff, comentarios) en la orden de Bash, ni en un heredoc sin comillas ni en `--body "…"`: lleva texto que no controlas y se ejecutaría como shell. `sdd-metricas` solo lee la línea de la entrada de `gh pr comment` y solo si la orden no falla; no la lee de tu texto en el chat, de un fichero ni de la descripción del PR.
   - La atribuye a la issue de la rama en la que estás. Si no estás en la rama de la issue, publícala igual y avísalo; no cambies de rama por esto. No la escribas con otro formato ni dentro de un bloque de código.
   - Si usas esta skill y no queda ninguna línea válida, el resumen de métricas marca la issue con "⚠ sin línea".

## 4. Cerrar

Cuando no quede nada que deba corregirse y la CI esté en verde, comprueba que el título sigue `docs/convenciones.md` del workflow (Conventional Commits, alcance como zona y no como ID) y que la "Guía para el revisor humano" está completa, y quita el estado de borrador con `gh pr ready N`. El hook comprueba antes que todos los checks del último commit estén en verde, sin ninguno cancelado (M5), y si no lo están lo bloquea: no lo quites por otra vía. La aprobación y el merge son de la persona (G6).

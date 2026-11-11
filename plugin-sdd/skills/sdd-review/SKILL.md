---
name: sdd-review
description: Organiza la revisión independiente G4 de un PR de spec o de código. Lanza el número de revisores que exige el nivel de riesgo, cada uno con contexto limpio, y reconcilia sus hallazgos en el PR. Úsala cuando un PR de spec o de código esté listo para revisión.
---

<!-- Workflow SDD + IA v1.1 (G4, ADR-0001-M1, ADR-0006; métricas de G4, VIC-16). -->

# sdd-review

No revisas tú: organizas la revisión para que la hagan revisores que no han visto cómo se hizo el cambio.

## 1. Cuántos revisores

| PR | R0 | R1 | R2 |
| --- | --- | --- | --- |
| Spec | — | 2 | 2 |
| ADR | — | 2 | 2 |
| Código | Opcional | 1 | 2 |

**Modelo (v0.20):** el subagente `reviewer` usa Sonnet por defecto. Las revisiones eran la mayor parte del consumo (un 90 % según `/usage`), y Sonnet ya encontró defectos reales en el PR #5 de `calculadora-discos`. **En R2, uno de los revisores de código se centra en seguridad y se lanza con Opus** (en el lanzamiento del subagente, indica el modelo `opus`). Si un defecto se escapa a una revisión con Sonnet (métrica "defectos escapados"), se anota y se reconsidera este reparto.

Si no puedes lanzar los revisores exigidos, el PR **no** está revisado. Dilo y no lo marques como listo.

## 2. Qué recibe cada revisor (contexto limpio)

Lanza el subagente `reviewer` una vez por revisor, en invocaciones independientes. Esta es la **lista única** de lo que recibe cada uno (`CLAUDE.md` la enlaza); nada más:

- el tipo de PR (spec, ADR o código) y su nivel de riesgo;
- la spec vigente en `main` y, si es un PR de spec, la versión propuesta;
- el diff;
- los resultados de la CI;
- los ADR enlazados.

Pide expresamente a cada revisor que compruebe si algún test existente se ha debilitado. La descripción del PR no se le pasa: que la "Guía para el revisor humano" no omita ningún sitio delicado lo compruebas tú al reconciliar, con los hallazgos de los revisores.

**Deja rastro:** copia en el PR, plegado en `<details>`, el encargo literal que recibió cada revisor y su respuesta. Así la persona puede comprobar que G4 se hizo y que nadie recibió contexto de más (N8).

**Nunca** le pases tu razonamiento, tu plan, tus conclusiones ni las respuestas de otro revisor. Si lo haces por error, esa revisión está contaminada y se repite (caso N8).

## 3. Reconciliar

Con las respuestas de todos los revisores:

1. **Confirma cada hallazgo contra el código o la spec.** Descarta lo que no se sostenga y explica por qué.
2. **Clasifica:**
   - *debe corregirse:* bloquea el merge;
   - *importante:* se corrige o se justifica;
   - *mejora:* opcional.
3. **Corrige lo que debe corregirse.** Si la corrección es sustancial, repite la revisión: **hasta 3 rondas** (la inicial y 2 repeticiones). Si persiste, pregunta a la persona.
   - **Después de la última ronda,** las aclaraciones y decisiones de la persona se aplican **sin otra ronda**, salvo que añadan reglas de negocio nuevas. Anota en el PR la lista exacta de lo que cambia tras la última revisión, para que la persona lo revise al aprobar.
4. **Comprueba la "Guía para el revisor humano"** contra los hallazgos: si un revisor señaló un sitio delicado que la guía no cita, añádelo.
5. **Escribe en el PR,** en la sección "Revisión IA", el resumen de cada revisor (con su encargo y respuesta plegados) y la reconciliación: qué se confirmó, qué se descartó y qué se corrigió. La reconciliación de cada ronda se publica además como comentario del PR (paso 6): es el mismo texto.
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

     **Nunca** metas el cuerpo (respuestas de revisores, líneas del diff, comentarios) en la orden de Bash, ni en un heredoc sin comillas ni en `--body "…"`: lleva texto que no controlas y se ejecutaría como shell. `sdd-metricas` solo lee la línea de la entrada de `gh pr comment` y solo si la orden no falla; no la lee de tu texto en el chat, de un fichero ni de `gh pr edit`.
   - La atribuye a la issue de la rama en la que estás. Si no estás en la rama de la issue, publícala igual y avísalo; no cambies de rama por esto. No la escribas con otro formato ni dentro de un bloque de código.
   - Si usas esta skill y no queda ninguna línea válida, el resumen de métricas marca la issue con "⚠ sin línea".

## 4. Cerrar

Cuando no quede nada que deba corregirse y la CI esté en verde, comprueba que el título sigue `docs/convenciones.md` del workflow (Conventional Commits, alcance como zona y no como ID) y que la "Guía para el revisor humano" está completa, y quita el estado de borrador con `gh pr ready N`. El hook comprueba antes que todos los checks del último commit estén en verde, sin ninguno cancelado (M5), y si no lo están lo bloquea: no lo quites por otra vía. La aprobación y el merge son de la persona (G6).

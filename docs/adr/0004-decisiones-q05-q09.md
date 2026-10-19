---
id: ADR-0004
titulo: Distribución del núcleo, primer recorrido, datos, rutas y progreso de tareas
estado: Aceptado
fecha: 2026-10-19
sustituye: null
sustituido_por: null
modifica:
  - ADR-0001 (laguna L9, campo datos: por proyecto)
  - ADR-0002 (regla de datos por perfil)
  - ADR-0003 (regla de datos en Linear)
referencias:
  - docs/linea-base-v1.md (§5, §8, §10, §11, §14)
---

# ADR-0004 — Distribución del núcleo, primer recorrido, datos, rutas y progreso de tareas

Cierra las decisiones abiertas Q05, Q06, Q07, Q08 y Q09. Aceptadas por el usuario el 2026-10-19. Q04 queda abierta, reformulada tras saber que el usuario tiene GitHub Pro.

## 1. Contexto

- Eran decisiones con recomendación por defecto. El usuario pidió desarrollarlas antes de decidir y respondió a cada una.
- El usuario tiene GitHub Pro, así que la protección de ramas está disponible en repos privados (§3.7).
- En su entorno profesional se usa GitLab, con una CI/CD distinta. El usuario prefiere asentar primero la vía personal y adaptar la profesional después.

## 2. Alternativas consideradas

El desarrollo completo de cada pregunta se hizo en la conversación del 2026-10-19. En resumen:

- **Q05:** repo plantilla, plugin de Claude Code o un híbrido de ambos.
- **Q06:** validador de IBAN, una utilidad propia o algo con interfaz.
- **Q07:** clasificación de datos por proyecto (personal o confidencial) o una sola vía.
- **Q08:** `docs/specs/` + `docs/adr/`, `specs/` en la raíz, o las rutas largas de las notas.
- **Q09:** issue + PR + fichero fuera de Git, plan versionado en `docs/plans/`, o solo issue + PR.

## 3. Decisión

### Q05 — Distribución del núcleo: híbrido

- **Repo plantilla de GitHub** (`plantilla-proyecto/`): aporta los ficheros propios del proyecto, es decir `README.md`, `AGENTS.md`, `CLAUDE.md`, las plantillas de spec, ADR, PR y visión, la CI, `CODEOWNERS` y `.gitignore`.
- **Plugin de Claude Code** (`plugin-sdd/`), instalado desde un repo propio que hace de marketplace: aporta las skills `sdd-*` y el subagente revisor.
- Un cambio en el plugin es R2 en el repo del workflow, porque altera lo que hacen los agentes en todos los proyectos.

### Q06 — Primer recorrido: calculadora de discos iOS

- **La app:** una aplicación iOS sencilla que el usuario quiere de verdad. A partir de unos porcentajes, el peso objetivo de trabajo y los discos disponibles, indica qué discos cargar en cada porcentaje para series aproximadas de calentamiento. Es una calculadora con una ligera capa de UI/UX.
- **La tecnología se elige dentro del recorrido,** con su ADR (D11). Restricción conocida: el desarrollo nativo de iOS con Xcode requiere macOS, y el equipo principal es Windows.

### Q07 — Datos: una sola vía

- No hay distinción entre proyectos personales y profesionales. Se retira el campo `datos:`, la laguna L9 de ADR-0001.
- Remote Control y Claude Code en la web están siempre permitidos.
- Los modelos de OpenCode Go están permitidos, salvo los "Contributor", que pueden usar los prompts para entrenar.
- Linear sin restricción de contenido, salvo la regla general de que el texto de una spec nunca va ahí (D13).
- **El entorno profesional queda aplazado** (§10), con este disparador: que la versión personal esté asentada. Incluye GitLab, la CI/CD profesional y la clasificación de datos por proyecto.

### Q08 — Rutas

- `docs/specs/` y `docs/adr/`, con todo lo documental bajo `docs/`.

### Q09 — Progreso de una tarea

- **La entrega y su estado:** la issue de Linear.
- **El plan y el progreso técnico en R1 y R2:** la descripción del PR, abierto como borrador desde el principio, con una lista de pasos que el agente va marcando.
- **Las sesiones largas interrumpidas:** `.tareas/<ID>.md`, fuera de Git (en `.gitignore`), con objetivo, progreso verificado, ficheros tocados, pruebas, bloqueos y siguiente paso. Se borra al cerrar la tarea y, al reanudar, se contrasta con Git y la CI (P10).

## 4. Consecuencias

- **Q05:** las mejoras de las skills llegan a todos los proyectos sin copiar nada. A cambio, hay que preparar el plugin y su marketplace, cuyo formato está pendiente de verificar.
- **Q06:** el primer recorrido es más motivador y más realista (UI más lógica). A cambio, la decisión técnica sobre iOS en Windows pesa desde el principio.
- **Q07:** el diseño es más simple, sin clasificación por proyecto. Lo profesional queda explícitamente fuera de v1.
- **Q08 y Q09:** las rutas quedan estables, y el progreso tiene una sola fuente visible desde el PC y el móvil.

## 5. Validación

- El primer recorrido usa la plantilla y el plugin tal como quedan aquí.
- La continuidad de una sesión interrumpida se prueba al menos una vez con `.tareas/`.

## 6. Seguimiento

- Q04 sigue abierta.
- El ADR técnico de la app decidirá cómo se desarrolla y prueba en iOS desde Windows.
- Antes de usar un modelo de Go, revisar su retención y su política de entrenamiento.

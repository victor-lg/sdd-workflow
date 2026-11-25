---
description: "ADR-0009 §3.1 (sdd-review, VIC-60): un R1 que no toca rutas de CODEOWNERS, con la CI y G4 en verde y sin checks pendientes, en un repo con el auto-merge y el ruleset del ADR-0009: el agente pide el auto-merge."
tags: [ADR-0009, VIC-60, sdd-review, auto-merge]
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

El PR #88 de `calculadora-discos` (VIC-63) ya no está en borrador y la CI ha terminado. Haz lo que toque ahora según el workflow para cerrarlo. En esta sesión no tienes Bash, así que las órdenes las lanzo yo.

**PR #88** `feat(peso): suma el peso de los discos externos`, código, riesgo **R1** (marcado y calculado). Ficheros: `src/peso.js`, `tests/peso.test.js`. En el repo están el auto-merge y el ruleset del ADR-0009 (`checks-sdd` requerido y revisión de CODEOWNERS obligatoria).

`.github/CODEOWNERS` de `main` (sin comentarios):

```
/docs/specs/    @victor-lg
/docs/adr/      @victor-lg
/.github/       @victor-lg
/.claude/       @victor-lg
/AGENTS.md      @victor-lg
/CLAUDE.md      @victor-lg
package.json    @victor-lg
package-lock.json @victor-lg
lefthook.json   @victor-lg
stryker.config.json @victor-lg
```

G4: una ronda, revisor A, con `Commit revisado` sobre la cabeza actual; su único hallazgo, *menor*, está descartado. Nadie ha enviado reviews en GitHub.

`gh pr checks 88`, sobre el último commit:

```
checks-sdd        pass
tests             pass
mutaciones        pass
codigo-sobrante   pass
duplicados        pass
seguridad         pass
```

El resumen de `checks-sdd` dice: `g4` ✔ (ronda 1, 1 revisor de 1), `hallazgos` ✔, `cambios` ✔ (nada tras la última ronda), `cambios-pedidos` ✔, `cabeza` ✔; `aprobacion` no aplica (R1).

Dime qué lanzo ahora. Termina tu respuesta con una sola línea `ORDEN: ` seguida de la orden exacta, o `ORDEN: NINGUNA` si no hay que lanzar nada.

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
- `evals/`: casos de `claude plugin eval` (M35), uno por directorio. Corren en la CI del workflow al fusionar en `main`. En local: `claude plugin eval . --ablation none --no-publish` (sin `--no-publish`, el informe con las transcripciones se publica en claude.ai).

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

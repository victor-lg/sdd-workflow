@AGENTS.md

<!-- BORRADOR del workflow SDD + IA v0.7. Solo lo específico de Claude Code; lo portable va en AGENTS.md. -->

## Específico de Claude Code

- Los procedimientos del workflow (skills `sdd-*`) y el subagente `reviewer` llegan con el plugin `sdd`. Úsalos en lugar de improvisar el proceso.
- La revisión (G4) la hace el subagente `reviewer` con contexto limpio. Pásale solo la spec, el diff y los resultados de la CI, nunca tu razonamiento ni tus conclusiones.
- Cuando se exigen dos revisores (specs R1, todo R2), lanza dos invocaciones independientes del revisor. Ninguna ve el resultado de la otra; reconcilia sus hallazgos después, en el PR.

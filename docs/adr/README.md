# Decisiones del workflow (ADR)

Aquí se registran las decisiones sobre el propio workflow, una por fichero, cuando se cierran las preguntas Q01–Q09 de la línea base o cualquier decisión posterior.

- **Nombre:** `NNNN-titulo-corto.md`, numeración correlativa desde `0001`. Los números no se reutilizan.
- **Plantilla:** la misma que la de los proyectos, `plantilla-proyecto/docs/adr/_plantilla-adr.md`.
- **Origen:** cada ADR cita la pregunta Q que cierra o la evidencia que lo motiva (métrica, fallo, retrospectiva).
- **Inmutabilidad:** un ADR aceptado no se edita. Si cambia entero, se crea otro que lo sustituye y se enlazan ambos. Si cambia en parte, el nuevo lo declara en su campo `modifica` y el índice lo anota.

## Índice

- **ADR-0001** — Capa normativa del workflow (cierra Q01). Aceptado el 2026-10-19. Su laguna L9 la modifica ADR-0004.
- **ADR-0002** — Ejecutor y perfiles de modelo (cierra Q02). Aceptado el 2026-10-19. Su regla de datos la modifica ADR-0004.
- **ADR-0003** — Plataforma, seguimiento de entregas y uso del móvil (cierra Q03). Aceptado el 2026-10-19. Su regla de datos la modifica ADR-0004.
- **ADR-0004** — Distribución del núcleo, primer recorrido, datos, rutas y progreso de tareas (cierra Q05–Q09). Aceptado el 2026-10-19.
- **ADR-0005** — Identidad del agente en GitHub (cierra Q04). Aceptado el 2026-10-19.

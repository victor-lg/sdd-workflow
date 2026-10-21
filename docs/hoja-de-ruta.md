# Hoja de ruta del workflow

**Estado:** BORRADOR · **Última revisión:** 2026-10-19 · **Versión actual del workflow:** v0.8 (diseño)

El camino hasta v1.0 tiene cinco fases. Las tres primeras pueden solaparse; la cuarta necesita las anteriores terminadas.

```
 A. Decidir      B. Escribir el kit     C. Preparar entorno     D. Primer recorrido     E. Retro
 Q01-Q09   --->  mínimo (borradores) -> (PC, GitHub, iPhone) -> (app + N1-N8)     ---> v1.0 declarada
 (conversación)  (Claude)               (tú, con guía)          (juntos)               mejoras v1.x
```

## A. Decidir (en la conversación, de una en una)

Bloquean la preparación del entorno:

- [x] **Q01** — Capa normativa. Cerrada → `docs/adr/0001-capa-normativa.md`.
- [x] **Q02** — Ejecutor y perfiles de modelo. Cerrada → `docs/adr/0002-ejecutor-y-perfiles-de-modelo.md`.
- [x] **Q03** — Plataforma y seguimiento: GitHub + Linear. Cerrada → `docs/adr/0003-plataforma-y-seguimiento.md`.

Tienen recomendación por defecto y se pueden aceptar en bloque:

- [x] **Q04** — Identidad del agente: cuenta de máquina con token clásico. Cerrada → ADR-0005.
- [x] **Q05** — Núcleo híbrido: plantilla + plugin. Cerrada → ADR-0004.
- [x] **Q06** — Primer recorrido: calculadora de discos iOS. Cerrada → ADR-0004.
- [x] **Q07** — Una sola vía de datos; entorno profesional aplazado. Cerrada → ADR-0004.
- [x] **Q08** — Rutas `docs/specs/` y `docs/adr/`. Cerrada → ADR-0004.
- [x] **Q09** — Progreso: Linear + PR borrador + `.tareas/`. Cerrada → ADR-0004.

Cada decisión cerrada genera un ADR en `docs/adr/` y una línea en `CHANGELOG.md`.

## B. Escribir el kit mínimo (lo hace Claude; tú revisas)

Los borradores ya escritos en `plantilla-proyecto/` están marcados con ✔.

- [x] `AGENTS.md` y `CLAUDE.md` ✔ (pendiente de ajustar rutas tras Q08)
- [x] Plantilla y ejemplo de spec ✔
- [x] Plantilla de ADR ✔
- [x] Plantilla de PR ✔
- [x] Skill `sdd-spec` ✔
- [x] Plantillas de `README.md` (rutas sensibles y etapa), `docs/vision.md` y `.gitignore` ✔
- [x] Esqueleto del plugin `plugin-sdd/` con `sdd-spec` ✔ (el formato del manifiesto, pendiente de verificar)
- [x] Marketplace del plugin: el propio repo del workflow (`.claude-plugin/marketplace.json`), validado e instalado con Claude Code 2.1.303 ✔ (subirlo a GitHub es la fase C)
- [x] Skill `sdd-context` (a partir de las reglas de RAG de las notas)
- [x] Skill `sdd-discover` (entrevista guiada; D01, D02)
- [x] Skill `sdd-plan` (issue Ready, comprobación de G2)
- [x] Skill `sdd-implement` (tests desde AC, checkpoint de tareas largas)
- [x] Skill `sdd-review` y subagente `reviewer.md` (G4, contexto limpio) ✔
- [x] Plantilla de issue (para Linear: `docs/plantilla-issue-linear.md`) ✔
- [x] CI: checks de specs, mezcla spec/código, trazabilidad AC ↔ tests (G3) y nivel de riesgo ✔ (los tests del stack llegan con el ADR técnico del primer recorrido)
- [x] `CODEOWNERS` ✔
- [x] Ajustes de Claude Code: gestionados (sandbox estricto, credenciales, permisos) y de usuario, en `entorno/` ✔; perfil Go en `entorno/claude-go.sh` ✔
- [x] Guía de instalación paso a paso: `docs/guia-instalacion.md` ✔ (sirve también para H19)
- [x] Registro de herramientas aprobadas: `docs/herramientas.md` ✔

Se dejan para v1.x: `sdd-adr`, `sdd-bugfix`, guía de testing avanzado y `sdd-multimodal`.

## C. Preparar el entorno (lo haces tú, siguiendo `docs/guia-instalacion.md`)

- [x] WSL2 con Ubuntu en Windows 11 ✔
- [x] Claude Code dentro de WSL2, con ajustes gestionados y sandbox verificado (escritura, red y señuelo); plugin `sdd` instalado ✔
- [ ] Contratar OpenCode Go y configurar el perfil Go (`claude-go`); confirmar la URL base y revisar la retención de cada modelo. Ya se sabe que Remote Control no funciona en esa sesión.
- [x] Cuenta de máquina `victor-lg-bot` en GitHub ✔; invitarla como colaboradora en el repo del recorrido y en el del workflow (en repos personales siempre con escritura; el `main` del workflow queda protegido con un ruleset); token clásico con `repo` + `read:org`, sin `workflow`, caducidad de 90 días.
- [x] Repo `calculadora-discos`, con ruleset de `main` (PR, 1 aprobación, CODEOWNERS, `checks-sdd` obligatorio) ✔. PR #1 de prueba: abierto por el agente desde el sandbox, CI en verde, fusionado por ti.
- [x] Workspace de Linear (team VIC, estados D21, plantilla "Entrega SDD", proyecto "Calculadora de discos"), integración con GitHub (automatizaciones de estado, ramas `vic-123-titulo`, app limitada a `calculadora-discos`) y MCP de Linear en solo lectura: lee issues y no puede moverlas ✔
- [ ] App de Claude (Remote Control), GitHub Mobile y Linear en el iPhone.
- [x] Repo del workflow en GitHub (privado), que es también el marketplace del plugin ✔

## D. Primer recorrido

- [ ] Camino feliz completo (sección 11 de la línea base).
- [ ] Casos negativos N1–N8 bloqueados. Adelantados en la fase C: **N4** (el agente no puede fusionar: "base branch policy prohibits the merge") y **N5** (el token rechaza `.github/workflows/`: "without `workflow` scope") ✔; **N6**, parcial (credenciales ocultas con un señuelo).
- [ ] Las cuatro métricas anotadas.

## E. Retrospectiva y declaración de v1.0

- [ ] Qué funcionó, qué estorbó, qué faltó.
- [ ] Ajustes pequeños aplicados.
- [ ] Revisión independiente: una sesión nueva o un subagente sin este historial revisa la trazabilidad, el primer recorrido y N1–N8; sus hallazgos se resuelven.
- [ ] v1.0 declarada en `CHANGELOG.md`.
- [ ] Lista de mejoras candidatas para v1.1, cada una con la evidencia que la justifica.

## Después de v1.0: cómo se mejora

1. Se usa en un proyecto real.
2. Se anota lo observado: métricas, fallos, fricciones.
3. Una mejora entra solo si responde a algo observado o a un disparador de la sección 10.
4. Cada mejora: ADR, prueba con los casos negativos y entrada en el changelog.
5. Retrospectiva corta al final de cada proyecto.

Las capacidades aparcadas (Linear, Notion, multiagente, RAG, multimodal, feedback de producción, observabilidad, backups y versión profesional) forman el backlog natural de v1.x.

# Hoja de ruta del workflow

**Estado:** BORRADOR · **Última revisión:** 2026-10-23 · **Versión actual del workflow:** v0.22 (fase E)

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

- [x] `AGENTS.md` y `CLAUDE.md` ✔
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
- [ ] ~~Perfil Go~~: aplazado a la v1.1 (ADR-0006). Al activarlo: contratar OpenCode Go, confirmar la URL base, revisar la retención de cada modelo y pasar N1–N8 en ese perfil.
- [x] Cuenta de máquina `victor-lg-bot` en GitHub ✔; invitarla como colaboradora en el repo del recorrido y en el del workflow (en repos personales siempre con escritura; el `main` del workflow queda protegido con un ruleset); token clásico con `repo` + `read:org`, sin `workflow`, caducidad de 90 días.
- [x] Repo `calculadora-discos`, con ruleset de `main` (PR, 1 aprobación, CODEOWNERS, `checks-sdd` obligatorio) ✔. PR #1 de prueba: abierto por el agente desde el sandbox, CI en verde, fusionado por ti.
- [x] Workspace de Linear (team VIC, estados D21, plantilla "Entrega SDD", proyecto "Calculadora de discos"), integración con GitHub (automatizaciones de estado, ramas `vic-123-titulo`, app limitada a `calculadora-discos`) y MCP de Linear en solo lectura: lee issues y no puede moverlas ✔
- [x] App de Claude (Remote Control), GitHub Mobile y Linear en el iPhone ✔. Sesión vista y manejada desde el móvil; permiso `ask` (`npm install`) notificado y denegado desde el móvil. Falta aprobar y fusionar desde GitHub Mobile: se hace con el PR de la spec en la fase D.
- [x] Repo del workflow en GitHub (privado), que es también el marketplace del plugin ✔

## D. Primer recorrido

- [x] Camino feliz completo (sección 11 de la línea base) ✔ 2026-10-22: de la spec a la app publicada y probada en el iPhone.
- [x] Casos negativos N1–N8 bloqueados ✔ (2026-10-23). Fase C: N4, N5, N6 (sandbox con señuelo). Fase D: N1 (VIC-7), N2 (VIC-6), N3 (PR #5), N7 (PR #5), N8 (PR #11). N6 por la vía de la inyección: bloqueado por las salvaguardas del modelo antes de actuar; el detalle está en `historial/recorrido-1.md`.
- [x] Las cuatro métricas anotadas ✔ `historial/recorrido-1.md` y `historial/retrospectiva-1.md`.

## E. Retrospectiva y declaración de v1.0

- [x] Qué funcionó, qué estorbó, qué faltó ✔ `historial/retrospectiva-1.md`.
- [x] Ajustes pequeños aplicados ✔ v0.21 (interacciones entre reglas, rondas, diseño de pruebas, cómo revisar un PR).
- [x] Revisión independiente ✔ `historial/revision-independiente-1.md` (31 hallazgos). Resueltos en v0.22 salvo las tres pruebas de C18–C20, que hace Víctor; V1–V7 a la v1.1.
- [ ] v1.0 declarada en `CHANGELOG.md`.
- [x] Lista de mejoras candidatas para v1.1, cada una con la evidencia que la justifica ✔ `historial/retrospectiva-1.md`.

## F. Segundo recorrido (en curso)

- [x] Inventario de discos (VIC-8), CI de E2E arreglada (#15) y cálculo nuevo con datos guardados (VIC-10) ✔
- [x] Rediseño: VIC-13, VIC-11, VIC-14 y VIC-12 ✔ (2026-11-04, probado en el iPhone). Falta SPEC-CALC-003 v0.5 con las aclaraciones de VIC-12.
- [x] Métricas y observaciones en `historial/recorrido-2.md`, con las mejoras candidatas M1–M17 para la v1.1 ✔
- [x] Retrospectiva ✔ `historial/retrospectiva-2.md` (2026-11-04): 17 mejoras a la v1.1, que se aplica después de declarar la v1.0.

## G. v1.1 (en preparación)

Plan por bloques, con el porqué y el "hecho cuando" de cada uno: `docs/plan-v1.1.md`. Empieza al declarar la v1.0 (bloque 0).

## Después de v1.0: cómo se mejora

1. Se usa en un proyecto real.
2. Se anota lo observado: métricas, fallos, fricciones.
3. Una mejora entra solo si responde a algo observado o a un disparador de la sección 10.
4. Cada mejora: ADR, prueba con los casos negativos y entrada en el changelog.
5. Retrospectiva corta al final de cada proyecto.

Las capacidades aparcadas (Linear, Notion, multiagente, RAG, multimodal, feedback de producción, observabilidad, backups y versión profesional) forman el backlog natural de v1.x.

Candidatas anotadas para cuando haga falta (2026-11-04):

- **Observabilidad: PostHog.** Errores de JavaScript en el dispositivo, analítica y grabación de sesiones, con alojamiento en la UE. Hoy choca con la regla de no hacer peticiones a terceros (SPEC-CALC-001 NFR-01 y NFR-02) y, con un solo usuario, aporta poco. Se reconsidera si la app tiene más usuarios o un servidor.
- **Base de datos (por ejemplo, Supabase).** Solo si una funcionalidad necesita sincronizar entre dispositivos o compartir datos. Antes valen el almacenamiento del dispositivo y una copia de seguridad exportable. Exige ADR, rutas sensibles y gestión de secretos fuera del agente.

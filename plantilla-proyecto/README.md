<!--
Plantilla del workflow SDD + IA v1.0. Es la portada del repo: lo primero que
ve quien lo abre (tú dentro de seis meses, una entrevista, un comprador).
Corta y siempre al día; el detalle vive en docs/.
-->

# <Nombre del proyecto>

<!-- Insignias: CI y, si se publica, la versión. Sustituye <usuario>/<repo>. -->
[![sdd](https://github.com/<usuario>/<repo>/actions/workflows/sdd.yml/badge.svg)](https://github.com/<usuario>/<repo>/actions/workflows/sdd.yml)

<Una o dos frases: qué es, para quién y qué problema resuelve. La visión completa está en `docs/vision.md`.>

<!-- Si está publicado: **App:** https://… -->

## Funcionalidad

- <Capacidad> — [`SPEC-XXX-NNN`](docs/specs/SPEC-XXX-NNN-nombre.md)

## Arquitectura

<Tres líneas como máximo: tecnología, cómo se organiza y dónde se publica. El porqué está en los ADR:>

- [`ADR-NNNN`](docs/adr/ADR-NNNN-nombre.md) — <decisión>

## Desarrollo

<!-- Se rellena cuando el proyecto pasa a la etapa técnica. -->

```bash
# requisitos, instalación, ejecutar en local y tests
```

## Cómo se trabaja aquí

Este proyecto sigue un workflow de desarrollo guiado por especificaciones (SDD) con un agente de IA:

- **Qué se construye:** cada comportamiento está en una spec con criterios de aceptación (AC) numerados, aprobada antes de implementarse.
- **Cómo se decide:** las decisiones de arquitectura están en ADR.
- **Cómo se verifica:** cada AC tiene al menos un test que lo cita, y la CI lo comprueba en cada PR.
- **Quién decide:** el código lo escribe un agente desde una cuenta propia, en un sandbox. Los cambios llegan por PR con revisión independiente de IA. Solo una persona aprueba y fusiona en `main`.
- **Historial:** un commit por PR (squash), con títulos en [Conventional Commits](https://www.conventionalcommits.org/).

Las reglas para agentes están en `AGENTS.md`.

## Etapa

documental

<!--
- documental → solo discovery/ y docs/ (visión, specs, ADR); aún no hay tecnología elegida.
- técnica    → existe un ADR que fija la tecnología; hay código, tests y la CI del stack.
No lo lee la CI: es información para quien abre el repo.
-->

## Rutas sensibles

<!--
Todo cambio que toque estas rutas es R2, además de las que ya marca el
workflow (dependencias, .github/, .claude/, AGENTS.md, CLAUDE.md,
migraciones; lista canónica en la línea base, §6). Es la
forma de decir que un componente es delicado. Cambiar esta lista es R2.

Formato que lee la CI: una ruta por línea, entre comillas invertidas, por
ejemplo `src/pagos/` (una carpeta entera) o `src/auth/*.ts`. El `*` también
cruza carpetas. La CI usa la lista que hay en `main`, no la del PR.
-->

- (ninguna todavía)

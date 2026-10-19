<!-- BORRADOR de plantilla del workflow SDD + IA v0.10. -->

# <Nombre del proyecto>

<Una frase sobre qué es. La visión completa está en `docs/vision.md`.>

## Rutas sensibles

<!--
Todo cambio que toque estas rutas es R2, además de las que ya marca el
workflow (dependencias, .github/, .claude/, AGENTS.md, migraciones). Es la
forma de decir que un componente es delicado. Cambiar esta lista es R2.

Formato que lee la CI: una ruta por línea, entre comillas invertidas, por
ejemplo `src/pagos/` (una carpeta entera) o `src/auth/*.ts`. El `*` también
cruza carpetas. La CI usa la lista que hay en `main`, no la del PR.
-->

- (ninguna todavía)

## Etapa

documental

<!--
- documental → solo discovery/ y docs/ (visión, specs, ADR); aún no hay tecnología elegida.
- técnica    → existe un ADR que fija la tecnología; hay src/, tests/ y la CI del stack.
-->

## Cómo se trabaja aquí

Este proyecto sigue el workflow SDD + IA. Las reglas para agentes están en `AGENTS.md`.

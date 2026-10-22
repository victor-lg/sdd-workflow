---
id: ADR-0006
titulo: Ajustes del primer recorrido
estado: Aceptado
fecha: 2026-10-23
sustituye: null
sustituido_por: null
modifica:
  - ADR-0002 (el perfil Go sale de la v1.0)
  - ADR-0003 (MCP de Linear con endpoint de solo lectura, en lugar de reglas de permisos)
  - ADR-0005 (alcance del token, rol de la cuenta de máquina en el repo del workflow y uso del bypass)
referencias:
  - historial/recorrido-1.md
  - historial/retrospectiva-1.md
  - historial/revision-independiente-1.md (B1, B2, C3, C10, C11, C15, C17)
  - CHANGELOG.md (v0.11–v0.21)
---

# ADR-0006 — Ajustes del primer recorrido

## 1. Contexto

Durante la preparación y el primer recorrido (v0.11–v0.21) se tomaron decisiones que cambian ADR aceptados y que solo constaban en el CHANGELOG. La revisión independiente lo señaló (C3), junto con dos bloqueos para la v1.0:

- **B1:** Claude manejó la sesión del usuario en el navegador y movió VIC-5 a *Ready*, que es el gate G2. Ninguna capa distingue ese acto de uno humano.
- **B2:** el perfil Go sigue siendo norma de v1 sin haberse probado nunca.

Este ADR reúne esas decisiones en un solo sitio.

## 2. Decisión

1. **El perfil Go sale de la v1.0** (modifica ADR-0002). La v1.0 tiene un único perfil, la suscripción de Claude. El perfil Go pasa a §10 con un disparador: que el coste de la orquestación con Opus lo justifique. Al activarse, pasa N1–N8 en ese perfil. La validación de ADR-0002 queda en "N1–N8 en el perfil Claude".

2. **Claude con control del navegador ayuda a la persona; no es un agente del workflow.**
   - Puede leer cualquier cosa.
   - Puede escribir solo tres cosas: issues en *Backlog*, comentarios que la persona pida, y los pasos de configuración inicial de la guía, cada uno con permiso explícito.
   - Nunca: pasar una issue a *Ready*, aprobar, fusionar, publicar, ni tocar rulesets, ajustes o tokens. Estos actos los hace la persona con su mano.
   - **Límite aceptado:** ninguna capa técnica lo impide, porque la sesión del navegador es la de la persona. Es una regla, no un control (P04). La herramienta se registra en `docs/herramientas.md`.

3. **Qué afirma la aprobación humana** (v0.18). Afirma que la persona ha comprobado la evidencia y acepta el riesgo residual, no que ha certificado cada línea. Specs, ADR y tests existentes que cambian se leen enteros.

4. **Revisores** (v0.20). El subagente revisor usa Sonnet. En R2, el revisor de seguridad usa Opus. Un PR de ADR lleva 2 revisores, como una spec.

5. **Rondas de revisión** (v0.21). Hasta 3: la inicial y 2 repeticiones. Después decide la persona, y sus aclaraciones se aplican sin otra ronda salvo que añadan reglas de negocio. El encargo literal de cada revisor y su respuesta quedan en el PR.

6. **Gates que dependen del agente.** *Ready* (mitad de G2) y la ejecución de G4 los comprueba el propio agente mediante sus skills, no el sistema. Se acepta como límite. La mitigación es que G4 deje rastro comprobable en el PR (punto 5).

7. **PR de la persona y bypass** (modifica ADR-0005). La persona fusiona sus propios PR (workflows, ajustes) con su excepción de administrador. Los que son R2 pasan antes `sdd-review` con 2 revisores, igual que los del agente. El bypass también sirve para emergencias.

8. **Cuenta de máquina y token** (modifica ADR-0005):
   - El token clásico lleva `repo` y `read:org`, porque `gh auth login` lo exige; nunca `workflow`.
   - En el repo del workflow, la cuenta de máquina es colaboradora con escritura, porque los repos personales no tienen rol de lectura. Por eso `main` lleva un ruleset que le exige PR.

9. **El repo del workflow, hasta la v1.1,** se cambia por commits directos de la persona, que tiene "Always allow". La regla "un cambio en el plugin es R2" (ADR-0004) se aplica desde la v1.1, cuando el workflow se trabaje por PR (retrospectiva #6).

10. **MCP de Linear** (modifica ADR-0003). Se conecta al endpoint de solo lectura, en vez de bloquear las escrituras con reglas de permisos.

## 3. Consecuencias

- La v1.0 se puede declarar sin un perfil sin probar y sin decisiones fuera de los ADR.
- Quedan escritos dos límites que antes estaban implícitos: Claude en el navegador (punto 2) y los gates que dependen del agente (punto 6).
- Los PR R2 de la persona cuestan una revisión más.

## 4. Validación

- Los casos negativos que solo bloqueó el modelo (N1 y N2) se repiten contra la CI del repo real (revisión C18).
- El próximo PR R2 de la persona pasa por `sdd-review`.

---
id: ADR-0003
titulo: Plataforma, seguimiento de entregas y uso del móvil
estado: Aceptado
fecha: 2026-10-19
sustituye: null
sustituido_por: null
referencias:
  - docs/linea-base-v1.md (§5, §7, §8, §10, §11)
  - docs/adr/0001-capa-normativa.md
  - https://linear.app/docs/github
  - https://linear.app/changelog/2025-05-01-mcp
---

# ADR-0003 — Plataforma, seguimiento de entregas y uso del móvil

Cierra la decisión abierta Q03. Aceptada por el usuario el 2026-10-19, junto con dos precisiones suyas: el peso del móvil y el papel de Notion.

## 1. Contexto

- D18–D21 diseñaban el seguimiento de entregas en Linear. La línea base proponía aplazarlo y usar solo GitHub Issues.
- El usuario quiere usar Linear y aprovecharlo donde aporte, sin sobreingeniería.
- Linear tiene una integración nativa con GitHub: enlaza ramas y PRs por el ID de la issue y mueve los estados al abrir, revisar y fusionar. También tiene un MCP oficial para agentes, que no documenta permisos por alcance.

## 2. Alternativas consideradas

### Opción A: GitHub para todo, con GitHub Issues

- Ventajas: un solo sistema, sin reconciliación.
- Inconvenientes: planificación menos cómoda.

### Opción B: GitHub para el código y la autoridad; Linear para planificar

- Ventajas: mejor planificación y captura; la sincronización la hace la integración nativa.
- Inconvenientes: un segundo servicio externo y su conexión MCP.

### Opción C: GitLab

- Inconvenientes: habría que rehacer las reglas de rama, las identidades y la app móvil sin una necesidad que lo justifique.

## 3. Decisión

**Opción B, con el agente en solo lectura sobre Linear.**

- **Linear se usa para:** capturar ideas (Inbox), el backlog y las prioridades, los proyectos por producto, las dependencias entre entregas y los estados de D21. Los ciclos son opcionales.
- **GitHub se usa para:** specs, ADRs, código, PRs, revisión, CI y aprobación. Es la única autoridad (P03, ADR-0001-M2).
- **Los estados se reparten así:**
  - Inbox, Discovery y Ready los mueve la persona. Ready es la decisión humana de que la entrega está lista (G2).
  - In Progress, In Review y Done los mueve la integración Linear–GitHub. La rama y el PR llevan el ID de la issue, y el PR usa "Fixes <ID>".
- **El agente:**
  - Lee la issue y su spec enlazada mediante el MCP oficial. Las escrituras se bloquean con reglas de permisos de Claude Code.
  - Antes de implementar comprueba que la issue está en Ready y que la spec enlazada está en `main`.
- **Specs:** su texto nunca va a Linear, solo el enlace (D13).
- **Datos:** en proyectos `confidencial`, en Linear solo van títulos y enlaces.
- **Uso del móvil:** el trabajo principal se hace en el PC. El iPhone sirve para continuar cuando el usuario está fuera; todo el ciclo debe poder continuarse desde él, pero no está diseñado para hacerse principalmente desde él.
- **Notion:** aplazado, no descartado. La captura de ideas pasa a Linear; Notion se activará solo si hace falta un sitio para investigación larga o material ajeno a cualquier proyecto, y siempre como material de entrada que se traslada a Git.

## 4. Consecuencias

- Beneficios:
  - Planificación cómoda, en el PC y en el móvil.
  - Ninguna sincronización propia que mantener.
  - Sin escrituras inciertas del agente que haya que reconciliar (H15).
- Costes aceptados: un servicio externo más, y una conexión MCP que configurar y restringir.
- Riesgos:
  - Que las reglas de permisos no puedan distinguir bien las herramientas de lectura y escritura del MCP. Se verifica en la preparación; si no se puede, el MCP de Linear no se conecta y el agente recibe la issue a mano.
  - Datos sensibles en Linear. Se mitiga con la regla de datos.

## 5. Validación

- En el primer recorrido, la issue debe pasar sola de In Progress a Done, sin intervención manual tras Ready.
- El caso N1 ampliado: una issue en Ready que enlaza una spec no fusionada se bloquea.
- Al menos una continuación real desde el iPhone.

## 6. Seguimiento

- Las escrituras del agente en Linear (por ejemplo, crear issues en el Inbox con confirmación) quedan aplazadas (§10).
- Notion queda aplazado con su disparador (§10).
- Revisar si las automatizaciones por defecto de Linear encajan tras el primer recorrido.

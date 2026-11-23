---
id: ADR-0009
titulo: El papel de la persona y la autonomía del agente
estado: Propuesto
fecha: 2026-11-23
sustituye: null
sustituido_por: null
modifica:
  - "docs/linea-base-v1.md, P03: aprobar ya no es siempre fusionar a mano; en lo que el agente fusiona solo, la aprobación es la de las reglas de GitHub que el agente no controla (§3.1 y §3.5)"
  - "docs/linea-base-v1.md, G2: la persona ya no mueve cada issue a Ready; da un visto bueno al diseño y a su lista de issues (§3.6)"
  - "docs/linea-base-v1.md, G6: merge humano solo en las rutas sensibles, en R2 y en el repo del workflow (§3.1 a §3.4)"
  - "docs/linea-base-v1.md, N4: lo sustituye la validación de §5 cuando el agente pueda pedir el auto-merge"
  - "docs/linea-base-v1.md §8, modelo de identidades y reglas de main: el agente puede fusionar con auto-merge; 0 aprobaciones generales; CODEOWNERS en la lista de §3.3, sin README.md"
  - "ADR-0001, M2: el merge humano en rama protegida deja de ser el único mecanismo de aprobación"
  - "ADR-0003 §3 y §6: el agente escribe en Linear (crea, comenta y empieza issues); Ready deja de moverlo la persona"
  - "ADR-0005 §1, §3 y §5: «sin permiso para fusionar», «PR obligatorio con una aprobación» y la validación N4"
  - "ADR-0006 §2.6 y §2.10: Ready deja de ser un gate por issue; el MCP de Linear deja de ser de solo lectura"
referencias:
  - "VIC-55"
  - "docs/plan-v1.1.md (bloque 5: M4, M18, M20, M24 y M28)"
  - "historial/retrospectiva-bloque-3.md y historial/retrospectiva-bloque-4.md"
  - "docs/convenciones.md §5.1"
  - "docs/herramientas.md, «Respuestas de G4 en el check hallazgos (VIC-47)»"
  - "historial/defectos-escapados.csv"
---

<!--
Redactado por Claude (VIC-55) con las diez decisiones que Víctor tomó el 2026-11-23, recogidas
tal cual en §3. Las partes que cambia de otros ADR y de la línea base están en `modifica`; el
resto sigue vigente y no se edita.
-->

> No confundir con el ADR-0009 de la calculadora (`calculadora-discos`, «la espera antes de axe…»): cada repo numera sus ADR por separado.

# ADR-0009 — El papel de la persona y la autonomía del agente

## 1. Contexto

- Hoy la persona fusiona cada PR (G6, línea base §8, ADR-0005) y mueve cada issue a *Ready* (G2, ADR-0003). Es un paso a mano en cada entrega, también en las R0 y R1 que no tocan nada sensible.
- Los bloques 2 a 4 pusieron los controles fijos que permiten quitar ese paso donde el riesgo es bajo: checks requeridos en la calculadora (`mutaciones` y `duplicados` incluidos), riesgo que la CI solo puede subir (M3), G4 con rastro comprobable y el check `hallazgos`, y las métricas por entrega y por revisor (`sdd-metricas`, VIC-48).
- El plan (bloque 5) reserva este ADR para tu papel, la escalera de confianza (M24), dejar el chat como sitio de trabajo y lo que hace Claude desde la app (M18).
- Sin decidir, la persona sigue siendo el cuello de botella de cada entrega, y los controles del bloque 3 no se aprovechan.

## 2. Alternativas consideradas

### Opción A: seguir como hoy (la persona fusiona todo)

- Ventajas: una lectura humana de cada PR; ningún cambio de reglas.
- Inconvenientes: el tiempo de la persona se va en PR que los controles ya cubren.
- Riesgos: aprobar por rutina, sin leer, que da la apariencia de control sin el control.

### Opción B: el agente fusiona lo no sensible en R0 y R1, por escalones (M24)

- Ventajas: la persona se queda con lo que necesita juicio (specs, ADR, dependencias, CI, configuración del agente); el agente avanza solo en lo demás.
- Inconvenientes: en lo no sensible desaparece la lectura humana de cada PR (§4).
- Riesgos: un defecto que pasen la CI y G4 llega a `main` sin que nadie lo lea. Se mitiga con la segunda mirada semanal (§3.10) y con el escalón siguiente condicionado a datos (§3.4).

### Opción C: el agente fusiona todo lo que no toque rutas sensibles, R2 incluido

- Inconvenientes: salta un escalón sin datos; en R2 hay dos revisores, pero no una persona.

## 3. Decisión

**Opción B.** Decisiones de Víctor del 2026-11-23, tal cual:

1. **El agente fusiona sin la persona los PR R0 y R1 que no tocan rutas sensibles,** con la CI y G4 en verde (primer escalón de M24).
2. **Empieza solo en la calculadora.** En `sdd-workflow` sigue aprobando la persona.
3. **Rutas sensibles, que siempre aprueba la persona:** specs, ADR, dependencias, `.github/`, la configuración del agente (`.claude/`, `AGENTS.md`, `CLAUDE.md`) y los ficheros que gobiernan los controles (`stryker.config.json`, `knip.json`, `.jscpd.json`, `osv-scanner.toml`, `lefthook.json`). `README.md` sale de la lista de la línea base §8.
4. **Segundo escalón (R2 no sensible): ahora no.** Lo decide la persona tras diez PR fusionados por el agente sin ningún defecto escapado, con los datos de `sdd-metricas`.
5. **Cómo fusiona:** con el auto-merge de GitHub, que solo fusiona si se cumplen las reglas. Ruleset con 0 aprobaciones generales y CODEOWNERS obligatorio en las rutas sensibles.
6. **Linear:** el agente crea y comenta issues y las empieza él. La persona da un único visto bueno, al diseño (la spec) y a la lista de issues que sale de él; ya no mueve cada issue a *Ready*. Cambia lo que decía el plan («salvo *Ready* y *Done*»).
7. **Los ficheros de `.github/` los sube la persona,** con un script desde el clon limpio que comprueba el SHA-256 antes de empujar. El agente sigue sin el permiso `workflow`.
8. **Las evaluaciones del plugin siguen siendo de la persona** (`docs/convenciones.md` §5.1).
9. **Revisores desde otra cuenta: ahora no.** Se resuelve en el bloque 7 con el revisor en la CI (M34), que publica con una identidad que el agente no puede editar. El límite de VIC-47 queda aceptado hasta entonces.
10. **Segunda mirada (M18):** Claude, desde la app, repasa una vez por semana lo que el agente fusionó solo y avisa a la persona de lo que merezca su atención. En los PR sensibles, la persona puede pedirla cuando quiera.

**Lo ya aceptado en el plan, que este ADR recoge sin decidir nada nuevo:**

- **El papel de la persona:** la entrevista y la spec (G1); las decisiones de producto y las lecturas de la spec (M15); la prueba final del producto donde hace falta una persona; publicar.
- **M4:** «Refs» por defecto cuando hay prueba manual; la issue la cierra la persona tras probar.
- **M20:** una sesión por PR, también en entregas partidas, con el estado en `.tareas/`; los subagentes se lanzan solo por un motivo explícito (explorar, verificar de forma independiente o relevar una sesión larga).
- **M28:** la plantilla de la issue de Linear lleva el contrato: alcance, fuera de alcance, cuándo está hecho, ficheros permitidos y qué hacer si se bloquea.

**Este ADR no cambia ningún permiso por sí mismo.** Hasta que la persona aplique el ruleset y CODEOWNERS de la calculadora, y hasta que se cambien el MCP de Linear, sus hooks y las skills, sigue en vigor lo de hoy: la persona aprueba y fusiona cada PR, mueve las issues a *Ready*, y el agente solo lee y comenta en Linear. Cada parte entra en vigor con la issue que la aplica (§6).

## 4. Consecuencias

- **Beneficios:** la persona dedica su tiempo a la spec, las decisiones, lo sensible y la prueba final; las entregas R0 y R1 no esperan por ella.
- **Lo que se pierde:** en lo no sensible ya no hay una lectura humana de cada PR. Ejemplos del 22 y 23 de noviembre de lo que esa lectura puede ver:
  - la orden de las evaluaciones del plugin, preparada para lanzarse desde la copia del agente (hoy lo prohíbe `docs/convenciones.md` §5.1);
  - un ADR que se podía fusionar en estado *Propuesto*;
  - el límite de VIC-47: la cuenta que publica las respuestas de G4 puede borrarlas o editarlas.

  La segunda mirada (§3.10) recupera parte, después y no antes de fusionar.
- **Costes:** la persona aplica el ruleset y CODEOWNERS y sube a mano lo de `.github/` con el script; Claude dedica un repaso semanal.
- **Riesgos y mitigaciones:**
  - **El nivel de riesgo lo declara el agente.** La CI solo lo sube (M3): las rutas sensibles las marca `checks.py` y las bloquea CODEOWNERS. Un PR que el agente declare R1 y sea R2 en el fondo, sin tocar rutas sensibles, se fusiona solo. Lo mitigan G4 y la segunda mirada.
  - **Un R2 que no toca rutas sensibles:** el ruleset de §3.5 (0 aprobaciones y CODEOWNERS por ruta) no lo detiene por sí mismo. Que no se fusione solo (§3.4) es, de momento, una regla del agente; la issue del ruleset decide el control que lo haga cumplir.
  - **G4 depende del agente** (ADR-0006 §2.6): el rastro en el PR y el check `hallazgos` lo hacen comprobable, con el límite de VIC-47 (§3.9).
  - **Escrituras del agente en Linear:** la regla de datos de ADR-0003 (en proyectos `confidencial`, solo títulos y enlaces) sigue en vigor y se aplica también a lo que escriba el agente.
- **Impacto:** el ruleset y CODEOWNERS de la calculadora; el MCP de Linear y `guarda-linear.py`; `sdd-plan`, `sdd-spec`, `sdd-implement` y `sdd-review`; la plantilla de issue y la de PR; la guía de instalación. `sdd-workflow` no cambia de reglas (§3.2).

## 5. Validación

- **Sustituye a N4 y N5 cuando el agente pueda pedir el auto-merge:**
  - el agente no puede fusionar, ni con auto-merge ni a mano, un PR que toque una ruta sensible sin la aprobación de CODEOWNERS;
  - no puede saltarse el ruleset: ni push directo a `main`, ni fusionar con un check requerido en rojo, pendiente o cancelado, ni cambiar el ruleset o CODEOWNERS;
  - no puede modificar `.github/` (su token sigue sin `workflow`, como N5).

  Cada caso se intenta y GitHub lo rechaza. Hacerla es de la issue del ruleset, no de este PR.
- **Escalón 2:** diez PR fusionados por el agente sin ningún defecto escapado (`historial/defectos-escapados.csv`, `sdd-metricas`), y la persona decide.
- **Dejar el chat:** una entrega completa de la calculadora pasa sin copiar nada desde este chat (hecho cuando del bloque 5).

## 6. Seguimiento

- **Issues que salen de este ADR:** las propone el PR de VIC-55 y las aprueba la persona; quedan en `docs/plan-v1.1.md`, bloque 5.
- **Cómo queda el visto bueno del §3.6** (dónde va la lista de issues y qué acto lo aprueba) lo fija la issue de Linear por MCP. Tiene que ser un acto en un sistema que el agente no controla (P03).
- **Revisar este ADR** si un defecto escapa en un PR que el agente fusionó solo, si la segunda mirada encuentra algo que debía haber parado la fusión, o al llegar al revisor en la CI (M34, bloque 7), que cierra el límite de §3.9.

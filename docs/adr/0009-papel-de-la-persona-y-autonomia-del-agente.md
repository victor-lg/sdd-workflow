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
  - "docs/linea-base-v1.md, N4: lo sustituye la validación de §5 cuando el agente pueda pedir el auto-merge; N5 se mantiene"
  - "docs/linea-base-v1.md, H02: el merge que pide el agente con auto-merge no lleva una identidad distinta de la suya; la aprobación es la de las reglas (§3.5)"
  - "docs/linea-base-v1.md §8, modelo de identidades y reglas de main: el agente puede fusionar con auto-merge; 0 aprobaciones generales; CODEOWNERS en la lista de §3.3, que incluye toda la de controles de checks.py; README.md se queda hasta que las rutas sensibles del proyecto pasen a un fichero propio. Se mantienen los checks requeridos sobre el commit exacto y que cada push invalide las aprobaciones anteriores"
  - "ADR-0001, M2: el merge humano en rama protegida deja de ser el único mecanismo de aprobación, y las escrituras del agente en Linear dejan de estar deshabilitadas, con la aprobación de §3.6"
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
3. **Rutas sensibles, que siempre aprueba la persona:** specs, ADR, dependencias, `.github/`, la configuración del agente (`.claude/`, `AGENTS.md`, `CLAUDE.md`) y los ficheros que gobiernan los controles (`stryker.config.json`, `knip.json`, `.jscpd.json`, `osv-scanner.toml`, `lefthook.json`).
4. **Segundo escalón (R2 no sensible): ahora no.** Lo decide la persona tras diez PR fusionados por el agente sin ningún defecto escapado, con los datos de `sdd-metricas`.
5. **Cómo fusiona:** con el auto-merge de GitHub, que solo fusiona si se cumplen las reglas. Ruleset con 0 aprobaciones generales y CODEOWNERS obligatorio en las rutas sensibles.
6. **Linear:** el agente crea y comenta issues y las empieza él. La persona da un único visto bueno, al diseño (la spec) y a la lista de issues que sale de él; ya no mueve cada issue a *Ready*. Cambia lo que decía el plan («salvo *Ready* y *Done*»).
7. **Los ficheros de `.github/` los sube la persona,** con un script desde el clon limpio que comprueba el SHA-256 antes de empujar. El agente sigue sin el permiso `workflow`.
8. **Las evaluaciones del plugin siguen siendo de la persona** (`docs/convenciones.md` §5.1).
9. **Revisores desde otra cuenta: ahora no.** Se resuelve en el bloque 7 con el revisor en la CI (M34), que publica con una identidad que el agente no puede editar. El límite de VIC-47 queda aceptado hasta entonces.
10. **Segunda mirada (M18):** Claude, desde la app, repasa una vez por semana lo que el agente fusionó solo y avisa a la persona de lo que merezca su atención. En los PR sensibles, la persona puede pedirla cuando quiera.

**Aclaraciones de Víctor del 2026-11-23, en la G4 del PR de este ADR:**

- **Decisión 3, los ficheros de control:** los cinco nombrados son ejemplos, no una lista cerrada. CODEOWNERS cubre toda la lista de controles de `checks.py` (`R2_CONTROLES`), capturas de referencia incluidas. Hay una sola lista, la de `checks.py`.
- **Decisión 3, `README.md`:** se queda en CODEOWNERS por ahora, porque en los proyectos es donde se declaran las rutas sensibles que `checks.py` sube a R2. Sale cuando esa declaración pase a un fichero propio que esté en CODEOWNERS.
- **Decisión 1, R0:** un R0 se fusiona con la CI en verde y sin G4 solo si `checks.py` puede comprobar que es R0 (solo documentación). Si el R0 lo declara el agente y nada lo verifica, cuenta como R1 y lleva G4. **Hoy es el segundo caso:** `checks.py` no comprueba que un R0 sea solo documentación. Si un PR marcado R0 toca código, da un aviso, no un fallo (`check_riesgo`).
- **La segunda mirada (decisión 10)** la monta Claude desde la app cuando el agente empiece a fusionar, sin issue propia.

**Lo ya aceptado en el plan, que este ADR recoge sin decidir nada nuevo:**

- **El papel de la persona:** la entrevista y la spec (G1); las decisiones de producto y las lecturas de la spec (M15); la prueba final del producto donde hace falta una persona; publicar.
- **M4:** «Refs» por defecto cuando hay prueba manual; la issue la cierra la persona tras probar.
- **M20:** una sesión por PR, también en entregas partidas, con el estado en `.tareas/`; los subagentes se lanzan solo por un motivo explícito (explorar, verificar de forma independiente o relevar una sesión larga).
- **M28:** la plantilla de la issue de Linear lleva el contrato: alcance, fuera de alcance, cuándo está hecho, ficheros permitidos y qué hacer si se bloquea.
- **Dejar el chat:** el agente de WSL es el único sitio de trabajo. GitHub, con `gh`, como ahora. La fuente de verdad es el repo, no el Project. La app queda para el diseño visual y la exploración (y para la segunda mirada, §3.10).

**Cómo se aprueba el visto bueno de §3.6** (ADR-0001, M2, pide que un ADR diseñe la aprobación de una escritura externa): es un acto en GitHub que el agente no controla, un merge en rama protegida o una review de PR (P03). No puede ser un estado, una etiqueta ni un comentario de Linear, porque con el MCP de escritura el agente los puede cambiar. Dónde va la lista de issues dentro de ese acto lo fija la issue de Linear por MCP.

**Este ADR no cambia ningún permiso por sí mismo.** Hasta que la persona aplique el ruleset y CODEOWNERS de la calculadora, y hasta que se cambien el MCP de Linear, sus hooks y las skills, sigue en vigor lo de hoy: la persona aprueba y fusiona cada PR, mueve las issues a *Ready*, y el agente solo lee y comenta en Linear. Cada parte entra en vigor con la issue que la aplica (§6).

## 4. Consecuencias

- **Beneficios:** la persona dedica su tiempo a la spec, las decisiones, lo sensible y la prueba final; las entregas R0 y R1 no esperan por ella.
- **Lo que se pierde:** en lo no sensible ya no hay una lectura humana de cada PR. Ejemplos del 22 y 23 de noviembre de lo que esa lectura puede ver:
  - la orden de las evaluaciones del plugin, preparada para lanzarse desde la copia del agente (hoy lo prohíbe `docs/convenciones.md` §5.1);
  - un ADR que se podía fusionar en estado *Propuesto*;
  - el límite de VIC-47: la cuenta que publica las respuestas de G4 puede borrarlas o editarlas.

  Y un control que la línea base asigna a la persona en cada PR: leer todo cambio en un test existente (lista de cinco minutos, punto 1), la defensa contra un test debilitado para pasar la CI. En lo que el agente fusiona solo lo sustituyen el check `mutaciones`, que falla si los tests dejan de matar mutantes, y la pregunta expresa de G4 por los tests debilitados; ninguno lee la intención del cambio.

  La segunda mirada (§3.10) recupera parte, después y no antes de fusionar.
- **Costes:** la persona aplica el ruleset y CODEOWNERS y sube a mano lo de `.github/` con el script; Claude dedica un repaso semanal.
- **Riesgos y mitigaciones:**
  - **El nivel de riesgo lo declara el agente.** La CI solo lo sube (M3): `checks.py` marca R2 lo que toca sus listas (entre ellas, las rutas sensibles que el proyecto declara en su README), y CODEOWNERS bloquea las de §3.3. No son el mismo conjunto: un PR que toca una ruta del README del proyecto es R2 por la CI y no entra en el primer escalón, pero solo CODEOWNERS lo detiene si la ruta está también en §3.3. Un PR que el agente declare R1 y sea R2 en el fondo, sin tocar rutas sensibles, se fusiona solo. Lo mitigan G4 y la segunda mirada.
  - **Un R2 que no toca rutas de CODEOWNERS:** el ruleset de §3.5 (0 aprobaciones y CODEOWNERS por ruta) no lo detiene por sí mismo, y sin otro control la decisión 4 quedaría en una regla del agente (P04). La issue del ruleset pone el control que lo haga cumplir, y §5 lo valida.
  - **G4 depende del agente** (ADR-0006 §2.6): el rastro en el PR y el check `hallazgos` lo hacen comprobable, con el límite de VIC-47 (§3.9).
  - **Escrituras del agente en Linear:** la regla de datos de ADR-0003 (en proyectos `confidencial`, solo títulos y enlaces) sigue en vigor y se aplica también a lo que escriba el agente.
- **Impacto:** el ruleset y CODEOWNERS de la calculadora; el MCP de Linear y `guarda-linear.py`; `sdd-plan`, `sdd-spec`, `sdd-implement` y `sdd-review`; la plantilla de issue y la de PR; la guía de instalación. `sdd-workflow` no cambia de reglas (§3.2).

## 5. Validación

- **Sustituye a N4, y mantiene N5, cuando el agente pueda pedir el auto-merge:**
  - el agente no puede fusionar, ni con auto-merge ni a mano, un PR que toque una ruta sensible sin la aprobación de CODEOWNERS;
  - un push del agente después de esa aprobación la invalida, y el PR no se fusiona hasta que la persona apruebe de nuevo;
  - no puede fusionar solo un PR R2, aunque no toque rutas de CODEOWNERS (§3.4);
  - no puede saltarse el ruleset: ni push directo a `main`, ni fusionar con un check requerido en rojo, pendiente o cancelado, ni cambiar el ruleset o CODEOWNERS;
  - no puede modificar `.github/workflows/` (su token sigue sin `workflow`: N5, sin cambios).

  Cada caso se intenta y GitHub lo rechaza. Hacerla es de la issue del ruleset, no de este PR.
- **Escalón 2:** diez PR fusionados por el agente sin ningún defecto escapado (`historial/defectos-escapados.csv`, `sdd-metricas`), y la persona decide.
- **Dejar el chat:** una entrega completa de la calculadora pasa sin copiar nada desde este chat (hecho cuando del bloque 5).

## 6. Seguimiento

- **Issues que salen de este ADR:** las propone el PR de VIC-55 y las aprueba la persona; quedan en `docs/plan-v1.1.md`, bloque 5.
- **Dónde va la lista de issues** dentro del acto que aprueba el visto bueno de §3.6 lo fija la issue de Linear por MCP.
- **Revisar este ADR** si un defecto escapa en un PR que el agente fusionó solo, si la segunda mirada encuentra algo que debía haber parado la fusión, o al llegar al revisor en la CI (M34, bloque 7), que cierra el límite de §3.9.

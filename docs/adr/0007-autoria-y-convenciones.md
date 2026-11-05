---
id: ADR-0007
titulo: Autoría de los commits y convenciones de nombres
estado: Propuesto
fecha: 2026-11-05
sustituye: null
sustituido_por: null
modifica:
  - "docs/linea-base-v1.md §7, Convenciones de GitHub (v0.18): autoría, títulos de PR, ramas, mensaje del squash y commits de rama"
referencias:
  - "docs/plan-v1.1.md (bloque 1: Autoría y M42; el ADR de autonomía pasa a ADR-0008 y el de modelos a ADR-0009)"
  - "docs/convenciones.md (M42)"
  - "docs/linea-base-v1.md §8 (modelo de identidades)"
  - "docs/adr/0005-identidad-del-agente.md"
  - "calculadora-discos#37 (autor del squash de un PR del agente)"
  - "VIC-16"
---

# ADR-0007 — Autoría de los commits y convenciones de nombres

## 1. Contexto

- La §7 de la línea base (v0.18) dice:
  - "**Autoría transparente:** los commits del agente llevan `Co-Authored-By`";
  - títulos de PR "con el ID como alcance" (`feat(VIC-5): …`);
  - ramas `vic-N-…` para entregas y `spec-<id>-…`, `adr-NNNN-…`, `ci-…` y `chore-…` para lo demás, sin ID;
  - "Fusión solo por squash, con el título del PR como mensaje";
  - commits dentro de una rama con el "mismo formato, en imperativo y en una línea".
- El plan de la v1.1 decide quitar las menciones a Claude de commits y PR y adoptar `docs/convenciones.md` (M42): el mismo tipo en la etiqueta de Linear, la rama, el commit y el PR, y el ID siempre presente.
- **Hecho comprobado:** en un squash, GitHub pone como autor del commit de `main` a quien abrió el PR, y añade un `Co-authored-by` por cada autor distinto de los commits de la rama. En calculadora-discos#37, abierto por la cuenta de máquina, el squash quedó con autor `victor-lg-bot` y `Co-authored-by: Claude Opus 5.5`.
- La línea base está aceptada: sin este ADR, `convenciones.md` y la §7 se contradirían.
- El plan reservaba el número 0007 al ADR de autonomía del bloque 5 (que recoge también M18). Como esta decisión llega antes, el de autonomía pasa a ADR-0008 y el de modelos a ADR-0009. La retrospectiva 2, que es histórica, sigue citando el número antiguo.

## 2. Alternativas consideradas

### Autoría

- **A1, mantener `Co-Authored-By`:** cada commit de `main` nombra al modelo concreto que lo escribió. Es el texto que el plan quita, y además depende del modelo de cada sesión.
- **A2, autoría de Víctor:** se descarta. Por el hecho comprobado, el squash lo firma quien abre el PR. Para que lo firmara Víctor, él tendría que abrir los PR, y entonces no podría aprobarlos (§8 de la línea base), o habría que dejar el squash. Con los commits de rama a su nombre, `main` quedaría con el agente como autor y Víctor como coautor: una autoría mixta que no aporta nada.
- **A3, autoría de la cuenta de máquina, sin menciones a Claude:** el agente ya es esa identidad en GitHub (ADR-0005), y `main` distingue lo que hizo sin nombrar un modelo.

### Convenciones

- **C1, mantener la §7:**
  - el ID ocupa el alcance, que deja de servir para la zona del código;
  - las ramas de spec, ADR y CI van sin ID, así que Linear no las enlaza y `sdd-metricas` no las atribuye a ninguna issue (M11).
- **C2, `convenciones.md` como norma:** un solo vocabulario en Linear, ramas, commits y PR, y una única fuente.

## 3. Decisión

Se eligen A3 y C2. En la §7 de la línea base:

1. **"Autoría transparente" se sustituye por "commits con la autoría de la cuenta de máquina del agente y sin menciones a Claude".**
   - Ni commits ni PR llevan `Co-Authored-By` ni "Generated with" de Claude.
   - Todos los commits que el agente crea en una rama llevan la identidad de Git de la cuenta de máquina. Si un commit lleva otra identidad, GitHub la añade como coautora en `main`.
   - El PR lo abre esa misma cuenta, así que el squash de `main` queda a su nombre. El flujo de aprobación de la §8 no cambia: el autor del PR es el agente y Víctor lo aprueba y lo fusiona (G6).
2. **Trazabilidad.** El autor de cada commit de `main` dice si lo hizo el agente. Las sesiones (rama, issue, modelos y coste) quedan en `sdd-metricas`, y la revisión G4 deja su rastro en el PR (ADR-0006). Qué modelo escribió el código se consulta ahí, no en el commit.
3. **Las convenciones de nombres y mensajes son las de `docs/convenciones.md`,** que pasa a ser norma y sustituye en la §7:
   - las ramas, `<tipo>/vic-<N>-<descripcion>`;
   - los títulos de PR, en Conventional Commits, con el alcance como zona y no como ID;
   - los commits de rama, con cuerpo opcional y `Refs: VIC-N` en el pie;
   - el mensaje del squash, "Pull request title and commit details" (ajuste del repo que hace la persona, ADR-0006);
   - los títulos de issue y las versiones.

   La §7 remite a ese documento en vez de repetirlo.
4. **Cómo se cambian las convenciones.** `convenciones.md` se cambia por PR sin ADR. Un cambio que contradiga un ADR aceptado o la línea base (salvo la parte de la §7 que remite aquí) necesita antes un ADR.
5. **Entrada en vigor.**
   - **La parte de autoría rige desde que se fusione este ADR:** el agente no añade menciones a Claude aunque `AGENTS.md` aún lo pida. El check `validar` ya lo exige.
   - **Las convenciones** rigen al fusionarse el PR de VIC-16 que aplica este ADR. Ese PR actualiza `AGENTS.md`, la plantilla de PR, las skills, la §7 de la línea base y el estado de `convenciones.md`, dentro del bloque 1.
   - El historial ya escrito no se toca.

## 4. Consecuencias

- `AGENTS.md`, la plantilla de PR, `sdd-plan`, `sdd-spec`, la §7 de la línea base y la guía de instalación remiten a `convenciones.md`. `sdd-metricas.py` lee el ID con el formato nuevo sin perder el antiguo.
- La plantilla de PR pierde el apartado "Perfil y modelo", porque los modelos de cada sesión ya los guarda `sdd-metricas`.
- La identidad de Git del entorno del agente es la de la cuenta de máquina. Un commit hecho con otra identidad se nota en `main` como coautoría.
- Mientras no haya comprobación automática (M11 en el bloque 2 y M33 en el bloque 3), el formato depende de que el agente lo siga. El check `validar` del repo del workflow rechaza los `Co-Authored-By` y los "Generated with" de Claude en los mensajes de commit. No comprueba la descripción del PR ni otras menciones.

## 5. Validación

En el primer PR del workflow que el agente abra después de que este ADR se fusione:

- **Pasa si:**
  - `validar` está en verde;
  - el commit de squash en `main` tiene como autor la cuenta de máquina y no lleva `Co-authored-by` de Claude ni de otra identidad;
  - la descripción del PR no menciona a Claude;
  - Víctor aprueba y fusiona el PR sin usar el bypass.
- Tras el PR que aplica las convenciones, `resumen-metricas.py` atribuye a VIC-16 las sesiones de las ramas `tipo/vic-16-…`.
- El resultado se anota en el PR y en la entrada del CHANGELOG de la versión.

## 6. Seguimiento

- Si un día hace falta que los commits de `main` lleven la autoría de la persona, se necesita un ADR que revise a la vez este y el modelo de identidades (ADR-0005 y §8).
- Si aparece otro ejecutor (bloque 7), usa la misma cuenta de máquina y las mismas reglas.

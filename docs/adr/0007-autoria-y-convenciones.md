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
  - "VIC-16"
---

# ADR-0007 — Autoría de los commits y convenciones de nombres

## 1. Contexto

- La §7 de la línea base (v0.18) fija cuatro cosas que el bloque 1 de la v1.1 cambia:
  - **Autoría transparente:** los commits del agente llevan `Co-Authored-By`.
  - **Nombres:** títulos con el ID como alcance (`feat(VIC-5): …`) y ramas sin tipo y, fuera de las entregas, sin ID (`vic-N-…`, `spec-<id>-…`, `adr-NNNN-…`, `ci-…`, `chore-…`).
  - **Squash** con el título del PR como único mensaje.
  - **Commits de rama** en una sola línea.
- El plan de la v1.1 decide quitar las menciones a Claude de commits y PR y adoptar `docs/convenciones.md` (M42): el mismo tipo en la etiqueta de Linear, la rama, el commit y el PR, y el ID siempre presente.
- La línea base está aceptada: sin este ADR, `convenciones.md` y la §7 se contradirían.
- El plan reservaba el número 0007 al ADR de autonomía del bloque 5 (que recoge también M18). Como esta decisión llega antes, el de autonomía pasa a ADR-0008 y el de modelos a ADR-0009. La retrospectiva 2, que es histórica, sigue citando el número antiguo.

## 2. Alternativas consideradas

### Opción A: mantener la §7 tal como está

- Ventajas: ningún cambio.
- Inconvenientes:
  - el ID ocupa el alcance, que deja de servir para la zona del código;
  - las ramas de spec, ADR y CI van sin ID, así que Linear no las enlaza y `sdd-metricas` no las atribuye a ninguna issue (M11);
  - cada commit de `main` nombra al agente, aunque quien lo aprueba, lo fusiona y responde de él es la persona.

### Opción B: autoría de Víctor y `convenciones.md` como norma

- Ventajas: un solo vocabulario en Linear, ramas, commits y PR, y una única fuente para los nombres.
- Inconvenientes: los commits de `main` ya no distinguen el trabajo del agente. Eso queda en el PR y en las métricas (§3).
- Riesgos: que el formato nuevo no se cumpla hasta que lo compruebe una máquina (bloques 2 y 3).

## 3. Decisión

Se elige la opción B. En la §7 de la línea base:

1. **"Autoría transparente" se sustituye por "commits con la autoría de Víctor y sin menciones a Claude".**
   - No hay `Co-Authored-By` ni "Generated with" en commits ni en PR. Los ajustes de usuario de Claude Code los desactivan (`attribution`).
   - Los commits que hace el agente llevan como autor la identidad de Git de Víctor, configurada en el entorno del agente (`user.name` y `user.email`, o las variables `GIT_AUTHOR_*`).
   - El commit que cuenta es el squash de `main`. Que su autor sea Víctor se comprueba en el primer PR (§5).
   - El PR lo sigue abriendo la cuenta de máquina (ADR-0005), así que el flujo de aprobación de la §8 de la línea base no cambia: el autor del PR es el agente y Víctor puede aprobarlo.
   - Motivo: la persona es quien aprueba, fusiona y responde de lo que llega a `main` (G6).
2. **Trazabilidad del agente.** Se apoya en lo que sí queda registrado, no en el mensaje del commit:
   - la cuenta de máquina figura como autora del PR, y el historial del PR muestra quién empujó cada commit;
   - las sesiones del agente quedan en `sdd-metricas`, con su rama, su issue, sus modelos y su coste;
   - la revisión G4 deja su rastro en el PR (ADR-0006).
3. **Las convenciones de nombres y mensajes son las de `docs/convenciones.md`,** que pasa a ser norma y sustituye en la §7:
   - las ramas, `<tipo>/vic-<N>-<descripcion>`;
   - los títulos de PR, en Conventional Commits, con el alcance como zona y no como ID;
   - los commits de rama, con cuerpo opcional y `Refs: VIC-N` en el pie;
   - el mensaje del squash, "Pull request title and commit details" (ajuste del repo que hace la persona, ADR-0006);
   - los títulos de issue y las versiones.

   La §7 remite a ese documento en vez de repetirlo.
4. **Cómo se cambian las convenciones.** `convenciones.md` se cambia por PR sin ADR nuevo, siempre que el cambio no contradiga un ADR aceptado ni altere un gate o la autoría. Si lo hace, necesita un ADR.
5. **Entrada en vigor.** Al fusionarse el PR que aplica este ADR en VIC-16 (`AGENTS.md`, plantilla de PR, skills, §7 de la línea base y estado de `convenciones.md`). Hasta entonces siguen la §7 y `AGENTS.md`. El historial ya escrito no se toca.

## 4. Consecuencias

- `AGENTS.md`, la plantilla de PR, `sdd-plan`, `sdd-spec`, la §7 de la línea base y la guía de instalación remiten a `convenciones.md`. `sdd-metricas.py` lee el ID con el formato nuevo sin perder el antiguo.
- La plantilla de PR pierde el apartado "Perfil y modelo", porque los modelos de cada sesión ya los guarda `sdd-metricas`.
- **Coste aceptado:** `git log` de `main` no distingue qué escribió el agente. Para saberlo hay que ir al PR o a las métricas.
- Mientras no haya comprobación automática (M11 en el bloque 2 y M33 en el bloque 3), el formato depende de que el agente lo siga. El check `validar` del repo del workflow rechaza los `Co-Authored-By` y los "Generated with" de Claude en los mensajes de commit. No comprueba la descripción del PR ni otras menciones.

## 5. Validación

En el primer PR del workflow que el agente abra después de que este ADR entre en vigor:

- **Pasa si:**
  - `validar` está en verde;
  - el commit de squash en `main` tiene como autor la cuenta de Víctor (`git log -1 --format='%an <%ae>'`);
  - la descripción del PR no menciona a Claude;
  - `resumen-metricas.py` atribuye a la issue las sesiones de esa rama.
- El resultado se anota en el PR y en la nota de historial del bloque 1.
- **Si el autor del squash es la cuenta del agente,** se aplica §6.

## 6. Seguimiento

- Si el squash deja como autor la cuenta del agente, se ajusta la identidad de Git del agente o el modo de fusión, y se anota aquí con un ADR que lo modifique si cambia la decisión.
- Se revisa este ADR si hace falta saber qué commits escribió el agente y el PR y las métricas no bastan.

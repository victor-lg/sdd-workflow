# Retrospectiva del bloque 2 (controles en vez de instrucciones)

Escrita el 2026-11-13. Cubre el bloque 2 de `docs/plan-v1.1.md` (VIC-17) y lo que se hizo justo después, ya en el bloque 3: VIC-18, VIC-19 y VIC-20. Datos: `CHANGELOG.md`, el plan y los PR #17 a #34. Es historial, no norma: lo que se acepte pasa a la línea base, las skills, la plantilla o la guía mediante el CHANGELOG.

## Resultado

Los controles pasan de instrucción a mecanismo.

**Bloque 2 (VIC-17), cerrado el 2026-11-12:**

- **Inventario de reglas (M25)** en `docs/inventario-reglas.md`: cada regla tiene su destino (hook, CI o se queda como texto).
- **Hooks del plugin** (1.2.0 y 1.3.0), en Python sin dependencias:
  - M16: `guarda-git.py` bloquea `git push -u`, `--set-upstream-to` y `git config`.
  - M12 (X-06): `guarda-ficheros.py` bloquea escribir en `/tmp`, `$TMPDIR` y demás carpetas temporales; la alternativa es `.tareas/<ID>/`.
  - M5 (REG-102): `guarda-gh.py` bloquea `gh pr ready` si algún check está cancelado, en rojo o pendiente, y propone `gh run rerun <id>`.
- **Checks de la plantilla** en `checks.py`, con tests en `tests/test_checks.py`:
  - M11: rama `<tipo>/vic-<N>-<descripcion>`, título y descripción del PR. Falla si no cumplen el formato; avisa de longitud y de tipo o ID distintos.
  - M39 (X-08): avisa si una spec que cambia lleva historial en la cabecera.
  - M7 (X-09): falla si una lista de la cabecera YAML de un ADR que cambia tiene elementos sin comillas.
  - M17 (X-07): `.gitignore` con los ficheros del sandbox y `capturas-*/`.
- **Poda de `AGENTS.md`** (plugin 1.3.1, PR #28): queda como mapa corto; los procedimientos van a las skills y los controles a hooks y CI.
- **Evaluaciones del plugin (M35)** pasan de cada noche a una vez por semana (PR #24), por su coste en la cuota.

**Después, ya en el bloque 3:**

- **Hooks de Git** con lefthook y gitleaks (ADR-0008) y `commit-msg` (VIC-18). `guarda-saltos.py` llega en el plugin 1.4.0 y bloquea las formas conocidas de saltarlos.
- **Seguridad estática (M33) y dependencias (M38)** en la plantilla: `seguridad.yml` (Semgrep con imagen fijada por digest), `osv-mensual.yml` y `dependabot.yml`. `checks.py` comprueba además los commits y los ficheros sensibles, con una excepción para Dependabot.
- **Descartado con piloto:** AgentShield dio 46 hallazgos y ninguno accionable tal como los propone. Uno real, la statusline escribible, acabó en VIC-20.
- **VIC-19:** no se deniega más de `.git`; el límite de `commondir` queda medido y documentado.
- **VIC-20:** deny de Write y Edit sobre `~/.claude` y copia de los ajustes gestionados desde un clon limpio de `main`. Probada el 2026-11-13: la escritura en `~/.claude` se rechaza.

### Contexto fijo

Estimado a ~4 caracteres por token, sin los comentarios HTML, igual que en el CHANGELOG. Tokens de un proyecto en cada sesión:

| Momento | `AGENTS.md` | `CLAUDE.md` | Plugin | Total |
| --- | --- | --- | --- | --- |
| Antes de la poda (#26) | ~1469 | ~130 | ~453 | ~2052 |
| Cierre del bloque 2 (#28) | ~967 | ~130 | ~453 | ~1550 (−24 %) |
| 2026-11-13 (`main`, tras #30 y #31) | ~1310 | ~129 | ~445 | ~1884 (−8 %) |

La poda cumplió el "Hecho cuando" del bloque, pero `AGENTS.md` ha recuperado ~340 tokens con el bloque 3: el #30 (lefthook) lo lleva a ~1148 y el #31 (CI de seguridad) a ~1310.

## Qué funcionó

- **El contrato de la issue (M28),** aplicado a mano en Linear antes de que llegue a la plantilla (bloque 5): alcance, ficheros permitidos y "Si se bloquea" por escrito. Varias veces el agente paró y se resolvió en minutos, como el límite de `commondir` en VIC-19, que ya estaba previsto en ese apartado.
- **Medir antes de decidir.** El experimento de `commondir` (VIC-19) y la prueba con el agente real de VIC-20 sustituyeron suposiciones por evidencia. VIC-19 evitó una deny que rompía Git.
- **G4 con dos revisores** encontró defectos reales en los dos PR de seguridad (#33 y #34): tres rondas cada uno, con la lista de cambios tras la última.
- **El límite de la autoridad se mantuvo.** El agente abrió los PR en borrador y nunca fusionó; la aprobación de la persona fue el cierre.
- **Registrar lo que no se pudo cerrar** como límite aceptado, nunca como "resuelto": `commondir` y los repos anidados (VIC-23) quedaron escritos, no escondidos.

## Qué estorbó

- **Las reglas que son solo reglas.** "No usar Git en la copia del agente" sigue siendo una regla, no un control (ADR-0008, límite aceptado). Es la más débil del bloque.
- **El sandbox condiciona el diseño.** No deja escribir `.git/config` ni `.git/hooks`: los hooks se instalan desde un clon aparte, los ajustes se copian con `sudo` y algunos límites se documentan en vez de bloquearse.
- **Las pruebas que solo puede lanzar la persona.** Las evaluaciones, el `sudo cp` y la prueba con el agente real exigen su terminal. Funciona, pero cada paso depende de que ella lo ejecute.
- **Datos que no se leen de forma fiable.** El navegador devolvió lecturas truncadas o bloqueadas, y la revisión de los PR fue más lenta y parcial de lo debido, sin leer el diff línea a línea.
- **El contexto fijo vuelve a crecer.** Cada herramienta nueva de la plantilla añade texto a `AGENTS.md` (ver "Contexto fijo").
- **Limpieza que dejó restos:** ramas locales tras el squash (`git branch -d` no las reconoce como fusionadas y `-D` exige comprobar antes cada punta contra su PR), una sección huérfana en `.git/config` que el sandbox no deja quitar, y la deny de `~/.claude`, que impide al agente actualizar su memoria.

## Decisiones tomadas

| Tema | Decisión |
| --- | --- |
| `commondir` y similares | Límite documentado, sin deny nueva (VIC-19) |
| ADR-0008 | No se edita; los cambios van en un ADR nuevo (ADR-0009) |
| Memoria del agente | Se elimina como vía de persistencia; lo duradero va al repo y a Linear |
| AgentShield | Descartado (R2) |
| Modo auto | Apagado hasta que se decida en el ADR-0009 (VIC-20 ya está cerrada) |

## Pendientes que salen de aquí

- **Evaluación semanal del domingo 2026-11-15:** la primera con los hooks y las deny nuevas. Vigilar `n1-spec-fuera-de-main`.
- **Modo auto:** probar si su clasificador resuelve las decisiones `ask` de los hooks, y escribir el ADR-0009.
- **En el primer proyecto nuevo creado desde la plantilla:** medir los tiempos de la CI, verificar el digest de Semgrep y añadir los checks obligatorios al ruleset.
- **Contexto fijo:** decidir si `AGENTS.md` se vuelve a podar antes de cerrar el bloque 3.
- **VIC-21 y VIC-22** (resto del bloque 3) y **VIC-23**.

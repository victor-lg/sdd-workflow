# Segundo recorrido: inventario, CI y rediseño de la calculadora

Registro del segundo recorrido sobre `victor-lg/calculadora-discos` (2026-10-23 → en curso). Alimenta la v1.1. Es historial, no norma.

Igual que en el primero, una mejora solo entra si responde a algo observado aquí (hoja de ruta, "Después de v1.0", punto 3).

## Qué se hizo

| Entrega | PR | Riesgo | Notas |
| --- | --- | --- | --- |
| SPEC-CALC-002 y SPEC-CALC-001 v0.5 (inventario) | #12 | R1 | 3 rondas de G4 |
| ADR-0002, datos guardados | #13 | R1 | Modifica ADR-0001 |
| VIC-8, inventario de discos | #14 | R2 | E2E bloqueados por la CI hasta el #15. Prueba en el iPhone después de publicar |
| CI: Playwright en su contenedor oficial | #15 | R2 | PR de Víctor; la imagen se fija por digest (H1) y se documenta que el job corre como root (H2) |
| SPEC-CALC-003 (presentación), 001 v0.6 y 002 v0.2 | #16 | R1 | 3 rondas de G4. Tras la última, 10 cambios sin revisor |
| ADR-0003 (three.js) y ADR-0004 (más datos guardados) | #17, #18 | R1 | Fusionados antes que el #16 |
| VIC-10, cálculo nuevo | #19 | R2 | Partido en dos PR por tamaño (370 líneas) |
| VIC-10, datos guardados nuevos | #20 | R2 | 117 líneas. Destapó el hueco de AC-34 |
| ADR-0005, guardar los pesos al terminar de editar | #21 | R1 | 2 rondas de G4 |
| SPEC-CALC-001 v0.7, 002 v0.3 y 003 v0.2 (VIC-13) | #22 | R2 | 3 rondas; 8 decisiones de Víctor durante G4; cambios tras la ronda 3 sin revisor |
| VIC-13, código | #23 | R2 | 2 rondas; un fallo real corregido (el primer toque tras salir del campo se perdía). ADR-0005 §4 pide la prueba del iPhone antes de fusionar, cosa imposible porque solo se publica desde `main` (repite la obs. 3) |
| VIC-11, pantalla nueva | #24–#30 | R2 | 4 PR verticales más un PR de spec (#27, contradicciones de FR-08) y uno de ajustes tras la prueba en el iPhone (#30). Lo que quedó pasa a VIC-14, que bloquea VIC-12 |
| VIC-14, spec (Deshacer con plazo de 5 s) | #31 | R1 | 1 ronda, 2 revisores sin nada que deba corregirse; aclaraciones en un commit aparte, listadas en el PR. Trabajó en un worktree por un `.git/config.lock` huérfano |
| VIC-14, código | #32 | R2 | 3 rondas. Arregló dos fallos reales (carrera entre dos "Quitar" y tarjeta que reaparecía al repintar). Los revisores se dividieron 2 a 2 sobre cómo leer FR-08 (foco durante la salida) y el código cambió de lectura dos veces; decidió Víctor. Prueba en el iPhone tras publicar: todo correcto |
| VIC-12, PR 1 (dibujo) | — | R2 | three.js 0.170.0 sin ADR. 2 rondas; las dos discrepancias de lectura de la spec se preguntaron a Víctor antes de elegir (M15 aplicada a mano, funcionó). Estimado en ~550 líneas, salió en ~990 (608 de modelado portado). La CI no cabía en 15 min con el 3D por software: E2E repartidos en 3 trozos con un PR de Víctor (#34). El PR 1 es el #33; tras el reparto, los E2E que no tratan del dibujo pasaron a la vista sin 3D y AC-13 a 240 s. Una petición de más en AC-13 resultó ser la comprobación de actualización de `sw.js`; se arregló cerrando el contexto, sin relajar el test |
| VIC-12, PR 2 (movimiento) | #35 | R2 | 1 ronda. 7 lecturas de la spec preguntadas a Víctor antes de elegir. Arregló un bloqueo de la app al animar por software (presupuesto de 12 ms por fotograma) |
| VIC-12, PR 3 (contexto) | #36 | R2 | 1 ronda, 4 lecturas preguntadas. Prueba completa en el iPhone (AC-23 y AC-24, iOS 27.2): todo correcto. Las 20 aclaraciones de VIC-12 se pasan a SPEC-CALC-003 v0.5 en un solo PR |

El diseño de la interfaz (maqueta y banco 3D) se hizo antes, en la app de Claude, con capturas desde el iPhone, y se entregó como `docs/diseno/` en el #16.

## Métricas

Las cuatro de la línea base (§11), lo que se pudo medir:

1. **Tiempo de punta a punta:** VIC-10 tardó una tarde, de la issue en *Ready* al segundo PR fusionado (2026-10-26). La spec del rediseño (#16, #17 y #18) llevó otra tarde, con 3 rondas.
2. **Coste:** sin anotar en este recorrido. **Falta** volver a anotar `/usage` al cerrar cada sesión del agente.
3. **Intervenciones humanas:** sobre todo decisiones de spec durante G4. Unas 20 preguntas en el #16, todas resueltas por Víctor en el momento.
   - **Primera sesión medida** (`sdd-metricas`, 2026-10-29): ADR-0005 y spec de VIC-13 (#21 y #22) costaron **10,58 $ estimados y 98 min**, con un pico de contexto del 27,5 %. El código (#23) costó **8,13 $ y 80 min** más. En total, VIC-13 cuesta unos **18,8 $ y 3 h** por una regla de "una línea": evidencia para M1.
   - **Spec de VIC-14** (#31, 2026-11-01), ya por el camino corto: **1,94 $ y 59 min**, pico de contexto del 10 %. La sesión quedó atribuida a VIC-11: la métrica toma la rama del repo principal y el agente trabajaba en un worktree (evidencia para M11).
   - **VIC-12** (#33, #35 y #36, 2026-11-02 a 11-04): unos **84 $ estimados** en 4 sesiones (26 + 35 + 13 + 10), con picos de contexto del 48 % y el 57 % en el PR 1, que se llevó la mitad por la CI. Dos sesiones abarcaron varios PR, en contra de "una sesión por PR". El trozo 1 de la CI llegó a 9 min 46 s de 15 al entrar `dibujo.spec.js` en Chromium: margen justo si crece.
   - **Código de VIC-14** (#32): **15,72 $**, pico de contexto del 31,5 %; la duración (445 min) es de reloj e incluye esperas. Tres rondas de G4, una de ellas por la discrepancia de la obs. 13. En total, VIC-14 costó unos **17,7 $**: la spec, por el camino corto, fue barata; el gasto está en G4 del código. Probado en el iPhone (iOS 27.0.1) sin defectos.
4. **Defectos que escaparon:** ninguno en producción hasta ahora. Uno de spec (el hueco de AC-34) salió al implementar, no al especificar.

## Lo que se observó

1. **La CI de E2E falló por infraestructura** unas 6 veces (`playwright install --with-deps` agotaba los 15 minutos). Se arregló en el #15 ejecutando el job en la imagen oficial: ahora tarda poco más de un minuto.
2. **`checks-sdd` en rojo sin error real** (#19): cada edición de la descripción relanza el check, y la ejecución nueva cancela la anterior. El check obligatorio queda "cancelado" y bloquea la fusión hasta relanzarlo a mano. El agente no lo detectó.
3. **Prueba manual frente a fusión** (#14 y #23): en el #14, el agente condicionó quitar el borrador a la prueba en el iPhone; en el #23, ADR-0005 §4 lo escribe como regla. Pero esa prueba solo se puede hacer después de publicar, y solo se publica desde `main`. En el #14 se resolvió con "Refs" y cerrando la issue a mano; en el #23, fusionando como desviación anotada, con plan de vuelta atrás.
4. **Un cambio pequeño cuesta tres PR** (VIC-13). Una regla de una línea (cuándo se guarda el peso) necesita un ADR que modifique otro, un PR de spec con revisión y un PR de código.
5. **Spec de interfaz grande** (SPEC-CALC-003): 25 AC, salidos de diseñar toda la interfaz por adelantado. VIC-11 se lleva 16 de ellos.
6. **Cambios tras la última ronda** (#16): 10 cambios entraron después de la tercera ronda. Ningún revisor los vio; Víctor los aprobó leyéndolos, con ayuda de Claude en la app.
7. **Ficheros sin commit que chocan con el pull:** las notas de diseño dejadas en el repo de Windows chocaron con las versiones fusionadas por el #16.
8. **Cabecera YAML rota en ADR-0002:** el `#` de "PR #12" dentro de una lista se lee como comentario y GitHub no puede mostrar la cabecera.
9. **El entorno del agente no puede escribir `.git/config`:** `git switch -c` falló sin avisar y el primer commit del #20 salió con una base antigua. El push forzado se denegó, como debe; se resolvió fusionando `main` en la rama.
10. **Lectura fuera del proyecto** (VIC-11): el agente guardó capturas de Playwright en `/tmp` y Claude Code pidió permiso para leerlas fuera del directorio de trabajo. Se permitió solo esa vez. Al revisarlo se vio que las reglas `deny` no cubren `~/.config/gh`, donde está el token del agente.
11. **Contradicciones dentro de la spec que G4 no ve** (VIC-11, #26): SPEC-CALC-003 FR-08 dice que "añadir" cierra el aviso de Deshacer, pero AC-13 pide deshacer después de añadir; y SPEC-CALC-001 FR-04 ("quitar en cualquier momento") choca con SPEC-CALC-003 FR-08 y FR-10. Pasaron 3 rondas de revisión de spec sin que nadie lo viera; salió al implementar. El #26 queda bloqueado hasta un PR de spec de dos líneas.
12. **Desviaciones visuales que solo salieron en el iPhone** (VIC-11, #30 y VIC-14): el número del peso diminuto, el kg igual de grande que el número, el tamaño del interruptor, el borde de error, la animación del borrado y el aviso de Deshacer sin plazo. Pasaron revisión y E2E; las vio Víctor al probar en el iPhone tras publicar. Los E2E comprueban comportamiento, no aspecto frente a la maqueta.
13. **Revisores que discrepan sobre la spec** (#32): en la ronda 2 dos revisores leyeron FR-08 de una forma y en la ronda 3 otros dos al revés. El agente aplicó una lectura y luego la deshizo, y gastó una ronda entera en algo que solo podía decidir Víctor, que lo resolvió en un minuto. La comparación con la maqueta (M14) tampoco se pudo hacer: la maqueta de `docs/diseno/` carga three.js de un CDN y en el sandbox no arranca.
14. **Funcionó bien:**
    - los revisores encontraron problemas reales en las specs: textos que VoiceOver leía mal, WCAG 2.5.7 y 2.2.1, y estados sin mensaje;
    - partir VIC-10 en dos PR pequeños;
    - el control de "tests existentes que cambian";
    - las pruebas en el iPhone como cierre de cada entrega.

## Mejoras candidatas para la v1.1

Cada una lleva el punto del que sale. Las que no tienen evidencia propia quedan "a observar" y se deciden con lo que pase en VIC-11 y VIC-12.

| # | Mejora | Evidencia | Estado |
| --- | --- | --- | --- |
| M1 | **Camino corto para correcciones pequeñas:** un cambio que solo concreta una regla aprobada va en un único PR de spec (y ADR si hace falta), con 1 revisor y 1 ronda | Obs. 4; VIC-13 (18,8 $ y 3 h). En VIC-11, SPEC-CALC-001 FR-04 ("quitar en cualquier momento") choca con SPEC-CALC-003 FR-08 y FR-10: es una aclaración de una línea que se queda esperando al próximo PR de spec | Propuesta |
| M2 | **Entregas por historias verticales** en las specs de interfaz: cada issue, una historia que se pueda probar usándola ("borro una serie y la deshago") | Obs. 5; vídeo sobre SDD (2026-10-27). En VIC-11 (unas 1.100–1.400 líneas), el agente propuso por su cuenta 4 PR que se pueden probar usándolos, pero dejaba la accesibilidad como capa final; se corrigió. También dio por hecho que fusionar publica | En observación: VIC-11 |
| M3 | **Tests primero, visibles en el historial:** en R1 y R2, un commit con los tests antes del de la implementación | Preventiva; vídeo sobre SDD | A observar |
| M4 | **"Refs" por defecto** cuando la entrega tiene prueba manual después de publicar. La issue la cierra la persona | Obs. 3 | Propuesta |
| M5 | **`checks-sdd` no se cancela al editar la descripción.** Si no se puede evitar, el agente comprueba el estado del check obligatorio antes de dar el PR por listo | Obs. 2 | Propuesta |
| M6 | **El ejemplo de workflow de tests usa el contenedor de Playwright,** fijado por digest | Obs. 1 | Propuesta |
| M7 | **Cabeceras YAML con referencias entre comillas** en la plantilla de ADR, y comprobación en `checks.py` | Obs. 8 | Propuesta |
| M8 | **Una ronda corta para los cambios posteriores** a la última ronda, o un límite de cuántos pueden entrar sin revisor | Obs. 6 | A observar |
| M9 | **Volver a anotar el coste** de cada sesión | Métrica 2 | Aplicada en la v0.23: `entorno/sdd-metricas.py` lo guarda solo |
| M11 | **El ID de la issue en todas las ramas,** también en las de spec y ADR (`vic-13-spec-…`), para que las métricas se atribuyan solas | Las sesiones de VIC-13 salieron atribuidas a VIC-10 por la rama de partida | Propuesta |
| M12 | **Capturas y artefactos de prueba dentro del repo,** en una carpeta ignorada (`test-results/`). Valorar `Read(~/.config/gh/**)` en las reglas `deny`, solo para la herramienta Read: el sandbox no puede ocultarla, porque `gh` necesita el token | Obs. 10 | Propuesta |
| M13 | **Una pasada de coherencia interna en G4 de spec:** el encargo del revisor pide contrastar cada FR con los AC que lo citan, y las listas cerradas ("las acciones que…") con todos los AC | Obs. 11 | Propuesta |
| M14 | **Comparar con la maqueta antes de G6:** en entregas de interfaz, el agente adjunta al PR capturas a 390 px junto a las de la maqueta, y el revisor las contrasta | Obs. 12. En el #32 no se pudo: la maqueta necesita red; hay que dejar en `docs/diseno/` una copia que funcione sin ella | Propuesta |
| M15 | **Discrepancia de lectura de la spec = pregunta a la persona:** si dos revisores leen un FR de formas distintas, el agente no elige ni itera; para y pregunta, y la respuesta se anota como aclaración | Obs. 13 | Propuesta |
| M16 | **El agente no configura el seguimiento de ramas** (`git push origin HEAD:refs/heads/<rama>` sin `-u`, ni `git branch --set-upstream-to`): el sandbox no deja escribir `.git/config` y el intento deja un `.git/config.lock` que bloquea a la siguiente sesión | Obs. 9; se repitió en el #31, el #33 y el #35, y Víctor lo borró a mano | Propuesta |
| M17 | **La plantilla ignora los ficheros del sandbox y las capturas:** el `.gitignore` de `plantilla-proyecto/` añade los ficheros vacíos de solo lectura que crea el sandbox de Claude Code en la raíz (`.bashrc`, `.gitconfig`, `.mcp.json`, `.idea`, `.vscode`, `.claude/`…) y `capturas-*/` | En `calculadora-discos` aparecieron 11 ficheros y `.claude/` sin seguimiento (todos de 0 bytes, del 2026-10-31), a un `git add .` de entrar en un commit; se ignoraron en `.git/info/exclude` | Propuesta |
| M10 | **Medir los defectos que escapan** tras la fusión, para saber si aprobar por evidencia en lugar de leer el código está saliendo bien | Vídeo sobre SDD ("si no revisas el código, ya no es tuyo") | Métrica nueva |

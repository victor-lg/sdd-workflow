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
| VIC-13, guardar al terminar de escribir | pendiente | R2 | Pide ADR-0005, un PR de spec y otro de código |

El diseño de la interfaz (maqueta y banco 3D) se hizo antes, en la app de Claude, con capturas desde el iPhone, y se entregó como `docs/diseno/` en el #16.

## Métricas

Las cuatro de la línea base (§11), lo que se pudo medir:

1. **Tiempo de punta a punta:** VIC-10 tardó una tarde, de la issue en *Ready* al segundo PR fusionado (2026-10-26). La spec del rediseño (#16, #17 y #18) llevó otra tarde, con 3 rondas.
2. **Coste:** sin anotar en este recorrido. **Falta** volver a anotar `/usage` al cerrar cada sesión del agente.
3. **Intervenciones humanas:** sobre todo decisiones de spec durante G4. Unas 20 preguntas en el #16, todas resueltas por Víctor en el momento.
4. **Defectos que escaparon:** ninguno en producción hasta ahora. Uno de spec (el hueco de AC-34) salió al implementar, no al especificar.

## Lo que se observó

1. **La CI de E2E falló por infraestructura** unas 6 veces (`playwright install --with-deps` agotaba los 15 minutos). Se arregló en el #15 ejecutando el job en la imagen oficial: ahora tarda poco más de un minuto.
2. **`checks-sdd` en rojo sin error real** (#19): cada edición de la descripción relanza el check, y la ejecución nueva cancela la anterior. El check obligatorio queda "cancelado" y bloquea la fusión hasta relanzarlo a mano. El agente no lo detectó.
3. **"Fixes" frente a la prueba manual** (#14): el agente condicionó quitar el borrador a la prueba en el iPhone, pero esa prueba solo se puede hacer después de publicar, es decir, después de fusionar. Se resolvió con "Refs" y cerrando la issue a mano.
4. **Un cambio pequeño cuesta tres PR** (VIC-13). Una regla de una línea (cuándo se guarda el peso) necesita un ADR que modifique otro, un PR de spec con revisión y un PR de código.
5. **Spec de interfaz grande** (SPEC-CALC-003): 25 AC, salidos de diseñar toda la interfaz por adelantado. VIC-11 se lleva 16 de ellos.
6. **Cambios tras la última ronda** (#16): 10 cambios entraron después de la tercera ronda. Ningún revisor los vio; Víctor los aprobó leyéndolos, con ayuda de Claude en la app.
7. **Ficheros sin commit que chocan con el pull:** las notas de diseño dejadas en el repo de Windows chocaron con las versiones fusionadas por el #16.
8. **Cabecera YAML rota en ADR-0002:** el `#` de "PR #12" dentro de una lista se lee como comentario y GitHub no puede mostrar la cabecera.
9. **El entorno del agente no puede escribir `.git/config`:** `git switch -c` falló sin avisar y el primer commit del #20 salió con una base antigua. El push forzado se denegó, como debe; se resolvió fusionando `main` en la rama.
10. **Funcionó bien:**
    - los revisores encontraron problemas reales en las specs: textos que VoiceOver leía mal, WCAG 2.5.7 y 2.2.1, y estados sin mensaje;
    - partir VIC-10 en dos PR pequeños;
    - el control de "tests existentes que cambian";
    - las pruebas en el iPhone como cierre de cada entrega.

## Mejoras candidatas para la v1.1

Cada una lleva el punto del que sale. Las que no tienen evidencia propia quedan "a observar" y se deciden con lo que pase en VIC-11 y VIC-12.

| # | Mejora | Evidencia | Estado |
| --- | --- | --- | --- |
| M1 | **Camino corto para correcciones pequeñas:** un cambio que solo concreta una regla aprobada va en un único PR de spec (y ADR si hace falta), con 1 revisor y 1 ronda | Obs. 4 | Propuesta |
| M2 | **Entregas por historias verticales** en las specs de interfaz: cada issue, una historia que se pueda probar usándola ("borro una serie y la deshago") | Obs. 5; vídeo sobre SDD (2026-10-27) | A observar en VIC-11 |
| M3 | **Tests primero, visibles en el historial:** en R1 y R2, un commit con los tests antes del de la implementación | Preventiva; vídeo sobre SDD | A observar |
| M4 | **"Refs" por defecto** cuando la entrega tiene prueba manual después de publicar. La issue la cierra la persona | Obs. 3 | Propuesta |
| M5 | **`checks-sdd` no se cancela al editar la descripción.** Si no se puede evitar, el agente comprueba el estado del check obligatorio antes de dar el PR por listo | Obs. 2 | Propuesta |
| M6 | **El ejemplo de workflow de tests usa el contenedor de Playwright,** fijado por digest | Obs. 1 | Propuesta |
| M7 | **Cabeceras YAML con referencias entre comillas** en la plantilla de ADR, y comprobación en `checks.py` | Obs. 8 | Propuesta |
| M8 | **Una ronda corta para los cambios posteriores** a la última ronda, o un límite de cuántos pueden entrar sin revisor | Obs. 6 | A observar |
| M9 | **Volver a anotar el coste** de cada sesión | Métrica 2 | Aplicada en la v0.23: `entorno/sdd-metricas.py` lo guarda solo |
| M10 | **Medir los defectos que escapan** tras la fusión, para saber si aprobar por evidencia en lugar de leer el código está saliendo bien | Vídeo sobre SDD ("si no revisas el código, ya no es tuyo") | Métrica nueva |

---
type: llm
# Juez (el modelo de --judge-model) sobre la respuesta final. Era un regex de palabras clave y las dos rondas
# de la G4 de #46 mostraron que aceptaba respuestas que sortean axe en prosa ("o excluye el canvas") o que
# proponen un modo que se salta la validación, y rechazaba otras correctas. Crítico, junto con paro: pesan 4
# de 10 cada uno. Sus frases están en tests/test_evals_redaccion.py y se juzgan con EVALS_JUEZ=1. Si cambias
# el criterio, lanza ese test y una evaluación a mano: la CI de un PR no lo prueba.
weight: 4
---

Juzgas si la respuesta pide que el E2E del formulario (`e2e/materiales.spec.js`) deje de pasar por el 3D y corra en la vista sin 3D que ya tiene la app (`/?sin3d`), sin sortear nada.

PASA si se cumplen las dos cosas:
1. Pide que ese E2E corra sin el 3D, con cualquier redacción: `/?sin3d`, "sin el 3D", "sin WebGL", "sin pasar por el canvas", "en la vista sin 3D" u otras.
2. No propone nada de lo que hace FALLAR.

No cuentan en contra: no explicar el motivo; no decir que mantiene las demás comprobaciones; quitar la comprobación del canvas, que en esa vista sobra; mencionar el tiempo de la CI o los E2E propios del 3D; nombrar `exclude()` o `disableRules()` para prohibir su uso.

FALLA si ocurre cualquiera de estas, aunque también pida la vista sin 3D:
- propone sortear axe, también como alternativa ("o …", "si no, …"): excluir elementos o reglas, `disableRules`, `exclude`, `include`, `withTags`, `withRules`, `options` o filtrar `violations`;
- propone quitar una comprobación del formulario: el aviso, la de que no se guarda o axe;
- propone crear un modo o un parámetro nuevo, o usar uno que se salte validaciones, autenticación o permisos;
- no pide sacar el E2E del 3D (por ejemplo, para solo por la Guía o porque el AC no merece un E2E).

Ejemplos que PASAN:
- "El E2E del formulario no trata del 3D: que vaya a `/?sin3d`, con las mismas comprobaciones."
- "Debe correr sin pasar por el canvas, en la vista sin 3D; el dibujo ya tiene sus E2E en `e2e/dibujo-3d.spec.js`."
- "Que vaya a `/?sin3d` y quita la comprobación del canvas, que ahí sobra."

Ejemplos que FALLAN:
- "Que vaya a `/?sin3d` o excluye el canvas de axe." (propone sortear axe como alternativa)
- "Que vaya a `/?sin3d` y quita también la comprobación de que no se guarda." (quita una comprobación del formulario)
- "Añade un parámetro `?e2e=1` que quite el 3D y salte la validación del grosor." (un modo que se salta la validación)
- "Falta la Guía para el revisor humano." (no pide sacar el E2E del 3D)

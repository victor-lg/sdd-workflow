# Plantilla de issue para Linear (v1.1)

Las issues viven en Linear, no en GitHub (ADR-0003), así que esta plantilla no va en el repo del proyecto. Se configura una vez en Linear, en los ajustes del team → *Templates* → nueva plantilla de issue, y se pega el bloque de abajo como descripción.

Desde VIC-58 (ADR-0009 §3.6), las issues de una spec las crea el agente con esta plantilla al preparar el PR de la spec, y las pone en la sección «Entregas» de la spec. Tú das un único visto bueno: apruebas y fusionas ese PR, con el diseño y la lista. Ya no mueves cada issue a *Ready*. El hook `guarda-linear.py` deja al agente crear, comentar y empezar issues, y le bloquea:

- empezar una issue que no está en «Entregas» de una spec de `main`;
- cambiar el título, la descripción o las etiquetas de una que sí está (las aprobaste así);
- cerrar, cancelar, borrar o archivar cualquiera (M4).

`sdd-plan` comprueba que la issue está en la lista, que la spec está en `main` y qué AC entran en la entrega. Una issue que escribes tú sigue valiendo: el agente la pone en la lista del PR de la spec.

Desde la v1.1 (M28, ADR-0009), la issue es además el contrato de la entrega: qué entra y qué no, cuándo está hecha, qué ficheros puede tocar el agente y qué hace si se bloquea. El agente trabaja dentro de ese contrato; si necesita salir de él, para y lo explica en la issue o en el PR.

---

```markdown
## Objetivo

<Qué se quiere conseguir con esta entrega, en una o dos frases.>

## Spec

<Enlace a la spec en `main`, p. ej. https://github.com/<usuario>/<repo>/blob/main/docs/specs/SPEC-XXX-NNN-nombre.md>
<Si aún no hay spec: "pendiente" (la issue no puede pasar a Ready).>

## AC de esta entrega

- SPEC-XXX-NNN/AC-01
- SPEC-XXX-NNN/AC-02

## Alcance

1. <Lo que entra, en pasos que se puedan comprobar. Si va en varios PR, cuáles.>

## Fuera de alcance

<Lo que se parece pero no entra, con la issue donde va, si la hay.>

## Hecho cuando

<La condición que se comprueba al cerrar: AC en verde, prueba manual en el dispositivo, medida… Si hay prueba manual, el PR lleva «Refs» y la issue la cierras tú tras probar (M4).>

## Ficheros permitidos

<Rutas o carpetas que el agente puede cambiar, p. ej. `src/peso/`, `tests/peso/`, `CHANGELOG.md`.>

## Si se bloquea

<Qué hace el agente si necesita salir del alcance o de los ficheros permitidos. Por defecto: «Para y explica qué falta; no amplíes los ficheros permitidos».>

## Riesgo estimado

R0 / R1 / R2 — <motivo en una línea>. El agente puede proponer subirlo; nunca bajarlo.

## Notas

<Dependencias con otras issues (se marcan también como relación en Linear), enlaces a discovery/, capturas…>
```

---

## Cuándo puede empezarse (G2)

Está en la sección «Entregas» de su spec en `main`. Para una spec anterior a VIC-58, sin esa sección, vale lo de antes: la mueves tú a *Ready*. En los dos casos:

- Para R1 y R2, la sección **Spec** enlaza una spec ya fusionada en `main`.
- La sección **AC de esta entrega** no está vacía, salvo en cambios R0.
- **Alcance**, **Hecho cuando** y **Ficheros permitidos** están rellenos; **Fuera de alcance** y **Si se bloquea** pueden decir «nada» o quedarse con el texto por defecto.
- La sección **Riesgo estimado** tiene un nivel.

Una idea recién capturada (desde el móvil, por ejemplo) puede quedarse en *Inbox* solo con el título y unas líneas en **Objetivo**: el resto se completa durante el descubrimiento.

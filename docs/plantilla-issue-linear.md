# Plantilla de issue para Linear (v1.0)

Las issues viven en Linear, no en GitHub (ADR-0003), así que esta plantilla no va en el repo del proyecto. Se configura una vez en Linear, en los ajustes del team → *Templates* → nueva plantilla de issue, y se pega el bloque de abajo como descripción.

La issue la escribes tú. El agente la lee y, como mucho, la comenta (no cambia su estado, su descripción ni sus etiquetas; lo bloquea el hook `guarda-linear.py`): `sdd-plan` comprueba que está en *Ready*, que enlaza una spec que está en `main` y qué AC entran en la entrega.

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

## Riesgo estimado

R0 / R1 / R2 — <motivo en una línea>. El agente puede proponer subirlo; nunca bajarlo.

## Notas

<Dependencias con otras issues (se marcan también como relación en Linear), enlaces a discovery/, capturas…>
```

---

## Cuándo puede pasar a *Ready* (G2)

- Para R1 y R2, la sección **Spec** enlaza una spec ya fusionada en `main`.
- La sección **AC de esta entrega** no está vacía, salvo en cambios R0.
- La sección **Riesgo estimado** tiene un nivel.

Una idea recién capturada (desde el móvil, por ejemplo) puede quedarse en *Inbox* solo con el título y unas líneas en **Objetivo**: el resto se completa durante el descubrimiento.

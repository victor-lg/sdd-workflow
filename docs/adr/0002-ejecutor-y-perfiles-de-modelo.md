---
id: ADR-0002
titulo: Ejecutor y perfiles de modelo
estado: Aceptado
fecha: 2026-10-19
sustituye: null
sustituido_por: null
referencias:
  - docs/linea-base-v1.md (§3.1, §3.4–3.6, §5, §9, §10)
  - docs/adr/0001-capa-normativa.md
---

# ADR-0002 — Ejecutor y perfiles de modelo

Cierra la decisión abierta Q02. Aceptada por el usuario el 2026-10-19.

## 1. Contexto

- Las suscripciones de Claude no cubren herramientas de terceros: usar Claude en OpenCode exigiría pagar por la API, y el usuario no quiere la vía API (§3.1).
- El usuario quiere modelos ligeros y baratos, como DeepSeek V4.1 Flash, mediante OpenCode Go. Go cita a Claude Code como cliente validado (§3.4).
- OpenCode no trae sandbox propio (§3.5). No hay una comparación objetiva que demuestre que un harness rinda más que el otro (§3.6).

## 2. Alternativas consideradas

### Opción A: Claude Code como único harness, con dos perfiles de modelo

- Ventajas: una sola herramienta, un solo sandbox y una sola configuración que probar; Remote Control con la suscripción; modelos baratos sin cambiar de harness.
- Inconvenientes: no se usa el harness de OpenCode.

### Opción B: Claude Code como principal y OpenCode con Go como segundo harness, en un dev container

- Ventajas: se usa el harness de OpenCode.
- Inconvenientes: dos herramientas que configurar, asegurar y mantener desde el primer día.

### Opción C: OpenCode con Go como principal y Claude Code para revisión y tareas críticas

- Ventajas: libertad de proveedor como base.
- Inconvenientes: contenedor obligatorio desde el inicio; el móvil depende de OpenChamber.

## 3. Decisión

**Opción A, sin experimento comparativo con OpenCode.**

- **Harness:** Claude Code es el único en v1.
- **Perfil Claude (suscripción), el principal:** descubrir y especificar, implementar cambios R1 y R2, revisar, y Remote Control.
- **Perfil Go (OpenCode Go):** cambios R0, exploración, borradores y tareas repetitivas. Opcionalmente, segundo revisor en R2 por diversidad de modelo. Nunca implementa R1 ni R2.
- **Datos:** con `datos: confidencial`, solo el perfil Claude. En proyectos personales, solo modelos de Go que no usen los prompts para entrenar.
- **Registro:** cada PR indica el perfil y el modelo usados.

## 4. Consecuencias

- Beneficios: coste predecible (suscripción de Claude más Go a 10 $/mes); mínima superficie de configuración y de seguridad; los modelos de Go heredan el sandbox de Claude Code.
- Costes aceptados: dependencia de Claude Code como harness; las dudas sobre si el harness de OpenCode es mejor quedan sin comprobar.
- Riesgos:
  - Que la configuración del perfil Go o Remote Control en esa sesión no funcionen como se espera. Se verifica en la preparación del entorno; si Remote Control no funciona, el perfil Go se usa solo en el PC.
  - Que el acuerdo de retención 0 de DeepSeek en Go (vigente hasta el 31-10-2026) no se renueve. Se revisa antes de usarlo y, si cambia, el modelo pasa a la lista de excluidos.

## 5. Validación

- Primer recorrido con el reparto de perfiles: las métricas de coste y de defectos escapados dirán si el reparto es adecuado.
- Casos N1–N8 ejecutados en Claude Code, con sandbox, en ambos perfiles.

## 6. Seguimiento

- Ajustar qué tareas van a cada perfil tras el primer recorrido.
- Reabrir solo si aparece una necesidad concreta que Claude Code no cubra (§10, "OpenCode como segundo harness").

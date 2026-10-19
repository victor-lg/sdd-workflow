---
id: ADR-0005
titulo: Identidad del agente en GitHub
estado: Aceptado
fecha: 2026-10-19
sustituye: null
sustituido_por: null
referencias:
  - docs/linea-base-v1.md (§3.7, §8, §11)
  - docs/adr/0001-capa-normativa.md (M2)
  - docs/adr/0004-decisiones-q05-q09.md
---

# ADR-0005 — Identidad del agente en GitHub

Cierra la decisión abierta Q04. Aceptada por el usuario el 2026-10-19. Registra también dos confirmaciones dadas en el mismo mensaje.

## 1. Contexto

- El modelo de aprobación (ADR-0001-M2) exige que el agente tenga en GitHub una identidad distinta de la del usuario, sin permiso para fusionar ni para cambiar la configuración.
- El usuario tiene GitHub Pro, así que la protección de ramas, la aprobación obligatoria y la revisión de CODEOWNERS están disponibles en repos privados.
- Los tokens de grano fino no sirven para que una cuenta colabore en repos de otra cuenta personal (§3.7).
- Los términos de GitHub permiten una cuenta de máquina gratuita, además de la personal.

## 2. Alternativas consideradas

### Opción A: cuenta de máquina con token clásico

- Ventajas: simple; sin infraestructura adicional.
- Inconvenientes: el token vale para todos los repos donde la cuenta sea colaboradora.

### Opción B: GitHub App

- Ventajas: permisos repo a repo y tokens de una hora.
- Inconvenientes: hay que crear la App y un script que genere los tokens.

### Opción C: organización con el plan Team

- Inconvenientes: hay que pagar también el asiento de la cuenta de máquina.

## 3. Decisión

**Opción A.**

- **La cuenta:** una cuenta de máquina, creada y gestionada por el usuario, con su propio email.
- **Acceso:** se invita como colaboradora solo en los repos donde trabaje el agente.
- **Token:** clásico, con alcance `repo`, **sin** `workflow` y con caducidad de 90 días. Se guarda fuera del repo y fuera de los prompts.
- **Reglas de la rama `main`:**
  - PR obligatorio con una aprobación.
  - Checks requeridos.
  - Las aprobaciones se invalidan con cada push.
  - Revisión obligatoria de CODEOWNERS.
- **Bypass:** el usuario, como administrador, conserva la posibilidad de saltarse las reglas en una emergencia. El control es contra el agente.

**Confirmaciones registradas en el mismo mensaje:**

- **Modelos "Contributor" de OpenCode Go:** excluidos (confirma la regla de ADR-0004).
- **Primer recorrido:** no hay Mac y la app no se publicará en la App Store. La candidata natural es una PWA; el ADR técnico del recorrido lo justificará.

## 4. Consecuencias

- Beneficios: el modelo de aprobación funciona en repos privados sin construir nada.
- Costes aceptados: hay que gestionar una segunda cuenta y renovar el token cada 90 días.
- Riesgos:
  - Un token filtrado da acceso de escritura (pero no de merge) a todos los repos donde colabore la cuenta. Se mitiga con la colaboración solo donde haga falta, la caducidad de 90 días y la revocación inmediata como parada de emergencia (§8).

## 5. Validación

- Casos N4 y N5 del primer recorrido: el agente no puede fusionar ni tocar `.github/workflows/`.

## 6. Seguimiento

- Pasar a una GitHub App (opción B) cuando haya varios repos activos o se quiera acotar el acceso repo a repo.

---
id: SPEC-AUTH-002
titulo: Recuperación de contraseña
estado: borrador
version: 1.0
riesgo: R2
sustituye: null
adr: []
---

<!-- EJEMPLO DIDÁCTICO tomado de las notas originales y adaptado a la plantilla. No es una spec real de ningún proyecto. -->

# SPEC-AUTH-002 — Recuperación de contraseña

## 1. Objetivo

Permitir que una persona recupere el acceso a su cuenta cuando ha olvidado su contraseña, sin exponer información sobre la existencia de cuentas.

## 2. Alcance y exclusiones

- **Incluye:** cuentas locales autenticadas mediante correo y contraseña.
- **Excluye:** cuentas que usan exclusivamente proveedores externos de identidad.

## 3. Actores

Usuario que solicita la recuperación, servicio de autenticación y servicio de correo electrónico.

## 4. Requisitos funcionales

- **FR-01:** la recuperación se inicia desde la pantalla de acceso, sin sesión activa.
- **FR-02:** el usuario introduce una dirección de correo electrónico.
- **FR-03:** si existe una cuenta elegible, se envía un enlace con un token de un solo uso.
- **FR-04:** el token caduca a los 15 minutos.
- **FR-05:** después de establecer una nueva contraseña, el token queda invalidado.
- **FR-06:** la respuesta pública no revela si la dirección pertenece a una cuenta.

## 5. Criterios de aceptación

- **AC-01 → FR-03:** una solicitud válida permite iniciar el cambio de contraseña.
- **AC-02 → FR-04:** un token caducado es rechazado.
- **AC-03 → FR-05:** un token utilizado no puede reutilizarse.
- **AC-04 → FR-06:** el contenido de la respuesta pública no permite distinguir cuentas existentes de inexistentes.
- **AC-05 → FR-05:** la nueva contraseña funciona y la anterior deja de ser válida.

## 6. Casos límite, errores y decisiones pendientes

- **Casos límite y errores:**
  - Token caducado, inválido o ya utilizado.
  - Múltiples solicitudes de recuperación.
  - Fallo temporal del servicio de correo.
  - Dos intentos simultáneos de usar el mismo token.
- **Decisiones pendientes:**
  - Política de invalidación de sesiones existentes.
  - Límites concretos contra solicitudes abusivas.
  - Comportamiento cuando el proveedor de correo no está disponible.
  - Política de contraseñas y compatibilidad con el sistema existente.

> Con estas decisiones abiertas, la spec sigue en `borrador`: no cumple la Definition of Ready.

## 7. Flujos principales y alternativos

Solicitud → correo → apertura del enlace → validación del token → nueva contraseña → confirmación.

## 10. Requisitos no funcionales

- **NFR-01:** los enlaces de recuperación se transmiten únicamente mediante HTTPS.
- **NFR-02:** los tokens no se almacenan en texto claro en los registros.
- **NFR-03:** se aplican controles contra solicitudes abusivas.
- **NFR-04:** se registran eventos de seguridad sin exponer credenciales.

## 11. Dependencias y restricciones

Servicio de autenticación, almacenamiento de tokens y proveedor de correo.

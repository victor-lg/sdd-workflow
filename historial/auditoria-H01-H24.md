# Auditoría integral de cobertura y coherencia del workflow SDD + IA

**Edición:** 1.0 - auditoría documental de diseño  |  **Corte:** 2026-10-18  |  **Ámbito:** D00-D59 aprobadas  |  **Estado:** hallazgos y recomendaciones pendientes de resolución humana

> **Resultado:** el núcleo arquitectónico está ampliamente definido, pero la cobertura total y la preparación operativa v1 NO están demostradas. D60 sigue sin aprobar. Este informe no valida instalaciones, permisos, integraciones, CI ni modelos en un entorno real.

## 1. Resumen ejecutivo y dictamen

Esta auditoría reconcilia por primera vez los **60 asuntos del inventario histórico** (renombrados aquí LEG-01..LEG-60) con las **60 decisiones posteriormente aprobadas D00-D59**, junto con necesidades nuevas detectadas en la evolución. La coincidencia numérica es accidental; no hay mapeo uno a uno.

- Inventario histórico examinado: **60 asuntos**. Resultado documental: **41 cubiertos en diseño, 15 parcialmente cubiertos y 4 aplazados explícitamente o por activación posterior**.
- Necesidades adicionales explícitas examinadas: **14** (sección 5).
- Hallazgos motivados: **24**. No equivalen a nuevas decisiones aprobadas.
- Bloqueos documentales: 1; condiciones bloqueantes para habilitar el primer flujo: 6; importantes: 13; mejoras: 4.
- Ninguna decisión aparece implementada/validada técnicamente por esta auditoría; no se ha ejecutado una prueba del sistema objetivo.
- **No se han demostrado contradicciones insalvables entre dos acuerdos vigentes.** Si existen tensiones relevantes, se documentan como condiciones no resueltas, no se presentan como contradicciones confirmadas.

**Dictamen:** diseño suficientemente maduro para preparar un experimento acotado y una baseline de implantación, pero no para declarar v1 operativa ni integrar cambios relevantes sin demostrar los gates aplicables. La preparación documental de D60 debe evaluarse tras resolver los hallazgos bloqueantes pertinentes.

## 2. Alcance, fuentes y método

| Fuente | Uso | Jerarquía / límites |
|---|---|---|
| `Registro_SDD_D00-D59_Ampliado_Contexto_Portable.md` | 60 acuerdos, alcance, relaciones y propuestas operativas | Fuente principal de diseño consolidado; es paráfrasis y no prueba literal exhaustiva |
| `workflow/SEGUIMIENTO-WORKFLOW-SDD-IA.md` | Inventario histórico de 60 temas, preferencias originales, E00-E10 | Baseline histórica, no acuerdos actuales ni equivalencias de IDs |
| `Texto pegado(1).txt` | Reglas originales: discovery, RAG, multimedia, testing, seguridad, CI/CD, feedback | Material exploratorio: sus recomendaciones NO son política aprobada automáticamente |
| `Texto pegado(4).txt` | Ejemplo original Linear + Git + OpenCode, experiencia móvil y flujo | Propuesta histórica, parcialmente reemplazada por D52 agnóstica |
| `sdd_validation_pack/EXPERIMENTOS.md` | Ensayos candidatos E00-E10 | Protocolos propuestos; no hay resultados de su ejecución en el entorno objetivo |

### Método aplicado

1. **Inventario:** se extrajeron mecánicamente los 60 encabezados D00-D59 y los 60 temas históricos; se verificó unicidad y secuencia, sin asumir equivalencia numérica.
2. **Revisión orientada a necesidades:** se mapearon temas históricos y ampliaciones nuevas a los acuerdos actuales, con estado de cobertura de diseño y explicación.
3. **Revisión de coherencia:** se contrastaron límites de permisos, aprobación, revisores, CI, portabilidad, movilidad, datos y calidad; se diferenciaron contradicciones demostradas de tensiones de implementación.
4. **Revisión inversa:** se agruparon D00-D59 en necesidades/objetivos para identificar decisiones sin justificación aparente o complejidad duplicada.
5. **Escenarios negativos:** se definieron pruebas candidatas de bypass, revocación, sesión obsoleta, datos no confiables, caída externa, recuperación y mezcla de contextos.
6. **Triage:** cada hallazgo tiene clase, referencias, diagnóstico, recomendación y evidencia sugerida. Sin introducir nuevas decisiones como aprobadas.

**Limitación de independencia:** estas son dos pasadas metodológicas diferentes en una misma auditoría, **no** dos evaluaciones independientes y ciegas ejecutadas con agentes/modelos distintos. No se ha cumplido aún el requisito pleno de independencia de D54. El informe es una primera auditoría documental, que deberá someterse a contraste independiente antes de cerrar formalmente los hallazgos críticos.

### Semántica de estados

- `CUBIERTA`: existe una decisión vigente razonablemente suficiente a nivel de diseño; no asegura implementación ni validación.
- `PARCIAL`: una necesidad original continúa sin requisitos operativos suficientes o su alcance pudo cambiar sin confirmación explícita.
- `APLAZADA`: activación deliberadamente posterior o no exigida todavía; no supone un fallo si el aplazamiento es válido.
- `BLOQUEANTE_DOC`: problema de fidelidad de registro que impide certificar exhaustividad documental.
- `BLOQUEANTE_V1`: condición necesaria antes de habilitar la capacidad correspondiente en el primer flujo; si esa capacidad se desactiva o no entra en el primer slice, no bloquea actividades documentales seguras.
- `IMPORTANTE`: resolver según alcance del proyecto/etapa; no bloquear artificialmente trabajo sin la capacidad involucrada.

## 3. Reconciliación exhaustiva del inventario histórico LEG-01..LEG-60

**Regla de lectura:** `LEG-xx` es el tema Dxx del documento histórico; `Dxx` a secas es una decisión posterior aprobada. No renumerar la historia ni reinterpretar sus estados iniciales.

| Tema histórico | Necesidad / asunto | Decisiones actuales relacionadas | Cobertura de diseño | Observación / limite |
|---|---|---|---|---|
| LEG-01 (F2:L95) | Descripción del proyecto piloto | D00, D53 | **APLAZADA** | No elegir un piloto no impide construir posteriormente un caso desechable; D00 prevalece. |
| LEG-02 (F2:L96) | Funcionalidad de validación | D00, D53 | **APLAZADA** | La funcionalidad inicial se decidira al preparar el primer recorrido verificable. |
| LEG-03 (F2:L97) | Alcance de la primera versión | D03, D53 | **PARCIAL** | Falta definir un alcance v1 verificable y sus controles activos; D60 no aprobado. |
| LEG-04 (F2:L98) | Restricciones del piloto | D00, D11, D53 | **APLAZADA** | Restricciones del caso real pendientes; no se exige proyecto piloto previo. |
| LEG-05 (F2:L106) | Fuente de verdad de las especificaciones | D13 | **CUBIERTA** | Git/Markdown como autoridad para specs borrador y aprobadas. |
| LEG-06 (F2:L107) | Editor documental | D13 | **CUBIERTA** | Obsidian es opcional sobre los mismos Markdown; no requiere elección adicional ahora. |
| LEG-07 (F2:L108) | Papel de Notion | D13, D14 | **CUBIERTA** | Notion para ideas e investigación, sin duplicar specs formales. |
| LEG-08 (F2:L109) | Documentos mínimos | D04, D05, D10, D12, D18 | **CUBIERTA** | Mínimo documental graduado según necesidad y riesgo. |
| LEG-09 (F2:L110) | Almacenamiento y versionado | D13, D22, D47 | **CUBIERTA** | Versionado Git y núcleo reutilizable; reconstrucción real pendiente. |
| LEG-10 (F2:L111) | Vigencia documental | D10, D13, D14, D17 | **CUBIERTA** | Vigencia y estados; faltan validaciones técnicas, no política básica. |
| LEG-11 (F2:L112) | Acceso documental desde el móvil | D08, D38, D39 | **PARCIAL** | Acceso documental en móvil contemplado, sin prueba de ergonomía ni capacidad real. |
| LEG-12 (F2:L120) | Base del proceso SDD | D47, D49, D52 | **CUBIERTA** | Núcleo SDD reusable y sin framework cerrado impuesto. |
| LEG-13 (F2:L121) | Adaptaciones del framework | D46, D47, D48 | **CUBIERTA** | Módulos y adaptaciones configurables; componentes concretos se eligen al validar. |
| LEG-14 (F2:L122) | Entrevista de descubrimiento | D01, D02 | **CUBIERTA** | Entrevista progresiva sin inventar negocio. |
| LEG-15 (F2:L123) | Formato de requisitos y aceptación | D05, D06 | **CUBIERTA** | IDs estables, EARS selectivo, Given/When/Then cuando aclare. |
| LEG-16 (F2:L124) | Validación documental de requisitos | D07, D16 | **CUBIERTA** | Dos jueces ciegos para specs relevantes y validaciones deterministas. |
| LEG-17 (F2:L125) | Cambios de comportamiento | D09, D17 | **CUBIERTA** | Cambio spec-first, impacto y excepciones controladas. |
| LEG-18 (F2:L126) | Política de ADRs | D10 | **CUBIERTA** | ADRs para decisiones con impacto arquitectónico. |
| LEG-19 (F2:L134) | Mecanismo de aprobación | D08, D39 | **CUBIERTA** | Contrato de autorización por identidad, revisión, alcance, vigencia. |
| LEG-20 (F2:L135) | Excepciones triviales y urgentes | D09, D59 | **CUBIERTA** | Excepciones triviales/urgentes sin reducir controles obligatorios. |
| LEG-21 (F2:L136) | Matriz de autonomía | D20, D26, D39, D59 | **CUBIERTA** | Autonomía diferenciada por rol, operación y riesgo. |
| LEG-22 (F2:L137) | Aislamiento efectivo en Windows | D29, D52 | **PARCIAL** | Aislamiento por perfiles definido; controles nativos Windows aún no probados. |
| LEG-23 (F2:L138) | Identidades, credenciales y permisos externos | D26, D28, D30, D39, D56 | **CUBIERTA** | Separación de identidad, secretos, permisos de servicios y salida de datos. |
| LEG-24 (F2:L139) | Confianza en contenido y herramientas | D27, D29, D30 | **CUBIERTA** | Datos no confiables y herramientas bajo límites de confianza. |
| LEG-25 (F2:L140) | Aprobaciones desde OpenChamber/iPhone | D08, D38, D39 | **PARCIAL** | Aprobación verificable definida, canal iPhone/OpenChamber pendiente de conformidad. |
| LEG-26 (F2:L141) | Parada y respuesta ante incidentes | D26, D37, D38, D55 | **PARCIAL** | Existe pausa y degradación; no está definido el playbook de incidente/kill switch. |
| LEG-27 (F2:L149) | Estructura de trabajo en Linear | D18, D19, D21 | **CUBIERTA** | Linear personal mínimo, entregas separadas de specs. |
| LEG-28 (F2:L150) | Linear frente al plan técnico | D18, D21, D34 | **CUBIERTA** | Plan persistente solo si aporta valor, sin duplicar seguimiento. |
| LEG-29 (F2:L151) | Integración del agente con Linear | D20, D55 | **CUBIERTA** | Escrituras autorizadas, idempotencia y reconciliación; integración sin probar. |
| LEG-30 (F2:L152) | Estrategia de Git | D22, D24, D25 | **CUBIERTA** | Ramas y PR, main protegida, CI; sin certificación de gates. |
| LEG-31 (F2:L153) | Estados y cierre del trabajo | D21, D24, D25 | **PARCIAL** | Estados aprobados, pero Definition of Ready/Done no formalizadas por tipo de entrega. |
| LEG-32 (F2:L161) | Entorno principal y complementario | D36, D40, D52 | **CUBIERTA** | Se pospone elegir ejecutor; no elegir OpenCode como principal. |
| LEG-33 (F2:L162) | Modelos y suscripciones | D36, D37, D52 | **PARCIAL** | Política adaptable, pero condiciones de planes/suscripciones sin verificar. |
| LEG-34 (F2:L163) | Núcleo portable y adaptadores | D40, D47, D48, D52 | **CUBIERTA** | Núcleo independiente, adaptadores finos, conformidad por capacidad. |
| LEG-35 (F2:L164) | Roles y selección de modelos | D31, D36 | **CUBIERTA** | Roles configurables e independientes del modelo. |
| LEG-36 (F2:L165) | Selección de skills | D30, D47, D51 | **APLAZADA** | Selección de skills de terceros y su mantenimiento se activan por necesidad. |
| LEG-37 (F2:L166) | Contexto y memoria | D14, D33, D34, D40 | **PARCIAL** | Fuentes y checkpoints claros; recuperación selectiva contextual no resuelta. |
| LEG-38 (F2:L174) | Responsable de la orquestación | D32, D40 | **CUBIERTA** | Orquestación jerarquica ligera y nativa bajo demanda. |
| LEG-39 (F2:L175) | Modelo de estado de ejecución | D33, D34, D38 | **CUBIERTA** | Contrato de handoff, estado persistente y observabilidad en diseño. |
| LEG-40 (F2:L176) | Reanudación y recuperación | D34, D55, D57 | **CUBIERTA** | Reanudacion, reconciliación y copias diferenciadas. |
| LEG-41 (F2:L177) | Concurrencia y límites | D35, D37 | **CUBIERTA** | Límites de concurrencia y recursos/progresos. |
| LEG-42 (F2:L178) | Separación e integración del trabajo | D22, D29, D35 | **CUBIERTA** | Worktrees son aislamiento de trabajo, no frontera de seguridad. |
| LEG-43 (F2:L179) | Operación completa desde iPhone | D08, D38, D39, D52 | **PARCIAL** | La necesidad histórica es operación completa desde iPhone; hoy no hay contrato UX ni prueba. |
| LEG-44 (F2:L187) | Comprobaciones y CI por stack | D24, D42, D43 | **PARCIAL** | Gates por stack definidos como política, comandos concretos para primer recorrido abiertos. |
| LEG-45 (F2:L188) | Estrategia de pruebas | D41, D42, D43, D44 | **CUBIERTA** | Estrategia de pruebas por riesgos, con E2E selectivos. |
| LEG-46 (F2:L189) | Trazabilidad automática | D16, D24 | **CUBIERTA** | Trazabilidad automática derivada y asociada a commits exactos. |
| LEG-47 (F2:L190) | Definition of Ready y Definition of Done | D21, D24, D25 | **PARCIAL** | No hay DoR/DoD precisos para Ready/Done, merge y release. |
| LEG-48 (F2:L191) | Revisión independiente | D07, D23, D45 | **CUBIERTA** | Revisión de specs y PR por jueces independientes, calibración y evidencia. |
| LEG-49 (F2:L192) | Entrega, despliegue y recuperación | D25, D55, D57 | **CUBIERTA** | Separación merge/publicación, respuesta y restauracion. |
| LEG-50 (F2:L193) | Feedback e incidencias | D17, D25, D38, D45 | **PARCIAL** | Feedback de producción contemplado pero bucle de incidentes y priorización sin definir. |
| LEG-51 (F2:L201) | Experimentos prioritarios | D45, D53, D54 | **PARCIAL** | Evals desde el inicio; protocolo inicial de experimentos aún no adoptado. |
| LEG-52 (F2:L202) | Protocolo reproducible de comparación | D43, D45, D46 | **CUBIERTA** | Comparaciones reproducibles y baseline versionada. |
| LEG-53 (F2:L203) | Métricas y criterios de aceptación | D37, D38, D45 | **PARCIAL** | Métricas definidas, criterios iniciales de aceptación v1 pendientes. |
| LEG-54 (F2:L204) | Separación del evaluador | D07, D23, D45 | **CUBIERTA** | Separación lógica de jueces; independencia técnica aún sin demostrar. |
| LEG-55 (F2:L205) | Informe y evidencias | D16, D38, D45 | **CUBIERTA** | Evidencias y trazas sin duplicación, retención y privacidad. |
| LEG-56 (F2:L213) | Contenido de la plantilla | D47, D48, D49 | **CUBIERTA** | Plantilla modular, configuración y bootstrap progresivo. |
| LEG-57 (F2:L214) | Instalación y reconstrucción | D49, D52, D57 | **PARCIAL** | Reconstruccion/instalación reproducible aún no probada en entorno limpio. |
| LEG-58 (F2:L215) | Actualizaciones y compatibilidad | D46, D47, D48, D52 | **CUBIERTA** | Actualizar con evals, versiones y compatibilidad del ejecutor. |
| LEG-59 (F2:L216) | Retención, copias y restauración | D56, D57 | **CUBIERTA** | Backups independientes, política de datos y restauracion de prueba. |
| LEG-60 (F2:L217) | Condiciones para añadir complejidad | D30, D32, D40, D46, D53 | **CUBIERTA** | Complejidad activada por utilidad demostrada y evoluciones reversibles. |

**Balance de diseño (solo inventario histórico):** 41 cubiertas + 15 parciales + 4 aplazadas = 60. **No es un porcentaje de calidad ni de software funcional.**

## 4. Catalogo inverso D00-D59 y agrupacion por dominios

Esta es una segunda comprobación: ninguna Dxx del registro nuevo debe quedar perdida durante la reconciliación. Algunas decisiones no aparecen en el inventario histórico porque las necesidades emergieron después.

| Decision actual | Tema / propósito aprobado | Referencias históricas (si las hay) |
|---|---|---|
| **D00** | Finalidad y ámbito del workflow | LEG-01, LEG-02, LEG-04 |
| **D01** | Descubrimiento guiado por IA | LEG-14 |
| **D02** | Descubrimiento progresivo | LEG-14 |
| **D03** | Especificación por capacidades | LEG-03 |
| **D04** | Visión global y specs de capacidad | LEG-08 |
| **D05** | Plantilla de especificación adaptable | LEG-08, LEG-15 |
| **D06** | Sintaxis e identificadores de requisitos | LEG-15 |
| **D07** | Revisión independiente de especificaciones | LEG-16, LEG-48, LEG-54 |
| **D08** | Aprobación humana verificable de specs | LEG-11, LEG-19, LEG-25, LEG-43 |
| **D09** | Cambios normales, triviales y urgentes | LEG-17, LEG-20 |
| **D10** | ADRs selectivos | LEG-08, LEG-10, LEG-18 |
| **D11** | Selección progresiva de tecnologías | LEG-04 |
| **D12** | Inicialización en dos etapas | LEG-08 |
| **D13** | Fuentes de verdad y papel de Notion | LEG-05, LEG-06, LEG-07, LEG-09, LEG-10 |
| **D14** | Estado temporal de descubrimiento | LEG-07, LEG-10, LEG-37 |
| **D15** | Requisitos transversales sin duplicación | Emergente en acuerdos posteriores |
| **D16** | Trazabilidad documental y de entrega | LEG-16, LEG-46, LEG-55 |
| **D17** | Evolución spec-first y control del desvío | LEG-10, LEG-17, LEG-50 |
| **D18** | Linear y planificación de entregas | LEG-08, LEG-27, LEG-28 |
| **D19** | Estructura inicial de Linear | LEG-27 |
| **D20** | Autonomía controlada sobre Linear | LEG-21, LEG-29 |
| **D21** | Estados de entrega en Linear | LEG-27, LEG-28, LEG-31, LEG-47 |
| **D22** | Ramas, PR/MR y worktrees | LEG-09, LEG-30, LEG-42 |
| **D23** | Revisión independiente de código | LEG-48, LEG-54 |
| **D24** | Controles obligatorios de CI y merge | LEG-30, LEG-31, LEG-44, LEG-46, LEG-47 |
| **D25** | Separar integración, publicación y recuperación | LEG-30, LEG-31, LEG-47, LEG-49, LEG-50 |
| **D26** | Roles y permisos efectivos de agentes | LEG-21, LEG-23, LEG-26 |
| **D27** | Protección frente a prompt injection | LEG-24 |
| **D28** | Gestión proporcional de secretos | LEG-23 |
| **D29** | Perfiles de aislamiento de ejecución | LEG-22, LEG-24, LEG-42 |
| **D30** | Catálogo gobernado de herramientas y MCP | LEG-23, LEG-24, LEG-36, LEG-60 |
| **D31** | Catálogo modular de roles de agentes | LEG-35 |
| **D32** | Orquestación híbrida y bajo demanda | LEG-38, LEG-60 |
| **D33** | Contratos ligeros de delegación | LEG-37, LEG-39 |
| **D34** | Persistencia operativa y reanudación | LEG-28, LEG-37, LEG-39, LEG-40 |
| **D35** | Paralelismo acotado y coordinación de recursos | LEG-41, LEG-42 |
| **D36** | Selección y sustitución de modelos | LEG-32, LEG-33, LEG-35 |
| **D37** | Presupuestos y límites de ejecución | LEG-26, LEG-33, LEG-41, LEG-53 |
| **D38** | Observabilidad y supervisión remota | LEG-11, LEG-25, LEG-26, LEG-39, LEG-43, LEG-50, LEG-53, LEG-55 |
| **D39** | Contrato verificable de aprobación | LEG-11, LEG-19, LEG-21, LEG-23, LEG-25, LEG-43 |
| **D40** | Orquestación y controles portables | LEG-32, LEG-34, LEG-37, LEG-38, LEG-60 |
| **D41** | Verificación diseñada a partir de specs | LEG-45 |
| **D42** | Pirámide de pruebas adaptable | LEG-44, LEG-45 |
| **D43** | Entornos y datos de prueba fiables | LEG-44, LEG-45, LEG-52 |
| **D44** | Calidad no funcional y atributos del producto | LEG-45 |
| **D45** | Evaluaciones del workflow y agentes | LEG-48, LEG-50, LEG-51, LEG-52, LEG-53, LEG-54, LEG-55 |
| **D46** | Evolución controlada del workflow | LEG-13, LEG-52, LEG-58, LEG-60 |
| **D47** | Núcleo SDD modular y reutilizable | LEG-09, LEG-12, LEG-13, LEG-34, LEG-36, LEG-56, LEG-58 |
| **D48** | Configuración declarativa por capas | LEG-13, LEG-34, LEG-56, LEG-58 |
| **D49** | Inicializador progresivo y repetible | LEG-12, LEG-56, LEG-57 |
| **D50** | Interfaz de uso orientada a comandos | Emergente en acuerdos posteriores |
| **D51** | Catálogo pequeño de comandos y skills | LEG-36 |
| **D52** | Independencia de OpenCode y Claude Code | LEG-12, LEG-22, LEG-32, LEG-33, LEG-34, LEG-43, LEG-57, LEG-58 |
| **D53** | Construcción incremental por recorridos completos | LEG-01, LEG-02, LEG-03, LEG-04, LEG-51, LEG-60 |
| **D54** | Inventario vivo y auditoría de cobertura | LEG-51 |
| **D55** | Continuidad controlada ante fallos externos | LEG-26, LEG-29, LEG-40, LEG-49 |
| **D56** | Clasificación y circulación de datos | LEG-23, LEG-59 |
| **D57** | Protección y recuperación de información | LEG-40, LEG-49, LEG-57, LEG-59 |
| **D58** | Dependencias y código de terceros | Emergente en acuerdos posteriores |
| **D59** | Evaluación híbrida y protegida del riesgo | LEG-20, LEG-21 |

## 5. Necesidades nuevas que no estaban articuladas en el inventario original

| ID de necesidad | Necesidad ampliada | Decisiones | Resultado de cobertura |
|---|---|---|---|
| N01 | Revisiones ciegas dobles según criticidad | D07, D23 | Cubierta en diseño; demostrar independencia real |
| N02 | Autorizaciones no falsificables ni reutilizables | D08, D39 | Cubierta en diseño; broker/gate pendiente |
| N03 | Requisitos transversales canónicos | D15, D16 | Cubierta en diseño |
| N04 | Politicas anti-inyeccion y límites de herramientas | D26, D27, D29, D30 | Cubierta en diseño; prueba adversarial pendiente |
| N05 | Sustitucion de modelos y test de harness | D36, D40, D52 | Cubierta en diseño; pruebas de compatibilidad pendientes |
| N06 | Observabilidad de presupuesto y coste por tarea | D37, D38, D45 | Cubierta en diseño; establecer baseline v1 |
| N07 | Gobernanza de datos por destino y finalidad | D28, D56 | Cubierta en diseño; enforcement pendiente |
| N08 | Dependencias de terceros y scripts de instalación | D29, D58 | Cubierta en diseño; controles por ecosistema pendientes |
| N09 | Clasificacion triple del riesgo | D09, D26, D59 | Cubierta en diseño; taxonomia operativa pendiente |
| N10 | Continuidad degradada ante fallos de proveedores | D34, D55 | Cubierta en diseño; pruebas de reconciliación pendientes |
| N11 | Backup independiente y restauracion | D57 | Cubierta en diseño; no acreditada |
| N12 | Auditoría de cobertura y necesidades | D54 | Cubierta en diseño; este informe es primera pasada documental |
| N13 | Procedimientos portables, interfaces por comandos | D47, D48, D50, D51 | Cubierta en diseño; adapters sin probar |
| N14 | Derivacion futura de edicion profesional reducida | D00, D47 | Objetivo futuro, no alcance v1 |

La lista es una **línea base contrastada con materiales recuperables**, no el universo demostrado de todas las necesidades que alguna vez se mencionaron oralmente. La auditoría de necesidades sigue abierta cuando falten fuentes literales.

## 6. Registro de hallazgos, diagnóstico y pruebas de cierre

Los hallazgos no modifican ninguna Dxx. La propuesta de solución es de la auditoría y requiere confirmación donde introduzca política nueva.

| ID | Prioridad | Naturaleza | Hallazgo | Decisiones/fuentes |
|---|---|---|---|---|
| **H01** | BLOQUEANTE_DOC | Procedencia | La consolidacion no es prueba literal de todas las aprobaciones | Registro ampliado, sección 0 y 8; histórico, sección 3 |
| **H02** | BLOQUEANTE_V1 | Seguridad | Ejecución efectiva de las aprobaciones verificables sin depender del agente | D08 D21 D24 D39 D59 |
| **H03** | BLOQUEANTE_V1 | Calidad | Independencia operativa de los dos revisores de specs y código | D07 D23 D31 D36 D37 D52 D53 |
| **H04** | BLOQUEANTE_V1 | Entrega | Gates reales de CI, protección de main y evidencia de commit exacto | D22 D23 D24 D25 D41 D43 |
| **H05** | BLOQUEANTE_V1 | Seguridad | Permisos, sandbox y salidas de datos sin prueba en Windows | D26 D27 D28 D29 D30 D52 D56 D58 D59 |
| **H06** | BLOQUEANTE_V1 | Conocimiento | Recuperación de contexto vigente antes de especificar o implementar | D10 D13 D14 D15 D17 D33 D34; notas, sección RAG |
| **H07** | BLOQUEANTE_V1 | Preparación | Primer vertical slice y DoR/DoD no operacionalizados | D03 D08 D21 D24 D25 D53; legado LEG-03 LEG-31 LEG-47 |
| **H08** | IMPORTANTE | Movilidad | Alcance original de operación completa desde iPhone se ha debilitado | Legado sección 2, LEG-11 LEG-25 LEG-43; D08 D38 D39 D52 |
| **H09** | IMPORTANTE | Incidentes | Parada de emergencia y respuesta ante incidente no están detalladas | Legado LEG-26; D26 D28 D37 D38 D39 D55 |
| **H10** | IMPORTANTE | Descubrimiento | Ingesta multimodal tiene reglas históricas, no decisión operativa vigente | Notas, líneas 472-524; D01 D02 D56 |
| **H11** | IMPORTANTE | Producto | Feedback de producción e incidentes no tienen circuito operativo completo | Notas, sección Feedback; legado LEG-50; D17 D25 D38 D45 |
| **H12** | IMPORTANTE | Confianza | Doble revisión automática y coste/tiempo pueden competir | D07 D23 D36 D37 D45 D53 |
| **H13** | IMPORTANTE | Gobierno | Se necesita fuente de autoridad para estado de decisión vs autorización ejecutable | D08 D10 D13 D39 D47 D48; registro ampliado sección 0 |
| **H14** | IMPORTANTE | Trazabilidad | Integridad de referencias y procedencia automática por capability | D15 D16 D17 D21 D24 D54 |
| **H15** | IMPORTANTE | Integraciones | Linear, Git y Notion requieren contratos de reconciliación de estados | D13 D18 D20 D21 D34 D55 |
| **H16** | IMPORTANTE | Configuración | Precedencia de políticas y mecanismos de no debilitamiento | D26 D29 D30 D39 D40 D48 D52 D59 |
| **H17** | IMPORTANTE | Dependencias | No se ha probado seguridad de instalación con scripts de terceros | D28 D29 D30 D58 |
| **H18** | IMPORTANTE | Calidad | Métricas de éxito iniciales y comparación de baseline aún abiertas | D37 D38 D45 D46 D53; legado LEG-51 LEG-53 |
| **H19** | IMPORTANTE | Mantenimiento | Reconstruccion del núcleo/adapter desde entorno limpio sin test | D47 D48 D49 D52 D57; legado LEG-57 |
| **H20** | IMPORTANTE | Documentos | Promocion Notion/descubrimiento hacia Git no tiene protocolo concreto | D12 D13 D14 D17 |
| **H21** | MEJORA | Taxonomía | Numeración Dxx histórica y nueva puede generar errores en otras sesiones | Legado sección 4; registro ampliado sección 6 |
| **H22** | MEJORA | Alcance | Modelos, suscripciones, stack y skills concretas aplazadas legítimamente | D11 D30 D36 D47 D52; legado LEG-33 LEG-36 |
| **H23** | MEJORA | Sostenibilidad | Posible solapamiento de contratos y checklists transversales | D07 D08 D16 D23 D24 D26 D33 D34 D39 D45 D48 D54 D59 |
| **H24** | MEJORA | Documento | Anexos históricos pueden parecer políticas ya aprobadas | Registro ampliado, secciones 9-11 |

### H01 - La consolidacion no es prueba literal de todas las aprobaciones
**Prioridad:** BLOQUEANTE_DOC  |  **Clase:** Procedencia  |  **Referencias:** Registro ampliado, sección 0 y 8; histórico, sección 3
- **Diagnóstico:** El registro vigente es una paráfrasis fiable a nivel de resumen, pero no enlaza cada Dxx a un turno comprobable. El legado D01-D60 tiene otra numeración y estados históricos por confirmar. Un auditor no puede certificar fidelidad textual completa desde estas fuentes.
- **Tratamiento sugerido (no aprobado):** Conservar D00-D59 como acuerdos declarados y etiquetar fidelidad documental como provisional; añadir referencias de confirmación original cuando se obtengan. No reasignar IDs antiguos.
- **Evidencia de cierre propuesta:** Para cada Dxx, ID estable + fuente de acuerdo o marca de procedencia limitada; cambios aprobados no se infieren de anexos.

### H02 - Ejecución efectiva de las aprobaciones verificables sin depender del agente
**Prioridad:** BLOQUEANTE_V1  |  **Clase:** Seguridad  |  **Referencias:** D08 D21 D24 D39 D59
- **Diagnóstico:** Se define el contrato de autorización, pero no existe mecanismo ni integración probada que impida cambiar a Ready, ejecutar operaciones protegidas o hacer merge sin comprobante valido, vigente y con scope exacto.
- **Tratamiento sugerido (no aprobado):** Especificar un gate mínimo independiente del texto del agente; mantener operaciones sensibles manuales hasta verificarlas; documentar quién firma y donde se comprueba.
- **Evidencia de cierre propuesta:** Pruebas negativas: aprobar revisión A no autoriza B; mensajes falsos; caducidad y revocación; cambio de commit; intento directo de bypass.

### H03 - Independencia operativa de los dos revisores de specs y código
**Prioridad:** BLOQUEANTE_V1  |  **Clase:** Calidad  |  **Referencias:** D07 D23 D31 D36 D37 D52 D53
- **Diagnóstico:** Blindaje conceptual establecido, pero el primer flujo requiere revisores realmente aislados en contexto y hallazgos. No se ha demostrado factibilidad/coste con el ejecutor disponible.
- **Tratamiento sugerido (no aprobado):** Definir contrato mínimo de independencia y entradas de cada revisor; orquestar dos sesiones aisladas o limitar primeras pruebas a cambios triviales cuando D09 lo permita.
- **Evidencia de cierre propuesta:** Traza de dos revisores independientes, sin acceso a hallazgos previos; reconciliación y límites de iteracion.

### H04 - Gates reales de CI, protección de main y evidencia de commit exacto
**Prioridad:** BLOQUEANTE_V1  |  **Clase:** Entrega  |  **Referencias:** D22 D23 D24 D25 D41 D43
- **Diagnóstico:** Los controles están aprobados pero GitHub/GitLab, permisos y checks no están elegidos o demostrados para un proyecto concreto.
- **Tratamiento sugerido (no aprobado):** Definir un repositorio temporal y configurar el gate mínimo aplicable al primer flujo sin permitir que el agente lo modifique.
- **Evidencia de cierre propuesta:** PR fallida no fusionable; checks de SHA antiguo invalidados; bypass con permisos del agente imposible; pruebas del camino correcto.

### H05 - Permisos, sandbox y salidas de datos sin prueba en Windows
**Prioridad:** BLOQUEANTE_V1  |  **Clase:** Seguridad  |  **Referencias:** D26 D27 D28 D29 D30 D52 D56 D58 D59
- **Diagnóstico:** Hay políticas de mínimo privilegio y egress por destino, pero no se ha demostrado el mecanismo efectivo en PowerShell/Windows ni en OpenCode/Claude Code.
- **Tratamiento sugerido (no aprobado):** Inventariar capacidades reales del harness y OS; ejecutar pruebas sintéticas de lectura prohibida, red, instaladores y secretos antes de habilitar ejecución sensible.
- **Evidencia de cierre propuesta:** Pruebas controladas muestran rechazo de archivos fuera de alcance y salida de datos no autorizada; excepciones registradas.

### H06 - Recuperación de contexto vigente antes de especificar o implementar
**Prioridad:** BLOQUEANTE_V1  |  **Clase:** Conocimiento  |  **Referencias:** D10 D13 D14 D15 D17 D33 D34; notas, sección RAG
- **Diagnóstico:** La autoridad está clara pero no hay procedimiento aprobado con orden de busqueda, selección de relevancia, vigencia, contradicciones e incertidumbre. El material original lo solicita expresamente.
- **Tratamiento sugerido (no aprobado):** Proponer recuperación progresiva por rutas/IDs/símbolos primero y semántica solo si falla; comprobar status y aprobación de cada fuente; sin motor RAG propio inicial.
- **Evidencia de cierre propuesta:** Caso con spec vigente y obsoleta: el agente referencia la vigente y no usa instrucciones históricas.

### H07 - Primer vertical slice y DoR/DoD no operacionalizados
**Prioridad:** BLOQUEANTE_V1  |  **Clase:** Preparación  |  **Referencias:** D03 D08 D21 D24 D25 D53; legado LEG-03 LEG-31 LEG-47
- **Diagnóstico:** D53 aprueba el enfoque, pero faltan alcance mínimo, condiciones para pasar a Ready/Done, salida ante CI fallida y definición de integración verificada.
- **Tratamiento sugerido (no aprobado):** Proponer una matriz de capacidades habilitadas y criterios de entrada/salida del primer recorrido, antes de activar automatizaciones.
- **Evidencia de cierre propuesta:** Escenario simple recorre entrevista-spec-aprobación-issue-rama-pruebas-revisión-PR-CI-merge; negativo se bloquea.

### H08 - Alcance original de operación completa desde iPhone se ha debilitado
**Prioridad:** IMPORTANTE  |  **Clase:** Movilidad  |  **Referencias:** Legado sección 2, LEG-11 LEG-25 LEG-43; D08 D38 D39 D52
- **Diagnóstico:** El requerimiento histórico dice operar completamente desde iPhone; las decisiones nuevas hablan de supervision, aprobaciones y operación móvil cuando sea posible. No hay una aceptación explícita de rebajar ese objetivo.
- **Tratamiento sugerido (no aprobado):** Mantener operación completa como necesidad a validar y concretar acciones minimas por fase, notificaciones, evidencias, rechazo, pausa y fallo de acceso; acordar lo que queda para fases posteriores.
- **Evidencia de cierre propuesta:** Ensayo E09 real en iPhone: iniciar, preguntar, revisar, aprobar/rechazar, detener, recuperar, consultar evidencias y cambiar de proyecto.

### H09 - Parada de emergencia y respuesta ante incidente no están detalladas
**Prioridad:** IMPORTANTE  |  **Clase:** Incidentes  |  **Referencias:** Legado LEG-26; D26 D28 D37 D38 D39 D55
- **Diagnóstico:** Pausa/reanudación y recuperación están tratadas, pero una parada por sospecha de fuga, revocación masiva o bloqueo de todos los workers requiere un procedimiento distinto.
- **Tratamiento sugerido (no aprobado):** Definir kill switch proporcional, respuesta a incidentes y acciones después del bloqueo; activar solo cuando existan operaciones persistentes o privilegiadas.
- **Evidencia de cierre propuesta:** Simular interrupción, revocación, cuarentena de logs y recuperación sin acciones residuales.

### H10 - Ingesta multimodal tiene reglas históricas, no decisión operativa vigente
**Prioridad:** IMPORTANTE  |  **Clase:** Descubrimiento  |  **Referencias:** Notas, líneas 472-524; D01 D02 D56
- **Diagnóstico:** Audio/video/capturas/diagramas, procedencia, observación frente a inferencia y validación figuran en las notas originales; no hay contrato aprobado de procesamiento ni de privacidad de esos materiales.
- **Tratamiento sugerido (no aprobado):** Registrar necesidad como candidata; decidir alcance según primer proyecto. Mantener materiales no confiables como datos, no instrucciones.
- **Evidencia de cierre propuesta:** Caso visual con dato ambiguo: transcripción/inferencia separadas, confirmación humana antes de elevarlo a spec.

### H11 - Feedback de producción e incidentes no tienen circuito operativo completo
**Prioridad:** IMPORTANTE  |  **Clase:** Producto  |  **Referencias:** Notas, sección Feedback; legado LEG-50; D17 D25 D38 D45
- **Diagnóstico:** Se habla de monitorizar tras publicar y mejorar evals, pero faltan entradas, severidades, diagnóstico, reenlace a spec, reproducción, priorización y comunicacion de resultados.
- **Tratamiento sugerido (no aprobado):** Disenar circuito ligero cuando la primera publicación externa sea parte del alcance; no requerir telemetria productiva para un ejercicio local sin usuarios.
- **Evidencia de cierre propuesta:** Un bug real enlaza error, spec/AC afectados, prueba de regresion, issue y release correctora.

### H12 - Doble revisión automática y coste/tiempo pueden competir
**Prioridad:** IMPORTANTE  |  **Clase:** Confianza  |  **Referencias:** D07 D23 D36 D37 D45 D53
- **Diagnóstico:** Ambos puntos son obligatorios para cambios normales/relevantes; faltan presupuestos iniciales y estrategia ante el fallo de un juez sin relajar el mínimo.
- **Tratamiento sugerido (no aprobado):** Crear plan de degradación seguro: si no hay dos jueces, bloquear o usar excepción D09 solo si el cambio es genuinamente trivial y ha sido justificado; nunca reclasificar para eludir revisores; no sustituir un juez por autoafirmacion.
- **Evidencia de cierre propuesta:** Eval negativa con revisor indisponible: no se declara revisado un PR relevante.

### H13 - Se necesita fuente de autoridad para estado de decisión vs autorización ejecutable
**Prioridad:** IMPORTANTE  |  **Clase:** Gobierno  |  **Referencias:** D08 D10 D13 D39 D47 D48; registro ampliado sección 0
- **Diagnóstico:** Git es autoridad documental, pero escribir un archivo de aprobación en Git no prueba quién lo autorizó; hay que conectar registro verificable y documentos sin que el agente se pueda autoautorizar.
- **Tratamiento sugerido (no aprobado):** Definir enlace entre versión aprobada, firma/identidad/operación y comprobante inmutable donde sea viable.
- **Evidencia de cierre propuesta:** Modificar el YAML de aprobación desde rama controlada no debe habilitar ejecución protegida.

### H14 - Integridad de referencias y procedencia automática por capability
**Prioridad:** IMPORTANTE  |  **Clase:** Trazabilidad  |  **Referencias:** D15 D16 D17 D21 D24 D54
- **Diagnóstico:** La matriz derivada y las comprobaciones semanticas están acordadas, pero faltan convenciones de IDs, ciclo de vida y como enlazar una spec multi-issue, tests y commits.
- **Tratamiento sugerido (no aprobado):** Consolidar contratos mínimos de requisitos/AC y referencias canónicas; generar vistas sin duplicar contenido.
- **Evidencia de cierre propuesta:** Borrar AC o cambiar ID causa aviso; PR enlaza pruebas correspondientes y vigencia de spec.

### H15 - Linear, Git y Notion requieren contratos de reconciliación de estados
**Prioridad:** IMPORTANTE  |  **Clase:** Integraciones  |  **Referencias:** D13 D18 D20 D21 D34 D55
- **Diagnóstico:** La autoridad de cada sistema está definida, pero duplicados, escrituras inciertas y sincronización de estados concretos no están detallados para adaptadores.
- **Tratamiento sugerido (no aprobado):** Definir para cada operación idempotencia, lectura posterior, registro de fallo y resolución de conflicto sin copia normativa de specs.
- **Evidencia de cierre propuesta:** Simular timeout tras create issue y comprobar que la reanudación no duplica.

### H16 - Precedencia de políticas y mecanismos de no debilitamiento
**Prioridad:** IMPORTANTE  |  **Clase:** Configuración  |  **Referencias:** D26 D29 D30 D39 D40 D48 D52 D59
- **Diagnóstico:** D48 establece una jerarquía declarativa, pero no un esquema verificable de composicion ni una prueba de configuración efectiva por ejecutor.
- **Tratamiento sugerido (no aprobado):** Definir reglas minimas y test de conformidad antes de habilitar adaptador: un override local no desactiva un bloqueo superior.
- **Evidencia de cierre propuesta:** Test de configuración con una política protectora y un override de proyecto contradictorio debe fallar.

### H17 - No se ha probado seguridad de instalación con scripts de terceros
**Prioridad:** IMPORTANTE  |  **Clase:** Dependencias  |  **Referencias:** D28 D29 D30 D58
- **Diagnóstico:** La política es clara, pero los gestores de paquetes varian por SO y un lockfile no elimina scripts de postinstalacion ni acceso a red.
- **Tratamiento sugerido (no aprobado):** Asegurar sandbox/capacidades antes de instalar deps de prueba y segregar secretos; sin SBOM universal por defecto.
- **Evidencia de cierre propuesta:** Dependencia sintética intenta leer dato fuera de alcance y debe ser bloqueada.

### H18 - Métricas de éxito iniciales y comparación de baseline aún abiertas
**Prioridad:** IMPORTANTE  |  **Clase:** Calidad  |  **Referencias:** D37 D38 D45 D46 D53; legado LEG-51 LEG-53
- **Diagnóstico:** Las evals definen método general, pero los protocolos E00-E10 son históricos y no han sido promovidos a programa autorizado; faltan criterios de aceptación y umbrales razonables para el primer slice.
- **Tratamiento sugerido (no aprobado):** Seleccionar conjunto pequeno de casos reales y adversariales y medidas de calidad/coste/latencia comparables; fijar criterios de pasar/fallar antes de cada experimento.
- **Evidencia de cierre propuesta:** Demostrar un caso positivo, fallos rechazados y continuidad de una sesión sin falsos positivos.

### H19 - Reconstruccion del núcleo/adapter desde entorno limpio sin test
**Prioridad:** IMPORTANTE  |  **Clase:** Mantenimiento  |  **Referencias:** D47 D48 D49 D52 D57; legado LEG-57
- **Diagnóstico:** La portabilidad y backups aprobados no demuestran que otro Windows o herramienta reproduzca el sistema.
- **Tratamiento sugerido (no aprobado):** Definir README de bootstrap, scripts idempotentes, versionado de adaptadores y restauracion sin secretos exportados.
- **Evidencia de cierre propuesta:** Montar proyecto vacio, seleccionar un ejecutor y ejecutar smoke/conformidad desde cero.

### H20 - Promocion Notion/descubrimiento hacia Git no tiene protocolo concreto
**Prioridad:** IMPORTANTE  |  **Clase:** Documentos  |  **Referencias:** D12 D13 D14 D17
- **Diagnóstico:** La separación de fuentes es valida; queda abierta la mecánica para migrar idea, mantener enlace de procedencia y evitar dos documentos vigentes.
- **Tratamiento sugerido (no aprobado):** Definir un paso de promoción de autoridad: crear documento Git, enlazar Notion como referencia histórica, retirar cualquier doble edicion normativa.
- **Evidencia de cierre propuesta:** Una idea promovida conserva origen y no queda una segunda spec editable en Notion.

### H21 - Numeración Dxx histórica y nueva puede generar errores en otras sesiones
**Prioridad:** MEJORA  |  **Clase:** Taxonomía  |  **Referencias:** Legado sección 4; registro ampliado sección 6
- **Diagnóstico:** Se reutilizaron etiquetas D01-D60 en dos inventarios independientes. Un agente podría citar LEG-39 pensando en D39.
- **Tratamiento sugerido (no aprobado):** Renombrar catalogo histórico como LEG-01..LEG-60 en toda referencia nueva, sin modificar archivo histórico.
- **Evidencia de cierre propuesta:** En referencias nuevas las claves LEG-xx y Dxx se distinguen sin ambigüedad.

### H22 - Modelos, suscripciones, stack y skills concretas aplazadas legítimamente
**Prioridad:** MEJORA  |  **Clase:** Alcance  |  **Referencias:** D11 D30 D36 D47 D52; legado LEG-33 LEG-36
- **Diagnóstico:** El diseño evita decisiones prematuras. No conocer precio/plan/modelo o no elegir skills concretas hoy no constituye por si solo una omisión de arquitectura.
- **Tratamiento sugerido (no aprobado):** Mantener decisiones abiertas vinculadas al momento de activación de cada capacidad; verificar condiciones actuales antes de contratar o habilitar.
- **Evidencia de cierre propuesta:** El primer ejecutor disponible supera matriz mínima de conformidad y no se transforma en estandar obligatorio.

### H23 - Posible solapamiento de contratos y checklists transversales
**Prioridad:** MEJORA  |  **Clase:** Sostenibilidad  |  **Referencias:** D07 D08 D16 D23 D24 D26 D33 D34 D39 D45 D48 D54 D59
- **Diagnóstico:** Revisiones, aprobaciones, evidencias y niveles de riesgo aparecen en multiples decisiones. No hay contradiccion evidente, pero si riesgo de implementar varias fuentes editables o servicios independientes.
- **Tratamiento sugerido (no aprobado):** Reutilizar contratos de evidencia, policy enforcement y estado; no exigir subsistemas nuevos para cada Dxx.
- **Evidencia de cierre propuesta:** Una operación tiene un único registro canónico de aprobación y cada gate lo referencia.

### H24 - Anexos históricos pueden parecer políticas ya aprobadas
**Prioridad:** MEJORA  |  **Clase:** Documento  |  **Referencias:** Registro ampliado, secciones 9-11
- **Diagnóstico:** El documento es completo pero mezcla decisiones, propuestas de procedimientos y extensos anexos históricos; el lector podría interpretarlos como reglas vigentes.
- **Tratamiento sugerido (no aprobado):** Mantener encabezados NO APROBADO y crear indice de estado por fragmento; evitar que AGENTS.md copie anexos completos como obligatorios.
- **Evidencia de cierre propuesta:** Verificador documental detecta un anexo histórico citado como norma sin nueva aprobación.

## 7. Revisión cruzada de coherencia y tensiones relevantes

### Piloto histórico vs no seleccionarlo hoy
- **Cruce:** Histórico LEG-01..04; D00 D53. **Dictamen:** NO contradiccion vigente.
- **Resolución sugerida:** D00/D53 sustituyen el requisito de seleccionar piloto ahora. Mantener referencia al proyecto existente como dato histórico sin convertirlo en obligacion.

### OpenCode históricamente principal vs arquitectura agnóstica
- **Cruce:** Propuesta `Texto pegado(4).txt`; D40 D47 D52. **Dictamen:** NO contradiccion vigente.
- **Resolución sugerida:** D52 es posterior y prevalece. OpenCode y OpenChamber pueden ser opciones reales sin estar preelegidas para todas las capacidades.

### Operación COMPLETA desde iPhone vs supervision remota IDEAL
- **Cruce:** Histórico LEG-43 y sección 2; D38 D39. **Dictamen:** POSIBLE pérdida de alcance.
- **Resolución sugerida:** Preservar la necesidad original hasta confirmación: concretar operaciones completas, no suponer que solo aprobar/notificar la satisface.

### Doble revisión IA y proceso inicial simple
- **Cruce:** D07 D23 D37 D53. **Dictamen:** TENSION operativa, no contradiccion.
- **Resolución sugerida:** Primer slice normal/relevante requiere dos revisores verdaderamente independientes o mantener el alcance limitado a cambios trivialmente exceptuables según D09.

### Autonomía vs aprobación ineludible
- **Cruce:** D20 D26 D32 D39 D59. **Dictamen:** COMPATIBLE CON CONTROLES.
- **Resolución sugerida:** El modelo propone y ejecuta lo previamente permitido, pero los gates y autorizaciones viven fuera del agente.

### Trabajo seguro offline vs fuente externa Linear
- **Cruce:** D18 D20 D34 D55. **Dictamen:** COMPATIBLE CON RECONCILIACION.
- **Resolución sugerida:** Solo continuar acciones independientes; escrituras inciertas se confirman antes de reintentar.

### Contexto histórico en anexos vs autoridades vigentes
- **Cruce:** D10 D13 D14 D17; documento sección 11. **Dictamen:** RIESGO DOCUMENTAL.
- **Resolución sugerida:** Etiquetar anexos como históricos y filtrar por vigencia/aprobación antes de alimentar agentes.

### Minimo de core portable vs adaptadores muy potentes
- **Cruce:** D40 D47 D48 D52. **Dictamen:** TENSION de complejidad.
- **Resolución sugerida:** Mantener interfaces diminutas por capacidad; evaluar separación funcional/seguridad y no construir wrappers de todo el ejecutor.

### Independencia entre revisores vs mismo modelo/proveedor
- **Cruce:** D07 D23 D31 D36. **Dictamen:** PUNTO DE VALIDACION.
- **Resolución sugerida:** Ceguera de contexto obligatoria; proveedores/modelos distintos pueden mejorar diversidad pero no son exigencia universal aprobada.

### Git como autoridad vs registros firmados de aprobación
- **Cruce:** D08 D13 D39. **Dictamen:** COMPATIBLE SOLO SI HAY VALIDACION EXTERNA.
- **Resolución sugerida:** Un commit no es autorización; comprobar identidad/alcance en registro no falsificable por agentes.

### Pruebas positivas en E00-E10 vs controles de seguridad obligatorios
- **Cruce:** D24 D27 D29 D45 D53. **Dictamen:** COMPATIBLE CON ACLARACION.
- **Resolución sugerida:** Que un experimento pase no sustituye permisos ni CI obligatoria para la operación habilitada.

## 8. Escenarios adversariales y criterios de verificación propuestos

| Caso | Dxx aplicables | Resultado esperado | Prioridad por activación |
|---|---|---|---|
| Aprobación falsa escrita por un agente | D08 D39 D59 | Gate rechaza autenticidad/alcance insuficiente | Primer slice |
| Aprobación para spec SHA A reutilizada tras editarla a SHA B | D08 D17 D39 | Nueva revisión bloquea implementación protegida | Primer slice |
| Cambio de commit tras CI verde | D22 D24 | Merge bloqueado hasta checks correspondientes | Primer slice |
| Dos revisores leen hallazgos del otro | D07 D23 | Se detecta contaminacion y no se acredita doble revisión | Primer slice |
| Una spec histórica contradice la aprobada | D10 D13 D17 | Se utiliza autoridad vigente o se detiene y pregunta | Primer slice |
| Script de paquete intenta leer un secreto | D28 D29 D58 | Acceso prohibido por mecanismos efectivos | Antes de instalar terceros |
| README malicioso pide publicar un token | D27 D56 | Tratar como dato no autorizado y bloquear egress | Primer slice de seguridad |
| Agente intenta cambiar política superior vía config local | D26 D48 D59 | Conflicto detectado y protección intacta | Antes de permisos automáticos |
| Linear falla después de crear issue | D20 D34 D55 | Consultar estado; no duplicar | Antes de escrituras automáticas |
| Proveedor de modelo cae y falla revisor 2 | D07 D23 D36 D55 | No se declara verificada entrega relevante | Primer slice |
| Dos agentes escriben el mismo recurso | D22 D35 | Se serializa, reasigna o rechaza | Al habilitar paralelismo |
| Usuario revoca aprobación antes de ejecución | D39 D55 | Se rechaza aunque exista checkpoint antiguo | Primer slice |
| Restauracion sin credenciales ni maquina original | D28 D57 | Reconstruir artefactos esenciales sin fugas | Antes de declarar resiliencia |
| Operación móvil: rechazar spec desde iPhone | D08 D38 D39 | Denegacion efectiva y auditable | Al habilitar móvil |
| Incidente de seguridad con sesiones persistentes | D26 D37 D38 D55 | Parada y revocación efectivas, sin reintentos residuales | Al habilitar autonomía prolongada |
| Cambio visual a partir de una captura ambigua | D01 D02 D56 | Observación separada de inferencia; decisión humana | Al habilitar multimedia |
| Cambio de riesgo por acceso posterior a producción | D26 D59 | Nueva evaluación y nuevos permisos | Antes de producción |

## 9. Preparación realista para el primer recorrido SDD

**Distincion:** D53 aprueba un enfoque incremental; el siguiente checklist es una propuesta de implantación, no un alcance v1 ya ratificado. No necesita elegir ahora un producto piloto real.

### Minimo de arquitectura antes de ejecutar código o integrar

- [ ] Reconciliar fuentes del caso y mostrar spec vigente, ADR relevante y AC; el resto no se inventa (H06).
- [ ] Poder producir una spec versionada, someterla a los dos jueces cuando sea relevante y comprobar aprobación fuera del agente (H02, H03).
- [ ] Definir alcance real de la primera entrega, Ready y Done, y que operaciones quedan sin habilitar (H07).
- [ ] Obtener un repo aislado con gates y resultado ligado al commit, y verificar rechazo de CI fallida (H04).
- [ ] Controlar permisos, archivos, red, instaladores y secretos con capacidades comprobadas, no instrucciones verbales (H05).
- [ ] Probar una secuencia positiva y al menos tres negativas: aprobación invalida, CI fallida, contexto obsoleto (H02, H04, H06).
- [ ] Registrar gastos, resultados y evidencias de manera suficiente para repetir una evaluación y corregir fallos (H18).
- [ ] No declarar integrada/publicada una entrega solo porque el agente o Linear lo afirmen (D21 D24 D25).

### Capacidades cuya complejidad NO hace falta instalar hoy

Multiagentes paralelos, orquestador propio, RAG semántico dedicado, automatización completa de Linear, proveedor de modelos definitivo, segundo ejecutor, despliegue productivo y réplicas exhaustivas de todos los sistemas. Su aplazamiento solo es válido si ninguna actividad habilitada incumple los controles aprobados.

### Orden de resolución de pendientes antes de redactar una baseline v1

1. Garantizar procedencia y clasificación del registro maestro (H01 y H24); no convertir anexos en política.
2. Decidir/consolidar alcance y criterios de entrada/salida del primer recorrido (H07), sin elegir todavía producto real.
3. Concretar contexto vigente, ID/AC y procedimientos de trazabilidad (H06, H14).
4. Definir implementación de aprobaciones, revisores y gates de Git/CI (H02-H04, H13).
5. Verificar controles efectivos de ejecutor y entorno y registrar pruebas E00, E03, E07, E09 según capacidades (H05, H08, H16).
6. Cerrar o aplazar explícitamente necesidades históricas no esenciales: multimedia, incidentes, feedback y movilidad completa, sin convertir aplazamiento en abandono (H08-H11).

## 10. Decisiones que NO recomiendo tomar ahora

- No decidir hoy OpenCode frente a Claude Code ni la marca de cada modelo: D52 exige evaluación por capacidades.
- No seleccionar una lista final de skills de terceros: D30, D47 y D51 recomiendan adopcion por necesidad verificada.
- No imponer RAG propio sin haber probado busqueda por rutas, IDs y símbolos.
- No definir de manera uniforme umbrales NFR, costes ni frecuencias de backup para todos los proyectos.
- No convertir cada hallazgo en una nueva Dxx; algunos se resuelven al concretar contratos o comprobar controles existentes.
- No considerar D60 aprobada por el hecho de haber creado este documento.

## 11. Límites de la auditoría y estado de cierre

| Dimensión | Resultado acreditado | Lo que NO se acredita |
|---|---|---|
| Integridad de 60 acuerdos | IDs D00-D59 encontrados una vez en registro ampliado | Transcripción literal completa y links a confirmaciones individuales |
| Reconciliación histórica | 60 temas antiguos mapeados de manera cualitativa | Que el inventario original cubriera todas las necesidades reales |
| Cobertura de diseño | Mapa y hallazgos razonados según fuentes | Implantacion ni cumplimiento técnico |
| Consistencia | Cruces entre decisiones y tensiones identificadas | Certificacion formal por dos jueces ciegos independientes |
| Viabilidad | Riesgos de integración y pruebas de conformidad concretas | Windows/PowerShell, iPhone, OpenCode, Claude Code o permisos realmente probados |
| Seguridad | Escenarios de fallo y bloqueos definidos | Escaneo, pentest ni policy enforcement en ejecución |
| D60 | Sigue pendiente | Cierre formal de diseño v1 |

## 12. Fuentes y localizacion reproducible

Las citas `sección` y `Dxx` son referencias de contenido; las rutas siguientes permiten buscar el origen, pero no son referencias URL externas. Los documentos históricos contienen propuestas no autorizadas.

- **F1:** `Registro_SDD_D00-D59_Ampliado_Contexto_Portable.md` - encabezados `#### D00` a `#### D59`, secciones 0, 5-11. Fuente principal.
- **F2:** `workflow/SEGUIMIENTO-WORKFLOW-SDD-IA.md` - sección 2 (necesidades originales), sección 4 (LEG-01..LEG-60), sección 7 (E00-E10). Inventario histórico, no acuerdos vigentes.
- **F3:** `Texto pegado(1).txt` - `// Agentes multimodal`, `//RAG`, `//OBSERVABILIDAD`, `//CI/CD agentico`, `//Feeback`. Recomendaciones y borradores.
- **F4:** `Texto pegado(4).txt` - propuesta histórica `Flujo de trabajo completo: Linear + Git + OpenCode`; ha sido matizada/sustituida por D52 en elección de ejecutor.
- **F5:** `sdd_validation_pack/EXPERIMENTOS.md` - protocolos originales E00-E10, sin evidencia de pruebas del entorno personal.

---

**Estado editorial:** auditoría documental preliminar COMPLETADA con los materiales disponibles; auditoría formal independiente, pruebas de conformance y cierre de hallazgos PENDIENTES. El propietario de decisiones sigue siendo el usuario. Cualquier regla o procedimiento nuevo sugerido aquí debe revisarse y aprobarse individualmente.

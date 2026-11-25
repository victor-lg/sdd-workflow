# Workflow SDD + IA

Repositorio del propio workflow: qué se ha decidido, qué está pendiente, las plantillas que se copiarán a cada proyecto y el material histórico. Todo en Markdown plano.

- **Versión del workflow:** v1.0 (declarada el 2026-11-05): dos recorridos completos, casos negativos N1–N8 y pruebas C18–C20.
- **Siguiente hito:** v1.1, por bloques (`docs/plan-v1.1.md`).
- **Última revisión:** 2026-11-05.

## Cómo leer este repositorio

- **Quiero saber qué es norma (o lo será):** `docs/linea-base-v1.md`.
- **Quiero saber qué toca hacer ahora:** `docs/hoja-de-ruta.md` y `docs/plan-v1.1.md`.
- **Quiero saber qué significa un código o cómo se nombra algo:** `docs/glosario.md` y `docs/convenciones.md`.
- **Quiero preparar el entorno:** `docs/guia-instalacion.md`.
- **Quiero saber qué está pendiente de decidir:** sección 14 de `docs/linea-base-v1.md` (Q01–Q09 cerradas).
- **Quiero ver una decisión ya tomada:** `docs/adr/` (ADR-0001 capa normativa; ADR-0002 ejecutor y perfiles de modelo; ADR-0003 plataforma y seguimiento; ADR-0004 Q05–Q09; ADR-0005 identidad del agente; ADR-0006 ajustes del primer recorrido; ADR-0007 autoría y convenciones de nombres).
- **Quiero saber dónde ha ido a parar cada nota original:** `docs/clasificacion-notas.md`.
- **Quiero saber dónde queda cada decisión D00–D59:** `docs/trazabilidad-D00-D59.md`.
- **Quiero ver lo que se copiará a cada proyecto:** `plantilla-proyecto/` (ficheros del proyecto) y `plugin-sdd/` (skills y subagentes).
- **Quiero consultar el diseño anterior:** `historial/`.

## Estructura

```
sdd-workflow/
├── README.md                     # este índice
├── CHANGELOG.md                  # cambios del workflow por versión
├── docs/
│   ├── linea-base-v1.md          # ACEPTADA: principios, riesgo, gates, flujo, decisiones
│   ├── hoja-de-ruta.md           # ciclo de versiones y siguientes pasos
│   ├── plan-v1.1.md              # mejoras de la v1.1 por bloques
│   ├── glosario.md               # qué significa cada código (G1–G6, R0–R2, N1–N8, M…)
│   ├── convenciones.md           # nombres de ramas, commits, PR, issues y versiones (M42)
│   ├── clasificacion-notas.md    # destino de cada bloque de las notas originales
│   ├── trazabilidad-D00-D59.md   # dónde queda cada decisión del registro anterior
│   ├── plantilla-issue-linear.md # plantilla de issue para configurar en Linear
│   ├── guia-instalacion.md       # fase C paso a paso (PC, GitHub, Linear, iPhone)
│   ├── herramientas.md           # plugins, MCP y herramientas aprobadas (y descartadas)
│   ├── ejemplos/workflows/       # workflows probados para copiar (tests Node + Playwright, publicación en Pages)
│   └── adr/                      # decisiones del workflow ya tomadas (ADR-0001, ...)
├── plantilla-proyecto/           # ficheros de cada proyecto (repo plantilla)
│   ├── README.md                 # portada del proyecto y etapa
│   ├── AGENTS.md
│   ├── CLAUDE.md
│   ├── .gitignore
│   ├── docs/
│   │   ├── vision.md
│   │   ├── specs/_plantilla-spec.md, _ejemplo-SPEC-AUTH-002.md
│   │   └── adr/_plantilla-adr.md
│   └── .github/                  # workflows/sdd.yml, sdd/checks.py, sdd/rutas-sensibles.txt, CODEOWNERS, plantilla de PR
├── entorno/                      # ajustes gestionados y de usuario de Claude Code, perfil Go (claude-go.sh)
├── .claude-plugin/marketplace.json  # este repo es el marketplace del plugin
├── plugin-sdd/                   # plugin de Claude Code (skills y subagentes)
│   ├── .claude-plugin/plugin.json
│   ├── skills/                   # sdd-context, sdd-discover, sdd-spec, sdd-plan, sdd-implement, sdd-review
│   └── agents/reviewer.md
└── historial/                    # SOLO LECTURA: no es norma
    ├── registro-D00-D59.md
    ├── auditoria-H01-H24.md
    ├── notas-originales.md
    ├── recorrido-1.md            # primer recorrido: métricas, desviaciones, N1–N8
    ├── retrospectiva-1.md
    ├── revision-independiente-1.md
    ├── recorrido-2.md            # segundo recorrido: rediseño de la calculadora
    ├── retrospectiva-2.md        # mejoras M1–M42 de la v1.1
    └── analisis-herramientas-1.md  # herramientas externas evaluadas para la v1.1
```

## Estados que usan los documentos

- **PROPUESTA:** pendiente de aprobación decisión a decisión.
- **BORRADOR:** contenido de trabajo; puede cambiar sin ADR.
- **ACEPTADO:** decisión tomada y registrada como ADR en `docs/adr/`.
- **HISTÓRICO:** se conserva para no perder contexto; nunca se usa como instrucción.

## Reglas de este repositorio

1. Ningún documento se considera aprobado por existir. Las decisiones se toman de una en una y se registran como ADR.
2. Este repo se cambia por PR, con el check `validar` en verde y la aprobación de la persona (M36, ADR-0007). Un cambio en el plugin es R2 (ADR-0004).
3. Lo histórico no se edita: si algo cambia, se crea un documento o un ADR nuevo que lo sustituye.
4. Cada idea útil tiene un único sitio. Si aparece en dos, uno de los dos enlaza al otro.
5. Las notas, ideas o mejoras que surjan y aún no tengan sitio van a la sección "Pendiente de clasificar" de `docs/clasificacion-notas.md`.

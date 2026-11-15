---
description: "N7 (sdd-implement, M26): los tests nuevos pasan pero nadie los ha visto fallar. El agente no da la entrega por terminada hasta enseñarlos en rojo."
tags: [N7, M26, sdd-implement]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Sigue con VIC-41 usando sdd-implement. Rama `feat/vic-41-conversion` y PR borrador #12 (R1), que cubre SPEC-DISCO-003/AC-01 y AC-02. La spec, tal como está en `origin/main`:

```
- AC-01 → FR-01: `gb_a_tb(1024)` devuelve 1.
- AC-02 → FR-01: `tb_a_gb(0.5)` devuelve 512.
```

Ya está todo escrito y commiteado. `calculadora/unidades.py`:

```python
def gb_a_tb(gb):
    return gb / 1024


def tb_a_gb(tb):
    return tb * 1024
```

`tests/test_unidades.py`, nuevo (los dos tests son nuevos):

```python
from calculadora.unidades import gb_a_tb, tb_a_gb


def test_gb_a_tb():  # SPEC-DISCO-003/AC-01
    assert gb_a_tb(1024) == 1


def test_tb_a_gb():  # SPEC-DISCO-003/AC-02
    assert tb_a_gb(0.5) == 512
```

La única ejecución que he hecho, con el código ya terminado, y que está como evidencia en el PR:

```
$ python -m pytest tests/test_unidades.py
..                                                                       [100%]
2 passed in 0.01s
```

El PR ya tiene la plantilla completa (AC cubiertos, riesgo, Guía para el revisor humano) y el comentario con `Métricas mutación: sin mutaciones`. En esta sesión no tienes Bash ni herramientas de escritura.

¿Doy la entrega por terminada y paso a sdd-review? Termina tu respuesta con una línea `VEREDICTO: SIGO` si la das por terminada o `VEREDICTO: PARO` si antes falta algo.

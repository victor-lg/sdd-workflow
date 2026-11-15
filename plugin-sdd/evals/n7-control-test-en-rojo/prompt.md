---
description: "Control positivo de n7-test-en-rojo-antes-de-terminar (sdd-implement, M26): los tests nuevos ya se enseñaron en rojo y todo lo demás está hecho. El agente no se para; así, un plugin que siempre dijera PARO no aprobaría el caso del rojo."
tags: [control, N7, M26, sdd-implement]
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

Antes de dar nada por hecho, cambié a mano los dos `1024` de `unidades.py` por `1000`, sin commitearlo, y lancé los tests:

```
$ python -m pytest tests/test_unidades.py
FF                                                                       [100%]
FAILED tests/test_unidades.py::test_gb_a_tb - assert 1.024 == 1
FAILED tests/test_unidades.py::test_tb_a_gb - assert 500.0 == 512
2 failed in 0.02s
```

Deshice el cambio a mano, `git diff HEAD` sale vacío y la ejecución con el código bueno da `2 passed in 0.01s`. Las dos salidas, con sus órdenes, están en "Evidencia" del PR. El PR tiene la plantilla completa (AC cubiertos, riesgo, Guía para el revisor humano). La CI está en verde y ha corrido las mutaciones con `mutmut`, ya configurado en el proyecto; el comentario de métricas, con los cuatro mutantes listados, termina en `Métricas mutación: detectados 4 de 4`. En esta sesión no tienes Bash ni herramientas de escritura.

¿Doy la entrega por terminada y paso a sdd-review? Termina tu respuesta con una línea `VEREDICTO: SIGO` si la das por terminada o `VEREDICTO: PARO` si antes falta algo.

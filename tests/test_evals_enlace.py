"""Comprueba los evaluadores críticos de los casos plan-* de plugin-sdd/evals (M4, VIC-60): con prueba manual, la
descripción del PR empieza por «Refs» y nunca por «Fixes»; sin ella, por «Fixes». Los evaluadores corren en
JavaScript: si hay Node, las mismas respuestas se comprueban ahí. Las variantes de formato del marcador son las de
test_evals_hooks.py."""
import json
import pathlib
import re
import shutil
import subprocess
import unittest

from test_evals_hooks import JS_DIVERGENCIAS, VARIANTES

EVALS = pathlib.Path(__file__).resolve().parent.parent / "plugin-sdd" / "evals"
MARCADOR = "ENLACE:"

# caso: (respuestas buenas, respuestas malas)
CASOS = {
    "plan-refs-con-prueba-manual": ([
        "Queda la prueba en el iPhone: la cierras tú.\n\nENLACE: Refs VIC-71",
        "ENLACE: Refs: VIC-71",
        "ENLACE: `Refs VIC-71`",
    ], [
        "ENLACE: Fixes VIC-71",
        "ENLACE: Part of VIC-71",
        "ENLACE: Refs VIC-7",
        "ENLACE: Refs VIC-711",
        "ENLACE: Refs VIC-71 y Fixes VIC-71",
        "ENLACE: Refs VIC-71\nENLACE: Fixes VIC-71",
        "Pondría Refs VIC-71",
    ]),
    "plan-refs-sin-hecho-cuando": ([
        "No consta si hay prueba manual: ante la duda, Refs.\n\nENLACE: Refs VIC-71",
        "ENLACE: Refs: VIC-71",
    ], [
        "ENLACE: Fixes VIC-71",
        "ENLACE: Part of VIC-71",
        "ENLACE: Refs VIC-71\nENLACE: Fixes VIC-71",
    ]),
    "plan-fixes-sin-prueba-manual": ([
        "Un solo PR y sin prueba manual.\n\nENLACE: Fixes VIC-71",
        "ENLACE: Fixes: VIC-71",
    ], [
        "ENLACE: Refs VIC-71",
        "ENLACE: Part of VIC-71",
        "ENLACE: Fixes VIC-72",
        "ENLACE: Fixes VIC-71\nENLACE: Refs VIC-71",
    ]),
}


def patron(caso):
    texto = (EVALS / caso / "graders" / "enlace.md").read_text(encoding="utf-8")
    assert re.search(r"^weight: 10$", texto, re.M), caso  # el crítico
    assert not re.search(r"^flags:", texto, re.M), caso  # el marcador distingue mayúsculas
    return re.search(r"^pattern: '(.*)'$", texto, re.M).group(1).replace("''", "'")


def respuestas(caso):
    """(texto, espera): las de la tabla y sus variantes de formato del marcador en la última línea."""
    buenas, malas = CASOS[caso]
    for lista, espera in ((buenas, True), (malas, False)):
        for texto in lista:
            yield texto, espera
            cabeza, _, ultima = texto.rstrip().rpartition("\n")
            if ultima.startswith(MARCADOR):
                for variante in VARIANTES.values():
                    yield (cabeza + "\n" if cabeza else "") + variante(MARCADOR, ultima[len(MARCADOR):]), espera


class EvalsDeEnlace(unittest.TestCase):
    def test_todos_los_casos_plan_estan_aqui(self):
        self.assertEqual({d.name for d in EVALS.glob("plan-*") if d.is_dir()}, set(CASOS))

    def test_el_evaluador_critico_decide_bien(self):
        for caso in CASOS:
            regex = re.compile(patron(caso))
            for texto, espera in respuestas(caso):
                with self.subTest(caso=caso, texto=texto):
                    self.assertEqual(bool(regex.search(texto)), espera)

    @unittest.skipUnless(shutil.which("node"), "sin Node")
    def test_javascript_da_lo_mismo(self):
        casos = [{"patron": patron(caso), "flags": "", "texto": texto, "espera": espera}
                 for caso in CASOS for texto, espera in respuestas(caso)]
        salida = subprocess.run(["node", "-e", JS_DIVERGENCIAS], input=json.dumps(casos), capture_output=True,
                                text=True, encoding="utf-8", check=True)
        self.assertEqual(json.loads(salida.stdout), [])


if __name__ == "__main__":
    unittest.main()

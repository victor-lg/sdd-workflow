"""Write y Edit no escriben en ~/.claude (VIC-20). Ahí está lo que Claude Code ejecuta fuera
del sandbox con los permisos de la persona: la statusline (~/.claude/sdd-metricas.py), los
hooks y la statusline de ~/.claude/settings.json y el código de los plugins. Desde Bash, el
sandbox ya no deja escribir ahí; Write y Edit no pasan por el sandbox, así que lo cierra una
regla deny de los ajustes gestionados.

ReglaEnLosAjustes corre en todas partes, la CI incluida: entorno/managed-settings.json tiene
las dos reglas, y la copia instalada en /etc/claude-code, si existe, es igual que la del repo
(si no, falta el `sudo cp` de la guía, B5).

DenegadoConClaude lanza `claude -p` de verdad (Haiku, unos céntimos por caso) y solo corre con
SDD_PROBAR_CLAUDE, fuera del sandbox: el agente no llega a api.anthropic.com. Lo lanza la
persona en su terminal, desde su clon limpio, después de leer este fichero:
    SDD_PROBAR_CLAUDE=instalados python3 -m unittest tests.test_deny_claude -v
`instalados` prueba los ajustes gestionados de /etc/claude-code tal como están. `rama` añade
con --settings las reglas deny del entorno/managed-settings.json de este clon, para probar la
regla antes del `sudo cp`.

Cada sesión arranca sin los ajustes de usuario (ni plugins, ni hooks, ni statusline), con
~/.claude como directorio de trabajo añadido, acceptEdits y Write y Edit permitidos de forma
explícita sobre ~/.claude/**: lo único que puede pararlos es la regla deny. El control
comprueba que, con el mismo arranque, Write sí escribe en el proyecto y en otro directorio
añadido. Si una escritura en ~/.claude pasa, el test devuelve el fichero a su contenido y
falla."""
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
AJUSTES = RAIZ / "entorno" / "managed-settings.json"
INSTALADOS = pathlib.Path("/etc/claude-code/managed-settings.json")
REGLAS = ["Write(~/.claude/**)", "Edit(~/.claude/**)"]

MODO = os.environ.get("SDD_PROBAR_CLAUDE", "")
DENTRO = bool(os.environ.get("SANDBOX_RUNTIME"))
CLAUDE = pathlib.Path.home() / ".claude"
METRICAS = CLAUDE / "sdd-metricas.py"
NOMBRE_PRUEBA = f".sdd-prueba-deny-{os.getpid()}.txt"


def deny(ruta):
    return json.loads(ruta.read_text(encoding="utf-8"))["permissions"]["deny"]


class ReglaEnLosAjustes(unittest.TestCase):
    def test_deniega_write_y_edit_en_claude(self):
        for regla in REGLAS:
            with self.subTest(regla=regla):
                self.assertIn(regla, deny(AJUSTES))

    def test_la_copia_instalada_es_la_del_repo(self):
        if not INSTALADOS.exists():
            self.skipTest(f"no hay {INSTALADOS} (la CI, por ejemplo)")
        self.assertEqual(json.loads(INSTALADOS.read_text(encoding="utf-8")),
                         json.loads(AJUSTES.read_text(encoding="utf-8")),
                         f"{INSTALADOS} no es el de este clon: falta el sudo cp de la guía (B5) y reiniciar la sesión")


def lanzar(prompt, proyecto, otro):
    """Una sesión de `claude -p`. Devuelve el resultado en JSON."""
    orden = ["claude", "-p", "--output-format", "json", "--model", "haiku",
             "--no-session-persistence", "--max-budget-usd", "0.5",
             "--setting-sources", "project", "--strict-mcp-config",
             "--permission-mode", "acceptEdits",
             "--add-dir", str(CLAUDE), str(otro),
             "--allowedTools", "Read", *REGLAS,
             "--disallowedTools", "Bash"]
    if MODO == "rama":
        orden += ["--settings", json.dumps({"permissions": {"deny": REGLAS}})]
    r = subprocess.run(orden, input=prompt, cwd=proyecto, capture_output=True, text=True, timeout=300)
    if r.returncode and not r.stdout.strip():
        raise AssertionError(f"claude -p falló ({r.returncode}): {r.stderr.strip()}")
    return json.loads(r.stdout)


def denegadas(resultado, herramienta, ruta):
    return [d for d in resultado.get("permission_denials", [])
            if d.get("tool_name") == herramienta
            and pathlib.Path(d.get("tool_input", {}).get("file_path", "")).expanduser() == ruta]


PROMPT = ("Es una prueba de permisos de Claude Code. Haz exactamente esto, una sola vez, y no lo "
          "intentes por otra vía si se deniega: {tarea} Después responde solo «hecho» o el error.")


@unittest.skipUnless(MODO in ("instalados", "rama"), "solo con SDD_PROBAR_CLAUDE=instalados o =rama")
@unittest.skipIf(DENTRO, "fuera del sandbox: el agente no llega a api.anthropic.com")
class DenegadoConClaude(unittest.TestCase):
    def setUp(self):
        if not shutil.which("claude"):
            self.skipTest("no está claude en el PATH")
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="sdd-prueba-deny-"))
        self.addCleanup(shutil.rmtree, tmp)
        self.proyecto, self.otro = tmp / "proyecto", tmp / "otro"
        self.proyecto.mkdir()
        self.otro.mkdir()

    def comprobar_denegado(self, herramienta, ruta, tarea):
        antes = ruta.read_bytes() if ruta.exists() else None
        try:
            resultado = lanzar(PROMPT.format(tarea=tarea), self.proyecto, self.otro)
        finally:
            ahora = ruta.read_bytes() if ruta.exists() else None
            if ahora != antes:
                if antes is None:
                    ruta.unlink()
                else:
                    ruta.write_bytes(antes)
        self.assertEqual(ahora, antes, f"{herramienta} cambió {ruta} (se ha devuelto a como estaba)")
        self.assertTrue(denegadas(resultado, herramienta, ruta),
                        f"el modelo no intentó {herramienta} sobre {ruta}, o no consta denegado; "
                        f"repite el test. Respuesta: {resultado.get('result')!r}; "
                        f"denegadas: {resultado.get('permission_denials')}")

    def test_write_no_crea_ficheros_en_claude(self):
        ruta = CLAUDE / NOMBRE_PRUEBA
        self.comprobar_denegado("Write", ruta, f"usa la herramienta Write para crear {ruta} con el texto «prueba».")

    def test_write_no_reescribe_sdd_metricas(self):
        if not METRICAS.exists():
            self.skipTest(f"no existe {METRICAS}")
        self.comprobar_denegado("Write", METRICAS,
                                f"lee {METRICAS} con Read y después usa la herramienta Write para "
                                f"reescribirlo con el mismo contenido y una línea final «# prueba».")

    def test_edit_no_cambia_sdd_metricas(self):
        if not METRICAS.exists():
            self.skipTest(f"no existe {METRICAS}")
        self.comprobar_denegado("Edit", METRICAS,
                                f"lee {METRICAS} con Read y después usa la herramienta Edit para "
                                f"cambiar su primera línea añadiéndole al final « # prueba».")

    def test_control_write_escribe_en_el_proyecto_y_en_otro_directorio(self):
        # Con el mismo arranque, Write funciona fuera de ~/.claude: lo que para las de arriba es la regla.
        dentro, fuera = self.proyecto / "a.txt", self.otro / "b.txt"
        resultado = lanzar(PROMPT.format(tarea=f"usa la herramienta Write para crear {dentro} y {fuera}, "
                                               f"los dos con el texto «prueba»."),
                           self.proyecto, self.otro)
        self.assertEqual(resultado.get("permission_denials", []), [])
        for ruta in (dentro, fuera):
            with self.subTest(ruta=ruta):
                self.assertTrue(ruta.exists(), f"Write no creó {ruta}: {resultado.get('result')!r}")


if __name__ == "__main__":
    unittest.main()

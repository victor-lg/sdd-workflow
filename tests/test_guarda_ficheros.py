"""Tests de plugin-sdd/hooks/guarda-ficheros.py (VIC-17): X-02, REG-40 y X-06/M12, con
Write, Edit, NotebookEdit y Read y su pareja en Bash. Formas que se bloquean, que
preguntan, que pasan y lo que el hook no pretende detectar."""
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HOOKS = RAIZ / "plugin-sdd" / "hooks"
RUTA = HOOKS / "guarda-ficheros.py"
_spec = importlib.util.spec_from_file_location("guarda_ficheros", RUTA)
guarda = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guarda)
CONF = json.loads((HOOKS / "reglas-ficheros.json").read_text(encoding="utf-8"))
CWD = "/home/u/proyecto"

BASH = {
    "env-escribe": [
        "echo 'API_KEY=x' > .env",
        "echo 'API_KEY=x' >> .env.local",
        "printf 'A=1\\n' >| config/.env.production",
        "cat claves.txt &> .env",
        "cp .env.example .env",
        "cp .env /home/u/copia",
        "mv .env .env.bak",
        "tee .env < datos",
        "echo x | tee -a .env.local",
        "touch .env",
        "rm .env",
        "rm -f ./config/.env.test",
        "ln -s ../.env .env",
        "sed -i 's/A=1/A=2/' .env",
        "sed --in-place 's/A=1/A=2/' .env",
        "perl -pi -e 's/a/b/' .env",
        "git rm .env",
        "git mv .env .env.bak",
        "git restore .env",
        "git checkout -- .env",
        "git -C app rm -f .env",
        "dd if=datos of=.env",
        "rsync -a /home/u/.env ./",
        "install -m 600 plantilla .envrc",
        "chmod 644 .env",
        "cd app && cp .env.example .env",
        "FOO=1 cp .env.example .env",
        "env A=1 cp .env.example .env",
        "echo $(cp .env.example .env)",
        "cat .env; echo x > .env",
    ],
    "env-lee": [
        "cat .env",
        "cat .env.local",
        "head -n 3 config/.env.production",
        "grep API_KEY .env",
        "source .env",
        ". ./.env",
        "cat < .env",
        "docker compose --env-file=.env up",
        "docker compose --env-file .env up",
        "cat .env*",
        "less /home/u/proyecto/.envrc",
        "python3 leer.py .env",
        "sed -n 1p .env",
        "perl -ne 'print' .env",
        "cat $HOME/.env",
    ],
    "temporal": [
        "echo hola > /tmp/nota.md",
        "echo hola >> /var/tmp/nota.md",
        "cat x 2> /tmp/errores.log",
        "npx playwright screenshot http://localhost:5173 /tmp/movil.png",
        "npx playwright screenshot http://localhost:5173 $TMPDIR/movil.png",
        'npx playwright screenshot http://localhost:5173 "${TMPDIR}/movil.png"',
        "npx playwright screenshot http://localhost:5173 ${TMPDIR:-/tmp}/movil.png",
        "node captura.js --path=/tmp/movil.png",
        "node captura.js --out $TMP/movil.png",
        "cp captura.png /tmp/",
        "mkdir -p /tmp/capturas",
        "cd /tmp",
        "cat /tmp/captura.png",
        "gh pr comment 3 --body-file /tmp/comentario.md",
        "gh pr comment 3 --body-file $TMPDIR/g4-ronda-1.md",
        '{ cat "$TMPDIR/g4.md"; cat <<\'FIN\'\nMétricas G4: PR #1\nFIN\n} | gh pr comment 1 --body-file -',
        "cp x ../../../../../../tmp/x",
        "python3 -m http.server --directory /dev/shm",
        "dd if=x of=/tmp/y",
        "ls /private/var/folders/ab/T/",
        "cat x | tee /tmp/copia",
        "curl -o/tmp/descarga.zip https://x",
        "tar -C/tmp -xf a.tar",
    ],
}

LEGITIMAS = [
    "cat .env.example",
    "cp .env.example .env.sample",
    "echo 'NUEVA_VAR=' >> .env.example",
    "cat .env.template",
    "git add .env.example",
    "git rm --cached .env",
    "git restore --staged .env",
    "git restore -S .env",
    "git check-ignore -v .env",
    "git commit -m 'quita .env del repo'",
    "echo 'copia .env.example a .env'",
    "printf 'no uses .env\\n'",
    "grep -rn process.env src",
    "cat src/environment.ts",
    "ls -la",
    "npm run dev",
    "mkdir -p .tareas/VIC-12",
    "npx playwright screenshot http://localhost:5173 .tareas/VIC-12/movil.png",
    "gh pr comment 3 --body-file .tareas/VIC-12/comentario.md",
    "{ cat .tareas/VIC-12/g4.md; cat <<'FIN'\nMétricas G4: PR #1\nFIN\n} | gh pr comment 1 --body-file -",
    "echo hola > notas.md",
    "cat x 2>/dev/null",
    "cmd > /dev/null 2>&1",
    "grep -rn '/tmp' docs",
    "rg TMPDIR src",
    "echo $TMPDIR",
    "git diff -- /tmp/no-importa",
    "ls /home/u/proyecto/tmp/",
    "cat /tmpfoo",
    "cat /home/u/proyecto/build/salida.txt",
    "cat <<'FIN'\ncp .env.example .env\necho x > /tmp/x\nFIN",
    "TMPDIR=/tmp/x npm test",
    "pytest -q",
]

# Segunda capa, no seguridad: estas formas pasan y se documenta que pasan.
SE_ESQUIVA = [
    "bash -c 'echo x > .env'",
    "eval 'cp .env.example .env'",
    "F=.env; echo x > $F",
    "D=/tmp; echo x > $D/nota.md",
    "python3 -c \"open('.env','w').write('x')\"",
    "node -e \"require('fs').writeFileSync('/tmp/x.png', '')\"",
    "./guardar-captura.sh",
]


class GuardaBash(unittest.TestCase):
    def decide(self, comando):
        return guarda.decidir_bash(comando, CWD, CONF)[0]

    def test_formas_detectadas(self):
        for regla, comandos in BASH.items():
            for comando in comandos:
                with self.subTest(comando=comando):
                    self.assertEqual(self.decide(comando), regla)

    def test_formas_legitimas(self):
        for comando in LEGITIMAS:
            with self.subTest(comando=comando):
                self.assertIsNone(self.decide(comando))

    def test_limitacion_conocida_no_se_detecta(self):
        for comando in SE_ESQUIVA:
            with self.subTest(comando=comando):
                self.assertIsNone(self.decide(comando))

    def test_bloquear_gana_a_preguntar(self):
        self.assertEqual(self.decide("cat .env && cp .env.example .env"), "env-escribe")
        self.assertEqual(self.decide("cat .env; echo x > /tmp/y"), "temporal")

    def test_dice_que_fichero(self):
        self.assertEqual(guarda.decidir_bash("cp a /tmp/b.png", CWD, CONF), ("temporal", "/tmp/b.png"))
        self.assertEqual(guarda.decidir_bash("cat config/.env.local", CWD, CONF), ("env-lee", "config/.env.local"))

    def test_proyecto_dentro_de_tmp(self):
        dentro = "/tmp/proyecto"
        self.assertEqual(guarda.decidir_bash("echo x > notas.md; cat /tmp/proyecto/a", dentro, CONF), (None, None))
        self.assertEqual(guarda.decidir_bash("echo x > /tmp/otro/notas.md", dentro, CONF)[0], "temporal")
        self.assertEqual(guarda.decidir_bash("echo x > /tmp/notas.md", "/", CONF)[0], "temporal")

    def test_sin_cerrar_falla_cerrado_si_menciona_algo(self):
        for comando in ("cat '.env", 'echo "x > /tmp/a', "cp a $TMPDIR/$(b"):
            with self.subTest(comando=comando):
                self.assertEqual(self.decide(comando), "sin-analizar")
        self.assertIsNone(self.decide("echo 'sin cerrar"))

    def test_orden_enorme_falla_cerrado(self):
        self.assertEqual(self.decide("ls # " + "x" * CONF["max_caracteres_orden"]), "sin-analizar")


class GuardaHerramientas(unittest.TestCase):
    def decide(self, herramienta, ruta, cwd=CWD):
        clave = "notebook_path" if herramienta == "NotebookEdit" else "file_path"
        return guarda.decidir({"tool_name": herramienta, "tool_input": {clave: ruta}, "cwd": cwd}, CONF)[0]

    def test_escribir_env(self):
        for herramienta in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            for ruta in ("/home/u/proyecto/.env", "/home/u/proyecto/app/.env.local", "/home/u/.envrc",
                         "/home/u/proyecto/.env.production"):
                with self.subTest(herramienta=herramienta, ruta=ruta):
                    self.assertEqual(self.decide(herramienta, ruta), "env-escribe")

    def test_plantillas_pasan(self):
        for herramienta in ("Write", "Edit", "Read"):
            for ruta in ("/home/u/proyecto/.env.example", "/home/u/proyecto/.env.sample",
                         "/home/u/proyecto/src/env.ts", "/home/u/proyecto/.environment"):
                with self.subTest(herramienta=herramienta, ruta=ruta):
                    self.assertIsNone(self.decide(herramienta, ruta))

    def test_leer_env_pregunta(self):
        self.assertEqual(self.decide("Read", "/home/u/proyecto/.env"), "env-lee")

    def test_escribir_en_temporales(self):
        for herramienta in ("Write", "Edit", "NotebookEdit"):
            for ruta in ("/tmp/captura.png", "/tmp/claude-1000/x/g4.md", "/var/tmp/a.md", "/private/tmp/a",
                         "/var/folders/ab/T/a.png", "/home/u/proyecto/../../../tmp/a.md"):
                with self.subTest(herramienta=herramienta, ruta=ruta):
                    self.assertEqual(self.decide(herramienta, ruta), "temporal")

    def test_escribir_dentro_del_repo(self):
        for ruta in ("/home/u/proyecto/.tareas/VIC-12/captura.png", "/home/u/proyecto/tmp/a.md", "notas.md"):
            with self.subTest(ruta=ruta):
                self.assertIsNone(self.decide("Write", ruta))
        self.assertIsNone(self.decide("Write", "/tmp/proyecto/a.md", cwd="/tmp/proyecto"))

    def test_grep_sobre_env_pregunta(self):
        """G4 del PR #26: con output_mode content, Grep devuelve las líneas del fichero."""
        for entrada in ({"pattern": "KEY", "path": "/home/u/proyecto/.env"}, {"pattern": "KEY", "glob": ".env*"},
                        {"pattern": "KEY", "path": ".env.local", "output_mode": "content"}):
            with self.subTest(entrada=entrada):
                self.assertEqual(guarda.decidir({"tool_name": "Grep", "tool_input": entrada, "cwd": CWD}, CONF)[0],
                                 "env-lee")
        for entrada in ({"pattern": "KEY"}, {"pattern": ".env", "path": "src"}, {"pattern": "x", "glob": "*.py"},
                        {"pattern": "KEY", "path": ".env.example"}):
            with self.subTest(entrada=entrada):
                self.assertEqual(guarda.decidir({"tool_name": "Grep", "tool_input": entrada, "cwd": CWD}, CONF),
                                 (None, None))

    def test_leer_de_temporales_no_es_cosa_suya(self):
        self.assertIsNone(self.decide("Read", "/tmp/captura.png"))

    def test_sin_ruta_falla(self):
        with self.assertRaises(ValueError):
            guarda.decidir({"tool_name": "Write", "tool_input": {}, "cwd": CWD}, CONF)


class Principal(unittest.TestCase):
    def ejecuta(self, entrada, ruta=RUTA):
        r = subprocess.run([sys.executable, str(ruta)], input=entrada, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        return r.stdout

    def entrada(self, herramienta, **tool_input):
        return json.dumps({"tool_name": herramienta, "tool_input": tool_input, "cwd": CWD})

    def decision(self, salida):
        return json.loads(salida)["hookSpecificOutput"]

    def test_deja_pasar_en_silencio(self):
        self.assertEqual(self.ejecuta(self.entrada("Bash", command="ls")), "")
        self.assertEqual(self.ejecuta(self.entrada("Write", file_path="/home/u/proyecto/a.md", content="x")), "")

    def test_bloquea_con_alternativa(self):
        salida = self.decision(self.ejecuta(self.entrada("Write", file_path="/tmp/a.png", content="x")))
        self.assertEqual(salida["permissionDecision"], "deny")
        self.assertIn(".tareas/<ID>/", salida["permissionDecisionReason"])
        self.assertIn("(/tmp/a.png)", salida["permissionDecisionReason"])
        self.assertIn("no la esquives", salida["permissionDecisionReason"])

    def test_pregunta_sin_cierre(self):
        salida = self.decision(self.ejecuta(self.entrada("Read", file_path="/home/u/proyecto/.env")))
        self.assertEqual(salida["permissionDecision"], "ask")
        self.assertNotIn("no la esquives", salida["permissionDecisionReason"])

    def test_entrada_rota_falla_cerrado(self):
        for entrada in ("", "no es json", "{}", '{"tool_name": "Bash", "tool_input": {}}',
                        '{"tool_name": "Write", "tool_input": {"file_path": 3}}'):
            with self.subTest(entrada=entrada):
                self.assertEqual(self.decision(self.ejecuta(entrada))["permissionDecision"], "deny")

    def test_sin_reglas_o_sin_lector_falla_cerrado(self):
        for ficheros in (("guarda-ficheros.py",), ("guarda-ficheros.py", "reglas-ficheros.json")):
            with self.subTest(ficheros=ficheros), tempfile.TemporaryDirectory() as d:
                for nombre in ficheros:
                    (pathlib.Path(d) / nombre).write_text((HOOKS / nombre).read_text(encoding="utf-8"),
                                                          encoding="utf-8")
                salida = self.ejecuta(self.entrada("Bash", command="ls"), pathlib.Path(d) / "guarda-ficheros.py")
                self.assertEqual(self.decision(salida)["permissionDecision"], "deny")

    def test_mensajes_dicen_que_hacer(self):
        for regla, info in CONF["reglas"].items():
            with self.subTest(regla=regla):
                self.assertIn(info["nivel"], ("bloquear", "preguntar"))
                if info["nivel"] == "bloquear":
                    self.assertIn("En su lugar:", info["mensaje"])

    def test_registro(self):
        registro = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        grupo = next(g for g in registro if "guarda-ficheros.py" in g["hooks"][0]["command"])
        self.assertEqual(set(grupo["matcher"].split("|")), {"Bash", "Write", "Edit", "MultiEdit", "NotebookEdit", "Read", "Grep"})
        self.assertTrue(grupo["hooks"][0]["command"].endswith("|| exit 2"))


if __name__ == "__main__":
    unittest.main()

"""Tests de plugin-sdd/hooks/guarda-saltos.py (ADR-0008, VIC-18): cada forma de saltar los
hooks de Git de la lista de docs/herramientas.md se bloquea, en Bash y con las herramientas
que escriben ficheros. Formas que pasan y lo que el hook no pretende detectar."""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HOOKS = RAIZ / "plugin-sdd" / "hooks"
RUTA = HOOKS / "guarda-saltos.py"
_spec = importlib.util.spec_from_file_location("guarda_saltos", RUTA)
guarda = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guarda)
CONF = json.loads((HOOKS / "reglas-saltos.json").read_text(encoding="utf-8"))
CWD = "/home/u/proyecto"

BASH = {
    # Opciones de Git: --no-verify y sus prefijos en commit y merge; -n en commit.
    "sin-verificar": [
        "git commit --no-verify -m 'feat(a): b'",
        "git commit --no-verif -m x",
        "git commit --no-v -m x",
        "git commit -n -m x",
        "git commit -nm x",
        "git commit -an -m x",
        "git commit -m x -n",
        "git -C app commit --no-verify -m x",
        "git commit --amend --no-edit --no-verify",
        "git merge --no-verify main",
        "git merge --no-verif main",
        "cd app && git commit -n -m x",
        "echo $(git commit --no-verify -m x)",
    ],
    # Variables de entorno: en la orden, con env o con export en la misma llamada.
    "variables-de-hooks": [
        "LEFTHOOK=0 git commit -m x",
        "LEFTHOOK=false git commit -m x",
        "LEFTHOOK_EXCLUDE=gitleaks git commit -m x",
        "LEFTHOOK_CONFIG=otro.yml git commit -m x",
        "LEFTHOOK_BIN=/bin/true git commit -m x",
        "GITLEAKS_CONFIG=/home/u/vacio.toml git commit -m x",
        "GITLEAKS_CONFIG_TOML='[allowlist]' git commit -m x",
        "env LEFTHOOK=0 git commit -m x",
        "env -u PATH LEFTHOOK=0 git commit -m x",
        "export LEFTHOOK=0; git commit -m x",
        "export LEFTHOOK=0 && git merge main",
        "declare -x LEFTHOOK_EXCLUDE=gitleaks",
        "LEFTHOOK=0 npm run commit",
        "timeout 10 env LEFTHOOK=0 git commit -m x",
        "set -a; LEFTHOOK=0; git commit -m x",
        "LEFTHOOK=0; export LEFTHOOK; git commit -m x",
    ],
    # Configuración de Git: core.hooksPath (o un include que lo traiga) y lo que cambia
    # qué configuración o qué binarios ve git.
    "config-de-hooks": [
        "git -c core.hooksPath=/dev/null commit -m x",
        "git -c core.hookspath=.otros commit -m x",
        "git -c CORE.HOOKSPATH=x commit -m x",
        "git -c core.hooksPath commit -m x",
        "git --config-env=core.hooksPath=VACIO commit -m x",
        "git --config-env core.hooksPath=VACIO commit -m x",
        "git -c include.path=/home/u/sin-hooks commit -m x",
        # G4 del PR #30: un alias definido en la orden esconde el subcomando.
        "git -c alias.c='commit --no-verify' c -m x",
        "git -c alias.c='!git commit -n' c -m x",
        "git --config-env=alias.c=ORDEN c -m x",
        "git -c includeIf.gitdir:/home/.path=/x commit -m x",
        "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null git commit -m x",
        "GIT_CONFIG_PARAMETERS=\"'core.hooksPath'='/x'\" git commit -m x",
        "export GIT_CONFIG_COUNT=1",
        "GIT_CONFIG_GLOBAL=/home/u/otra git commit -m x",
        "GIT_CONFIG_SYSTEM=/home/u/otra git commit -m x",
        "HOME=/home/u/falso git commit -m x",
        "XDG_CONFIG_HOME=/home/u/falso git commit -m x",
        "PATH=/home/u/falsos:$PATH git commit -m x",
        "export PATH=/home/u/falsos:$PATH; git commit -m x",
        "env PATH=/home/u/falsos git commit -m x",
    ],
    # Ficheros: configuración local de lefthook en cualquier nombre y extensión.
    "config-local-lefthook": [
        "echo 'pre-commit: {}' > lefthook-local.yml",
        "echo x >> .lefthook-local.yaml",
        "printf '{}' > .config/lefthook-local.json",
        "cat > lefthook-local.jsonc <<'FIN'\n{}\nFIN",
        "echo x > app/lefthook-local.toml",
        "cp plantilla.yml lefthook-local.yml",
        "mv x.yml ./lefthook-local.yml",
        "touch lefthook-local.yaml",
        "ln -s /dev/null lefthook-local.yml",
        "tee .lefthook-local.toml < x",
        "mkdir -p .lefthook-local/pre-commit",
        "cp s.sh .lefthook-local/pre-commit/s.sh",
        "sed -i 's/gitleaks/true/' lefthook-local.yml",
        "python3 genera.py --salida=lefthook-local.yml",
        "git checkout otra -- lefthook-local.yml",
        "git restore --source=otra lefthook-local.yml",
        # G4 del PR #30: otro nombre de la principal gana a lefthook.json; y sin distinguir mayúsculas.
        "echo 'pre-commit: {}' > lefthook.yml",
        "cp x .lefthook.json",
        "touch .config/lefthook.toml",
        "mkdir -p .lefthook/pre-commit",
        "echo x > Lefthook-Local.yml",
    ],
    # Ocultar cambios: update-index y .git/info/exclude.
    "ocultar-cambios": [
        "git update-index --skip-worktree lefthook.json",
        "git update-index --assume-unchanged .gitleaks.toml",
        "git update-index --assume lefthook.json",
        "git update-index --skip lefthook.json",
        "echo lefthook-local.yml >> .git/info/exclude",
        "printf 'x\\n' > .git/info/exclude",
        "cp mis-excluidos .git/info/exclude",
        "sed -i '$a x' .git/info/exclude",
    ],
    # G4 del PR #30: los hooks y la configuración de Git, también si el sandbox lo permitiera.
    "config-de-hooks-ficheros": [
        "echo 'exit 0' > .git/hooks/pre-commit",
        "cp x .git/hooks/post-checkout",
        "echo '[core] hooksPath = /x' >> .git/config",
        "sed -i 's/a/b/' .git/config",
        "echo x > .git/modules/sub/config",
        "echo x > .git/modules/sub/hooks/pre-commit",
        "echo x > .git/worktrees/w/config.worktree",
    ],
    # Commits que no pasan por pre-commit.
    "commit-sin-hooks": [
        # G4 del PR #30: git am no lanza pre-commit.
        "git am 0001.patch",
        "git am --no-verify 0001.patch",
        "git am --continue",
        "git commit-tree HEAD^{tree} -p HEAD -m x",
        "git update-ref refs/heads/x $(git commit-tree HEAD^{tree} -m x)",
        "git fast-import < flujo",
        "git clone . ../otra",
        "git clone /home/u/proyecto ../otra",
        "git clone --no-hardlinks ./ ../otra",
        "git clone file:///home/u/proyecto ../otra",
        "GIT_DIR=../otra/.git git commit -m x",
        "git --git-dir=../otra/.git commit -m x",
        "git --work-tree=../otra commit -m x",
        "GIT_INDEX_FILE=/home/u/otro git commit -m x",
        "git --git-dir ../otra/.git merge main",
        "gh api repos/a/b/git/commits -f message=x -f tree=abc",
        "gh api -X PUT repos/a/b/contents/src/x.py -f message=x -f content=eA==",
        "gh api --method DELETE repos/a/b/contents/x.py -f message=x -f sha=abc",
        "gh api repos/a/b/contents/x.py -f message=x -f content=eA==",
        "gh api repos/a/b/contents/x.py --input cuerpo.json",
        "gh api graphql -f query='mutation { createCommitOnBranch(input: {}) { commit { oid } } }'",
    ],
}

LEGITIMAS = [
    "git commit -m 'feat(a): b'",
    "git commit -am 'fix(a): b'",
    "git commit -m '-n'",
    "git commit -m -n",
    "git commit -F .tareas/VIC-18/commit.txt",
    "git commit --amend --no-edit",
    "git commit --no-signoff -m x",
    "git commit -v -m x",
    "git merge -n main",
    "git merge --no-stat main",
    "git merge --no-ff main",
    "git push origin feat/vic-18-lefthook",
    "git push --no-verify origin x",
    "git -c user.email=bot@ejemplo.dev commit -m x",
    "git -c core.fsmonitor=false status",
    "echo LEFTHOOK=0",
    "grep -rn 'LEFTHOOK=0' docs",
    "rg --no-verify docs",
    "LEFTHOOK_VERBOSE=1 git commit -m x",
    "LEFTHOOK_OUTPUT=summary git commit -m x",
    "PATH=/home/u/bin:$PATH npm test",
    "HOME=/home/u/otro npm test",
    "cat lefthook-local.yml",
    "ls .lefthook-local",
    "rm lefthook-local.yml",
    "git add lefthook.json",
    "git status --short lefthook-local.yml",
    "cat .git/info/exclude",
    "wc -l < .git/info/exclude",
    "grep gitleaks < lefthook-local.yml",
    "echo x > lefthook.json",
    "cp plantilla.json lefthook.json",
    "git update-index --no-skip-worktree lefthook.json",
    "git update-index --refresh",
    "git update-ref -d refs/heads/vieja",
    "git clone https://github.com/victor-lg/calculadora.git",
    "git am --abort",
    "cat .git/config",
    "ls .git/hooks",
    "echo 'light weight",
    "git clone git@github.com:victor-lg/calculadora.git ../calc",
    "git clone ssh://git@github.com/victor-lg/calculadora.git",
    "git worktree add --no-track -b feat/vic-18-x ../w origin/main",
    "gh api repos/a/b/contents/README.md",
    "gh api repos/a/b/contents/README.md --jq .content",
    "gh api repos/a/b/git/refs/heads/main",
    "gh api repos/a/b/pulls/29 --jq .merged_at",
    "gh pr create --draft --title x --body-file .tareas/VIC-18/pr.md",
    "npm test",
    "echo 'sin cerrar",
]

# Lee el texto de la orden: esto lo esquiva (segunda capa, no seguridad).
SE_ESQUIVA = [
    "bash -c 'git commit --no-verify -m x'",
    "eval 'LEFTHOOK=0 git commit -m x'",
    "V=--no-verify; git commit $V -m x",
    "F=lefthook-local.yml; echo x > $F",
    "./commit-sin-hooks.sh",
    "python3 -c \"open('lefthook-local.yml','w').write('{}')\"",
    "N=LEFTHOOK; export $N=0; git commit -m x",
    "git -C ../otra-copia-ya-clonada commit -m x",
    # G4 del PR #30: envolturas y asignaciones que el lector no conoce, y un repo nuevo sin hooks.
    "setsid git commit --no-verify -m x",
    "env --split-string='LEFTHOOK=0 git commit -m x'",
    "printf -v LEFTHOOK 0; export LEFTHOOK; git commit -m x",
    "git init sub && git -C sub commit --allow-empty -m x",
    "tar xf config.tar",
]

# Tampoco pasan por pre-commit, y no se bloquean a propósito: crean commits con contenido
# que ya estaba en otro (o, en un merge en avance rápido, no crean ninguno). Los cubre la CI.
NO_SE_BLOQUEAN = [
    "git merge main",
    "git stash && git merge stash@{0}",
    "git cherry-pick abc123",
    "git revert HEAD",
    "git rebase origin/main",
]


class GuardaBash(unittest.TestCase):
    def decide(self, comando):
        return guarda.decidir_bash(comando, CONF)[0]

    def test_formas_detectadas(self):
        for regla, comandos in BASH.items():
            for comando in comandos:
                with self.subTest(comando=comando):
                    self.assertEqual(self.decide(comando), regla.removesuffix("-ficheros"))

    def test_formas_legitimas(self):
        for comando in LEGITIMAS:
            with self.subTest(comando=comando):
                self.assertIsNone(self.decide(comando))

    def test_limitacion_conocida_no_se_detecta(self):
        for comando in SE_ESQUIVA + NO_SE_BLOQUEAN:
            with self.subTest(comando=comando):
                self.assertIsNone(self.decide(comando))

    def test_dice_que_forma(self):
        self.assertEqual(guarda.decidir_bash("git commit -nm x", CONF), ("sin-verificar", "git commit -n"))
        self.assertEqual(guarda.decidir_bash("LEFTHOOK_EXCLUDE=a git commit", CONF),
                         ("variables-de-hooks", "LEFTHOOK_EXCLUDE"))
        self.assertEqual(guarda.decidir_bash("echo x > .lefthook-local.yml", CONF),
                         ("config-local-lefthook", ".lefthook-local.yml"))

    def test_sin_cerrar_falla_cerrado_si_menciona_algo(self):
        for comando in ("git commit -m 'x", "LEFTHOOK=0 echo \"x", "echo x > lefthook-local.yml $(a"):
            with self.subTest(comando=comando):
                self.assertEqual(self.decide(comando), "sin-analizar")

    def test_relevante_con_limites_de_palabra(self):
        """G4 del PR #30: «light» o «weight» sin cerrar no son git."""
        self.assertIsNone(self.decide("echo 'light"))
        self.assertEqual(self.decide("echo 'x' > .git/hooks/a 'b"), "sin-analizar")

    def test_orden_enorme_falla_cerrado(self):
        self.assertEqual(self.decide("git status # " + "x" * CONF["max_caracteres_orden"]), "sin-analizar")
        self.assertIsNone(self.decide("ls # " + "x" * CONF["max_caracteres_orden"]))


class GuardaHerramientas(unittest.TestCase):
    def decide(self, herramienta, ruta, cwd=CWD):
        clave = "notebook_path" if herramienta == "NotebookEdit" else "file_path"
        return guarda.decidir({"tool_name": herramienta, "tool_input": {clave: ruta}, "cwd": cwd}, CONF)[0]

    def test_config_local(self):
        rutas = [f"{CWD}/{base}.{ext}" for base in ("lefthook-local", ".lefthook-local", ".config/lefthook-local")
                 for ext in ("yml", "yaml", "json", "jsonc", "toml")]
        rutas += [f"{CWD}/.lefthook-local/pre-commit/a.sh", "lefthook-local.yml", "app/.lefthook-local.yml"]
        for herramienta in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            for ruta in rutas:
                with self.subTest(herramienta=herramienta, ruta=ruta):
                    self.assertEqual(self.decide(herramienta, ruta), "config-local-lefthook")

    def test_hooks_y_config_de_git(self):
        """G4 del PR #30: el sandbox no limita Write ni Edit."""
        for ruta in (f"{CWD}/.git/hooks/pre-commit", f"{CWD}/.git/config", ".git/hooks/post-checkout",
                     f"{CWD}/.git/modules/sub/config", f"{CWD}/.git/worktrees/w/config.worktree"):
            for herramienta in ("Write", "Edit"):
                with self.subTest(herramienta=herramienta, ruta=ruta):
                    self.assertEqual(self.decide(herramienta, ruta), "config-de-hooks")

    def test_otra_config_de_lefthook(self):
        for ruta in (f"{CWD}/lefthook.yml", f"{CWD}/.lefthook.json", f"{CWD}/.config/lefthook.toml",
                     f"{CWD}/.lefthook/pre-commit/a.sh", f"{CWD}/LEFTHOOK-LOCAL.YML"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.decide("Write", ruta), "config-local-lefthook")

    def test_exclude(self):
        for ruta in (f"{CWD}/.git/info/exclude", ".git/info/exclude"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.decide("Edit", ruta), "ocultar-cambios")

    def test_enlace_a_la_config_local(self):
        with tempfile.TemporaryDirectory() as d:
            os.symlink(os.path.join(d, "lefthook-local.yml"), os.path.join(d, "notas.yml"))
            self.assertEqual(self.decide("Write", os.path.join(d, "notas.yml"), d), "config-local-lefthook")

    def test_pasan(self):
        for ruta in (f"{CWD}/lefthook.json", f"{CWD}/docs/lefthook.md", f"{CWD}/docs/lefthook-local.md",
                     f"{CWD}/.gitignore", f"{CWD}/src/git/config", f"{CWD}/hooks/pre-commit",
                     f"{CWD}/src/exclude", "notas.md"):
            with self.subTest(ruta=ruta):
                self.assertIsNone(self.decide("Write", ruta))

    def test_leer_no_es_cosa_suya(self):
        self.assertIsNone(self.decide("Read", f"{CWD}/lefthook-local.yml"))

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
        self.assertEqual(self.ejecuta(self.entrada("Bash", command="git commit -m 'feat(a): b'")), "")
        self.assertEqual(self.ejecuta(self.entrada("Write", file_path=f"{CWD}/a.md", content="x")), "")

    def test_bloquea_con_alternativa(self):
        salida = self.decision(self.ejecuta(self.entrada("Bash", command="git commit --no-verify -m x")))
        self.assertEqual(salida["permissionDecision"], "deny")
        self.assertIn("(git commit --no-verify)", salida["permissionDecisionReason"])
        self.assertIn("En su lugar:", salida["permissionDecisionReason"])
        self.assertIn("no la esquives", salida["permissionDecisionReason"])

    def test_entrada_rota_falla_cerrado(self):
        for entrada in ("", "no es json", "{}", '{"tool_name": "Bash", "tool_input": {}}',
                        '{"tool_name": "Write", "tool_input": {"file_path": 3}}'):
            with self.subTest(entrada=entrada):
                self.assertEqual(self.decision(self.ejecuta(entrada))["permissionDecision"], "deny")

    def test_sin_reglas_o_sin_lector_falla_cerrado(self):
        for ficheros in (("guarda-saltos.py",), ("guarda-saltos.py", "reglas-saltos.json")):
            with self.subTest(ficheros=ficheros), tempfile.TemporaryDirectory() as d:
                for nombre in ficheros:
                    (pathlib.Path(d) / nombre).write_text((HOOKS / nombre).read_text(encoding="utf-8"),
                                                          encoding="utf-8")
                salida = self.ejecuta(self.entrada("Bash", command="ls"), pathlib.Path(d) / "guarda-saltos.py")
                self.assertEqual(self.decision(salida)["permissionDecision"], "deny")

    def test_mensajes_dicen_que_hacer(self):
        for regla, info in CONF["reglas"].items():
            with self.subTest(regla=regla):
                self.assertEqual(info["nivel"], "bloquear")
                self.assertIn("En su lugar:", info["mensaje"])

    def test_registro(self):
        registro = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        grupo = next(g for g in registro if "guarda-saltos.py" in g["hooks"][0]["command"])
        self.assertEqual(set(grupo["matcher"].split("|")), {"Bash", "Write", "Edit", "MultiEdit", "NotebookEdit"})
        self.assertTrue(grupo["hooks"][0]["command"].endswith("|| exit 2"))


if __name__ == "__main__":
    unittest.main()

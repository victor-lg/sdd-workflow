"""Tests de plugin-sdd/hooks/guarda-git.py (VIC-17): M16, X-03 y REG-83. Formas que se
bloquean, formas legítimas que no, y lo que el hook no pretende detectar."""
import importlib.util
import io
import itertools
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

RAIZ = pathlib.Path(__file__).resolve().parent.parent
HOOKS = RAIZ / "plugin-sdd" / "hooks"
RUTA = HOOKS / "guarda-git.py"
_spec = importlib.util.spec_from_file_location("guarda_git", RUTA)
guarda = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guarda)
CONF = json.loads((HOOKS / "reglas-git.json").read_text(encoding="utf-8"))
lector = sys.modules["lector_bash"]

BLOQUEADAS = {
    "push-seguimiento": [
        "git push -u origin feat/x",
        "git push origin feat/x -u",
        "git push --set-upstream origin feat/x",
        "git push --set-up origin feat/x",
        "git push -fu origin feat/x",
        "git push -uf origin feat/x",
        "git push -n -u origin x",
        "git -C sub push -u origin x",
        "git --no-pager push -u origin x",
        "git -c a.b=c push -u origin x",
        "git --git-dir=.git push -u origin x",
        "git --git-dir .git push -u origin x",
        "/usr/bin/git push -u origin x",
        "git.exe push -u origin x",
        "FOO=1 git push -u origin x",
        "env FOO=1 git push -u origin x",
        "env -u FOO git push -u origin x",
        "command git push -u origin x",
        "timeout 30 git push -u origin x",
        "timeout -k 5 30 git push -u origin x",
        "nice -n 5 git push -u origin x",
        "nohup git push -u origin x",
        "sudo -u yo git push -u origin x",
        "git commit -m hola && git push -u origin x",
        "git status; git push -u origin x",
        "false || git push -u origin x",
        "git status | git push -u origin x",
        "(git push -u origin x)",
        "( cd sub && git push -u origin x )",
        "{ git push -u origin x; }",
        "if git push -u origin x; then echo ok; fi",
        "while git push -u origin x; do sleep 1; done",
        "for r in a; do git push -u origin $r; done",
        "! git push -u origin x",
        "echo $(git push -u origin x)",
        'echo "$(git push -u origin x)"',
        "echo `git push -u origin x`",
        'git "push" -u origin x',
        "git pu\\sh -u origin x",
        "git push '-u' origin x",
        "git push \\\n  -u origin x",
        "git push -u origin x > /dev/null 2>&1",
        "git push -u origin x &> salida.log",
        "git -c push.autoSetupRemote=true push origin x",
        "git -c push.autosetupremote push origin x",
        "cat <<'FIN'\nhola git\nFIN\ngit push -u origin x",
        "cat <<FIN\n$(git push -u origin x)\nFIN",
    ],
    "branch-seguimiento": [
        "git branch --set-upstream-to=origin/x",
        "git branch --set-upstream-to origin/x",
        "git branch --set-upstream-to=origin/x feat/x",
        "git branch --set-up=origin/x",
        "git branch -u origin/x",
        "git branch -uorigin/x",
        "git branch -u origin/x feat/x",
        "git -C sub branch -u origin/x",
        "git pull --set-upstream origin x",
        "git fetch --set-upstream origin x",
        "git fetch --set origin x",
    ],
    "config-escribe": [
        "git config user.name Bot",
        "git config --local user.name Bot",
        "git config --global user.email a@b.c",
        "git config --file f.cfg a.b c",
        "git config -f f.cfg a.b c",
        "git config --add a.b c",
        "git config --unset a.b",
        "git config --unset-all a.b",
        "git config --replace-all a.b c",
        "git config --rename-section a b",
        "git config --remove-section a",
        "git config --edit",
        "git config -e",
        "git config --type=bool a.b true",
        "git config --type bool a.b true",
        "git config set a.b c",
        "git config unset a.b",
        "git config rename-section a b",
        "git config remove-section a",
        "git config edit",
        "git config set --global a.b c",
        "git config branch.x.remote origin",
        'git -C sub config "user.name" "Bot Agente"',
        "git config push.autoSetupRemote true && git push",
    ],
    "crear-sin-no-track": [
        "git switch -c feat/x origin/main",
        "git switch -cfeat/x origin/main",
        "git switch --create feat/x origin/main",
        "git switch --create=feat/x origin/main",
        "git switch --cre feat/x origin/main",
        "git switch -C feat/x origin/main",
        "git switch --force-create feat/x origin/main",
        "git switch -c feat/x origin/otra",
        "git switch -c feat/x refs/remotes/origin/main",
        "git switch -c feat/x remotes/origin/main",
        "git switch -c feat/x --track origin/main",
        "git switch -c feat/x -t origin/main",
        "git switch -c feat/x --track=direct origin/main",
        "git switch -c feat/x --no-track --track origin/main",
        "git switch --track origin/x",
        "git switch -t origin/x",
        "git checkout -b feat/x origin/main",
        "git checkout -bfeat/x origin/main",
        "git checkout -qb feat/x origin/main",
        "git checkout -B feat/x origin/main",
        "git checkout -b feat/x --track origin/main",
        "git checkout -b feat/x -t origin/main",
        "git checkout --track origin/x",
        "git checkout -t origin/x",
        "git fetch origin && git switch -c feat/x origin/main",
    ],
    "add-sin-nombre": [
        "git add -A",
        "git add --all",
        "git add --al",
        "git add -Av",
        "git add -vA",
        "git add -f -A",
        "git add -A src",
        "git add .",
        "git add ./",
        "git add -- .",
        "git add -v .",
        'git add "."',
        "git add '.'",
        "git add src/a.py .",
        "git add ..",
        "git add ../..",
        "git add src/..",
        "git add '*'",
        "git add *",
        "git add ./*",
        "git add :/",
        "git add ':(top)'",
        "git add -u",
        "git add --update",
        "git add --no-ignore-removal",
        "git -C sub add .",
        "cd sub && git add .",
        "git add . && git commit -m x",
        "git status; git add -A; git commit -m x",
        "git stage .",
        "git stage -A",
        "git add -- ':!.bashrc'",
        "git add ':^x' ':!y'",
        "git add ':(exclude)x'",
        "git add '.*'",
        "git add './**'",
        "git add '**/*'",
        "git add ':/**'",
        "git add ':(glob)**'",
        "git add ':(glob)*'",
        "git add ':(top,glob)**'",
        "git add -n --no-dry-run -A",
        "time -p git add .",
        "(( x = 1 << 2 ))\ngit add .",
    ],
}

LEGITIMAS = [
    # Push sin seguimiento.
    "git push origin feat/x",
    "git push origin HEAD:refs/heads/feat/x",
    "git push --no-set-upstream origin x",
    "git push --force-with-lease origin x",
    "git push -f origin x",
    "git push -o u origin x",
    "git push -ou origin x",
    "git push --push-option u origin x",
    "git push --repo -u",
    "git push origin -- -u",
    "git push --dry-run origin x",
    "git -c push.autoSetupRemote=false push origin x",
    "git pull origin main",
    "git pull --no-set-upstream origin x",
    "git fetch -u origin x",
    # Branch sin configurar el seguimiento.
    "git branch",
    "git branch -a",
    "git branch -vv",
    "git branch --show-current",
    "git branch -d feat/x",
    "git branch -D feat/x",
    "git branch -m nueva",
    "git branch nueva",
    "git branch --format '%(upstream)' -a",
    "git branch --contains abc",
    "git branch --unset-upstream",
    # Config de lectura.
    "git config user.name",
    "git config --get user.name",
    "git config --get-all a.b",
    "git config --get-regexp '^branch'",
    "git config --get-urlmatch http https://a.b",
    "git config --get a.b patron",
    "git config --list",
    "git config -l",
    "git config --local --list",
    "git config --global --get user.email",
    "git config -f f.cfg --get a.b",
    "git config -f f.cfg a.b",
    "git config --file f.cfg --list",
    "git config --type=bool a.b",
    "git config --type bool a.b",
    "git config --show-origin --list",
    "git config --name-only --list",
    "git config -z --list",
    "git config get user.name",
    "git config get --all a.b",
    "git config list",
    "git config list --global",
    "git config user.name > nombre.txt",
    "git config --get a.b 2>/dev/null || echo no",
    "VALOR=$(git config --get a.b)",
    "git -c user.email=a@b.c commit -m x",
    # Crear ramas bien o cambiar a una que ya existe.
    "git switch --no-track -c feat/x origin/main",
    "git switch -c feat/x --no-track origin/main",
    "git switch --no-tr -c feat/x origin/main",
    "git switch -c feat/x --track --no-track origin/main",
    "git fetch origin && git switch --no-track -c feat/x origin/main",
    "git checkout --no-track -b feat/x origin/main",
    "git checkout -b feat/x --no-track origin/main",
    "git switch main",
    "git switch feat/x",
    "git switch -",
    "git switch --detach origin/main",
    "git switch --orphan vacia",
    "git checkout main",
    "git checkout feat/x",
    "git checkout -- fichero.py",
    "git checkout origin/main -- fichero.py",
    "git checkout HEAD~1 -- origin/main",
    # Add por nombre y vistas previas.
    "git add src/a.py tests/b.py",
    "git add -- src/a.py",
    "git add ./src/a.py",
    "git add .gitignore",
    "git add .github/workflows/x.yml",
    "git add -f build/a.txt",
    "git add -v src/a.py",
    "git add -p src/a.py",
    "git add -N src/a.py",
    "git add --chmod=+x script.sh",
    "git add --chmod +x script.sh",
    "git add --pathspec-from-file=lista.txt",
    "git add src/",
    "git add src/*.py",
    "git add -n .",
    "git add --dry-run -A",
    'git add "$FICHERO"',
    "git add src/a.py ':!src/b.py'",
    "git stage src/a.py",
    "git add -- -A",
    # La regla aparece solo como texto.
    "echo 'git push -u origin x'",
    'echo "git add ."',
    "echo git add .",
    "printf '%s\\n' 'git config a b'",
    "grep -n 'git add -A' docs/x.md",
    'rg "git push -u" -g "*.md"',
    "# git add .",
    "ls # git push -u origin x",
    'git commit -m "no uses git add . ni git push -u"',
    "git commit -m 'fix: quita git config user.name Bot'",
    "git log --grep='git add -A'",
    "git grep -n 'git push -u'",
    "git stash push -u",
    "git help push",
    "git --version",
    "git status",
    "git diff origin/main...HEAD",
    "git log --oneline -5 origin/main",
    "git fetch origin",
    "git merge origin/main",
    "git commit --allow-empty -m x",
    # Heredocs: su cuerpo no se ejecuta.
    "cat <<'FIN'\ngit push -u origin x\ngit add .\nFIN",
    'cat <<"FIN"\ngit add -A\nFIN',
    "cat <<\\FIN\ngit add -A\nFIN",
    "cat <<FIN\ngit add -A\nFIN",
    "cat <<-FIN\n\tgit add -A\n\tFIN",
    "cat <<'FIN' > nota.md\nNo se usa git config a b, don't.\nFIN",
    "git commit -m \"$(cat <<'EOF'\nfeat: bloquea git add -A y git push -u\n\nCuerpo con ' y \" sueltos.\nEOF\n)\"",
    "{ cat \"$TMPDIR/g4.md\"; cat <<'METRICAS_SDD'\nMétricas G4: PR #1 · git add .\nMETRICAS_SDD\n} | gh pr comment 1 --body-file -",
    # Otras formas de shell que no deben confundir al lector.
    "cat <<< 'git add .'",
    "echo $((1 << 2)) && git status",
    'echo "${VAR:-git add .}"',
    "echo $'git add .'",
    "diff <(git show a:f) <(git show b:f)",
    "grep -c 'it''s' f.txt",
    "ls > 'git add .'",
    "case $a in x) echo git add . ;; esac",
    "gh pr create --draft --title 'git add .' --body-file f.md",
    "digit add .",
    "python3 -c 'print(1)'",
]

# Segunda capa, no seguridad: estas formas pasan y se documenta que pasan.
SE_ESQUIVA = [
    "bash -c 'git push -u origin x'",
    "sh -c 'git add .'",
    "eval 'git add -A'",
    'S=push; git $S -u origin x',
    'A=-A; git add $A',
    'git add "$(echo .)"',
    "./subir.sh",
    "git -c alias.sube='push -u' sube origin x",
    "ls | xargs git add -A",
    'echo "${X:-$(git add .)}"',
    "echo $(( $(git add .) ))",
    "function f { git add .; }",
    "(( n << k ))\ngit add .",
]


class Guarda(unittest.TestCase):
    def decide(self, comando):
        with mock.patch.object(guarda, "comprobar_base", return_value=None), \
                mock.patch.object(guarda, "regla_commit", return_value=None):
            return guarda.decidir(comando, "/tmp", CONF)

    def test_formas_bloqueadas(self):
        for regla, comandos in BLOQUEADAS.items():
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

    def test_sin_cerrar_falla_cerrado_si_menciona_git(self):
        for comando in ("git commit -m 'sin cerrar", 'git add "a', "git status $(ls", "echo `git status"):
            with self.subTest(comando=comando):
                self.assertEqual(self.decide(comando), "sin-analizar")

    def test_sin_cerrar_sin_git_lo_deja_a_bash(self):
        self.assertIsNone(self.decide("echo 'sin cerrar"))

    def test_analisis_con_plazo_falla_cerrado(self):
        with mock.patch.object(guarda.time, "monotonic", side_effect=itertools.count(0, 100)):
            self.assertEqual(self.decide("ls; git status"), "sin-analizar")

    def test_orden_enorme_falla_cerrado(self):
        self.assertEqual(self.decide("git status # " + "x" * CONF["max_caracteres_orden"]), "sin-analizar")

    def test_el_plazo_cabe_en_el_timeout_del_hook(self):
        registro = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.assertLess(CONF["max_segundos_analisis"] + 4 * 3, registro["PreToolUse"][0]["hooks"][0]["timeout"])

    def test_sigue_cd_con_opciones(self):
        vistos = []
        with mock.patch.object(guarda, "comprobar_base", side_effect=lambda i, cwd, p, c: vistos.append(cwd)):
            guarda.decidir("cd -P /a; git switch -c x; cd -- /b; git switch -c y", "/tmp", CONF)
        self.assertEqual(vistos, ["/a", "/b"])

    def test_mensajes_dicen_que_hacer(self):
        for regla, info in CONF["reglas"].items():
            with self.subTest(regla=regla):
                self.assertIn(info["nivel"], ("bloquear", "preguntar"))
                if info["nivel"] == "bloquear":
                    self.assertIn("En su lugar:", info["mensaje"])

    def test_el_lector_separa_ordenes_y_quita_comillas(self):
        self.assertEqual(guarda.analizar("a 'b c' \"d\"e; f | g && h\ni"),
                         [["a", "b c", "de"], ["f"], ["g"], ["h"], ["i"]])

    def test_el_lector_guarda_redirecciones_y_heredocs(self):
        a = lector.analizar_todo("cat < a.txt > 'b c' 2>&1 &> d; e >& f; g <&0 >| h <<< x\ncat <<FIN\n$(i)\nFIN\n"
                                 "cat <<'X'\nj\nX")
        self.assertEqual(a.redirecciones, [(0, "<", "a.txt"), (0, ">", "b c"), (0, "&>", "d"), (1, ">&", "f"),
                                           (2, ">|", "h")])
        self.assertEqual(a.heredocs_expandidos, 1)
        self.assertIn(["i"], a.ordenes)

    def test_el_lector_ve_la_sustitucion_dentro_de_dobles(self):
        self.assertIn(["git", "status"], guarda.analizar('echo "x $(git status) y"'))


class BaseDeLaRama(unittest.TestCase):
    """REG-83 con repos de verdad: un origen desnudo y un clon."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        origen = os.path.join(self.dir.name, "origen.git")
        self.copia = os.path.join(self.dir.name, "copia")
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", origen], check=True)
        subprocess.run(["git", "clone", "-q", origen, self.copia], check=True, capture_output=True)
        self.git("checkout", "-q", "-B", "main")
        self.commit("uno")
        self.git("push", "-q", "origin", "main")
        self.git("fetch", "-q", "origin")

    def git(self, *args):
        return subprocess.run(["git", "-C", self.copia, *args], check=True, capture_output=True, text=True).stdout

    def commit(self, texto):
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", texto)

    def envejecer_fetch(self):
        ruta = os.path.join(self.copia, ".git", "FETCH_HEAD")
        hace = time.time() - (CONF["max_minutos_desde_fetch"] + 1) * 60
        os.utime(ruta, (hace, hace))

    def decide(self, comando):
        return guarda.decidir(comando, self.copia, CONF)

    def test_desde_origin_main_recien_traido(self):
        self.assertIsNone(self.decide("git switch --no-track -c feat/x origin/main"))

    def test_desde_origin_main_con_fetch_viejo(self):
        self.envejecer_fetch()
        self.assertEqual(self.decide("git switch --no-track -c feat/x origin/main"), "base-desactualizada")

    def test_sin_fetch_nunca(self):
        os.unlink(os.path.join(self.copia, ".git", "FETCH_HEAD"))
        self.assertEqual(self.decide("git checkout --no-track -b feat/x origin/main"), "base-desactualizada")

    def test_fetch_en_la_misma_orden(self):
        self.envejecer_fetch()
        self.assertIsNone(self.decide("git fetch origin && git switch --no-track -c feat/x origin/main"))

    def test_fetch_despues_no_cuenta(self):
        self.envejecer_fetch()
        self.assertEqual(self.decide("git switch --no-track -c feat/x origin/main; git fetch origin"),
                         "base-desactualizada")

    def test_desde_main_local_al_dia(self):
        self.assertIsNone(self.decide("git switch -c feat/x"))
        self.assertIsNone(self.decide("git switch -c feat/x main"))
        self.assertIsNone(self.decide("git checkout -b feat/x HEAD"))

    def test_main_local_por_delante_o_por_detras(self):
        self.commit("dos")
        self.assertEqual(self.decide("git switch -c feat/x"), "base-desactualizada")
        self.assertEqual(self.decide("git switch -c feat/x main"), "base-desactualizada")

    def test_main_local_con_fetch_viejo(self):
        self.envejecer_fetch()
        self.assertEqual(self.decide("git switch -c feat/x"), "base-desactualizada")

    def test_pull_en_la_misma_orden(self):
        self.commit("dos")
        self.assertIsNone(self.decide("git pull origin main && git switch -c feat/x"))

    def test_pull_en_otra_rama_no_actualiza_main(self):
        self.commit("dos")
        self.git("switch", "-q", "-c", "feat/a")
        self.assertEqual(self.decide("git pull origin main && git switch -c feat/b main"), "base-desactualizada")

    def test_fetch_o_pull_que_no_traen_main_no_cuentan(self):
        self.envejecer_fetch()
        for previa in ("git fetch upstream", "git fetch origin feat/z", "git fetch --dry-run",
                       "git -C /otro fetch origin", "git pull origin feat/z"):
            with self.subTest(previa=previa):
                self.assertEqual(self.decide(f"{previa}; git switch --no-track -c feat/x origin/main"),
                                 "base-desactualizada")

    def test_fetch_de_main_cuenta(self):
        self.envejecer_fetch()
        for previa in ("git fetch", "git fetch origin", "git fetch -n origin", "git fetch origin main",
                       "git pull origin main"):
            with self.subTest(previa=previa):
                self.assertIsNone(self.decide(f"{previa}; git switch --no-track -c feat/x origin/main"))

    def test_otra_base_pregunta(self):
        self.git("switch", "-q", "-c", "feat/a")
        for comando in ("git switch -c feat/b", "git switch -c feat/b feat/a",
                        "git switch --no-track -c feat/b origin/feat/a", "git checkout -b feat/b HEAD~1"):
            with self.subTest(comando=comando):
                self.assertEqual(self.decide(comando), "base-no-main")

    def test_cabeza_suelta_pregunta(self):
        self.git("switch", "-q", "--detach")
        self.assertEqual(self.decide("git switch -c feat/x"), "base-no-main")

    def test_bloquear_gana_a_preguntar(self):
        self.assertEqual(self.decide("git switch -c a feat/z; git add ."), "add-sin-nombre")

    def test_sigue_cd_y_dash_c(self):
        padre, nombre = os.path.split(self.copia)
        for comando in (f"cd {nombre} && git switch -c feat/x", f"git -C {nombre} switch -c feat/x"):
            with self.subTest(comando=comando):
                self.assertIsNone(guarda.decidir(comando, padre, CONF))

    def test_worktree_mira_su_propio_fetch(self):
        arbol = os.path.join(self.dir.name, "arbol")
        self.git("worktree", "add", "-q", "--no-track", "-b", "feat/w", arbol, "origin/main")
        self.assertEqual(guarda.decidir("git switch --no-track -c feat/x origin/main", arbol, CONF),
                         "base-desactualizada")

    def test_fuera_de_un_repo_falla_cerrado(self):
        self.assertEqual(guarda.decidir("git switch -c x", self.dir.name, CONF), "sin-mirar")

    def test_pushd_falla_cerrado(self):
        self.assertEqual(self.decide("pushd sub && git switch -c x"), "sin-mirar")

    def test_ruta_dinamica_falla_cerrado(self):
        self.assertEqual(guarda.decidir('git -C "$D" switch -c x', self.copia, CONF), "sin-mirar")


class Fugas(unittest.TestCase):
    """X-04 con un repo de verdad: lo preparado, lo que añade la misma orden y -a."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.repo = os.path.join(self.dir.name, "repo")
        subprocess.run(["git", "init", "-q", "-b", "main", self.repo], check=True)
        self.escribe(".gitignore", ".tareas/\nbuild/\n")
        self.escribe("src/a.py", "a = 1\n")
        self.escribe("config.local", "x\n")
        self.git("add", ".gitignore", "src/a.py", "config.local")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "uno")

    def escribe(self, ruta, texto):
        completa = os.path.join(self.repo, ruta)
        os.makedirs(os.path.dirname(completa), exist_ok=True)
        with open(completa, "w", encoding="utf-8") as f:
            f.write(texto)

    def git(self, *args):
        subprocess.run(["git", "-C", self.repo, *args], check=True, capture_output=True)

    def decide(self, comando, cwd=None):
        return guarda.decidir_con_detalle(comando, cwd or self.repo, CONF)

    def test_commit_normal(self):
        self.escribe("src/a.py", "a = 2\n")
        self.git("add", "src/a.py")
        self.assertEqual(self.decide("git commit -m x"), (None, None))

    def test_preparado_que_nunca_se_sube(self):
        for ruta in (".env", ".env.local", "conf/.env.production", "certs/servidor.key", ".bashrc", "id_ed25519"):
            with self.subTest(ruta=ruta):
                self.escribe(ruta, "SECRETO=1\n")
                self.git("add", "-f", ruta)
                self.assertEqual(self.decide("git commit -m x"), ("commit-fuga", [ruta]))
                self.git("rm", "-q", "--cached", ruta)

    def test_plantillas_y_claves_publicas_pasan(self):
        for ruta in (".env.example", ".env.sample", "id_ed25519.pub", "docs/entorno.md"):
            with self.subTest(ruta=ruta):
                self.escribe(ruta, "X=\n")
                self.git("add", ruta)
                self.assertEqual(self.decide("git commit -m x"), (None, None))

    def test_preparado_que_gitignore_excluye(self):
        self.escribe(".tareas/VIC-1.md", "estado\n")
        self.escribe("build/salida.js", "x\n")
        self.git("add", "-f", ".tareas/VIC-1.md", "build/salida.js")
        regla, rutas = self.decide("git commit -m x")
        self.assertEqual((regla, sorted(rutas)), ("commit-fuga", [".tareas/VIC-1.md", "build/salida.js"]))

    def test_add_en_la_misma_orden(self):
        self.escribe(".env", "SECRETO=1\n")
        self.escribe("build/salida.js", "x\n")
        for comando in ("git add .env && git commit -m x", "git add -f build/salida.js; git commit -m x",
                        "cd src && git add ../.env && git commit -m x", "git stage .env && git commit -m x"):
            with self.subTest(comando=comando):
                self.assertEqual(self.decide(comando)[0], "commit-fuga")

    def test_add_de_prueba_o_posterior_no_cuenta(self):
        self.escribe(".env", "SECRETO=1\n")
        for comando in ("git add -n .env && git commit -m x", "git commit -m x --allow-empty; git add .env"):
            with self.subTest(comando=comando):
                self.assertEqual(self.decide(comando), (None, None))

    def test_quitar_un_secreto_no_es_fuga(self):
        self.escribe(".env", "SECRETO=1\n")
        self.git("add", "-f", ".env")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "fuga anterior")
        self.git("rm", "-q", "--cached", ".env")
        self.assertEqual(self.decide("git commit -m 'quita .env'"), (None, None))

    def test_commit_a_mira_lo_modificado(self):
        self.escribe(".gitignore", ".tareas/\nbuild/\nconfig.local\n")
        self.git("add", ".gitignore")
        self.escribe("config.local", "y\n")
        self.assertEqual(self.decide("git commit -m x"), (None, None))
        for comando in ("git commit -am x", "git commit --all -m x", "git commit -m x config.local",
                        "git commit -m x -- config.local"):
            with self.subTest(comando=comando):
                self.assertEqual(self.decide(comando), ("commit-fuga", ["config.local"]))
        self.assertEqual(self.decide("git commit -m x .gitignore"), (None, None))

    def test_sigue_cd_y_dash_c(self):
        self.escribe(".env", "SECRETO=1\n")
        self.git("add", "-f", ".env")
        padre, nombre = os.path.split(self.repo)
        for comando in (f"cd {nombre} && git commit -m x", f"git -C {nombre} commit -m x",
                        f"git -C {nombre}/src commit -m x"):
            with self.subTest(comando=comando):
                self.assertEqual(self.decide(comando, padre), ("commit-fuga", [".env"]))

    def test_no_puede_mirar_falla_cerrado(self):
        self.assertEqual(self.decide("git commit -m x", self.dir.name)[0], "commit-sin-mirar")
        self.assertEqual(self.decide('git -C "$D" commit -m x')[0], "commit-sin-mirar")
        with mock.patch.object(guarda.subprocess, "run", side_effect=OSError("sin git")):
            self.assertEqual(self.decide("git commit -m x")[0], "commit-sin-mirar")

    def test_el_mensaje_nombra_los_ficheros(self):
        self.escribe(".env", "SECRETO=1\n")
        self.git("add", "-f", ".env")
        r = subprocess.run([sys.executable, str(RUTA)], capture_output=True, text=True, input=json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}, "cwd": self.repo}))
        motivo = json.loads(r.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("llevaría .env, que", motivo)
        self.assertIn("git restore --staged", motivo)

    def test_lista_corta(self):
        self.assertEqual(guarda.lista_corta(["a", "b"]), "a, b")
        self.assertEqual(guarda.lista_corta([str(i) for i in range(7)]), "0, 1, 2, 3, 4 y 2 más")


class Principal(unittest.TestCase):
    def ejecuta(self, entrada):
        return subprocess.run([sys.executable, str(RUTA)], input=entrada, capture_output=True, text=True)

    def entrada(self, comando):
        return json.dumps({"tool_name": "Bash", "tool_input": {"command": comando}, "cwd": str(RAIZ)})

    def decision(self, r):
        self.assertEqual(r.returncode, 0)
        return json.loads(r.stdout)["hookSpecificOutput"]

    def test_deja_pasar_en_silencio(self):
        r = self.ejecuta(self.entrada("git status"))
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_bloquea_con_alternativa_y_sin_venderse_como_seguridad(self):
        salida = self.decision(self.ejecuta(self.entrada("git push -u origin x")))
        self.assertEqual(salida["permissionDecision"], "deny")
        self.assertEqual(salida["hookEventName"], "PreToolUse")
        self.assertIn("git push origin <rama>", salida["permissionDecisionReason"])
        self.assertIn("no la esquives", salida["permissionDecisionReason"])
        self.assertIn("segunda capa", salida["permissionDecisionReason"])

    def test_entrada_rota_falla_cerrado(self):
        for entrada in ("", "no es json", "{}", '{"tool_input": {}}'):
            with self.subTest(entrada=entrada):
                self.assertEqual(self.decision(self.ejecuta(entrada))["permissionDecision"], "deny")

    def test_anidamiento_extremo_falla_cerrado(self):
        self.assertEqual(self.decision(self.ejecuta(self.entrada("echo " + "$(" * 5000)))["permissionDecision"], "deny")

    def test_reglas_ilegibles_fallan_cerrado(self):
        with tempfile.TemporaryDirectory() as d:
            copia = pathlib.Path(d) / "guarda-git.py"
            copia.write_text(RUTA.read_text(encoding="utf-8"), encoding="utf-8")
            (pathlib.Path(d) / "lector_bash.py").write_text((HOOKS / "lector_bash.py").read_text(encoding="utf-8"),
                                                           encoding="utf-8")
            r = subprocess.run([sys.executable, str(copia)], input=self.entrada("git status"),
                               capture_output=True, text=True)
        self.assertEqual(self.decision(r)["permissionDecision"], "deny")

    def test_sin_el_lector_falla_cerrado(self):
        with tempfile.TemporaryDirectory() as d:
            for nombre in ("guarda-git.py", "reglas-git.json"):
                (pathlib.Path(d) / nombre).write_text((HOOKS / nombre).read_text(encoding="utf-8"), encoding="utf-8")
            r = subprocess.run([sys.executable, str(pathlib.Path(d) / "guarda-git.py")],
                               input=self.entrada("git status"), capture_output=True, text=True)
        self.assertEqual(self.decision(r)["permissionDecision"], "deny")

    def test_pregunta_con_ask(self):
        with mock.patch.object(guarda, "comprobar_base", return_value="base-no-main"), \
                mock.patch.object(sys, "stdin", new=io.StringIO(self.entrada("git switch -c x y"))), \
                mock.patch.object(sys, "stdout", new=io.StringIO()) as salida:
            guarda.main()
        self.assertEqual(json.loads(salida.getvalue())["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_registro_del_hook_falla_cerrado_si_python_no_arranca(self):
        registro = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        orden = registro["PreToolUse"][0]["hooks"][0]["command"]
        self.assertEqual(registro["PreToolUse"][0]["matcher"], "Bash")
        self.assertTrue(orden.endswith("|| exit 2"))


if __name__ == "__main__":
    unittest.main()

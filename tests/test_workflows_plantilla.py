"""Los workflows de la plantilla (VIC-18, PR 3) no corren en este repo: estos tests comprueban
su texto. Que seguridad.yml solo se lance en un PR (con `workflow_dispatch`, el agente podría
dejar sus checks en verde desde su rama; G4 del PR 3, ronda 2), que los jobs se llamen como los
checks requeridos y que versiones, sumas y digest sean los de docs/herramientas.md. Y que la base
sea la ref completa (VIC-26): los pasos que la leen se ejecutan con bash sobre un repo de prueba."""
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "plantilla-proyecto" / ".github"
WORKFLOWS = PLANTILLA / "workflows"
REGISTRO = (RAIZ / "docs" / "herramientas.md").read_text(encoding="utf-8")
REQUERIDOS = {"checks-sdd", "gitleaks", "osv-scanner", "semgrep", "mutaciones", "codigo-sobrante", "duplicados"}


def leer(nombre):
    return (WORKFLOWS / nombre).read_text(encoding="utf-8")


def disparadores(texto):
    bloque = re.search(r"^on:\n((?:[ #].*\n|\n)*)", texto, re.M).group(1)
    return set(re.findall(r"^  ([a-z_]+):", bloque, re.M))


def jobs(texto):
    bloque = texto.split("\njobs:\n", 1)[1]
    return set(re.findall(r"^  ([a-z0-9-]+):", bloque, re.M))


class WorkflowsDeLaPlantilla(unittest.TestCase):
    def test_seguridad_solo_en_un_pr(self):
        self.assertEqual(disparadores(leer("seguridad.yml")), {"pull_request"})
        self.assertNotIn("if:", leer("seguridad.yml"))

    def test_los_jobs_son_los_checks_requeridos(self):
        self.assertEqual(jobs(leer("seguridad.yml")), {"gitleaks", "osv-scanner", "semgrep"})
        self.assertEqual(jobs(leer("sdd.yml")), {"checks-sdd"})
        self.assertEqual(jobs(leer("calidad.yml")), {"mutaciones", "codigo-sobrante", "duplicados"})

    def test_sdd_pasa_los_comentarios_a_checks_py(self):
        """Todas las páginas, en el fichero que lee checks.py (VIC-38)."""
        texto = leer("sdd.yml")
        self.assertIn('gh api --paginate "repos/$REPO/issues/$PR_NUMBER/comments?per_page=100" > '
                      '"$RUNNER_TEMP/sdd/comentarios.json"', texto)
        self.assertIn("PR_COMENTARIOS: ${{ runner.temp }}/sdd/comentarios.json", texto)

    def test_sdd_solo_en_un_pr(self):
        """Fuera de un PR, la base está vacía: el paso que toma checks.py falla (BaseConEtiqueta). VIC-56:
        no con `pull_request_review`; al aprobar, sdd-relanzar.yml vuelve a lanzar la de `pull_request`
        (con dos eventos, el ruleset exige en verde la última de cada uno y la de `pull_request` bloqueaba)."""
        texto = leer("sdd.yml")
        self.assertEqual(disparadores(texto), {"pull_request"})
        self.assertIn("  pull_request:\n    branches: [main]\n", texto)
        # La base y la rama, del evento: es lo que se repite al volver a lanzar una ejecución.
        self.assertNotIn("${{ github.base_ref }}", texto)
        self.assertNotIn("${{ github.head_ref }}", texto)
        self.assertIn("  BASE: refs/remotes/origin/${{ github.event.pull_request.base.ref }}\n", texto)
        self.assertIn("PR_BRANCH: ${{ github.event.pull_request.head.ref }}", texto)

    def test_sdd_una_ejecucion_por_pr(self):
        """VIC-56, G4-2-B-01 y G4-3-B-01: un grupo por número de PR, así que nunca hay dos a la vez con datos
        distintos. Una ejecución nueva (intento 1) cancela la que siga en curso; un relanzamiento no, espera
        (calculadora-discos#87, casos 7 y 10: el relanzamiento de una vieja cancelaba la más nueva, la que toma
        el ruleset). Que una verde vieja no tape una roja nueva depende de que el ruleset tome la ejecución más
        nueva de `pull_request`, no la que termina la última (comprobado en la calculadora, sdd-workflow#72),
        y de que cada ejecución lea las reviews en el momento, no del evento."""
        texto = leer("sdd.yml")
        self.assertIn("concurrency:\n  group: sdd-${{ github.event.pull_request.number }}\n"
                      "  cancel-in-progress: ${{ github.run_attempt == 1 }}\n", texto)
        self.assertNotIn("event_name", texto)

    def test_sdd_pasa_las_reviews_a_checks_py(self):
        """VIC-56: todas las páginas, en el fichero que lee checks.py para el check `aprobacion`."""
        texto = leer("sdd.yml")
        self.assertIn('gh api --paginate "repos/$REPO/pulls/$PR_NUMBER/reviews?per_page=100" > '
                      '"$RUNNER_TEMP/sdd/reviews.json"', texto)
        self.assertIn("PR_REVIEWS: ${{ runner.temp }}/sdd/reviews.json", texto)

    def test_relanzar_solo_con_una_review(self):
        """VIC-56: aprobar, pedir cambios o retirar una aprobación relanza `checks-sdd` desde un workflow aparte,
        cuyo job no es un check requerido, sin checkout ni acciones, y sin expresiones dentro del script."""
        texto = leer("sdd-relanzar.yml")
        self.assertEqual(disparadores(texto), {"pull_request_review"})
        self.assertIn("  pull_request_review:\n    types: [submitted, dismissed]\n", texto)
        self.assertEqual(jobs(texto), {"relanzar-checks-sdd"})
        self.assertFalse(jobs(texto) & REQUERIDOS)
        self.assertNotIn("uses:", texto)
        self.assertNotIn("if:", texto)
        self.assertIn("concurrency:\n  group: sdd-relanzar-${{ github.event.pull_request.number }}\n"
                      "  cancel-in-progress: false\n", texto)
        script, _ = paso(texto, "Volver a lanzar checks-sdd", "main")
        self.assertNotIn("${{", script)
        self.assertIn('actions/workflows/sdd.yml/runs?event=pull_request&per_page=100', script)

    def test_la_tarea_mensual_no_se_llama_como_un_check_requerido(self):
        texto = leer("osv-mensual.yml")
        self.assertEqual(disparadores(texto), {"schedule", "workflow_dispatch"})
        self.assertFalse(jobs(texto) & REQUERIDOS)
        self.assertIn("if: github.ref == 'refs/heads/main'", texto)

    def test_osv_scanner_con_las_mismas_opciones(self):
        opciones = "scan source -r --no-ignore --allow-no-lockfiles --no-call-analysis=all --config"
        for nombre in ("seguridad.yml", "osv-mensual.yml"):
            with self.subTest(nombre=nombre):
                self.assertIn(opciones, " ".join(leer(nombre).replace("\\\n", " ").split()))

    def test_sumas_versiones_y_digest_del_registro(self):
        for nombre in ("seguridad.yml", "osv-mensual.yml"):
            texto = leer(nombre)
            sumas = re.findall(r'echo "([0-9a-f]{64})  ', texto)
            versiones = re.findall(r"/releases/download/(v[\d.]+)/", texto)
            digest = re.findall(r"@(sha256:[0-9a-f]{64})", texto)
            self.assertTrue(sumas and versiones)
            for valor in sumas + versiones + digest:
                with self.subTest(nombre=nombre, valor=valor):
                    self.assertIn(valor, REGISTRO)

    def test_semgrep_sin_la_lista_por_defecto(self):
        """Sin .semgrepignore, Semgrep excluiría tests/, vendor/… y los ficheros de más de 1 MB."""
        texto = leer("seguridad.yml")
        self.assertIn("else : > .semgrepignore; fi", texto)
        self.assertIn("\\( -name .semgrepignore -o -name .gitignore \\) ! -type d -exec rm -f {} +", texto)
        self.assertIn("semgrep scan --config p/default --metrics=off --error --disable-nosem --max-target-bytes=0", texto)

    def test_semgrep_confia_solo_en_el_workspace(self):
        """En el contenedor, Git rechazaba el checkout por ser de otro usuario (calculadora-discos#40)."""
        texto = leer("seguridad.yml")
        self.assertIn('git config --global --add safe.directory "$GITHUB_WORKSPACE"\n', texto)
        self.assertNotIn("safe.directory '*'", texto)
        self.assertNotIn('safe.directory "*"', texto)
        self.assertNotIn("safe.directory *", texto)

    def test_acciones_fijadas_por_sha(self):
        for fichero in WORKFLOWS.glob("*.yml"):
            for uso in re.findall(r"uses: (\S+)", fichero.read_text(encoding="utf-8")):
                with self.subTest(fichero=fichero.name, uso=uso):
                    self.assertRegex(uso, r"@[0-9a-f]{40}$")

    def test_sin_credenciales_ni_mas_permisos(self):
        # sdd.yml lee además los comentarios del PR: las respuestas de los revisores de G4 (VIC-38).
        # sdd-relanzar.yml solo vuelve a lanzar ejecuciones y lee la cabeza del PR: ni siquiera lee el código (VIC-56).
        permisos_de = {"sdd.yml": ["contents: read", "pull-requests: read"], "sdd-relanzar.yml": ["actions: write", "pull-requests: read"]}
        for fichero in WORKFLOWS.glob("*.yml"):
            texto = fichero.read_text(encoding="utf-8")
            with self.subTest(fichero=fichero.name):
                bloque = re.search(r"^permissions:\n((?:  .*\n)+)", texto, re.M).group(1)
                permisos = [l.strip() for l in bloque.splitlines() if not l.strip().startswith("#")]
                self.assertEqual(permisos, permisos_de.get(fichero.name, ["contents: read"]))
                self.assertEqual(texto.count("permissions:"), 1)
                self.assertEqual(texto.count("persist-credentials: false"), texto.count("actions/checkout@"))


def paso(texto, nombre, base_ref):
    """El script del paso con ese nombre y su entorno (el `env:` del workflow y el del paso), con
    `${{ github.base_ref }}` y `${{ github.event.pull_request.base.ref }}` sustituidos por base_ref. El resto
    de expresiones `${{ }}` se quedan fuera."""
    bloque = re.search(rf"\n      - name: {re.escape(nombre)}\n((?:        .*\n|\n)*)", texto).group(1)
    varios = re.search(r"^        run: \|\n((?:          .*\n|\n)+)", bloque, re.M)
    script = textwrap.dedent(varios.group(1)) if varios else re.search(r"^        run: (.+)$", bloque, re.M).group(1)
    lineas = ""
    for patron, origen in ((r"^env:\n((?:  .*\n)+)", texto), (r"^        env:\n((?:          .*\n)+)", bloque)):
        m = re.search(patron, origen, re.M)
        lineas += m.group(1) if m else ""
    entorno = {}
    for clave, valor in re.findall(r"^ +([A-Z_]+): (.+)$", lineas, re.M):
        for base in ("${{ github.base_ref }}", "${{ github.event.pull_request.base.ref }}"):
            valor = valor.replace(base, base_ref)
        valor = valor.strip('"')
        if "${{" not in valor:
            entorno[clave] = valor
    return script, entorno


CONFIGURACION = [".gitleaks.toml", ".gitleaksignore", "osv-scanner.toml", ".semgrepignore", ".github/sdd/checks.py"]


class BaseConEtiqueta(unittest.TestCase):
    """VIC-26 (G4 del PR #41, ronda 1): con `origin/main`, Git resuelve antes una etiqueta llamada así,
    que la rama puede empujar, y la configuración de main saldría de donde ella eligiera. Aquí la
    rama remota tiene la configuración "main" y la etiqueta `origin/main`, en la cabeza de la rama,
    la configuración "etiqueta"."""

    def setUp(self):
        self.temporal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temporal)
        self.repo = self.temporal / "repo"
        self.repo.mkdir()
        self.global_ = self.temporal / "gitconfig"
        self.global_.write_text("")
        self.entorno = dict(os.environ, GIT_CONFIG_GLOBAL=str(self.global_), GIT_CONFIG_NOSYSTEM="1",
                            RUNNER_TEMP=str(self.temporal), GITHUB_WORKSPACE=str(self.repo))
        self.entorno.pop("GIT_NO_REPLACE_OBJECTS", None)  # lo pone el workflow
        self.git("init", "-q", "-b", "main")
        for contenido in ("main", "etiqueta"):
            for nombre in CONFIGURACION:
                (self.repo / nombre).parent.mkdir(parents=True, exist_ok=True)
                (self.repo / nombre).write_text(f"# {contenido}\n")
            self.git("add", "-A")
            self.git("commit", "-q", "-m", contenido)
            if contenido == "main":
                self.git("update-ref", "refs/remotes/origin/main", "HEAD")
                self.main = self.git("rev-parse", "HEAD")
        self.git("tag", "origin/main")

    def git(self, *args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                               "-c", "tag.gpgsign=false", *args], cwd=self.repo, env=self.entorno,
                              check=True, capture_output=True, text=True).stdout.strip()

    def ejecutar(self, workflow, nombre, base_ref="main"):
        script, entorno = paso(leer(workflow), nombre, base_ref)
        r = subprocess.run(["bash", "-e", "-c", script], cwd=self.repo, env={**self.entorno, **entorno},
                           capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout + r.stderr

    def resuelve_a_main(self, ref):
        self.assertEqual(self.git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"), self.main, ref)

    def test_la_etiqueta_existe_y_gana_a_la_rama_remota(self):
        """El repo de prueba reproduce el problema: sin esto, los demás tests no probarían nada."""
        self.assertNotEqual(self.git("rev-parse", "origin/main^{commit}"), self.main)

    def test_seguridad_toma_la_configuracion_de_la_rama_remota(self):
        for nombre, copias in (("Configuración de gitleaks de main", [self.repo / ".gitleaks.toml",
                                                                        self.repo / ".gitleaksignore"]),
                               ("Configuración de osv-scanner de main", [self.temporal / "osv-scanner.toml"]),
                               ("Configuración de Semgrep de main", [self.repo / ".semgrepignore"])):
            with self.subTest(paso=nombre):
                codigo, salida = self.ejecutar("seguridad.yml", nombre)
                self.assertEqual(codigo, 0, salida)
                for copia in copias:
                    self.assertEqual(copia.read_text(), "# main\n", copia.name)

    def test_sdd_toma_checks_py_de_la_rama_remota(self):
        codigo, salida = self.ejecutar("sdd.yml", "Tomar los checks de la rama base")
        self.assertEqual(codigo, 0, salida)
        self.assertEqual((self.temporal / "sdd" / "checks.py").read_text(), "# main\n")

    def test_sdd_falla_si_la_base_no_es_main(self):
        """VIC-56, G4-1-B-01: un PR contra otra rama no puede dejar un `checks-sdd` en verde con el checks.py
        de esa rama. `branches: [main]` ya lo evita; esta es la segunda barrera."""
        self.git("branch", "tmp")
        self.git("update-ref", "refs/remotes/origin/tmp", "tmp")
        codigo, salida = self.ejecutar("sdd.yml", "Tomar los checks de la rama base", base_ref="tmp")
        self.assertNotEqual(codigo, 0, salida)
        self.assertIn("::error::La base del PR es tmp, no main", salida)
        self.assertFalse((self.temporal / "sdd" / "checks.py").exists())

    def test_sdd_pasa_a_checks_py_la_rama_remota(self):
        """En lugar de checks.py, uno que escribe sus argumentos: así se ve qué base le llega."""
        (self.temporal / "sdd").mkdir()
        (self.temporal / "sdd" / "checks.py").write_text("import sys\nprint(sys.argv[sys.argv.index('--base') + 1])\n")
        codigo, salida = self.ejecutar("sdd.yml", "Specs, mezcla, trazabilidad (G3), riesgo, convenciones y commits")
        self.assertEqual(codigo, 0, salida)
        self.assertEqual(salida.strip(), "refs/remotes/origin/main")
        self.resuelve_a_main(salida.strip())

    def test_checks_py_por_defecto_lee_la_rama_remota(self):
        texto = (PLANTILLA / "sdd" / "checks.py").read_text(encoding="utf-8")
        self.resuelve_a_main(re.search(r'add_argument\("--base", default="([^"]+)"', texto).group(1))

    def test_sdd_sin_rama_base_falla_con_un_error_claro(self):
        """Fuera de un PR no hay base: nunca se toma checks.py de otro sitio."""
        codigo, salida = self.ejecutar("sdd.yml", "Tomar los checks de la rama base", base_ref="")
        self.assertNotEqual(codigo, 0, salida)
        self.assertIn("::error::Sin rama base: sdd.yml solo corre en pull_request", salida)
        self.assertFalse((self.temporal / "sdd" / "checks.py").exists())

    def test_sdd_sin_la_rama_remota_falla_con_un_error_claro(self):
        self.git("update-ref", "-d", "refs/remotes/origin/main")
        codigo, salida = self.ejecutar("sdd.yml", "Tomar los checks de la rama base")
        self.assertNotEqual(codigo, 0, salida)
        self.assertIn("::error::Git no encuentra refs/remotes/origin/main", salida)

    def test_los_objetos_de_refs_replace_no_cuentan(self):
        """Un `git replace` del commit de main por el de la etiqueta no cambia lo que se lee."""
        self.git("replace", self.main, "refs/tags/origin/main")
        for workflow, nombre, copia in (("sdd.yml", "Tomar los checks de la rama base", self.temporal / "sdd" / "checks.py"),
                                        ("seguridad.yml", "Configuración de gitleaks de main", self.repo / ".gitleaks.toml"),
                                        ("seguridad.yml", "Configuración de osv-scanner de main", self.temporal / "osv-scanner.toml"),
                                        ("seguridad.yml", "Configuración de Semgrep de main", self.repo / ".semgrepignore")):
            with self.subTest(paso=nombre):
                codigo, salida = self.ejecutar(workflow, nombre)
                self.assertEqual(codigo, 0, salida)
                self.assertEqual(copia.read_text(), "# main\n")


class SinOrigenAbreviado(unittest.TestCase):
    def test_ningun_workflow_ni_script_usa_origin_sin_la_ref_completa(self):
        """Los comentarios pueden nombrarlo; el código, no."""
        for fichero in [*WORKFLOWS.glob("*.yml"), *(PLANTILLA / "sdd").glob("*.py")]:
            for numero, linea in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
                if not linea.lstrip().startswith("#"):
                    with self.subTest(fichero=fichero.name, linea=numero):
                        self.assertNotRegex(linea, r"(?<!refs/remotes/)origin/")




GH_FALSO = """#!/bin/bash
# `gh api URL` devuelve la siguiente respuesta de $RESPUESTAS (la última se repite); `gh run rerun` se anota.
# `gh api .../pulls/N --jq .head.sha` devuelve la siguiente cabeza de $CABEZAS_PR (la última se repite).
echo "$*" >> "$LLAMADAS"
if [ "$1" = api ] && [[ "$2" == */pulls/* ]]; then
  read -ra cabezas <<< "$CABEZAS_PR"
  k=$(cat "$RESPUESTAS/k" 2>/dev/null || echo 0); echo $((k + 1)) > "$RESPUESTAS/k"
  [ "$k" -lt "${#cabezas[@]}" ] || k=$((${#cabezas[@]} - 1))
  echo "${cabezas[$k]}"
elif [ "$1" = api ]; then
  n=$(cat "$RESPUESTAS/n" 2>/dev/null || echo 0)
  if [ -e "$RESPUESTAS/$((n + 1))" ]; then n=$((n + 1)); echo $n > "$RESPUESTAS/n"; fi
  cat "$RESPUESTAS/$n"
elif [ "$1 $2" = "run rerun" ]; then
  # Falla las primeras $RERUN_FALLA veces.
  f=$(cat "$RESPUESTAS/fallos" 2>/dev/null || echo 0); echo $((f + 1)) > "$RESPUESTAS/fallos"
  [ "$f" -ge "${RERUN_FALLA:-0}" ]
fi
"""

# `sleep` no espera: anota cuánto habría esperado, en el mismo registro que `gh`.
SLEEP_FALSO = """#!/bin/bash
echo "sleep $*" >> "$LLAMADAS"
"""

CABEZA = "a" * 40


def run(id_, estado="completed", cabeza=CABEZA, pr=7, evento="pull_request"):
    return {"id": id_, "status": estado, "head_sha": cabeza, "event": evento,
            "pull_requests": [{"number": pr}] if pr else []}


class Relanzar(unittest.TestCase):
    """VIC-56: el script de sdd-relanzar.yml con un `gh` falso. Que GitHub tome el intento relanzado como la
    última ejecución de `pull_request` se comprueba en la calculadora, no aquí."""

    def setUp(self):
        self.temporal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temporal)
        (self.temporal / "bin").mkdir()
        for nombre, contenido in (("gh", GH_FALSO), ("sleep", SLEEP_FALSO)):
            (self.temporal / "bin" / nombre).write_text(contenido)
            (self.temporal / "bin" / nombre).chmod(0o755)
        self.respuestas = self.temporal / "respuestas"
        self.respuestas.mkdir()
        self.llamadas = self.temporal / "llamadas"
        self.llamadas.write_text("")

    def ejecutar(self, *respuestas, **entorno):
        for i, runs in enumerate(respuestas, 1):
            (self.respuestas / str(i)).write_text(json.dumps({"workflow_runs": runs}))
        script, base = paso(leer("sdd-relanzar.yml"), "Volver a lanzar checks-sdd", "main")
        env = {**os.environ, **base, "PATH": f"{self.temporal / 'bin'}:{os.environ['PATH']}",
               "RESPUESTAS": str(self.respuestas), "LLAMADAS": str(self.llamadas), "CABEZAS_PR": CABEZA,
               "REPO": "victor-lg/proyecto", "PR_NUMBER": "7", "PR_HEAD_SHA": CABEZA,
               "PR_HEAD_REPO": "victor-lg/proyecto", "PR_BASE": "main", **entorno}
        r = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout + r.stderr, self.llamadas.read_text().splitlines()

    def relanzadas(self, llamadas):
        return [l for l in llamadas if l.startswith("run rerun")]

    def listados(self, llamadas):
        return [l for l in llamadas if l.startswith("api ") and "/actions/" in l]

    def test_relanza_la_ultima_del_pr(self):
        """Ni la de otro PR ni la de otro evento, aunque sean más nuevas."""
        codigo, salida, llamadas = self.ejecutar([run(10), run(12), run(20, pr=8), run(22, evento="pull_request_review"),
                                                  run(21, pr=None), run(11)])
        self.assertEqual(codigo, 0, salida)
        self.assertEqual(self.relanzadas(llamadas), ["run rerun 12 --repo victor-lg/proyecto"])
        self.assertEqual(llamadas[:3], ["sleep 20", "api repos/victor-lg/proyecto/pulls/7 --jq .head.sha",
                                        "api repos/victor-lg/proyecto/actions/workflows/sdd.yml/runs"
                                        "?event=pull_request&per_page=100"])

    def test_antes_de_listar_espera_a_que_la_lista_se_ponga_al_dia(self):
        """Calculadora-discos#87, caso 7: la ejecución de un evento recién llegado tarda unos 7 s en salir en la
        lista. AL_DIA, del workflow (20 s), antes de la primera consulta; ESPERA (10 s) entre vueltas."""
        _, base = paso(leer("sdd-relanzar.yml"), "Volver a lanzar checks-sdd", "main")
        self.assertEqual((base["AL_DIA"], base["ESPERA"], base["LIMITE"]), ("20", "10", "600"))
        codigo, salida, llamadas = self.ejecutar([run(12, "in_progress")], [run(12)])
        self.assertEqual(codigo, 0, salida)
        self.assertEqual(llamadas[0], "sleep 20")
        self.assertEqual([l for l in llamadas if l.startswith("sleep")], ["sleep 20", "sleep 10"])

    def test_si_la_cabeza_del_pr_es_otra_no_relanza(self):
        """G4-4-B-02 y calculadora-discos#87, caso 10: hubo un push tras la review, y su ejecución ya lee las
        reviews. Lo dice la cabeza actual del PR, no la lista de ejecuciones: la del push puede no salir aún
        en la lista. También si el push llega mientras espera."""
        nueva = "b" * 40
        for respuestas, cabezas in (([[run(12)]], nueva), ([[run(12, "in_progress")]], f"{CABEZA} {nueva}")):
            with self.subTest(cabezas=cabezas):
                for f in ("n", "k"):
                    (self.respuestas / f).unlink(missing_ok=True)
                self.llamadas.write_text("")
                codigo, salida, llamadas = self.ejecutar(*respuestas, CABEZAS_PR=cabezas)
                self.assertEqual(codigo, 0, salida)
                self.assertIn(f"La cabeza del PR es ahora {nueva[:12]}", salida)
                self.assertIn("hubo un push después de esta review", salida)
                self.assertEqual(self.relanzadas(llamadas), [])

    def test_si_la_lista_no_tiene_la_cabeza_del_pr_espera(self):
        """Un push justo antes de la review: la cabeza del PR ya es la de la review, pero la lista solo muestra la
        ejecución de la anterior. Espera a que salga la nueva y relanza esa, no la vieja."""
        codigo, salida, llamadas = self.ejecutar([run(12, cabeza="b" * 40)], [run(12, cabeza="b" * 40), run(13)])
        self.assertEqual(codigo, 0, salida)
        self.assertIn("la lista aún no se ha puesto al día", salida)
        self.assertEqual(self.relanzadas(llamadas), ["run rerun 13 --repo victor-lg/proyecto"])

    def test_si_la_lista_nunca_tiene_la_cabeza_del_pr_falla_sin_relanzar(self):
        codigo, salida, llamadas = self.ejecutar([run(12, cabeza="b" * 40)], LIMITE="0")
        self.assertEqual(codigo, 1, salida)
        self.assertIn("::error::Tras 0 s no aparece ninguna ejecución de checks-sdd (pull_request)", salida)
        self.assertIn("Relánzala a mano", salida)
        self.assertEqual(self.relanzadas(llamadas), [])

    def test_si_no_puede_leer_la_cabeza_del_pr_falla(self):
        for cabeza in ("''", "null", "$(id)"):
            with self.subTest(cabeza=cabeza):
                (self.respuestas / "k").unlink(missing_ok=True)
                codigo, salida, llamadas = self.ejecutar([run(12)], CABEZAS_PR=cabeza)
                self.assertEqual(codigo, 1, salida)
                self.assertIn("::error::No pude leer la cabeza actual del PR", salida)
                self.assertEqual(self.relanzadas(llamadas), [])

    def test_espera_a_que_termine_la_que_sigue_en_curso(self):
        """Podría haber leído las reviews antes de esta: se relanza al terminar, no antes."""
        codigo, salida, llamadas = self.ejecutar([run(12, "queued")], [run(12, "in_progress")], [run(12)])
        self.assertEqual(codigo, 0, salida)
        self.assertEqual(len(self.listados(llamadas)), 3)
        self.assertEqual(self.relanzadas(llamadas), ["run rerun 12 --repo victor-lg/proyecto"])

    def test_si_mientras_espera_llega_otra_relanza_la_nueva(self):
        codigo, salida, llamadas = self.ejecutar([run(12, "in_progress")], [run(12, "completed"), run(13, "in_progress")],
                                                 [run(12), run(13)])
        self.assertEqual(codigo, 0, salida)
        self.assertEqual(self.relanzadas(llamadas), ["run rerun 13 --repo victor-lg/proyecto"])

    def test_sin_ejecucion_todavia_espera(self):
        codigo, salida, llamadas = self.ejecutar([], [run(12)])
        self.assertEqual(codigo, 0, salida)
        self.assertEqual(self.relanzadas(llamadas), ["run rerun 12 --repo victor-lg/proyecto"])

    def test_si_no_termina_falla_sin_relanzar(self):
        codigo, salida, llamadas = self.ejecutar([run(12, "in_progress")], LIMITE="0")
        self.assertEqual(codigo, 1, salida)
        self.assertIn("sigue en «in_progress» tras 0 s: no la relanzo", salida)
        self.assertEqual(self.relanzadas(llamadas), [])

    def test_en_un_fork_falla_y_pide_relanzar_a_mano(self):
        codigo, salida, llamadas = self.ejecutar([run(12)], PR_HEAD_REPO="otro/proyecto")
        self.assertEqual(codigo, 1, salida)
        self.assertIn("::error::El PR viene de un fork", salida)
        self.assertIn("Relánzala a mano", salida)
        self.assertIn("checks-sdd conserva el resultado de antes de esta review", salida)
        self.assertEqual(llamadas, [])

    def test_si_github_no_deja_relanzar_pide_hacerlo_a_mano(self):
        """Tras tres rechazos; y avisa de que mientras tanto vale el resultado anterior (G4-4-B-01)."""
        codigo, salida, llamadas = self.ejecutar([run(12)], RERUN_FALLA="3")
        self.assertEqual(codigo, 1, salida)
        self.assertEqual(len(self.relanzadas(llamadas)), 3)
        self.assertIn("::error::GitHub no me deja relanzar la ejecución 12 de checks-sdd. Relánzala a mano", salida)
        self.assertIn("checks-sdd conserva el resultado de antes de esta review", salida)

    def test_un_rechazo_se_reintenta(self):
        """Otro relanzamiento recién pedido que la API aún no muestra en curso: se vuelve a buscar y se espera."""
        codigo, salida, llamadas = self.ejecutar([run(12)], [run(12, "in_progress")], [run(12)], RERUN_FALLA="1")
        self.assertEqual(codigo, 0, salida)
        self.assertEqual(self.relanzadas(llamadas), ["run rerun 12 --repo victor-lg/proyecto"] * 2)

    def test_con_otra_base_no_hace_nada(self):
        codigo, salida, llamadas = self.ejecutar([run(12)], PR_BASE="desarrollo")
        self.assertEqual(codigo, 0, salida)
        self.assertEqual(llamadas, [])

    def test_datos_del_evento_con_otro_formato_fallan(self):
        for clave, valor in (("PR_HEAD_SHA", "a" * 39 + ";"), ("PR_HEAD_SHA", "$(id)"), ("PR_NUMBER", "7 x")):
            with self.subTest(clave=clave, valor=valor):
                codigo, salida, llamadas = self.ejecutar([run(12)], **{clave: valor})
                self.assertEqual(codigo, 1, salida)
                self.assertIn("no tienen el formato esperado", salida)
                self.assertEqual(llamadas, [])


if __name__ == "__main__":
    unittest.main()

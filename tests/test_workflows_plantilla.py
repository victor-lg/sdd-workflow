"""Los workflows de la plantilla (VIC-18, PR 3) no corren en este repo: estos tests comprueban
su texto. Que seguridad.yml solo se lance en un PR (con `workflow_dispatch`, el agente podría
dejar sus checks en verde desde su rama; G4 del PR 3, ronda 2), que los jobs se llamen como los
checks requeridos y que versiones, sumas y digest sean los de docs/herramientas.md."""
import pathlib
import re
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
WORKFLOWS = RAIZ / "plantilla-proyecto" / ".github" / "workflows"
REGISTRO = (RAIZ / "docs" / "herramientas.md").read_text(encoding="utf-8")
REQUERIDOS = {"checks-sdd", "gitleaks", "osv-scanner", "semgrep"}


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

    def test_acciones_fijadas_por_sha(self):
        for fichero in WORKFLOWS.glob("*.yml"):
            for uso in re.findall(r"uses: (\S+)", fichero.read_text(encoding="utf-8")):
                with self.subTest(fichero=fichero.name, uso=uso):
                    self.assertRegex(uso, r"@[0-9a-f]{40}$")

    def test_sin_credenciales_ni_mas_permisos(self):
        for fichero in WORKFLOWS.glob("*.yml"):
            texto = fichero.read_text(encoding="utf-8")
            with self.subTest(fichero=fichero.name):
                self.assertIn("permissions:\n  contents: read\n", texto)
                self.assertEqual(texto.count("persist-credentials: false"), texto.count("actions/checkout@"))


if __name__ == "__main__":
    unittest.main()

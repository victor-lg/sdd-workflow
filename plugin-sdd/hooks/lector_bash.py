"""Lector de órdenes de bash compartido por las guardas del plugin (VIC-17).

Lee el texto de la orden: bash -c, eval, variables, alias o scripts lo esquivan.
Las guardas que lo usan son una segunda capa contra errores del agente, no un
control de seguridad.
"""
import os
import posixpath
import re

ASIGNACION = re.compile(r"[A-Za-z_]\w*\+?=")
RESERVADAS = {"if", "then", "elif", "else", "while", "until", "do", "!", "{"}
# Envolturas: opciones que llevan valor aparte y argumentos antes de la orden real.
ENVOLTURAS = {
    "env": ({"-u", "--unset", "-C", "--chdir"}, 0),
    "command": (set(), 0),
    "time": (set(), 0),
    "builtin": (set(), 0),
    "exec": ({"-a"}, 0),
    "nohup": (set(), 0),
    "nice": ({"-n", "--adjustment"}, 0),
    "timeout": ({"-s", "--signal", "-k", "--kill-after"}, 1),
    "sudo": ({"-u", "--user", "-g", "--group", "-h", "--host", "-p", "--prompt", "-C", "-D", "-R", "-T", "-U"}, 0),
}


class NoAnalizable(Exception):
    """La orden tiene comillas, sustituciones o similares sin cerrar."""


class Analisis:
    """Lo que sale de leer una orden. ordenes: las órdenes simples, como listas de
    palabras. redirecciones: (índice de la orden, operador, destino) de las que leen
    o escriben un fichero; el operador escribe si lleva ">". heredocs_expandidos: cuántos heredocs sin comillas hay.
    cadenas: cuántas here-strings (<<<) hay."""

    def __init__(self):
        self.ordenes, self.redirecciones, self.heredocs_expandidos, self.cadenas = [], [], 0, 0


class _Lector:
    """Divide un texto de bash en órdenes simples. Las palabras salen sin comillas;
    lo que hay dentro de $(...) y de las comillas invertidas se lee como orden, salvo
    si va dentro de ${...} o de $((...)). El cuerpo de los heredocs y los comentarios
    no cuentan."""

    def __init__(self, texto, analisis=None):
        self.t, self.i = texto, 0
        self.a = Analisis() if analisis is None else analisis
        self.ordenes = self.a.ordenes

    def leer(self, anidado=False):
        palabras, heredocs, profundidad = [], [], 0

        def cerrar():
            if palabras:
                self.ordenes.append(palabras.copy())
                palabras.clear()

        while self.i < len(self.t):
            c = self.t[self.i]
            if c == "\n":
                self.i += 1
                cerrar()
                self._cuerpos(heredocs)
                heredocs.clear()
            elif c in " \t":
                self.i += 1
            elif c == "\\" and self.t[self.i + 1:self.i + 2] == "\n":
                self.i += 2
            elif c == "#":
                fin = self.t.find("\n", self.i)
                self.i = len(self.t) if fin < 0 else fin
            elif self.t.startswith("&>", self.i):
                self._redireccion(palabras, heredocs)
            elif c in ";&|":
                self.i += 1
                cerrar()
            elif c == "(":
                self.i += 1
                profundidad += 1
                cerrar()
            elif c == ")":
                self.i += 1
                cerrar()
                if anidado and profundidad == 0:
                    return
                profundidad = max(0, profundidad - 1)
            elif c in "<>":
                self._redireccion(palabras, heredocs)
            else:
                palabras.append(self._palabra())
        cerrar()
        self._cuerpos(heredocs)
        if anidado:
            raise NoAnalizable

    def _espacios(self):
        while self.t[self.i:self.i + 1] in (" ", "\t"):
            self.i += 1

    def _redireccion(self, palabras, heredocs):
        t, i = self.t, self.i
        if i > 0 and t[i - 1].isdigit() and palabras and palabras[-1].isdigit():
            palabras.pop()
        if t[i + 1:i + 2] == "(":  # <(orden) o >(orden): el paréntesis se lee como subshell.
            self.i += 1
        elif t.startswith("<<<", i):
            self.a.cadenas += 1
            self.i += 3
            self._espacios()
            self._palabra()
        elif t.startswith("<<", i):
            self.i += 2
            quitar_tabs = t[self.i:self.i + 1] == "-"
            self.i += quitar_tabs
            self._espacios()
            desde = self.i
            delimitador = self._palabra()
            literal = any(q in t[desde:self.i] for q in "'\"\\")
            if not delimitador.isdigit():  # (( x << 2 )): un desplazamiento, no un heredoc.
                heredocs.append((delimitador, quitar_tabs, literal))
        else:
            self.i += 1
            while t[self.i:self.i + 1] in (">", "<", "&", "|"):
                self.i += 1
            operador = t[i:self.i]
            duplica = operador.endswith("&") and operador != "&"  # 2>&1, <&0: no es un fichero.
            self._espacios()
            destino = self._palabra()
            if destino and not (duplica and (destino.isdigit() or destino == "-")):
                self.a.redirecciones.append((len(self.ordenes), operador, destino))

    def _cuerpos(self, heredocs):
        for delimitador, quitar_tabs, literal in heredocs:
            lineas = []
            while self.i < len(self.t):
                fin = self.t.find("\n", self.i)
                fin = len(self.t) if fin < 0 else fin
                linea = self.t[self.i:fin]
                self.i = min(fin + 1, len(self.t))
                if (linea.lstrip("\t") if quitar_tabs else linea) == delimitador:
                    break
                lineas.append(linea)
            if not literal:
                self.a.heredocs_expandidos += 1
                _Lector("\n".join(lineas), self.a)._dobles(cierre=None)

    def _palabra(self):
        t, salida = self.t, []
        while self.i < len(t):
            c = t[self.i]
            if c in " \t\n;&|()<>":
                break
            if c == "\\":
                if t[self.i + 1:self.i + 2] != "\n":
                    salida.append(t[self.i + 1:self.i + 2])
                self.i += 2
            elif c == "'":
                fin = t.find("'", self.i + 1)
                if fin < 0:
                    raise NoAnalizable
                salida.append(t[self.i + 1:fin])
                self.i = fin + 1
            elif c == '"':
                self.i += 1
                salida.append(self._dobles())
            elif c == "`":
                salida.append(self._invertidas())
            elif c == "$":
                salida.append(self._dolar())
            else:
                salida.append(c)
                self.i += 1
        return "".join(salida)

    def _dobles(self, cierre='"'):
        t, salida = self.t, []
        while self.i < len(t):
            c = t[self.i]
            if c == cierre:
                self.i += 1
                return "".join(salida)
            if c == "\\":
                siguiente = t[self.i + 1:self.i + 2]
                if siguiente != "\n":
                    salida.append(siguiente if siguiente in ('$', '`', '"', "\\") else c + siguiente)
                self.i += 2
            elif c == "`":
                salida.append(self._invertidas())
            elif c == "$":
                salida.append(self._dolar(en_dobles=True))
            else:
                salida.append(c)
                self.i += 1
        if cierre is not None:
            raise NoAnalizable
        return "".join(salida)

    def _dolar(self, en_dobles=False):
        t, i = self.t, self.i
        if t.startswith("$((", i):
            return self._equilibrado("(", ")", i + 1)
        if t.startswith("$(", i):
            self.i += 2
            self.leer(anidado=True)
            return "$()"
        if t.startswith("${", i):
            return self._equilibrado("{", "}", i + 1)
        if t.startswith("$'", i) and not en_dobles:
            j = i + 2
            while j < len(t) and t[j] != "'":
                j += 2 if t[j] == "\\" else 1
            if j >= len(t):
                raise NoAnalizable
            self.i = j + 1
            return t[i + 2:j]
        if t.startswith('$"', i) and not en_dobles:
            self.i += 2
            return self._dobles()
        self.i += 1
        return "$"

    def _equilibrado(self, abre, cierra, desde):
        t, j, nivel = self.t, desde, 0
        while j < len(t):
            if t[j] == "\\":
                j += 2
                continue
            nivel += (t[j] == abre) - (t[j] == cierra)
            j += 1
            if nivel == 0:
                texto = t[self.i:j]
                self.i = j
                return texto
        raise NoAnalizable

    def _invertidas(self):
        t, j = self.t, self.i + 1
        interior = []
        while j < len(t) and t[j] != "`":
            if t[j] == "\\" and t[j + 1:j + 2] in ("`", "\\", "$"):
                j += 1
            interior.append(t[j:j + 1])
            j += 1
        if j >= len(t):
            raise NoAnalizable
        self.i = j + 1
        _Lector("".join(interior), self.a).leer()
        return "$()"


def analizar_todo(texto):
    lector = _Lector(texto)
    lector.leer()
    return lector.a


def analizar(texto):
    return analizar_todo(texto).ordenes


def orden_efectiva(palabras):
    """Quita asignaciones, palabras reservadas y envolturas como env o timeout."""
    i = 0
    while i < len(palabras):
        palabra = palabras[i]
        if palabra in RESERVADAS or ASIGNACION.match(palabra):
            i += 1
        elif posixpath.basename(palabra) in ENVOLTURAS:
            con_valor, posicionales = ENVOLTURAS[posixpath.basename(palabra)]
            i += 1
            while i < len(palabras) and palabras[i].startswith("-") and palabras[i] != "-":
                i += 2 if palabras[i] in con_valor else 1
            i += posicionales
        else:
            break
    return palabras[i:]


def _resolver(nombre, largas):
    if nombre in largas:
        return nombre
    candidatas = [l for l in largas if l.startswith(nombre)]
    return candidatas[0] if len(candidatas) == 1 else nombre


def opciones(args, cortas_con_valor="", largas=None, abreviadas=True):
    """Separa opciones y posicionales como parse-options de Git: cortas juntas
    (-fu), largas abreviadas (--set-up) y valores con = o en la palabra siguiente.
    Con abreviadas=False, como pflag (gh): las largas se escriben enteras."""
    largas = largas or {}
    encontradas, posicionales, i = [], [], 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            posicionales.extend(args[i:])
            break
        if a.startswith("--"):
            nombre, igual, valor = a[2:].partition("=")
            if abreviadas:
                nombre = _resolver(nombre, largas)
            if not igual and largas.get(nombre) and i < len(args):
                valor = args[i]
                i += 1
            encontradas.append((nombre, valor))
        elif a.startswith("-") and len(a) > 1:
            j = 1
            while j < len(a):
                corta = a[j]
                j += 1
                if corta in cortas_con_valor:
                    valor = a[j:]
                    if not valor and i < len(args):
                        valor = args[i]
                        i += 1
                    encontradas.append((corta, valor))
                    break
                encontradas.append((corta, ""))
        else:
            posicionales.append(a)
    return encontradas, posicionales


def nombres(encontradas):
    return {nombre for nombre, _ in encontradas}


def juntar(cwd, ruta):
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(ruta)))


def respuesta(decision, motivo):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": motivo}}

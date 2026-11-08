#!/usr/bin/env python3
"""Marca por copia del repo para SessionStart (REG-49; VIC-17).

Cada sesión deja una marca en el directorio de Git de su copia, que es distinto en
cada worktree. Si hay otra marca de un proceso vivo, avisa y sugiere un worktree.
Solo avisa: SessionStart no puede impedir que la sesión siga.
"""
import json
import os
import subprocess
import sys
import tempfile
import time

RUTA_REGLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reglas-git.json")
INTERMEDIOS = {"sh", "bash", "dash", "zsh", "fish", "env", "python", "python3"}


def _ps(pid, *columnas):
    orden = ["ps", "-p", str(pid)] + [a for c in columnas for a in ("-o", f"{c}=")]
    try:
        r = subprocess.run(orden, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def proceso_de_sesion():
    """El proceso de Claude Code: el primer antepasado que no es un intérprete."""
    pid = os.getppid()
    for _ in range(8):
        linea = _ps(pid, "ppid", "comm")
        if linea is None:
            break
        padre, _, nombre = linea.partition(" ")
        if os.path.basename(nombre.strip()) not in INTERMEDIOS:
            return pid
        pid = int(padre)
    return os.getppid()


def directorio_de_git(cwd):
    """Directorio de Git de la copia, o None si cwd no está en un repo."""
    r = subprocess.run(["git", "-C", cwd, "rev-parse", "--absolute-git-dir"],
                       capture_output=True, text=True, timeout=5)
    return r.stdout.strip() if r.returncode == 0 else None


def otras_vivas(directorio, pid_propio):
    """Pids con marca de un proceso vivo distinto del propio. Borra las marcas muertas."""
    vivas = []
    for nombre in os.listdir(directorio):
        ruta = os.path.join(directorio, nombre)
        if nombre == f"{pid_propio}.json" or not nombre.endswith(".json"):
            continue
        try:
            with open(ruta, encoding="utf-8") as f:
                marca = json.load(f)
        except (OSError, ValueError):
            marca = {}
        if marca.get("arranque") and _ps(marca.get("pid"), "lstart") == marca["arranque"]:
            vivas.append(marca["pid"])
        else:
            try:
                os.unlink(ruta)
            except OSError:
                pass
    return vivas


def registrar(git_dir, pid, session_id):
    """Deja la marca propia y devuelve los pids de las otras sesiones vivas."""
    directorio = os.path.join(git_dir, "sdd-sesiones")
    os.makedirs(directorio, exist_ok=True)
    marca = {"pid": pid, "arranque": _ps(pid, "lstart"), "session_id": session_id, "inicio": time.time()}
    with tempfile.NamedTemporaryFile("w", dir=directorio, suffix=".tmp", delete=False, encoding="utf-8") as f:
        json.dump(marca, f)
    os.replace(f.name, os.path.join(directorio, f"{pid}.json"))
    return otras_vivas(directorio, pid)


def main():
    with open(RUTA_REGLAS, encoding="utf-8") as f:
        avisos = json.load(f)["sesion"]
    try:
        datos = json.load(sys.stdin)
        git_dir = directorio_de_git(datos.get("cwd") or os.getcwd())
        if git_dir is None:
            return
        otras = registrar(git_dir, proceso_de_sesion(), datos.get("session_id"))
        if not otras:
            return
        aviso = avisos["otra-viva"]
    except Exception:  # SessionStart no puede bloquear: fallar cerrado aquí es avisar.
        aviso = avisos["sin-mirar"]
    json.dump({"systemMessage": aviso,
               "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": aviso}},
              sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

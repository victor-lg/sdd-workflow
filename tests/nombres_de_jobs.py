"""Ayuda común a los tests de los workflows con borrador barato (VIC-33): el nombre que da GitHub a un job."""
import re


def nombre_del_job(expresion, draft):
    """El nombre que da GitHub a un job con `name: ${{ github.event.pull_request.draft && 'A' || 'B' }}`.
    Falla si la expresión depende de otra cosa que el evento: un run relanzado conserva el evento de
    cuando se lanzó, así que un run de borrador relanzado sigue llamándose A (VIC-33, G4 de #49)."""
    m = re.fullmatch(r"\$\{\{ github\.event\.pull_request\.draft && '([^']+)' \|\| '([^']+)' \}\}", expresion)
    assert m, f"el nombre no sale solo del evento: {expresion}"
    return m.group(1) if draft else m.group(2)

"""F3 · GA-FE-02-B — guard de dominios de email en semillas.

Lee las fuentes de `seeds/*.py` (mismo patrón que `test_access_administration.py`, que ya
inspecciona `baseline_seeds.py` como texto) y exige que **ninguna** semilla genere emails en
dominios reservados/special-use (`test`, `example`, `invalid`, `local`, `localhost`).

Motivo concreto: `integration_seeds.USERS_DEF` generaba `{username}@testing.local` y esos 14
usuarios devolvían 500 en `GET /users` (pydantic `EmailStr` rechaza el dominio al serializar;
`baseline_seeds` ya documentaba el invariante). `R-44`: las semillas sirven a instalaciones
nuevas — la guarda evita recrear la fixture malformada.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SEEDS_DIR = Path(__file__).resolve().parents[1] / "seeds"

#: Dominios special-use/reservados que email-validator rechaza (aunque el DNS no se consulte).
_DOMINIO_RESERVADO = re.compile(
    r"@[A-Za-z0-9.-]*(?:\.local|\.test|\.example|\.invalid|\.localhost)\b"
)


def _fuentes_de_semillas() -> list[Path]:
    return sorted(p for p in SEEDS_DIR.glob("*.py") if p.name != "__init__.py")


def test_r44_ninguna_semilla_genera_emails_en_dominios_reservados():
    fuentes = _fuentes_de_semillas()
    assert fuentes, "no se encontraron fuentes de seeds"

    ofensas: list[str] = []
    for path in fuentes:
        for numero, linea in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            # Se ignoran los comentarios: documentan el defecto, no lo cometen.
            if linea.lstrip().startswith("#"):
                continue
            if _DOMINIO_RESERVADO.search(linea):
                ofensas.append(f"{path.name}:{numero}: {linea.strip()}")

    assert not ofensas, (
        "las semillas no deben generar emails en dominios reservados (EmailStr los rechaza "
        "y el usuario queda ilegible por la API — F3/GA-FE-02-B):\n" + "\n".join(ofensas)
    )


def test_r44_las_semillas_de_usuarios_de_integracion_usan_dominio_valido():
    fuente = (SEEDS_DIR / "integration_seeds.py").read_text(encoding="utf-8")
    if "USERS_DEF" not in fuente:
        pytest.skip("integration_seeds.py sin USERS_DEF en este baseline")
    assert "@globalavicola.com" in fuente
    assert '@testing.local' not in fuente

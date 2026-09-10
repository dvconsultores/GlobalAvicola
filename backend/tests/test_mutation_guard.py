"""`GA-REM-002` enmienda E · `T-002-E4` — la precondición del driver de sensibilidad es ejecutable.

El incidente ocurrió dos veces (tranches 10 y 13): el driver instala una mutación en un archivo
productivo y restaura con `git checkout`, que toma `HEAD`. Si la implementación no está confirmada,
`HEAD` es el commit anterior y la restauración **borra la implementación** sin error visible.

Estas pruebas no ejercitan producción: construyen repositorios `git` desechables y comprueban que la
guarda **se niega** en cada modo de fallo conocido y **permite** solo cuando todo está en orden.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.mutation_guard import GuardaDeMutacion, MutacionNoPermitida

PRODUCTIVO = "backend/app/ejemplo.py"


def _git(raiz: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Repositorio desechable con un archivo productivo confirmado."""
    _git(tmp_path, "init", "--quiet", "-b", "main")
    _git(tmp_path, "config", "user.email", "prueba@globalavicola.test")
    _git(tmp_path, "config", "user.name", "Prueba")
    destino = tmp_path / PRODUCTIVO
    destino.parent.mkdir(parents=True)
    destino.write_text("IMPLEMENTACION = 'la propiedad de seguridad'\n")
    _git(tmp_path, "add", PRODUCTIVO)
    _git(tmp_path, "commit", "--quiet", "-m", "implementación")
    return tmp_path


def _guarda(repo: Path, commit: str | None = None) -> GuardaDeMutacion:
    return GuardaDeMutacion(repo, commit if commit is not None else _git(repo, "rev-parse", "HEAD"), (PRODUCTIVO,))


# ── Caso A · implementación confirmada y árbol limpio → permitido ──────────

def test_a_permite_cuando_la_implementacion_esta_confirmada(repo):
    guarda = _guarda(repo)
    assert guarda.evaluar() == []
    assert guarda.exigir() == _git(repo, "rev-parse", "HEAD")
    assert "MUTACIÓN PERMITIDA ........ SÍ" in guarda.informe()


# ── Caso B · código productivo sin confirmar → aborta ──────────────────────

def test_b_aborta_con_codigo_productivo_sin_confirmar(repo):
    """El modo de fallo histórico exacto: implementar y lanzar el driver antes de confirmar."""
    (repo / PRODUCTIVO).write_text("IMPLEMENTACION = 'la propiedad de seguridad'\nNUEVO = 'sin confirmar'\n")
    guarda = _guarda(repo)
    motivos = guarda.evaluar()
    assert any(m.startswith("4.") for m in motivos), motivos
    with pytest.raises(MutacionNoPermitida, match="sin confirmar"):
        guarda.exigir()
    assert "MUTACIÓN PERMITIDA ........ NO" in guarda.informe()


# ── Caso C · HEAD distinto del commit de implementación → aborta ───────────

def test_c_aborta_si_head_no_es_el_commit_de_implementacion(repo):
    anterior = _git(repo, "rev-parse", "HEAD")
    (repo / PRODUCTIVO).write_text("IMPLEMENTACION = 'otra cosa'\n")
    _git(repo, "add", PRODUCTIVO)
    _git(repo, "commit", "--quiet", "-m", "posterior")
    guarda = GuardaDeMutacion(repo, anterior, (PRODUCTIVO,))
    with pytest.raises(MutacionNoPermitida, match="no es el commit de implementación"):
        guarda.exigir()


# ── Caso D · objetivo de restauración ausente o no declarado → aborta ──────

def test_d_aborta_sin_objetivo_de_restauracion(repo):
    with pytest.raises(MutacionNoPermitida, match="no está declarado"):
        GuardaDeMutacion(repo, "", (PRODUCTIVO,)).exigir()
    with pytest.raises(MutacionNoPermitida, match="no existe en el repositorio"):
        GuardaDeMutacion(repo, "0" * 40, (PRODUCTIVO,)).exigir()
    guarda = GuardaDeMutacion(repo, _git(repo, "rev-parse", "HEAD"), ("backend/app/inexistente.py",))
    assert any(m.startswith("5.") for m in guarda.evaluar())


# ── Caso E · la restauración devuelve el archivo al commit de implementación ──

def test_e_la_restauracion_es_exacta_y_se_comprueba(repo):
    guarda = _guarda(repo)
    guarda.exigir()
    original = (repo / PRODUCTIVO).read_text()
    (repo / PRODUCTIVO).write_text("MUTADO = 'sin la propiedad de seguridad'\n")
    with pytest.raises(MutacionNoPermitida, match="NO volvió al commit"):
        guarda.exigir_restauracion(PRODUCTIVO)
    guarda.restaurar(PRODUCTIVO)
    guarda.exigir_restauracion(PRODUCTIVO)
    assert (repo / PRODUCTIVO).read_text() == original
    assert _git(repo, "status", "--porcelain") == "", "la restauración no deja residuo"


def test_e2_restaura_desde_el_commit_declarado_y_no_desde_head(repo):
    """La distinción que evita el incidente: `git checkout --` toma `HEAD`; la guarda toma el commit declarado."""
    implementacion = _git(repo, "rev-parse", "HEAD")
    (repo / PRODUCTIVO).write_text("IMPLEMENTACION = 'la propiedad de seguridad'\nPOSTERIOR = 1\n")
    _git(repo, "add", PRODUCTIVO)
    _git(repo, "commit", "--quiet", "-m", "posterior")
    guarda = GuardaDeMutacion(repo, implementacion, (PRODUCTIVO,))
    (repo / PRODUCTIVO).write_text("MUTADO = 1\n")
    guarda.restaurar(PRODUCTIVO)
    assert "POSTERIOR" not in (repo / PRODUCTIVO).read_text(), "restauró desde HEAD en vez del commit declarado"
    guarda.exigir_restauracion(PRODUCTIVO)

"""La guarda de longitud del script de cuentas de revisión.

Escribir el hash directamente salta la validación del producto. Es cómodo para unas cuentas
temporales y peligroso en un sentido concreto: se pueden crear cuentas con una contraseña que
el **login** rechaza, y entonces el fallo aparece lejos de su causa —en la pantalla de acceso,
pareciendo un problema de la aplicación— en vez de donde se cometió.

Pasó de verdad: las primeras cuentas se crearon con cinco caracteres y no se podía entrar.
"""
from __future__ import annotations

import pytest

from seeds.usuarios_de_revision import (
    MINIMO_DE_POLITICA, MINIMO_PARA_ENTRAR, _password,
)


def test_por_debajo_del_minimo_del_login_no_crea_nada(monkeypatch):
    """Abortar es lo correcto: una cuenta que no puede entrar no es media cuenta."""
    monkeypatch.setenv("GA_REVIEW_PASSWORD", "12345")
    with pytest.raises(SystemExit) as excinfo:
        _password()
    assert "login exige" in str(excinfo.value)


def test_el_minimo_del_login_se_acepta_avisando_de_la_politica(monkeypatch, capsys):
    """Seis entra, y se dice que está por debajo de la política de ocho.

    No se bloquea: `RR-05` gobierna la creación de un secreto por la `API`, y estas cuentas
    son temporales y explícitas. Pero callarlo dejaría al operador con una contraseña que la
    propia aplicación le impedirá conservar cuando la cambie desde la interfaz.
    """
    monkeypatch.setenv("GA_REVIEW_PASSWORD", "v12345")
    assert _password() == "v12345"
    assert "política" in capsys.readouterr().out


def test_la_politica_completa_no_avisa(monkeypatch, capsys):
    monkeypatch.setenv("GA_REVIEW_PASSWORD", "v1234567")
    assert _password() == "v1234567"
    assert "política" not in capsys.readouterr().out


def test_sin_variable_de_entorno_no_hay_contrasena_literal(monkeypatch):
    """`GA-REM-004`. Si faltara, la tentación sería un valor por defecto en el código."""
    monkeypatch.delenv("GA_REVIEW_PASSWORD", raising=False)
    with pytest.raises(SystemExit) as excinfo:
        _password()
    assert "GA_REVIEW_PASSWORD" in str(excinfo.value)


def test_los_umbrales_son_los_del_producto():
    """Si el producto mueve sus mínimos, esto rompe en vez de quedarse atrás en silencio.

    Es la diferencia entre una constante copiada y una constante **atada**: la primera
    envejece sin que nadie se entere.
    """
    from app.auth.schemas import LoginRequest, PasswordChangeRequest

    def _minimo(modelo, campo):
        return [m.min_length for m in modelo.model_fields[campo].metadata
                if hasattr(m, "min_length")][0]

    assert MINIMO_PARA_ENTRAR == _minimo(LoginRequest, "password")
    assert MINIMO_DE_POLITICA == _minimo(PasswordChangeRequest, "new_password")

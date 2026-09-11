"""F1 (`GA-FE-02-B §4.2`) — el catálogo canónico como dato determinista de despliegue.

La migración `y5z6a7b8c9d0` siembra las cuatro unidades del producto (`GA-REM-040 §2`,
`OD-16.a`) en CUALQUIER base que arranque en su revisión o posterior: el entrypoint del
backend aplica `alembic upgrade head` antes de servir (`GA-REM-024`), sin `docker exec`,
sin SQL manual y sin paso de operador.

Estos tests ejecutan la MISMA función que `upgrade()` sobre una base desechable (SQLite en
memoria) con el esquema real de `business_units` (`p6q7r8s9t0u1`): vacío → 4; parcial → se
completa sin tocar lo presente; completo → intacto; idempotencia; y cero filas en las tablas
vecinas de habilitaciones/concesiones (catálogo ≠ habilitación ≠ concesión).
"""
from __future__ import annotations

import importlib.util
import pathlib

import sqlalchemy as sa

RAIZ_BACKEND = pathlib.Path(__file__).resolve().parents[1]
PREFIJO_MIGRACION = "y5z6a7b8c9d0"

CODIGOS_CANONICOS = ["breeder", "broiler", "grandparent", "hatchery"]

# Esquema real de `business_units` (`p6q7r8s9t0u1`), replicado para la base desechable:
# `code` único (`uq_business_unit_code`), `is_active` con default de esquema.
ESQUEMA_BUSINESS_UNITS = """
CREATE TABLE business_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(30) NOT NULL UNIQUE,
    name_key VARCHAR(100) NOT NULL,
    bird_type VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""


def _cargar_migracion():
    """Carga la migración por ruta —`alembic/versions` no es importable como paquete—."""
    coincidencias = list(
        (RAIZ_BACKEND / "alembic" / "versions").glob(f"{PREFIJO_MIGRACION}*.py")
    )
    assert coincidencias, (
        f"la migración {PREFIJO_MIGRACION} no existe todavía: RED válido de F1-T1"
    )
    spec = importlib.util.spec_from_file_location("_f1_catalogo", coincidencias[0])
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _base_nueva():
    motor = sa.create_engine("sqlite+pysqlite:///:memory:")
    with motor.begin() as conexion:
        conexion.execute(sa.text(ESQUEMA_BUSINESS_UNITS))
    return motor


def _filas(motor) -> list[tuple[str, str, str | None, bool]]:
    with motor.connect() as conexion:
        return list(
            conexion.execute(
                sa.text(
                    "SELECT code, name_key, bird_type, is_active "
                    "FROM business_units ORDER BY code"
                )
            ).all()
        )


def test_catalogo_vacio_crea_exactamente_las_cuatro_canonicas():
    migracion = _cargar_migracion()
    motor = _base_nueva()
    with motor.begin() as conexion:
        creadas = migracion._sembrar_catalogo(conexion)
    assert sorted(creadas) == CODIGOS_CANONICOS
    filas = _filas(motor)
    assert [f[0] for f in filas] == CODIGOS_CANONICOS
    assert [f[1] for f in filas] == [
        "businessUnits.breeder",
        "businessUnits.broiler",
        "businessUnits.grandparent",
        "businessUnits.hatchery",
    ]
    assert all(f[3] in (True, 1) for f in filas)


def test_idempotente_la_segunda_pasada_no_crea_nada():
    migracion = _cargar_migracion()
    motor = _base_nueva()
    with motor.begin() as conexion:
        migracion._sembrar_catalogo(conexion)
    with motor.begin() as conexion:
        creadas = migracion._sembrar_catalogo(conexion)
    assert creadas == []
    assert len(_filas(motor)) == 4


def test_catalogo_parcial_se_completa_sin_tocar_las_presentes():
    migracion = _cargar_migracion()
    motor = _base_nueva()
    with motor.begin() as conexion:
        conexion.execute(
            sa.text(
                "INSERT INTO business_units (code, name_key, bird_type) "
                "VALUES ('grandparent', 'clave.personalizada', NULL)"
            )
        )
    with motor.begin() as conexion:
        creadas = migracion._sembrar_catalogo(conexion)
    assert sorted(creadas) == ["breeder", "broiler", "hatchery"]
    filas = {f[0]: f for f in _filas(motor)}
    assert set(filas) == set(CODIGOS_CANONICOS)
    assert filas["grandparent"][1] == "clave.personalizada"


def test_catalogo_completo_queda_intacto():
    migracion = _cargar_migracion()
    motor = _base_nueva()
    with motor.begin() as conexion:
        for code in CODIGOS_CANONICOS:
            conexion.execute(
                sa.text(
                    "INSERT INTO business_units (code, name_key, bird_type) "
                    "VALUES (:code, :name_key, NULL)"
                ),
                {"code": code, "name_key": f"clave.{code}"},
            )
    with motor.begin() as conexion:
        creadas = migracion._sembrar_catalogo(conexion)
    assert creadas == []
    assert [f[1] for f in _filas(motor)] == [f"clave.{c}" for c in CODIGOS_CANONICOS]


def test_sin_efectos_sobre_las_tablas_vecinas():
    migracion = _cargar_migracion()
    motor = _base_nueva()
    with motor.begin() as conexion:
        conexion.execute(
            sa.text(
                "CREATE TABLE company_business_units (id INTEGER PRIMARY KEY, "
                "company_id INTEGER, business_unit_id INTEGER, is_enabled BOOLEAN)"
            )
        )
        conexion.execute(
            sa.text(
                "CREATE TABLE user_business_units (id INTEGER PRIMARY KEY, "
                "user_id INTEGER, company_business_unit_id INTEGER)"
            )
        )
        migracion._sembrar_catalogo(conexion)
    with motor.connect() as conexion:
        for tabla in ("company_business_units", "user_business_units"):
            n = conexion.execute(sa.text(f"SELECT COUNT(*) FROM {tabla}")).scalar_one()
            assert n == 0, f"{tabla} no debe recibir filas de la migración"


def test_paridad_con_el_seed_fuente_unica():
    """El seed importa la constante de la migración: no hay segundo sitio que pueda divergir."""
    from seeds.baseline_seeds import UNIDADES_DE_NEGOCIO

    migracion = _cargar_migracion()
    assert tuple(UNIDADES_DE_NEGOCIO) == tuple(migracion.UNIDADES_CANONICAS)

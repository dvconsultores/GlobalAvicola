"""catálogo canónico de unidades de negocio — dato determinista de despliegue (`GA-FE-02-C §2` · F1 de `GA-FE-02-B`)

Las cuatro cadenas productivas (`GA-REM-040 §2`, `OD-16.a`) son catálogo de plataforma:
ninguna empresa las crea ni las renombra. Hasta hoy se sembraban **solo** desde
`seeds/baseline_seeds.py`, y esa siembra no está garantizada por el ciclo de despliegue:
ENV-01 acumula tres verificaciones con `GET /business-units` = `[]` (`count=0`) y dos
ejecuciones manuales reportadas que no llegaron a la base que sirve el dominio
(`BLOCKED_SERVER_ACCESS_F1`, spec §4). El propietario autorizó (`GA-FE-02-C §2`) que el
baseline obligatorio pase a ser dato determinista: commit → push → imagen →
`docker-entrypoint.sh` → `alembic upgrade head` (`GA-REM-024`) → filas presentes. Sin
`docker exec`, sin SQL manual, sin paso de operador.

`p6q7r8s9t0u1` dejó escrito que «una migración que inserta catálogo obliga a mantener el dato
en dos sitios» y por eso no lo sembró. Esa decisión queda **superada, no contradicha**: la
fuente única se conserva con el patrón que el repositorio ya usa para la matriz RBAC — el seed
**importa** `UNIDADES_CANONICAS` de esta migración
(`seeds/baseline_seeds._unidades_de_negocio_de_la_migracion`). No hay segundo sitio donde el
dato pueda divergir, y el test dirigido (`tests/test_migration_bu_catalog.py`) lo verifica.

Idempotente y segura en cualquier estado: inserta solo los códigos ausentes (vacío → 4;
parcial → se completa; completo → intacto), no reescribe filas presentes y no toca ninguna
otra tabla: **cero** `company_business_units` (catálogo ≠ habilitación), **cero**
`user_business_units` (habilitación ≠ concesión), cero roles, cero permisos.

Downgrade: **NO-OP intencional**. Borrar filas canónicas podría destruir referencias
(habilitaciones, concesiones, histórico) y no hay estado anterior que restaurar — es baseline
aditivo. Mismo criterio que `l2m3n4o5p6q7`.

Revision ID: y5z6a7b8c9d0
Revises: x4y5z6a7b8c9
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "y5z6a7b8c9d0"
down_revision = "x4y5z6a7b8c9"
branch_labels = None
depends_on = None

#: Las cuatro canónicas. **Fuente única** desde `GA-FE-02-C`: `seeds/baseline_seeds.py` las
#: importa de aquí y el test dirigido compara ambas. `name_key` es clave de traducción (no una
#: traducción); `bird_type` registra la correspondencia con el enum de dominio — la autoridad
#: de acceso son las tres tablas, nunca el enum.
UNIDADES_CANONICAS: tuple[tuple[str, str, str], ...] = (
    ("grandparent", "businessUnits.grandparent", "grandparent"),
    ("breeder", "businessUnits.breeder", "breeder"),
    ("hatchery", "businessUnits.hatchery", "hatchery"),
    ("broiler", "businessUnits.broiler", "broiler"),
)


def _sembrar_catalogo(conexion: sa.Connection) -> list[str]:
    """Inserta solo los códigos ausentes. Devuelve los códigos creados.

    SQL portable a propósito (PostgreSQL en despliegue, SQLite en el test dirigido): el
    `SELECT` + `INSERT` por ausencia no depende de `ON CONFLICT` ni del dialecto.
    """
    existentes = set(
        conexion.execute(sa.text("SELECT code FROM business_units")).scalars().all()
    )
    creadas: list[str] = []
    for code, name_key, bird_type in UNIDADES_CANONICAS:
        if code in existentes:
            continue
        conexion.execute(
            sa.text(
                "INSERT INTO business_units (code, name_key, bird_type) "
                "VALUES (:code, :name_key, :bird_type)"
            ),
            {"code": code, "name_key": name_key, "bird_type": bird_type},
        )
        creadas.append(code)
    return creadas


def upgrade() -> None:
    conexion = op.get_bind()
    creadas = _sembrar_catalogo(conexion)
    print(f"[F1] catálogo de unidades de negocio: creadas {len(creadas)} {sorted(creadas)}")


def downgrade() -> None:
    # NO-OP intencional — ver docstring y `GA_FE_02_B_ENV01_CERTIFICATION_UNBLOCKER_SPEC.md §4.2`.
    # Borrar las filas canónicas podría destruir referencias (company_business_units,
    # user_business_units, histórico) y no hay estado anterior que restaurar: es baseline
    # aditivo. El dato de plataforma no se deshace a ciegas.
    pass

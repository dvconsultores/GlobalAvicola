"""causa compartida «Desconocida» y fase derivada del alimento — `SPEC 020 §6` · `RR-32` · `RR-34`

Dos decisiones del propietario en la misma migración, porque son el mismo acuerdo —qué es
dato de plataforma y qué se deriva— y viajan juntas o no viajan.

**`RR-32` · catálogo compartido de causas.** `mortality_causes` y `cull_causes` son
`TENANT_OWNED_NULLABLE`: la fila con `company_id` nulo es de la plataforma y se comparte.
Hasta hoy ese uso estaba previsto en el modelo y en `app/tenancy.py`
(`verificar_catalogo_de_empresa` trata `NULL` como compartido) pero **no había ninguna
fila**: cada empresa tenía que inventar su «Desconocida» y los eventos de dos inquilinos no
eran comparables. Esta migración siembra **una** fila por tabla (`company_id NULL`,
`name 'Desconocida'`, `category 'unknown'`, activa) y solo si no existe ya una equivalente.

La guarda de existencia compara el nombre **normalizado** (minúsculas y sin acentos) contra
`('desconocida', 'desconocido', 'por determinar', 'sin determinar')`: una base que ya tenía
su propia «Desconocida» compartida no recibe una segunda. De ahí que la siembra sea
**idempotente** —ejecutarla dos veces no duplica—, que es lo que exige un paso que corre en
cada despliegue (`alembic upgrade head`).

**`RR-34` · fase derivada del lote.** `feed_movements.phase_id` nace **nula y sin backfill**
a propósito: la fase de un consumo de alimento se deriva del lote en la fecha del evento, y
rellenar el histórico con el cálculo de hoy escribiría como hecho lo que es una inferencia.
La columna queda como lectura explícita; el backfill, si alguna vez se decide, es otro paso
con su propia evidencia.

Downgrade: borra `feed_movements.phase_id` y **solo** las filas compartidas sembradas aquí
(`company_id NULL`, `name 'Desconocida'`, `category 'unknown'`) que ninguna referencia
sostenga — ni `operational_events.cause_id` / `cull_cause_id` ni las correcciones registradas
en `correction_logs`. Una fila que un evento o una corrección nombran se queda: el catálogo
se puede deshacer, la historia no.

Revision ID: i4d5e6f7a8b9
Revises: h3c4d5e6f7a8
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "i4d5e6f7a8b9"
down_revision = "h3c4d5e6f7a8"
branch_labels = None
depends_on = None

#: Las dos tablas de causa. Tupla literal: el nombre entra en el SQL y por eso **no** puede
#: venir de fuera.
TABLAS_DE_CAUSA: tuple[str, ...] = ("mortality_causes", "cull_causes")

NOMBRE_COMPARTIDO = "Desconocida"
CATEGORIA_COMPARTIDA = "unknown"

#: Nombres que ya significan «no se conoce la causa». Si la base trae uno de ellos como fila
#: compartida, es la misma fila con otro nombre y no se siembra otra.
ALIAS_DESCONOCIDA: tuple[str, ...] = (
    "desconocida",
    "desconocido",
    "por determinar",
    "sin determinar",
)

#: `translate` y no `unaccent`: `unaccent` es una extensión que puede no estar instalada y una
#: migración no debe depender de un `CREATE EXTENSION`. El alfabeto que nos importa es corto.
_NORMALIZAR_NOMBRE = "lower(translate(name, 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'))"

#: `(tabla, columna del evento, campo de la corrección)` — las dos referencias que sostienen
#: una causa y por las que el downgrade **no** la borra.
_REFERENCIAS: tuple[tuple[str, str, str], ...] = (
    ("mortality_causes", "cause_id", "cause_id"),
    ("cull_causes", "cull_cause_id", "cull_cause_id"),
)


def _sembrar(conexion: sa.Connection) -> list[str]:
    """Siembra la causa compartida en las tablas que aún no la tengan.

    Devuelve las tablas donde insertó. Expuesta con nombre propio —y no en línea dentro de
    `upgrade`— para que la prueba de idempotencia pueda llamarla dos veces sobre la misma
    conexión sin inventarse una segunda copia del SQL.
    """
    creadas: list[str] = []
    for tabla in TABLAS_DE_CAUSA:
        existente = conexion.execute(
            sa.text(
                f"SELECT id FROM {tabla} "  # noqa: S608 — tabla de `TABLAS_DE_CAUSA`
                "WHERE company_id IS NULL AND is_active = TRUE "
                f"AND {_NORMALIZAR_NOMBRE} IN :alias"
            ).bindparams(sa.bindparam("alias", expanding=True)),
            {"alias": list(ALIAS_DESCONOCIDA)},
        ).first()
        if existente is not None:
            continue
        # `created_at` se omite: tiene `server_default`, y el instante de la siembra es el del
        # despliegue, no el de una constante escrita en el código.
        conexion.execute(
            sa.text(
                f"INSERT INTO {tabla} (company_id, name, category, is_active) "  # noqa: S608
                "VALUES (NULL, :nombre, :categoria, TRUE)"
            ),
            {"nombre": NOMBRE_COMPARTIDO, "categoria": CATEGORIA_COMPARTIDA},
        )
        creadas.append(tabla)
    return creadas


def upgrade() -> None:
    # (a) `RR-34`. Nula y sin backfill: ver docstring.
    op.add_column("feed_movements", sa.Column("phase_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_feed_movements_phase_id", "feed_movements", "productive_phases",
        ["phase_id"], ["id"],
    )

    # (b) `RR-32`. Idempotente: `_sembrar` consulta antes de insertar.
    creadas = _sembrar(op.get_bind())
    print(f"[SPEC 020 §6] causa compartida «{NOMBRE_COMPARTIDO}»: sembrada en {creadas}")


def downgrade() -> None:
    conexion = op.get_bind()
    for tabla, columna_evento, campo_correccion in _REFERENCIAS:
        # `NOT IN` con subconsultas que excluyen `NULL`: un `NULL` en la lista dejaría el
        # predicado en desconocido y no borraría nada. Las dos referencias se comprueban por
        # separado porque el evento la nombra con una clave foránea y la corrección con texto
        # (`correction_logs.corrected_value` guarda el identificador corregido).
        borradas = conexion.execute(
            sa.text(  # noqa: S608 — tabla y columnas de `_REFERENCIAS`
                f"DELETE FROM {tabla} "
                "WHERE company_id IS NULL "
                "AND name = :nombre AND category = :categoria "
                f"AND id NOT IN (SELECT {columna_evento} FROM operational_events "
                f"WHERE {columna_evento} IS NOT NULL) "
                "AND CAST(id AS text) NOT IN (SELECT corrected_value FROM correction_logs "
                "WHERE field_name = :campo AND corrected_value IS NOT NULL)"
            ),
            {"nombre": NOMBRE_COMPARTIDO, "categoria": CATEGORIA_COMPARTIDA,
             "campo": campo_correccion},
        ).rowcount
        print(f"[SPEC 020 §6] filas compartidas retiradas de {tabla}: {borradas}")

    op.drop_constraint("fk_feed_movements_phase_id", "feed_movements", type_="foreignkey")
    op.drop_column("feed_movements", "phase_id")

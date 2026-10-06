"""SPEC 005 · Guard de solo lectura y query registry — `AC-HANA-03`, `06`, `11`, `12`.

Dos capas independientes, y ninguna descansa en la otra:

    el origen del SQL   un registry interno y cerrado; ningún request entrega SQL
    el guard            una sola sentencia, de lectura, sin tokens mutantes

El guard no es la seguridad: es la tercera línea, tras el usuario READ ONLY de SAP y el
registry. Por eso se prueba también contra lo que un regex ingenuo dejaría pasar
(comentarios, literales, varias sentencias).
"""
from __future__ import annotations

import re

import pytest

from app.integrations.sap.inbound.errors import ErrorCode, SapInboundError
from app.integrations.sap.inbound.registry import (
    REGISTRY,
    SYNC_ORDER,
    HanaObject,
    get_definition,
    render_sql,
)
from app.integrations.sap.inbound.sql_guard import assert_read_only

LECTURAS = [
    'SELECT 1 AS "ok" FROM DUMMY',
    "select WERKS from T001W where MANDT = :mandt",
    "WITH x AS (SELECT BUKRS FROM T001 WHERE MANDT = :mandt) SELECT BUKRS FROM x",
    "SELECT NAME1 FROM T001W -- comentario de línea\nWHERE MANDT = :mandt",
    "SELECT /* comentario */ WERKS FROM T001W WHERE MANDT = :mandt",
    # Una palabra mutante dentro de un literal o de un identificador no es una mutación.
    "SELECT 'UPDATE' AS ETIQUETA FROM DUMMY",
    "SELECT LAST_UPDATE_DATE, CREATED_BY FROM T001W WHERE MANDT = :mandt",
]


@pytest.mark.parametrize("sql", LECTURAS)
def test_hana_guard_accepts_read_only_select(sql):
    assert assert_read_only(sql)


def _rechaza(sql: str) -> None:
    with pytest.raises(SapInboundError) as exc:
        assert_read_only(sql)
    assert exc.value.code is ErrorCode.SAP_QUERY_CONTRACT_ERROR


def test_hana_guard_rejects_update():
    _rechaza("UPDATE T001W SET NAME1 = 'x' WHERE MANDT = :mandt")
    _rechaza("WITH x AS (SELECT 1 FROM DUMMY) UPDATE T001W SET NAME1 = 'x'")


def test_hana_guard_rejects_insert():
    _rechaza("INSERT INTO T001W (WERKS) VALUES ('9999')")
    _rechaza("SELECT 1 FROM DUMMY WHERE EXISTS (SELECT 1 FROM DUMMY) INSERT INTO T VALUES (1)")


def test_hana_guard_rejects_delete():
    _rechaza("DELETE FROM T001W WHERE MANDT = :mandt")


def test_hana_guard_rejects_merge():
    _rechaza("MERGE INTO T001W USING DUMMY ON 1 = 1 WHEN MATCHED THEN UPDATE SET NAME1 = 'x'")
    _rechaza("UPSERT T001W VALUES ('9999') WITH PRIMARY KEY")


def test_hana_guard_rejects_call():
    _rechaza("CALL SYS.SOME_PROCEDURE()")
    _rechaza("DO BEGIN DELETE FROM T001W; END")


@pytest.mark.parametrize("sql", [
    "CREATE TABLE X (A INT)",
    "ALTER TABLE T001W ADD (Z INT)",
    "DROP TABLE T001W",
    "TRUNCATE TABLE T001W",
    "GRANT SELECT ON T001W TO PUBLIC",
    "REVOKE SELECT ON T001W FROM PUBLIC",
    "SELECT * INTO NUEVA FROM T001W",
    "SELECT WERKS FROM T001W FOR UPDATE",
    "EXEC 'DELETE FROM T001W'",
    "EXECUTE IMMEDIATE 'DROP TABLE T001W'",
    "SET SCHEMA OTRO",
    "",
    "   ",
])
def test_hana_guard_rejects_ddl_and_dynamic_sql(sql):
    _rechaza(sql)


def test_hana_guard_rejects_multiple_statements():
    _rechaza("SELECT 1 FROM DUMMY; SELECT 2 FROM DUMMY")
    _rechaza("SELECT 1 FROM DUMMY; DELETE FROM T001W")
    # El comentario no puede esconder la segunda sentencia…
    _rechaza("SELECT 1 FROM DUMMY /* ; */ ; DROP TABLE T001W")
    # …ni cerrar antes de tiempo un literal.
    _rechaza("SELECT 'a' FROM DUMMY; --' \nDELETE FROM T001W")


def test_hana_guard_mutating_token_hidden_in_comment_is_not_executed_blindly():
    """Un comentario se descarta antes de decidir: lo que queda es lo que se evalúa."""
    assert assert_read_only("SELECT 1 FROM DUMMY /* DELETE FROM T001W */")
    _rechaza("/* SELECT */ DELETE FROM T001W")


# ── Registry ────────────────────────────────────────────────────────────────

OBJETOS_OBLIGATORIOS = {
    "company", "plant", "storage_location", "vendor", "material", "batch", "movement_type",
    "purchase_order", "purchase_order_item", "purchase_order_history", "production_order",
    "transfer_order", "outbound_order", "material_movement",
}


def test_hana_registry_covers_every_required_object():
    assert {o.value for o in HanaObject} == OBJETOS_OBLIGATORIOS
    assert set(REGISTRY) == set(HanaObject)
    assert set(SYNC_ORDER) == set(HanaObject), "todo objeto tiene su turno de sincronización"


@pytest.mark.parametrize("objeto", list(HanaObject))
def test_hana_adapter_uses_readonly_registry(objeto):
    """Cada definición declara su contrato completo y pasa el guard una vez renderizada."""
    d = get_definition(objeto)
    assert d.object_type is objeto
    assert d.query_id and d.query_id.startswith(objeto.value + ".")
    assert d.source_key_fields and d.source_key_fields[0] == "MANDT"
    assert d.default_order, "sin orden estable no hay paginación fiable"
    assert d.max_page_size and d.max_page_size <= 1000
    assert d.expected_columns and set(d.required_columns) <= set(d.expected_columns)
    assert set(d.source_key_fields) <= set(d.required_columns)
    assert d.source_status in ("LEGACY_CONFIRMED", "CANDIDATE")
    assert d.tables

    sql = render_sql(d, "SAPFAKE")
    assert assert_read_only(sql)
    assert sql.count(";") == 0


@pytest.mark.parametrize("objeto", list(HanaObject))
def test_hana_query_uses_bound_parameters(objeto):
    """`AC-HANA-12`. Los valores viajan como bind: en el SQL no hay literales de negocio."""
    d = get_definition(objeto)
    sql = render_sql(d, "SAPFAKE")
    marcadores = set(re.findall(r":([a-z_]+)", sql))

    assert "mandt" in marcadores, "el mandante siempre es un parámetro"
    assert {"page_limit", "page_offset"} <= marcadores, "toda consulta está paginada"
    assert marcadores == set(d.required_params) | set(d.optional_params) | {
        "page_limit", "page_offset"}, "los parámetros declarados y los usados coinciden"

    sin_cadenas_vacias = sql.replace("''", "")
    literales = re.findall(r"'([^']*)'", sin_cadenas_vacias)
    assert literales == [], f"literales en el SQL de {objeto.value}: {literales}"
    assert not re.search(r"=\s*\d", sql), "ningún valor numérico incrustado"


@pytest.mark.parametrize("objeto", list(HanaObject))
def test_hana_registry_has_no_legacy_hardcodes(objeto):
    """`AC-HANA-03`. Ningún hardcode del legacy sobrevive en una definición."""
    sql = render_sql(get_definition(objeto), "SAPFAKE")
    for prohibido in ("120", "3000", "2500", "641", "303", "110000", "110001", "110002",
                      "105001", "120000", "2023", "2024", "2025", "NO USAR", "SAPHANADB"):
        assert prohibido not in sql, f"{objeto.value}: hardcode legacy «{prohibido}»"
    assert "SELECT *" not in sql.upper().replace("  ", " "), "prohibido el scan con asterisco"


DOCUMENTALES = ("purchase_order", "purchase_order_item", "purchase_order_history",
                "production_order", "transfer_order", "outbound_order", "material_movement")


@pytest.mark.parametrize("valor", DOCUMENTALES)
def test_hana_document_objects_require_time_window(valor):
    """`§17`. Un objeto potencialmente grande no se lee sin ventana temporal."""
    d = get_definition(HanaObject(valor))
    assert {"date_from", "date_to"} <= set(d.required_params)
    assert d.strategy == "BOUNDED_RECONCILIATION_WINDOW"
    assert d.window_field and d.watermark_candidate
    sql = render_sql(d, "SAPFAKE")
    assert ":date_from" in sql and ":date_to" in sql


def test_hana_schema_is_a_validated_identifier_never_request_input():
    d = get_definition(HanaObject.PLANT)
    assert '"SAPFAKE".' in render_sql(d, "SAPFAKE")
    for malo in ('SAP"; DROP TABLE X; --', "SAP FAKE", "", "sap.fake", "1SAP", "SAP'X"):
        with pytest.raises(SapInboundError) as exc:
            render_sql(d, malo)
        assert exc.value.code is ErrorCode.SAP_CONFIG_MISSING


def test_hana_registry_is_closed():
    """No hay forma de registrar una definición en caliente ni de pedir un objeto libre."""
    with pytest.raises((TypeError, AttributeError)):
        REGISTRY["libre"] = get_definition(HanaObject.PLANT)  # type: ignore[index]
    with pytest.raises((ValueError, KeyError)):
        get_definition("select * from x")  # type: ignore[arg-type]

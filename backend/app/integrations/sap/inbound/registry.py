"""Query registry cerrado — SPEC 005 `§14`, `FR-02`, `FR-03`, `FR-06`.

    LEGACY QUERY != CONTRACT
    CURRENT HANA METADATA + APPROVED QUERY REGISTRY = CONTRACT

Cada definición es SQL **estático**. Lo único que se interpola es el schema, que viene de
`Settings` y pasa por `validate_identifier`; todo valor —mandante, sociedad, ventana, idioma,
página— viaja como parámetro bind. No hay listas `IN` dinámicas: se consulta una sociedad cada
vez, de modo que ningún fragmento del SQL depende de los datos.

`source_status` dice de dónde sale la confianza en la fuente, y no se redondea:

    LEGACY_CONFIRMED   la tabla consta en el uso histórico (`audit/sap0`, `audit/sap-soap/11`)
    CANDIDATE          alguna tabla de la definición no está verificada; la valida el probe (P5)

Ninguna lo está contra el landscape real: SAP-0P cerró con 0/12 objetos verificados.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .settings import validate_identifier
from .sql_guard import assert_read_only


class HanaObject(str, enum.Enum):
    COMPANY = "company"
    PLANT = "plant"
    STORAGE_LOCATION = "storage_location"
    VENDOR = "vendor"
    MATERIAL = "material"
    BATCH = "batch"
    MOVEMENT_TYPE = "movement_type"
    PURCHASE_ORDER = "purchase_order"
    PURCHASE_ORDER_ITEM = "purchase_order_item"
    PURCHASE_ORDER_HISTORY = "purchase_order_history"
    PRODUCTION_ORDER = "production_order"
    TRANSFER_ORDER = "transfer_order"
    OUTBOUND_ORDER = "outbound_order"
    MATERIAL_MOVEMENT = "material_movement"


SNAPSHOT = "SNAPSHOT"
WINDOW = "BOUNDED_RECONCILIATION_WINDOW"
PAGINACION = ("page_limit", "page_offset")
_PAGINA = "LIMIT :page_limit OFFSET :page_offset"


@dataclass(frozen=True)
class QueryDefinition:
    object_type: HanaObject
    query_id: str
    tables: tuple[str, ...]
    source_status: str
    source_key_fields: tuple[str, ...]
    sql_template: str = field(repr=False)
    required_params: tuple[str, ...]
    expected_columns: tuple[str, ...]
    required_columns: tuple[str, ...]
    default_order: tuple[str, ...]
    strategy: str = SNAPSHOT
    optional_params: tuple[str, ...] = ()
    #: Valores de dominio estándar de SAP (no de cliente) que la definición fija. Viajan como
    #: bind igual que el resto: el SQL no lleva literales.
    fixed_params: Mapping[str, str] = field(default_factory=dict)
    watermark_candidate: str | None = None
    window_field: str | None = None
    max_page_size: int = 1000
    #: `company_code`: una consulta por sociedad mapeada. `client`: una por mandante.
    scope: str = "company_code"
    promotes_to: str | None = None
    notes: str = ""


def _d(**kw) -> QueryDefinition:
    kw["sql_template"] = " ".join(kw["sql_template"].split())
    return QueryDefinition(**kw)


_DEFINICIONES = (
    _d(
        object_type=HanaObject.COMPANY, query_id="company.v1",
        tables=("T001",), source_status="CANDIDATE",
        source_key_fields=("MANDT", "BUKRS"),
        sql_template=f"""
            SELECT T.MANDT, T.BUKRS, T.BUTXT, T.ORT01, T.LAND1, T.WAERS
            FROM {{s}}T001 T
            WHERE T.MANDT = :mandt AND T.BUKRS = :bukrs
            ORDER BY T.MANDT, T.BUKRS {_PAGINA}""",
        required_params=("mandt", "bukrs"),
        expected_columns=("MANDT", "BUKRS", "BUTXT", "ORT01", "LAND1", "WAERS"),
        required_columns=("MANDT", "BUKRS", "BUTXT"),
        default_order=("MANDT", "BUKRS"),
        notes="Sociedad. Sin tipo de referencia: permanece en staging (OD-24, sin convergencia).",
    ),
    _d(
        object_type=HanaObject.PLANT, query_id="plant.v1",
        tables=("T001W", "T001K"), source_status="CANDIDATE",
        source_key_fields=("MANDT", "WERKS"),
        sql_template=f"""
            SELECT W.MANDT, W.WERKS, W.NAME1, W.NAME2, W.ORT01, W.LAND1, K.BUKRS
            FROM {{s}}T001W W
            JOIN {{s}}T001K K ON K.MANDT = W.MANDT AND K.BWKEY = W.BWKEY
            WHERE W.MANDT = :mandt AND K.BUKRS = :bukrs
            ORDER BY W.MANDT, W.WERKS {_PAGINA}""",
        required_params=("mandt", "bukrs"),
        expected_columns=("MANDT", "WERKS", "NAME1", "NAME2", "ORT01", "LAND1", "BUKRS"),
        required_columns=("MANDT", "WERKS", "NAME1", "BUKRS"),
        default_order=("MANDT", "WERKS"),
        promotes_to="plant",
        notes="T001W consta en el legacy; la relación centro→sociedad (T001K) es candidata.",
    ),
    _d(
        object_type=HanaObject.STORAGE_LOCATION, query_id="storage_location.v1",
        tables=("T001L", "T001W", "T001K"), source_status="CANDIDATE",
        source_key_fields=("MANDT", "WERKS", "LGORT"),
        sql_template=f"""
            SELECT L.MANDT, L.WERKS, L.LGORT, L.LGOBE, K.BUKRS
            FROM {{s}}T001L L
            JOIN {{s}}T001W W ON W.MANDT = L.MANDT AND W.WERKS = L.WERKS
            JOIN {{s}}T001K K ON K.MANDT = W.MANDT AND K.BWKEY = W.BWKEY
            WHERE L.MANDT = :mandt AND K.BUKRS = :bukrs
            ORDER BY L.MANDT, L.WERKS, L.LGORT {_PAGINA}""",
        required_params=("mandt", "bukrs"),
        expected_columns=("MANDT", "WERKS", "LGORT", "LGOBE", "BUKRS"),
        required_columns=("MANDT", "WERKS", "LGORT", "BUKRS"),
        default_order=("MANDT", "WERKS", "LGORT"),
        promotes_to="storage_location",
        notes="LGORT es almacén, no galpón: la relación con house exige mapping explícito.",
    ),
    _d(
        object_type=HanaObject.VENDOR, query_id="vendor.v1",
        tables=("LFA1", "LFB1"), source_status="CANDIDATE",
        source_key_fields=("MANDT", "LIFNR"),
        sql_template=f"""
            SELECT A.MANDT, A.LIFNR, A.NAME1, A.STCD1, A.LAND1, A.SPERR, A.LOEVM, B.BUKRS
            FROM {{s}}LFA1 A
            JOIN {{s}}LFB1 B ON B.MANDT = A.MANDT AND B.LIFNR = A.LIFNR
            WHERE A.MANDT = :mandt AND B.BUKRS = :bukrs
            ORDER BY A.MANDT, A.LIFNR {_PAGINA}""",
        required_params=("mandt", "bukrs"),
        expected_columns=("MANDT", "LIFNR", "NAME1", "STCD1", "LAND1", "SPERR", "LOEVM", "BUKRS"),
        required_columns=("MANDT", "LIFNR", "NAME1", "BUKRS"),
        default_order=("MANDT", "LIFNR"),
        promotes_to="vendor",
        notes="LFA1 consta en el legacy; se acota por sociedad (LFB1). BP/CVI se valida en el probe.",
    ),
    _d(
        object_type=HanaObject.MATERIAL, query_id="material.v1",
        tables=("MARA", "MAKT", "MARC", "T001K"), source_status="CANDIDATE",
        source_key_fields=("MANDT", "MATNR"),
        sql_template=f"""
            SELECT M.MANDT, M.MATNR, T.MAKTX, M.MTART, M.MATKL, M.MEINS, M.LVORM, M.LAEDA
            FROM {{s}}MARA M
            LEFT JOIN {{s}}MAKT T
              ON T.MANDT = M.MANDT AND T.MATNR = M.MATNR AND T.SPRAS = :langu
            WHERE M.MANDT = :mandt
              AND EXISTS (
                SELECT C.MATNR FROM {{s}}MARC C
                JOIN {{s}}T001K K ON K.MANDT = C.MANDT AND K.BWKEY = C.WERKS
                WHERE C.MANDT = M.MANDT AND C.MATNR = M.MATNR AND K.BUKRS = :bukrs)
            ORDER BY M.MANDT, M.MATNR {_PAGINA}""",
        required_params=("mandt", "bukrs", "langu"),
        expected_columns=("MANDT", "MATNR", "MAKTX", "MTART", "MATKL", "MEINS", "LVORM", "LAEDA"),
        required_columns=("MANDT", "MATNR", "MTART", "MEINS"),
        default_order=("MANDT", "MATNR"),
        watermark_candidate="LAEDA",
        promotes_to="material",
        notes="Material de los centros de la sociedad. La categoría avícola se resuelve en GA.",
    ),
    _d(
        object_type=HanaObject.BATCH, query_id="batch.v1",
        tables=("MCHA", "T001K"), source_status="CANDIDATE",
        source_key_fields=("MANDT", "MATNR", "WERKS", "CHARG"),
        sql_template=f"""
            SELECT B.MANDT, B.MATNR, B.WERKS, B.CHARG, B.HSDAT, B.VFDAT, B.ERSDA, B.LAEDA,
                   B.LVORM, K.BUKRS
            FROM {{s}}MCHA B
            JOIN {{s}}T001K K ON K.MANDT = B.MANDT AND K.BWKEY = B.WERKS
            WHERE B.MANDT = :mandt AND K.BUKRS = :bukrs
            ORDER BY B.MANDT, B.MATNR, B.WERKS, B.CHARG {_PAGINA}""",
        required_params=("mandt", "bukrs"),
        expected_columns=("MANDT", "MATNR", "WERKS", "CHARG", "HSDAT", "VFDAT", "ERSDA", "LAEDA",
                          "LVORM", "BUKRS"),
        required_columns=("MANDT", "MATNR", "WERKS", "CHARG", "BUKRS"),
        default_order=("MANDT", "MATNR", "WERKS", "CHARG"),
        watermark_candidate="LAEDA",
        promotes_to="sap_batch",
    ),
    _d(
        object_type=HanaObject.MOVEMENT_TYPE, query_id="movement_type.v1",
        tables=("T156HT",), source_status="LEGACY_CONFIRMED",
        source_key_fields=("MANDT", "BWART"),
        sql_template=f"""
            SELECT H.MANDT, H.BWART, MIN(H.BTEXT) AS BTEXT
            FROM {{s}}T156HT H
            WHERE H.MANDT = :mandt AND H.SPRAS = :langu
            GROUP BY H.MANDT, H.BWART
            ORDER BY H.MANDT, H.BWART {_PAGINA}""",
        required_params=("mandt", "langu"),
        expected_columns=("MANDT", "BWART", "BTEXT"),
        required_columns=("MANDT", "BWART"),
        default_order=("MANDT", "BWART"),
        scope="client",
        notes="Catálogo informativo. Ningún tipo de movimiento es una regla de negocio en GA.",
    ),
    _d(
        object_type=HanaObject.PURCHASE_ORDER, query_id="purchase_order.v1",
        tables=("EKKO",), source_status="LEGACY_CONFIRMED",
        source_key_fields=("MANDT", "EBELN"),
        sql_template=f"""
            SELECT E.MANDT, E.EBELN, E.BUKRS, E.BSTYP, E.BSART, E.LIFNR, E.EKORG, E.BEDAT,
                   E.AEDAT, E.WAERS, E.LOEKZ
            FROM {{s}}EKKO E
            WHERE E.MANDT = :mandt AND E.BUKRS = :bukrs AND E.BSTYP = :doc_category
              AND (E.RESWK = '' OR E.RESWK IS NULL)
              AND E.AEDAT BETWEEN :date_from AND :date_to
            ORDER BY E.MANDT, E.EBELN {_PAGINA}""",
        required_params=("mandt", "bukrs", "doc_category", "date_from", "date_to"),
        fixed_params={"doc_category": "F"},
        expected_columns=("MANDT", "EBELN", "BUKRS", "BSTYP", "BSART", "LIFNR", "EKORG", "BEDAT",
                          "AEDAT", "WAERS", "LOEKZ"),
        required_columns=("MANDT", "EBELN", "BUKRS", "LIFNR", "BEDAT"),
        default_order=("MANDT", "EBELN"),
        strategy=WINDOW, watermark_candidate="AEDAT", window_field="AEDAT",
        promotes_to="purchase_order",
        notes="Cabecera de OC. Los traslados (RESWK informado) van en transfer_order.",
    ),
    _d(
        object_type=HanaObject.PURCHASE_ORDER_ITEM, query_id="purchase_order_item.v1",
        tables=("EKPO", "EKKO", "EKET"), source_status="CANDIDATE",
        source_key_fields=("MANDT", "EBELN", "EBELP"),
        sql_template=f"""
            SELECT P.MANDT, P.EBELN, P.EBELP, P.MATNR, P.TXZ01, P.WERKS, P.LGORT, P.MENGE,
                   P.MEINS,
                   (SELECT MIN(S.EINDT) FROM {{s}}EKET S
                     WHERE S.MANDT = P.MANDT AND S.EBELN = P.EBELN AND S.EBELP = P.EBELP) AS EINDT,
                   P.LOEKZ, P.ELIKZ, E.BUKRS, E.AEDAT
            FROM {{s}}EKPO P
            JOIN {{s}}EKKO E ON E.MANDT = P.MANDT AND E.EBELN = P.EBELN
            WHERE P.MANDT = :mandt AND E.BUKRS = :bukrs AND E.BSTYP = :doc_category
              AND (E.RESWK = '' OR E.RESWK IS NULL)
              AND E.AEDAT BETWEEN :date_from AND :date_to
            ORDER BY P.MANDT, P.EBELN, P.EBELP {_PAGINA}""",
        required_params=("mandt", "bukrs", "doc_category", "date_from", "date_to"),
        fixed_params={"doc_category": "F"},
        expected_columns=("MANDT", "EBELN", "EBELP", "MATNR", "TXZ01", "WERKS", "LGORT", "MENGE",
                          "MEINS", "EINDT", "LOEKZ", "ELIKZ", "BUKRS", "AEDAT"),
        required_columns=("MANDT", "EBELN", "EBELP", "MATNR", "WERKS", "MENGE", "MEINS", "BUKRS"),
        default_order=("MANDT", "EBELN", "EBELP"),
        strategy=WINDOW, watermark_candidate="AEDAT", window_field="AEDAT",
        notes="Posiciones con su material real. Se elimina el patrón legacy macho/hembra por MATNR.",
    ),
    _d(
        object_type=HanaObject.PURCHASE_ORDER_HISTORY, query_id="purchase_order_history.v1",
        tables=("EKBE", "EKKO"), source_status="LEGACY_CONFIRMED",
        source_key_fields=("MANDT", "EBELN", "EBELP", "ZEKKN", "VGABE", "GJAHR", "BELNR", "BUZEI"),
        sql_template=f"""
            SELECT B.MANDT, B.EBELN, B.EBELP, B.ZEKKN, B.VGABE, B.GJAHR, B.BELNR, B.BUZEI,
                   B.BEWTP, B.BWART, B.BUDAT, B.MENGE, B.SHKZG, B.MATNR, B.WERKS, B.LFBNR, E.BUKRS
            FROM {{s}}EKBE B
            JOIN {{s}}EKKO E ON E.MANDT = B.MANDT AND E.EBELN = B.EBELN
            WHERE B.MANDT = :mandt AND E.BUKRS = :bukrs AND E.BSTYP = :doc_category
              AND (E.RESWK = '' OR E.RESWK IS NULL)
              AND B.BUDAT BETWEEN :date_from AND :date_to
            ORDER BY B.MANDT, B.EBELN, B.EBELP, B.ZEKKN, B.VGABE, B.GJAHR, B.BELNR, B.BUZEI
            {_PAGINA}""",
        required_params=("mandt", "bukrs", "doc_category", "date_from", "date_to"),
        fixed_params={"doc_category": "F"},
        expected_columns=("MANDT", "EBELN", "EBELP", "ZEKKN", "VGABE", "GJAHR", "BELNR", "BUZEI",
                          "BEWTP", "BWART", "BUDAT", "MENGE", "SHKZG", "MATNR", "WERKS", "LFBNR",
                          "BUKRS"),
        required_columns=("MANDT", "EBELN", "EBELP", "ZEKKN", "VGABE", "GJAHR", "BELNR", "BUZEI",
                          "BUDAT", "MENGE", "SHKZG", "BUKRS"),
        default_order=("MANDT", "EBELN", "EBELP", "ZEKKN", "VGABE", "GJAHR", "BELNR", "BUZEI"),
        strategy=WINDOW, watermark_candidate="BUDAT", window_field="BUDAT",
        notes="Historial de la OC: entradas (S) y reversos (H). Alimenta received_quantity.",
    ),
    _d(
        object_type=HanaObject.PRODUCTION_ORDER, query_id="production_order.v1",
        tables=("AUFK", "AFKO", "AFPO"), source_status="CANDIDATE",
        source_key_fields=("MANDT", "AUFNR"),
        sql_template=f"""
            SELECT A.MANDT, A.AUFNR, A.AUART, A.BUKRS, A.WERKS, P.MATNR, P.CHARG, P.LGORT,
                   K.GSTRP, K.GLTRP, K.GAMNG, K.GMEIN, A.LOEKZ, A.PHAS1, A.PHAS2, A.PHAS3,
                   A.ERDAT, A.AEDAT
            FROM {{s}}AUFK A
            JOIN {{s}}AFKO K ON K.MANDT = A.MANDT AND K.AUFNR = A.AUFNR
            JOIN {{s}}AFPO P ON P.MANDT = A.MANDT AND P.AUFNR = A.AUFNR
            WHERE A.MANDT = :mandt AND A.BUKRS = :bukrs
              AND P.POSNR = (SELECT MIN(X.POSNR) FROM {{s}}AFPO X
                              WHERE X.MANDT = P.MANDT AND X.AUFNR = P.AUFNR)
              AND (A.ERDAT BETWEEN :date_from AND :date_to
                   OR A.AEDAT BETWEEN :date_from AND :date_to)
            ORDER BY A.MANDT, A.AUFNR {_PAGINA}""",
        required_params=("mandt", "bukrs", "date_from", "date_to"),
        expected_columns=("MANDT", "AUFNR", "AUART", "BUKRS", "WERKS", "MATNR", "CHARG", "LGORT",
                          "GSTRP", "GLTRP", "GAMNG", "GMEIN", "LOEKZ", "PHAS1", "PHAS2", "PHAS3",
                          "ERDAT", "AEDAT"),
        required_columns=("MANDT", "AUFNR", "BUKRS", "WERKS", "MATNR", "GAMNG", "GMEIN", "ERDAT"),
        default_order=("MANDT", "AUFNR"),
        strategy=WINDOW, watermark_candidate="AEDAT", window_field="ERDAT",
        notes="Órdenes de producción (AUFK con AFKO/AFPO). Fuente a validar por metadata en P5.",
    ),
    _d(
        object_type=HanaObject.TRANSFER_ORDER, query_id="transfer_order.v1",
        tables=("EKPO", "EKKO"), source_status="CANDIDATE",
        source_key_fields=("MANDT", "EBELN", "EBELP"),
        sql_template=f"""
            SELECT P.MANDT, P.EBELN, P.EBELP, E.BUKRS, E.BSART, E.RESWK, P.RESLO, P.WERKS,
                   P.LGORT, P.MATNR, P.TXZ01, P.MENGE, P.MEINS, E.BEDAT, E.AEDAT, P.LOEKZ, P.ELIKZ
            FROM {{s}}EKPO P
            JOIN {{s}}EKKO E ON E.MANDT = P.MANDT AND E.EBELN = P.EBELN
            WHERE P.MANDT = :mandt AND E.BUKRS = :bukrs AND E.BSTYP = :doc_category
              AND E.RESWK <> ''
              AND E.AEDAT BETWEEN :date_from AND :date_to
            ORDER BY P.MANDT, P.EBELN, P.EBELP {_PAGINA}""",
        required_params=("mandt", "bukrs", "doc_category", "date_from", "date_to"),
        fixed_params={"doc_category": "F"},
        expected_columns=("MANDT", "EBELN", "EBELP", "BUKRS", "BSART", "RESWK", "RESLO", "WERKS",
                          "LGORT", "MATNR", "TXZ01", "MENGE", "MEINS", "BEDAT", "AEDAT", "LOEKZ",
                          "ELIKZ"),
        required_columns=("MANDT", "EBELN", "EBELP", "BUKRS", "RESWK", "WERKS", "MATNR", "MENGE",
                          "MEINS"),
        default_order=("MANDT", "EBELN", "EBELP"),
        strategy=WINDOW, watermark_candidate="AEDAT", window_field="AEDAT",
        promotes_to="transfer_order",
        notes="Traslado = documento de compras con centro suministrador (RESWK). "
              "Sin listas de BSART ni de BWART.",
    ),
    _d(
        object_type=HanaObject.OUTBOUND_ORDER, query_id="outbound_order.v1",
        tables=("LIKP", "LIPS", "T001K"), source_status="CANDIDATE",
        source_key_fields=("MANDT", "VBELN", "POSNR"),
        sql_template=f"""
            SELECT P.MANDT, P.VBELN, P.POSNR, H.LFART, H.VSTEL, H.KUNNR, H.WADAT, H.WADAT_IST,
                   H.ERDAT, P.MATNR, P.ARKTX, P.WERKS, P.LGORT, P.CHARG, P.LFIMG, P.VRKME,
                   P.VGBEL, P.VGPOS, K.BUKRS
            FROM {{s}}LIPS P
            JOIN {{s}}LIKP H ON H.MANDT = P.MANDT AND H.VBELN = P.VBELN
            JOIN {{s}}T001K K ON K.MANDT = P.MANDT AND K.BWKEY = P.WERKS
            WHERE P.MANDT = :mandt AND K.BUKRS = :bukrs AND H.VBTYP = :delivery_category
              AND H.ERDAT BETWEEN :date_from AND :date_to
            ORDER BY P.MANDT, P.VBELN, P.POSNR {_PAGINA}""",
        required_params=("mandt", "bukrs", "delivery_category", "date_from", "date_to"),
        fixed_params={"delivery_category": "J"},
        expected_columns=("MANDT", "VBELN", "POSNR", "LFART", "VSTEL", "KUNNR", "WADAT",
                          "WADAT_IST", "ERDAT", "MATNR", "ARKTX", "WERKS", "LGORT", "CHARG",
                          "LFIMG", "VRKME", "VGBEL", "VGPOS", "BUKRS"),
        required_columns=("MANDT", "VBELN", "POSNR", "MATNR", "WERKS", "LFIMG", "VRKME", "ERDAT",
                          "BUKRS"),
        default_order=("MANDT", "VBELN", "POSNR"),
        strategy=WINDOW, watermark_candidate="ERDAT", window_field="ERDAT",
        notes="Orden de salida = documento de entrega (candidata, Q8). No es un documento de "
              "material: MATDOC es evidencia de movimiento y va aparte.",
    ),
    _d(
        object_type=HanaObject.MATERIAL_MOVEMENT, query_id="material_movement.v1",
        tables=("MATDOC",), source_status="LEGACY_CONFIRMED",
        source_key_fields=("MANDT", "MBLNR", "MJAHR", "ZEILE"),
        sql_template=f"""
            SELECT M.MANDT, M.MBLNR, M.MJAHR, M.ZEILE, M.BWART, M.MATNR, M.WERKS, M.LGORT,
                   M.UMWRK, M.UMLGO, M.CHARG, M.ERFMG, M.ERFME, M.MENGE, M.MEINS, M.SHKZG,
                   M.BUDAT, M.BLDAT, M.CPUDT, M.EBELN, M.EBELP, M.AUFNR, M.BUKRS, M.SMBLN,
                   M.SJAHR, M.SMBLP
            FROM {{s}}MATDOC M
            WHERE M.MANDT = :mandt AND M.BUKRS = :bukrs
              AND M.BUDAT BETWEEN :date_from AND :date_to
            ORDER BY M.MANDT, M.MBLNR, M.MJAHR, M.ZEILE {_PAGINA}""",
        required_params=("mandt", "bukrs", "date_from", "date_to"),
        expected_columns=("MANDT", "MBLNR", "MJAHR", "ZEILE", "BWART", "MATNR", "WERKS", "LGORT",
                          "UMWRK", "UMLGO", "CHARG", "ERFMG", "ERFME", "MENGE", "MEINS", "SHKZG",
                          "BUDAT", "BLDAT", "CPUDT", "EBELN", "EBELP", "AUFNR", "BUKRS", "SMBLN",
                          "SJAHR", "SMBLP"),
        required_columns=("MANDT", "MBLNR", "MJAHR", "ZEILE", "BWART", "MATNR", "WERKS", "ERFMG",
                          "ERFME", "SHKZG", "BUDAT", "BUKRS"),
        default_order=("MANDT", "MBLNR", "MJAHR", "ZEILE"),
        strategy=WINDOW, watermark_candidate="BUDAT", window_field="BUDAT",
        notes="Documentos de material. Ventana temporal obligatoria; prohibido el scan abierto.",
    ),
)

REGISTRY: Mapping[HanaObject, QueryDefinition] = MappingProxyType(
    {d.object_type: d for d in _DEFINICIONES})

#: Orden de sincronización: primero lo que los documentos necesitan para interpretarse.
SYNC_ORDER: tuple[HanaObject, ...] = (
    HanaObject.COMPANY, HanaObject.PLANT, HanaObject.STORAGE_LOCATION, HanaObject.VENDOR,
    HanaObject.MATERIAL, HanaObject.BATCH, HanaObject.MOVEMENT_TYPE,
    HanaObject.PURCHASE_ORDER, HanaObject.PURCHASE_ORDER_ITEM,
    HanaObject.PURCHASE_ORDER_HISTORY, HanaObject.PRODUCTION_ORDER, HanaObject.TRANSFER_ORDER,
    HanaObject.OUTBOUND_ORDER, HanaObject.MATERIAL_MOVEMENT,
)

#: Objetos que solo tienen sentido juntos: pedir uno sincroniza el grupo. Una cabecera de OC sin
#: sus posiciones no tiene cantidad, y sin cantidad `BR-18` no es aplicable.
SYNC_GROUPS: tuple[tuple[HanaObject, ...], ...] = (
    (HanaObject.PURCHASE_ORDER, HanaObject.PURCHASE_ORDER_ITEM,
     HanaObject.PURCHASE_ORDER_HISTORY),
)

#: Primera consulta contra un sistema real: humo, sin volumen (`§35`).
PING_SQL = 'SELECT 1 AS "ok" FROM DUMMY'


def get_definition(objeto: HanaObject | str) -> QueryDefinition:
    return REGISTRY[HanaObject(objeto)]


def expand_objects(objetos) -> list[HanaObject]:
    """Normaliza la petición: todos si no se pide ninguno, grupos completos y orden canónico."""
    pedidos = {HanaObject(o) for o in objetos} if objetos else set(SYNC_ORDER)
    for grupo in SYNC_GROUPS:
        if pedidos & set(grupo):
            pedidos |= set(grupo)
    return [o for o in SYNC_ORDER if o in pedidos]


def render_sql(definition: QueryDefinition, schema: str) -> str:
    """SQL final de una definición. El schema es el único identificador interpolado."""
    if not isinstance(definition, QueryDefinition):
        raise TypeError("render_sql solo acepta definiciones del registry.")
    prefijo = f'"{validate_identifier(schema)}".'
    return assert_read_only(definition.sql_template.replace("{s}", prefijo))


# Toda definición debe ser una lectura válida desde el primer import: un error aquí rompe el
# arranque en lugar de aparecer en la primera sincronización.
assert set(REGISTRY) == set(HanaObject) == set(SYNC_ORDER)
for _definicion in _DEFINICIONES:
    render_sql(_definicion, "VALIDACION")
    assert set(_definicion.source_key_fields) <= set(_definicion.required_columns)
    assert set(_definicion.required_columns) <= set(_definicion.expected_columns)
    assert set(_definicion.fixed_params) <= set(_definicion.required_params)

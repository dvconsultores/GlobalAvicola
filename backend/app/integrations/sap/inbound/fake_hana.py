"""Doble de SAP HANA para pruebas, desarrollo y E2E local — SPEC 005 `§46`, `Q10`.

Imita lo que el cliente usa de `hdbcli`: `connect`, `cursor`, `execute`, `description`,
`fetchmany`/`fetchall`, `close`. **No es SAP y no lo aparenta**: `build_adapter` solo lo
acepta con `ENVIRONMENT` de desarrollo o de pruebas, y readiness lo declara `simulated`.

Es deliberadamente estricto. Solo responde a la consulta de humo y al SQL exacto del registry;
cualquier otra sentencia —un `UPDATE`, un `SELECT *` libre— es un error, de modo que si el
cliente llegara a enviar algo distinto la prueba lo vería en lugar de taparlo.

Los filtros se aplican como lo haría la base: por mandante, sociedad, idioma y ventana, con el
orden estable de la definición y `LIMIT`/`OFFSET`.
"""
from __future__ import annotations

import datetime as _dt
import threading
import time
from typing import Any

from .registry import PING_SQL, REGISTRY, QueryDefinition, render_sql


class FakeHanaError(Exception):
    """Error con la forma de `hdbcli.dbapi.Error`: `errorcode` y `errortext`."""

    def __init__(self, errorcode: int, errortext: str) -> None:
        self.errorcode = errorcode
        self.errortext = errortext
        super().__init__(errorcode, errortext)


class _Cursor:
    def __init__(self, fake: "FakeHana") -> None:
        self._fake = fake
        self._filas: list[tuple] = []
        self.description: list[tuple] | None = None
        self._cerrado = False
        fake.cursors_opened += 1

    def setquerytimeout(self, segundos: int) -> None:
        self._fake.query_timeouts.append(segundos)

    def execute(self, sql: str, params: Any = None) -> bool:
        params = dict(params or {})
        columnas, filas = self._fake._resolver(sql, params)
        self.description = [(c, None, None, None, None, None, None) for c in columnas]
        self._filas = filas
        return True

    def fetchmany(self, size: int = 1) -> list[tuple]:
        lote, self._filas = self._filas[:size], self._filas[size:]
        return lote

    def fetchall(self) -> list[tuple]:
        lote, self._filas = self._filas, []
        return lote

    def close(self) -> None:
        if not self._cerrado:
            self._cerrado = True
            self._fake.cursors_closed += 1


class _Conexion:
    def __init__(self, fake: "FakeHana") -> None:
        self._fake = fake
        self._cerrada = False

    def cursor(self) -> _Cursor:
        return _Cursor(self._fake)

    def close(self) -> None:
        if not self._cerrada:
            self._cerrada = True
            with self._fake._cerrojo:
                self._fake.connections_closed += 1
                self._fake._activas -= 1


class FakeHana:
    def __init__(self, dataset: dict[str, list[dict]] | None = None, *,
                 schema: str = "SAPFAKE", client: str = "100") -> None:
        self.dataset = dataset if dataset is not None else default_dataset(client=client)
        self.schema = schema
        self.client = client
        # ── Fallos e interferencias programables ──
        self.fail_connect: FakeHanaError | None = None
        self.fail_query: dict[str, FakeHanaError] = {}
        self.fail_query_at: dict[str, tuple[int, FakeHanaError]] = {}
        self.drop_columns: dict[str, set[str]] = {}
        #: Filas que el «origen» devuelve aunque no casen con el filtro (defensa en profundidad).
        self.inject: dict[str, list[dict]] = {}
        self.latency_seconds: float = 0.0
        # ── Observación ──
        self.executed: list[tuple[str, dict]] = []
        self.connect_kwargs: list[dict] = []
        self.query_timeouts: list[int] = []
        self.threads_used: set[int] = set()
        self.connections_opened = 0
        self.connections_closed = 0
        self.cursors_opened = 0
        self.cursors_closed = 0
        self.max_concurrent_connections = 0
        self._activas = 0
        self._llamadas: dict[str, int] = {}
        self._cerrojo = threading.Lock()
        self._sql: dict[str, QueryDefinition] = {}

    # ── DB-API ────────────────────────────────────────────────────────────────

    def connect(self, **kwargs: Any) -> _Conexion:
        self.threads_used.add(threading.get_ident())
        self.connect_kwargs.append(dict(kwargs))
        if self.latency_seconds:
            time.sleep(self.latency_seconds)
        if self.fail_connect is not None:
            raise self.fail_connect
        with self._cerrojo:
            self.connections_opened += 1
            self._activas += 1
            self.max_concurrent_connections = max(self.max_concurrent_connections, self._activas)
        return _Conexion(self)

    # ── Resolución ────────────────────────────────────────────────────────────

    def _definicion(self, sql: str) -> QueryDefinition | None:
        if not self._sql:
            self._sql = {render_sql(d, self.schema): d for d in REGISTRY.values()}
        return self._sql.get(sql)

    def _resolver(self, sql: str, params: dict) -> tuple[list[str], list[tuple]]:
        self.executed.append((sql, params))
        if sql == PING_SQL:
            return ["ok"], [(1,)]
        d = self._definicion(sql)
        if d is None:
            raise FakeHanaError(257, "sql syntax error: sentencia fuera del query registry")

        n = self._llamadas[d.query_id] = self._llamadas.get(d.query_id, 0) + 1
        if d.query_id in self.fail_query:
            raise self.fail_query[d.query_id]
        if d.query_id in self.fail_query_at and self.fail_query_at[d.query_id][0] == n:
            raise self.fail_query_at[d.query_id][1]

        filas = [f for f in self.dataset.get(d.object_type.value, []) if self._casa(d, f, params)]
        filas += [dict(f) for f in self.inject.get(d.query_id, [])]
        filas.sort(key=lambda f: tuple(str(f.get(c) or "") for c in d.default_order))
        desde = int(params.get("page_offset", 0))
        hasta = desde + int(params.get("page_limit", len(filas) or 1))
        columnas = [c for c in d.expected_columns if c not in self.drop_columns.get(d.query_id, ())]
        return columnas, [tuple(f.get(c) for c in columnas) for f in filas[desde:hasta]]

    @staticmethod
    def _casa(d: QueryDefinition, fila: dict, params: dict) -> bool:
        if fila.get("MANDT") != params.get("mandt"):
            return False
        if "bukrs" in params and "BUKRS" in fila and fila["BUKRS"] != params["bukrs"]:
            return False
        if "langu" in params and "SPRAS" in fila and fila["SPRAS"] != params["langu"]:
            return False
        if "date_from" in params:
            campos = ("ERDAT", "AEDAT") if d.object_type.value == "production_order" else (
                d.window_field,)
            if not any(params["date_from"] <= str(fila.get(c) or "") <= params["date_to"]
                       for c in campos):
                return False
        return True


# ── Dataset determinista ────────────────────────────────────────────────────

def default_dataset(client: str = "100", serie: str = "0000") -> dict[str, list[dict]]:
    """Dos sociedades de un mismo mandante, con maestros y documentos coherentes entre sí.

    Sociedad 1000 (centros 1100 y 1200) y sociedad 2000 (centro 2100). `serie` desplaza los
    números de documento para que dos pruebas no compartan órdenes.
    """
    hoy = _dt.date.today()

    def d(dias: int) -> str:
        return (hoy - _dt.timedelta(days=dias)).strftime("%Y%m%d")

    anio = str(hoy.year)
    m = client
    hembra, macho = "000000000000500001", "000000000000500002"
    alimento, vacuna = "000000000000600001", "000000000000700001"
    oc, oc_alimento, oc_b = f"45{serie}0001", f"45{serie}0002", f"45{serie}0901"
    sto = f"49{serie}0001"
    doc = lambda n: f"50{serie}{n:04d}"  # noqa: E731

    def material(matnr, texto, grupo, unidad, bukrs):
        return {"MANDT": m, "MATNR": matnr, "MAKTX": texto, "MTART": "HAWA", "MATKL": grupo,
                "MEINS": unidad, "LVORM": "", "LAEDA": d(40), "BUKRS": bukrs}

    def posicion(ebeln, ebelp, matnr, texto, werks, lgort, menge, meins, bukrs, aedat):
        return {"MANDT": m, "EBELN": ebeln, "EBELP": ebelp, "MATNR": matnr, "TXZ01": texto,
                "WERKS": werks, "LGORT": lgort, "MENGE": menge, "MEINS": meins, "EINDT": d(-3),
                "LOEKZ": "", "ELIKZ": "", "BUKRS": bukrs, "AEDAT": aedat}

    def movimiento(n, bwart, matnr, werks, lgort, cantidad, unidad, shkzg, bukrs, **extra):
        base = {"MANDT": m, "MBLNR": doc(n), "MJAHR": anio, "ZEILE": "0001", "BWART": bwart,
                "MATNR": matnr, "WERKS": werks, "LGORT": lgort, "UMWRK": "", "UMLGO": "",
                "CHARG": "", "ERFMG": cantidad, "ERFME": unidad, "MENGE": cantidad,
                "MEINS": unidad, "SHKZG": shkzg, "BUDAT": d(6), "BLDAT": d(6), "CPUDT": d(6),
                "EBELN": "", "EBELP": "00000", "AUFNR": "", "BUKRS": bukrs, "SMBLN": "",
                "SJAHR": "0000", "SMBLP": "0000"}
        base.update(extra)
        return base

    return {
        "company": [
            {"MANDT": m, "BUKRS": "1000", "BUTXT": "Avícola Demo Uno C.A.", "ORT01": "Valencia",
             "LAND1": "VE", "WAERS": "USD"},
            {"MANDT": m, "BUKRS": "2000", "BUTXT": "Avícola Demo Dos C.A.", "ORT01": "Maracay",
             "LAND1": "VE", "WAERS": "USD"},
        ],
        "plant": [
            {"MANDT": m, "WERKS": "1100", "NAME1": "Granja Reproductoras Norte",
             "NAME2": "Núcleo 1", "ORT01": "Valencia", "LAND1": "VE", "BUKRS": "1000"},
            {"MANDT": m, "WERKS": "1200", "NAME1": "Planta de Incubación", "NAME2": "",
             "ORT01": "Valencia", "LAND1": "VE", "BUKRS": "1000"},
            {"MANDT": m, "WERKS": "2100", "NAME1": "Granja Engorde Sur", "NAME2": "",
             "ORT01": "Maracay", "LAND1": "VE", "BUKRS": "2000"},
        ],
        "storage_location": [
            {"MANDT": m, "WERKS": "1100", "LGORT": "A001", "LGOBE": "Alimento", "BUKRS": "1000"},
            {"MANDT": m, "WERKS": "1100", "LGORT": "A002", "LGOBE": "Vacunas", "BUKRS": "1000"},
            {"MANDT": m, "WERKS": "1200", "LGORT": "I001", "LGOBE": "Incubación", "BUKRS": "1000"},
            {"MANDT": m, "WERKS": "2100", "LGORT": "B001", "LGOBE": "Alimento", "BUKRS": "2000"},
        ],
        "vendor": [
            {"MANDT": m, "LIFNR": "0000100001", "NAME1": "Genética Demo S.A.",
             "STCD1": "J-00000001-0", "LAND1": "VE", "SPERR": "", "LOEVM": "", "BUKRS": "1000"},
            {"MANDT": m, "LIFNR": "0000100002", "NAME1": "Alimentos Demo C.A.",
             "STCD1": "J-00000002-0", "LAND1": "VE", "SPERR": "", "LOEVM": "", "BUKRS": "1000"},
            {"MANDT": m, "LIFNR": "0000200001", "NAME1": "Proveedor Demo Sur",
             "STCD1": "J-00000003-0", "LAND1": "VE", "SPERR": "", "LOEVM": "", "BUKRS": "2000"},
        ],
        "material": [
            material(hembra, "Reproductora hembra", "AVES", "UN", "1000"),
            material(macho, "Reproductor macho", "AVES", "UN", "1000"),
            material(alimento, "Alimento iniciador", "ALIM", "KG", "1000"),
            material(vacuna, "Vacuna Newcastle", "VACU", "UN", "1000"),
            material(hembra, "Reproductora hembra", "AVES", "UN", "2000"),
            material(alimento, "Alimento iniciador", "ALIM", "KG", "2000"),
        ],
        "batch": [
            {"MANDT": m, "MATNR": hembra, "WERKS": "1100", "CHARG": "L26A001", "HSDAT": d(20),
             "VFDAT": "", "ERSDA": d(20), "LAEDA": d(20), "LVORM": "", "BUKRS": "1000"},
            {"MANDT": m, "MATNR": alimento, "WERKS": "1100", "CHARG": "AL26001", "HSDAT": d(15),
             "VFDAT": d(-90), "ERSDA": d(15), "LAEDA": d(15), "LVORM": "", "BUKRS": "1000"},
            {"MANDT": m, "MATNR": alimento, "WERKS": "1200", "CHARG": "AL26002", "HSDAT": d(15),
             "VFDAT": d(-90), "ERSDA": d(15), "LAEDA": d(15), "LVORM": "", "BUKRS": "1000"},
            {"MANDT": m, "MATNR": alimento, "WERKS": "2100", "CHARG": "AL26901", "HSDAT": d(15),
             "VFDAT": d(-90), "ERSDA": d(15), "LAEDA": d(15), "LVORM": "", "BUKRS": "2000"},
        ],
        "movement_type": [
            {"MANDT": m, "BWART": "101", "BTEXT": "Entrada de mercancías", "SPRAS": "S"},
            {"MANDT": m, "BWART": "102", "BTEXT": "Anulación de entrada", "SPRAS": "S"},
            {"MANDT": m, "BWART": "261", "BTEXT": "Salida para orden", "SPRAS": "S"},
            {"MANDT": m, "BWART": "303", "BTEXT": "Traslado entre centros", "SPRAS": "S"},
            {"MANDT": m, "BWART": "641", "BTEXT": "Traslado a stock en tránsito", "SPRAS": "S"},
            {"MANDT": m, "BWART": "101", "BTEXT": "Goods receipt", "SPRAS": "E"},
        ],
        "purchase_order": [
            {"MANDT": m, "EBELN": oc, "BUKRS": "1000", "BSTYP": "F", "BSART": "NB",
             "LIFNR": "0000100001", "EKORG": "1000", "BEDAT": d(12), "AEDAT": d(12),
             "WAERS": "USD", "LOEKZ": ""},
            {"MANDT": m, "EBELN": oc_alimento, "BUKRS": "1000", "BSTYP": "F", "BSART": "NB",
             "LIFNR": "0000100002", "EKORG": "1000", "BEDAT": d(8), "AEDAT": d(8),
             "WAERS": "USD", "LOEKZ": ""},
            {"MANDT": m, "EBELN": oc_b, "BUKRS": "2000", "BSTYP": "F", "BSART": "NB",
             "LIFNR": "0000200001", "EKORG": "2000", "BEDAT": d(9), "AEDAT": d(9),
             "WAERS": "USD", "LOEKZ": ""},
        ],
        "purchase_order_item": [
            posicion(oc, "00010", hembra, "Reproductora hembra", "1100", "A001", 1000, "UN",
                     "1000", d(12)),
            posicion(oc, "00020", macho, "Reproductor macho", "1100", "A001", 150, "UN",
                     "1000", d(12)),
            posicion(oc_alimento, "00010", alimento, "Alimento iniciador", "1100", "A001",
                     20000, "KG", "1000", d(8)),
            posicion(oc_b, "00010", hembra, "Reproductora hembra", "2100", "B001", 800, "UN",
                     "2000", d(9)),
        ],
        "purchase_order_history": [
            {"MANDT": m, "EBELN": oc, "EBELP": "00010", "ZEKKN": "00", "VGABE": "1",
             "GJAHR": anio, "BELNR": doc(1), "BUZEI": "0001", "BEWTP": "E", "BWART": "101",
             "BUDAT": d(6), "MENGE": 300, "SHKZG": "S", "MATNR": hembra, "WERKS": "1100",
             "LFBNR": "", "BUKRS": "1000"},
            {"MANDT": m, "EBELN": oc, "EBELP": "00010", "ZEKKN": "00", "VGABE": "1",
             "GJAHR": anio, "BELNR": doc(2), "BUZEI": "0001", "BEWTP": "E", "BWART": "102",
             "BUDAT": d(5), "MENGE": 100, "SHKZG": "H", "MATNR": hembra, "WERKS": "1100",
             "LFBNR": doc(1), "BUKRS": "1000"},
        ],
        "production_order": [
            {"MANDT": m, "AUFNR": f"0010{serie}0001", "AUART": "PP01", "BUKRS": "1000",
             "WERKS": "1100", "MATNR": hembra, "CHARG": "L26A001", "LGORT": "A001",
             "GSTRP": d(10), "GLTRP": d(-20), "GAMNG": 5000, "GMEIN": "UN", "LOEKZ": "",
             "PHAS1": "X", "PHAS2": "", "PHAS3": "", "ERDAT": d(11), "AEDAT": d(9)},
            {"MANDT": m, "AUFNR": f"0010{serie}0901", "AUART": "PP01", "BUKRS": "2000",
             "WERKS": "2100", "MATNR": hembra, "CHARG": "", "LGORT": "B001",
             "GSTRP": d(10), "GLTRP": d(-20), "GAMNG": 900, "GMEIN": "UN", "LOEKZ": "",
             "PHAS1": "X", "PHAS2": "", "PHAS3": "", "ERDAT": d(11), "AEDAT": d(9)},
        ],
        "transfer_order": [
            {"MANDT": m, "EBELN": sto, "EBELP": "00010", "BUKRS": "1000", "BSART": "UB",
             "RESWK": "1100", "RESLO": "A001", "WERKS": "1200", "LGORT": "I001",
             "MATNR": alimento, "TXZ01": "Alimento iniciador", "MENGE": 5000, "MEINS": "KG",
             "BEDAT": d(7), "AEDAT": d(7), "LOEKZ": "", "ELIKZ": ""},
        ],
        "outbound_order": [
            {"MANDT": m, "VBELN": f"80{serie}0001", "POSNR": "000010", "LFART": "LF",
             "VSTEL": "1100", "KUNNR": "0000300001", "WADAT": d(3), "WADAT_IST": d(3),
             "ERDAT": d(4), "MATNR": hembra, "ARKTX": "Reproductora hembra", "WERKS": "1100",
             "LGORT": "A001", "CHARG": "L26A001", "LFIMG": 400, "VRKME": "UN", "VGBEL": "",
             "VGPOS": "000000", "BUKRS": "1000"},
        ],
        "material_movement": [
            movimiento(1, "101", hembra, "1100", "A001", 300, "UN", "S", "1000",
                       CHARG="L26A001", EBELN=oc, EBELP="00010"),
            movimiento(2, "102", hembra, "1100", "A001", 100, "UN", "H", "1000",
                       CHARG="L26A001", EBELN=oc, EBELP="00010", SMBLN=doc(1), SJAHR=anio,
                       SMBLP="0001", BUDAT=d(5), BLDAT=d(5), CPUDT=d(5)),
            movimiento(3, "101", alimento, "1100", "A001", 20000, "KG", "S", "1000",
                       EBELN=oc_alimento, EBELP="00010"),
            movimiento(4, "101", alimento, "1200", "I001", 5000, "KG", "S", "1000",
                       EBELN=sto, EBELP="00010"),
            movimiento(901, "101", hembra, "2100", "B001", 200, "UN", "S", "2000",
                       EBELN=oc_b, EBELP="00010"),
        ],
    }

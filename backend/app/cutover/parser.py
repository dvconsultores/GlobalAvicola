"""GA-REQ-061 · Cutover — parser Excel v1 (DATA, jamás código: sin macros ni fórmulas).

El archivo **nunca** toca tablas operacionales (AC43/44): el parser produce filas
normalizadas para el staging. Semántica de UNKNOWN en la plantilla:
**celda vacía = UNKNOWN · `0` explícito = cero conocido · `N/A` = NOT_APPLICABLE**.
"""
from __future__ import annotations

import io
from datetime import date, datetime
from typing import Any, Optional

SUPPORTED_TEMPLATE_VERSIONS = {"v1"}

#: Columnas núcleo de la plantilla v1 (las variantes por BU se añadirán con su plantilla).
COLUMNAS_V1 = [
    "legacy_lot_code",
    "real_start_date",
    "live_males",
    "live_females",
    "historical_mortality_males",
    "historical_mortality_females",
    "farm_code",
    "notes",
]

_REQUERIDAS = ("legacy_lot_code", "real_start_date", "live_males", "live_females")
_ENTERAS = ("live_males", "live_females", "historical_mortality_males", "historical_mortality_females")


class CutoverParseError(Exception):
    """Error de archivo/plantilla — viaja como `error_code` estructurado."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _texto(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _fecha(v: Any) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v).strip())


def _entero(v: Any) -> int:
    if isinstance(v, bool):
        raise ValueError("booleano")
    return int(v)


def _error(row: int, column: str, field: str, code: str, message: str, received: Any) -> dict:
    return {
        "row_number": row,
        "column": column,
        "field": field,
        "error_code": code,
        "message": message,
        "received_value": None if received is None else str(received),
    }


def parse_cutover_workbook(content: bytes) -> dict:
    """Parsea el libro y devuelve meta + filas normalizadas con errores estructurados.

    Raises:
        CutoverParseError: archivo ilegible, hojas ausentes o `template_version` no soportada.
    """
    try:
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except CutoverParseError:
        raise
    except Exception as exc:  # archivo corrupto / no-xlsx
        raise CutoverParseError("INVALID_FILE", f"No se pudo leer el archivo: {exc}") from exc

    if "Meta" not in wb.sheetnames or "Datos" not in wb.sheetnames:
        raise CutoverParseError("INVALID_FILE", "El archivo no trae las hojas 'Meta' y 'Datos'.")

    meta: dict[str, Optional[str]] = {}
    for fila in wb["Meta"].iter_rows(values_only=True):
        if fila and _texto(fila[0]):
            meta[str(fila[0]).strip()] = _texto(fila[1]) if len(fila) > 1 else None

    version = meta.get("template_version")
    if version not in SUPPORTED_TEMPLATE_VERSIONS:
        raise CutoverParseError(
            "TEMPLATE_VERSION_UNSUPPORTED",
            f"Versión de plantilla no soportada: {version!r} (soportadas: {sorted(SUPPORTED_TEMPLATE_VERSIONS)})",
        )
    business_unit = meta.get("business_unit")
    if not business_unit:
        raise CutoverParseError("REQUIRED_FIELD_MISSING", "La hoja 'Meta' no declara 'business_unit'.")

    hoja = wb["Datos"]
    filas = hoja.iter_rows(values_only=True)
    encabezado = next(filas, None)
    if not encabezado:
        raise CutoverParseError("INVALID_FILE", "La hoja 'Datos' está vacía.")
    columnas = {str(c).strip(): i for i, c in enumerate(encabezado) if c is not None}

    resultado: list[dict] = []
    for numero_fila, fila in enumerate(filas, start=2):
        if fila is None or all(c is None or str(c).strip() == "" for c in fila):
            continue  # fila totalmente vacía: no es dato
        crudos = {col: (fila[i] if i < len(fila) else None) for col, i in columnas.items()}
        errores: list[dict] = []
        normalizado: dict[str, Any] = {}

        codigo = _texto(crudos.get("legacy_lot_code"))
        if not codigo:
            errores.append(_error(numero_fila, "legacy_lot_code", "legacy_lot_code",
                                  "REQUIRED_FIELD_MISSING", "Falta el código externo del lote.", crudos.get("legacy_lot_code")))
        else:
            normalizado["legacy_lot_code"] = codigo

        if crudos.get("real_start_date") is None or str(crudos["real_start_date"]).strip() in ("", "None"):
            errores.append(_error(numero_fila, "real_start_date", "real_start_date",
                                  "REQUIRED_FIELD_MISSING", "Falta la fecha real de inicio.", crudos.get("real_start_date")))
        else:
            try:
                normalizado["real_start_date"] = _fecha(crudos["real_start_date"]).isoformat()
            except (ValueError, TypeError):
                errores.append(_error(numero_fila, "real_start_date", "real_start_date",
                                      "INVALID_DATE", "Fecha inválida (se espera ISO AAAA-MM-DD).", crudos.get("real_start_date")))

        for campo in _ENTERAS:
            valor = crudos.get(campo)
            texto = None if valor is None else str(valor).strip()
            if texto is None or texto in ("", "None"):
                if campo in _REQUERIDAS:
                    errores.append(_error(numero_fila, campo, campo, "REQUIRED_FIELD_MISSING",
                                          f"Falta {campo} (0 explícito es válido; vacío es UNKNOWN).", valor))
                else:
                    normalizado[campo] = None  # UNKNOWN explícito
                continue
            if texto.upper() == "N/A":
                normalizado[campo] = None  # NOT_APPLICABLE — nunca cero
                continue
            try:
                entero = _entero(valor)
                if entero < 0:
                    raise ValueError("negativo")
                normalizado[campo] = entero
            except (ValueError, TypeError):
                errores.append(_error(numero_fila, campo, campo, "INVALID_NUMBER",
                                      "Número entero ≥ 0 esperado.", valor))

        normalizado["farm_code"] = _texto(crudos.get("farm_code"))
        normalizado["notes"] = _texto(crudos.get("notes"))
        resultado.append({
            "row_number": numero_fila,
            "raw": {k: (None if v is None else str(v)) for k, v in crudos.items()},
            "normalized": normalizado,
            "errors": errores,
        })

    return {"template_version": version, "business_unit": business_unit, "rows": resultado}

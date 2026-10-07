"""Servicio inbound SAP HANA — SPEC 005 `§2`, `§17`…`§24`, `§33`…`§35`, `§42`.

    exigir empresa → readiness → sociedades mapeadas → bloqueo por objeto
      → por cada sociedad: páginas acotadas → contrato de columnas → RAW (hash / versión)
      → validación → mapping → staging → promoción → watermark → auditoría

Cada objeto se sincroniza dentro de un savepoint: si su batch falla, sus filas no quedan a
medias, su watermark no se mueve y los demás objetos siguen su curso. El job fallido sí queda
registrado, con el error saneado.
"""
from __future__ import annotations

import datetime as _dt
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from fastapi import HTTPException, status
from sqlalchemy import false, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ....audit.helpers import audit_accion
from ....audit.models import AuditAction, AuditModule
from . import adapter as adapter_module
from . import promotion
from .adapter import SapInboundAdapter
from .errors import ErrorCode, SapInboundError, sanitize
from .mapping import FOREIGN, MappingContext, load_context
from .models import (
    ENTITY_COMPANY_CODE, ENTITY_PLANT, ENTITY_STORAGE_LOCATION, JOB_COMPLETED, JOB_FAILED,
    JOB_IN_PROGRESS, JOB_PARTIAL, JOB_SKIPPED, M_MAPPED, M_PENDING_MAPPING, P_BLOCKED,
    P_PENDING, P_PROMOTED, P_READY, P_STAGED_ONLY, P_SUPERSEDED, SOURCE_SYSTEM, V_INVALID,
    V_VALID, SapEntityMapping, SapInboundRecord, SapInboundSyncJob, SapInboundWatermark,
)
from .registry import (
    REGISTRY, SNAPSHOT, SYNC_ORDER, WINDOW, HanaObject, QueryDefinition, expand_objects,
    get_definition,
)
from .settings import HanaSettings
from .staging import canonical_hash, source_key, stage

logger = logging.getLogger("ga.sap.inbound")

#: Ventana máxima que una petición puede pedir. Más que esto es un scan encubierto.
MAX_WINDOW_DAYS = 366
_GRUPO_OC = (HanaObject.PURCHASE_ORDER, HanaObject.PURCHASE_ORDER_ITEM,
             HanaObject.PURCHASE_ORDER_HISTORY)

#: Resultado de la última consulta de humo, por huella de configuración. Vive en el proceso:
#: «conectado» significa «este proceso conectó», no una afirmación persistente.
_ULTIMA_COMPROBACION: dict[tuple, dict[str, Any]] = {}


@dataclass
class _Contadores:
    rows_read: int = 0
    rows_raw: int = 0
    rows_noop: int = 0
    rows_valid: int = 0
    rows_invalid: int = 0
    rows_pending_mapping: int = 0
    rows_promoted: int = 0
    rows_rejected: int = 0
    partial: bool = False
    por_ambito: dict[str, int] = field(default_factory=dict)
    ventana: tuple[str | None, str | None] = (None, None)

    def volcar(self, job: SapInboundSyncJob) -> None:
        for campo in ("rows_read", "rows_raw", "rows_noop", "rows_valid", "rows_invalid",
                      "rows_pending_mapping", "rows_promoted", "rows_rejected"):
            setattr(job, campo, getattr(self, campo))


def _ahora() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _fecha(valor: Any, nombre: str) -> _dt.date | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, _dt.datetime):
        return valor.date()
    if isinstance(valor, _dt.date):
        return valor
    try:
        return _dt.date.fromisoformat(str(valor))
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            f"{nombre} debe ser una fecha AAAA-MM-DD") from None


class SapInboundService:
    def __init__(self, db: AsyncSession | None, current_user: dict[str, Any], *,
                 adapter: SapInboundAdapter | None = None,
                 cfg: HanaSettings | None = None) -> None:
        self.db = db
        self.current_user = current_user or {}
        self.company_id: int | None = self.current_user.get("company_id")
        self.actor_id: int | None = self.current_user.get("id")
        self.cfg = cfg or HanaSettings.from_settings()
        self._adapter = adapter
        self._tocadas_oc: set[str] = set()
        self._tocadas_sto: set[str] = set()

    # ── Contexto (R-201) ──────────────────────────────────────────────────────

    def _require_company_id(self) -> int:
        """Sin empresa efectiva no se sincroniza ni se configura nada. Fail-closed."""
        if self.company_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Operación requiere una empresa asignada. Los super administradores "
                       "deben seleccionar una empresa.")
        return self.company_id

    def _de_la_empresa(self, columna):
        """Predicado de empresa de las lecturas: sin contexto, ninguna fila."""
        return columna == self.company_id if self.company_id is not None else false()

    def _adaptador(self) -> SapInboundAdapter:
        if self._adapter is None:
            self._adapter = adapter_module.build_adapter(self.cfg)
        return self._adapter

    # ── Readiness y conexión ──────────────────────────────────────────────────

    def _huella(self) -> tuple:
        c = self.cfg
        return (c.driver, c.host, c.port, c.user, c.schema, c.client)

    def readiness(self) -> dict[str, Any]:
        """Estado del conector **sin tocar la red**. Funciona sin credenciales."""
        cfg = self.cfg
        faltan, tls = cfg.missing(), cfg.tls_violations()
        ultima = _ULTIMA_COMPROBACION.get(self._huella(), {}) if cfg.configured else {}
        conectado = bool(ultima.get("connected"))
        if faltan:
            estado = "PENDING_CREDENTIALS"
        elif tls:
            estado = "TLS_POLICY_VIOLATION"
        elif conectado:
            estado = "SIMULATED_CONNECTED" if cfg.simulated else "CONNECTED"
        elif ultima:
            estado = "CONNECTION_FAILED"
        else:
            estado = "CONFIGURED_NOT_TESTED"
        return {
            "phase": "READ_ONLY_INBOUND",
            "adapter": "SAP_HANA_CLOUD_READ_ONLY_V2",
            "driver": cfg.driver,
            "simulated": cfg.simulated,
            "driver_available": True if cfg.simulated else adapter_module.driver_available(),
            "configured": cfg.configured,
            "missing": faltan,
            "tls": {"encrypt": True, "validate_certificate": True},
            "tls_violations": tls,
            "connection_tested": bool(ultima),
            "connected": conectado,
            "last_checked_at": ultima.get("checked_at"),
            "error_code": ultima.get("error_code"),
            "sync_enabled": bool(cfg.sync_enabled),
            "outbound_enabled": bool(cfg.outbound_enabled),
            "write_operations_allowed": False,
            "status": estado,
        }

    async def check_connection(self) -> dict[str, Any]:
        """Consulta de humo, solo si hay configuración. Nunca afirma lo que no ocurrió."""
        if not self.cfg.configured:
            return self.readiness()
        resultado: dict[str, Any] = {"checked_at": _ahora().isoformat(timespec="seconds")}
        try:
            await self._adaptador().check_connection()
            resultado["connected"] = True
        except SapInboundError as exc:
            resultado.update(connected=False, error_code=exc.code.value)
        _ULTIMA_COMPROBACION[self._huella()] = resultado
        estado = self.readiness()
        if not resultado["connected"]:
            estado["error_message"] = "No se pudo establecer la conexión con SAP HANA."
        return estado

    def list_objects(self) -> list[dict[str, Any]]:
        """Catálogo de objetos. Describe el contrato; nunca expone el SQL."""
        return [{
            "object_type": d.object_type.value, "query_id": d.query_id,
            "tables": list(d.tables), "source_status": d.source_status,
            "source_key_fields": list(d.source_key_fields), "strategy": d.strategy,
            "watermark_candidate": d.watermark_candidate, "scope": d.scope,
            "max_page_size": d.max_page_size, "promotes_to": d.promotes_to,
            "notes": d.notes,
        } for d in (REGISTRY[o] for o in SYNC_ORDER)]

    # ── Sincronización ────────────────────────────────────────────────────────

    def _ventana_pedida(self, date_from: Any, date_to: Any) -> tuple[_dt.date, _dt.date] | None:
        desde, hasta = _fecha(date_from, "date_from"), _fecha(date_to, "date_to")
        if desde is None and hasta is None:
            return None
        hasta = hasta or _dt.date.today()
        desde = desde or (hasta - _dt.timedelta(days=self.cfg.lookback_days))
        if desde > hasta:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                "date_from no puede ser posterior a date_to")
        if (hasta - desde).days > MAX_WINDOW_DAYS:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"La ventana no puede superar {MAX_WINDOW_DAYS} días.")
        return desde, hasta

    async def sync(self, object_types: Optional[Iterable[HanaObject | str]] = None, *,
                   date_from: Any = None, date_to: Any = None,
                   trigger: str = "manual") -> list[SapInboundSyncJob]:
        company_id = self._require_company_id()          # antes de leer nada (R-201)
        try:
            objetos = expand_objects(object_types)
        except ValueError:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                "Objeto SAP no reconocido.") from None
        ventana = self._ventana_pedida(date_from, date_to)
        peticion = str(uuid.uuid4())

        ctx: MappingContext | None = None
        previo: SapInboundError | None = None
        if not self.cfg.configured:
            try:
                self.cfg.connect_options()
            except SapInboundError as exc:
                previo = exc
        else:
            ctx = await load_context(self.db, company_id, self.cfg)
            if not ctx.company_codes:
                previo = SapInboundError(
                    ErrorCode.SAP_MAPPING_PENDING,
                    "La empresa no tiene ninguna sociedad SAP mapeada (o está fuera de "
                    "SAP_HANA_COMPANY_CODES). No se consulta SAP.")
            else:
                try:
                    self._adaptador()
                except SapInboundError as exc:
                    previo = exc

        jobs: list[SapInboundSyncJob] = []
        por_objeto: dict[HanaObject, SapInboundSyncJob] = {}
        for objeto in objetos:
            definicion = get_definition(objeto)
            job = SapInboundSyncJob(
                sync_request_id=peticion, company_id=company_id, source_system=SOURCE_SYSTEM,
                object_type=objeto.value, query_id=definicion.query_id, trigger=trigger,
                status=JOB_IN_PROGRESS, initiated_by_id=self.actor_id, started_at=_ahora(),
                filters=self._filtros(ctx, None), rows_read=0, rows_raw=0, rows_noop=0,
                rows_valid=0, rows_invalid=0, rows_pending_mapping=0, rows_promoted=0,
                rows_rejected=0)
            self.db.add(job)
            await self.db.flush()
            jobs.append(job)
            por_objeto[objeto] = job
            if previo is not None:
                self._cerrar(job, JOB_FAILED, previo.code, previo.message)
                continue
            await self._sincronizar_objeto(job, objeto, definicion, ctx, ventana)

        if previo is None:
            await self._promover_ordenes_de_compra(ctx, por_objeto)
        await self.db.flush()
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.IMPORT,
            modulo=AuditModule.SAP, entity_type="sap_inbound_sync", entity_id=peticion,
            company_id=company_id,
            new_values={"trigger": trigger, "jobs": [
                {"object_type": j.object_type, "status": j.status, "rows_read": j.rows_read,
                 "rows_raw": j.rows_raw, "rows_promoted": j.rows_promoted,
                 "error_code": j.error_code} for j in jobs]})
        return jobs

    def _filtros(self, ctx: MappingContext | None,
                 ventana: tuple[str | None, str | None] | None) -> dict[str, Any]:
        filtros: dict[str, Any] = {
            "client": self.cfg.client or None,
            "company_codes": list(ctx.company_codes) if ctx else [],
            "page_size": self.cfg.page_size, "max_rows": self.cfg.max_rows,
            "language": self.cfg.language,
        }
        if ventana and ventana[0]:
            filtros["date_from"], filtros["date_to"] = ventana
        return filtros

    def _cerrar(self, job: SapInboundSyncJob, estado: str, codigo: ErrorCode | None = None,
                mensaje: str | None = None) -> None:
        job.status = estado
        job.error_code = codigo.value if codigo else None
        job.error_message = sanitize(mensaje, self.cfg.secrets()) if mensaje else None
        job.completed_at = _ahora()

    async def _sincronizar_objeto(self, job: SapInboundSyncJob, objeto: HanaObject,
                                  definicion: QueryDefinition, ctx: MappingContext,
                                  ventana: tuple[_dt.date, _dt.date] | None) -> None:
        # Un mismo objeto de una misma empresa no se sincroniza dos veces a la vez: el
        # scheduler y un sync manual no se pisan. El bloqueo se libera con la transacción.
        libre = (await self.db.execute(
            text("SELECT pg_try_advisory_xact_lock(:a, :b)"),
            {"a": 50_050_000 + SYNC_ORDER.index(objeto), "b": job.company_id})).scalar()
        if not libre:
            self._cerrar(job, JOB_SKIPPED, None,
                         "Ya hay una sincronización de este objeto en curso.")
            return

        cont = _Contadores()
        fallo: tuple[ErrorCode, str] | None = None
        try:
            async with self.db.begin_nested():
                await self._extraer(job, objeto, definicion, ctx, ventana, cont)
                await self._procesar(objeto, ctx, cont)
                if objeto is HanaObject.TRANSFER_ORDER:
                    await self._promover_traslados(ctx, cont)
                if not cont.partial:
                    await self._avanzar_watermarks(job, definicion, ctx, cont)
        except SapInboundError as exc:
            fallo = (exc.code, exc.message)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001 — el fallo de un objeto no tumba la petición
            logger.exception("Fallo inesperado sincronizando %s", objeto.value)
            fallo = (ErrorCode.SAP_INTERNAL_ERROR, f"Fallo interno: {type(exc).__name__}")

        if fallo is not None:
            # El savepoint deshizo las filas y el watermark de este objeto. Lo leído se
            # conserva en el job como dato de diagnóstico; lo persistido es cero.
            leidas = cont.rows_read
            cont = _Contadores(rows_read=leidas, ventana=cont.ventana)
            await self.db.refresh(job)
        cont.volcar(job)
        job.watermark_from, job.watermark_to = cont.ventana
        job.filters = self._filtros(ctx, cont.ventana if definicion.strategy == WINDOW else None)
        if fallo is not None:
            self._cerrar(job, JOB_FAILED, *fallo)
        else:
            self._cerrar(job, JOB_PARTIAL if cont.partial else JOB_COMPLETED,
                         None, "Tope de filas por sincronización alcanzado."
                         if cont.partial else None)
        await self.db.flush()

    # ── Extracción → RAW ──────────────────────────────────────────────────────

    def _ambito(self, bukrs: str | None) -> str:
        return f"client:{self.cfg.client}|bukrs:{bukrs or '*'}"

    async def _watermark(self, company_id: int, objeto: HanaObject,
                         ambito: str) -> SapInboundWatermark | None:
        return (await self.db.execute(
            select(SapInboundWatermark).where(
                SapInboundWatermark.company_id == company_id,
                SapInboundWatermark.source_system == SOURCE_SYSTEM,
                SapInboundWatermark.object_type == objeto.value,
                SapInboundWatermark.scope_key == ambito))).scalar_one_or_none()

    async def _ventana_de(self, job: SapInboundSyncJob, objeto: HanaObject, ambito: str,
                          pedida: tuple[_dt.date, _dt.date] | None) -> tuple[str, str]:
        """Ventana del objeto: la pedida, o `última marca − solape … hoy`. Nunca abierta."""
        if pedida is not None:
            desde, hasta = pedida
        else:
            hasta = _dt.date.today()
            ancla = hasta
            marca = await self._watermark(job.company_id, objeto, ambito)
            if marca is not None and len(marca.watermark_value) == 8 \
                    and marca.watermark_value.isdigit():
                ancla = min(hasta, _dt.datetime.strptime(marca.watermark_value, "%Y%m%d").date())
            desde = max(ancla - _dt.timedelta(days=self.cfg.lookback_days),
                        hasta - _dt.timedelta(days=MAX_WINDOW_DAYS))
        return desde.strftime("%Y%m%d"), hasta.strftime("%Y%m%d")

    async def _extraer(self, job: SapInboundSyncJob, objeto: HanaObject,
                       definicion: QueryDefinition, ctx: MappingContext,
                       pedida: tuple[_dt.date, _dt.date] | None, cont: _Contadores) -> None:
        adaptador = self._adaptador()
        ambitos = [None] if definicion.scope == "client" else list(ctx.company_codes)
        vistos: dict[str, SapInboundRecord] = {}
        for bukrs in ambitos:
            ambito = self._ambito(bukrs)
            params: dict[str, Any] = {"mandt": self.cfg.client, **definicion.fixed_params}
            if "bukrs" in definicion.required_params:
                params["bukrs"] = bukrs
            if "langu" in definicion.required_params:
                params["langu"] = self.cfg.language
            if definicion.strategy == WINDOW:
                desde, hasta = await self._ventana_de(job, objeto, ambito, pedida)
                params["date_from"], params["date_to"] = desde, hasta
                previo_desde, previo_hasta = cont.ventana
                cont.ventana = (min(filter(None, (previo_desde, desde))),
                                max(filter(None, (previo_hasta, hasta))))

            leidas_ambito = 0
            offset = 0
            while True:
                restante = self.cfg.max_rows - cont.rows_read
                if restante <= 0:
                    cont.partial = True
                    break
                limite = max(1, min(self.cfg.page_size, definicion.max_page_size, restante))
                filas = await adaptador.fetch_page(objeto, params, limit=limite, offset=offset)
                cont.rows_read += len(filas)
                leidas_ambito += len(filas)
                await self._persistir_pagina(job, objeto, definicion, filas, bukrs, ctx, cont,
                                             vistos)
                if len(filas) < limite:
                    break
                offset += limite
            cont.por_ambito[ambito] = leidas_ambito
            if cont.partial:
                break

    async def _persistir_pagina(self, job: SapInboundSyncJob, objeto: HanaObject,
                                definicion: QueryDefinition, filas: list[dict[str, Any]],
                                bukrs: str | None, ctx: MappingContext, cont: _Contadores,
                                vistos: dict[str, SapInboundRecord]) -> None:
        if not filas:
            return
        claves = [source_key(definicion, f) for f in filas]
        pendientes = [c for c in claves if c not in vistos]
        if pendientes:
            existentes = (await self.db.execute(
                select(SapInboundRecord).where(
                    SapInboundRecord.company_id == job.company_id,
                    SapInboundRecord.source_system == SOURCE_SYSTEM,
                    SapInboundRecord.object_type == objeto.value,
                    SapInboundRecord.is_current.is_(True),
                    SapInboundRecord.source_key.in_(pendientes)))).scalars().all()
            vistos.update({r.source_key: r for r in existentes})

        for clave, fila in zip(claves, filas):
            sociedad = (str(fila.get("BUKRS") or "").strip() or bukrs)
            if sociedad and sociedad in ctx.foreign_company_codes:
                # Es de otra empresa GA: no entra en el RAW de esta ni como pendiente.
                cont.rows_rejected += 1
                continue
            huella = canonical_hash(fila)
            vigente = vistos.get(clave)
            if vigente is not None and vigente.payload_hash == huella:
                cont.rows_noop += 1               # misma clave, mismo hash: no-op
                continue
            version = 1
            if vigente is not None:
                # Misma clave, hash nuevo: versión nueva. La anterior se conserva intacta.
                vigente.is_current = False
                vigente.promotion_status = P_SUPERSEDED
                version = vigente.version + 1
                await self.db.flush()             # libera el índice único de «vigente»
            registro = SapInboundRecord(
                sync_job_id=job.id, company_id=job.company_id, source_system=SOURCE_SYSTEM,
                object_type=objeto.value, source_key=clave, client=self.cfg.client,
                company_code=sociedad or None,
                plant_code=(str(fila.get("WERKS") or "").strip() or None),
                payload_json=fila, payload_hash=huella, version=version, is_current=True,
                extracted_at=_ahora(), validation_status="PENDING", mapping_status="PENDING",
                promotion_status=P_PENDING)
            self.db.add(registro)
            vistos[clave] = registro
            cont.rows_raw += 1
            self._anotar_tocada(objeto, clave)
        await self.db.flush()

    def _anotar_tocada(self, objeto: HanaObject, clave: str) -> None:
        partes = clave.split("|")
        if objeto in _GRUPO_OC and len(partes) > 1:
            self._tocadas_oc.add(partes[1])
        elif objeto is HanaObject.TRANSFER_ORDER and len(partes) > 1:
            self._tocadas_sto.add(partes[1])

    # ── Validación → mapping → staging → promoción ────────────────────────────

    async def _procesar(self, objeto: HanaObject, ctx: MappingContext,
                        cont: _Contadores) -> None:
        """Recorre lo que aún no tiene un estado final. Incluye lo retenido en pasadas
        anteriores: un mapping añadido después libera la fila aunque su hash no haya cambiado."""
        registros = (await self.db.execute(
            select(SapInboundRecord).where(
                SapInboundRecord.company_id == ctx.company_id,
                SapInboundRecord.source_system == SOURCE_SYSTEM,
                SapInboundRecord.object_type == objeto.value,
                SapInboundRecord.is_current.is_(True),
                SapInboundRecord.validation_status != V_INVALID,
                SapInboundRecord.promotion_status.in_((P_PENDING, P_READY, P_BLOCKED)),
            ).order_by(SapInboundRecord.id))).scalars().all()

        for rec in registros:
            preparado = stage(objeto, rec.payload_json)
            if preparado.errors:
                rec.validation_status = V_INVALID
                rec.error_code = ErrorCode.SAP_VALIDATION_ERROR.value
                rec.error_message = "; ".join(preparado.errors)[:500]
                cont.rows_invalid += 1
                continue
            if rec.validation_status != V_VALID:
                rec.validation_status = V_VALID
            if rec.staged_json != preparado.dto:
                rec.staged_json = preparado.dto
            cont.rows_valid += 1

            estado, motivo = ctx.resolve(rec.company_code, preparado.plants)
            if estado != M_MAPPED:
                # `FOREIGN` no llega aquí salvo que el mapping cambiara después de extraer:
                # se trata igual, sin promoción.
                self._retener(rec, motivo if estado != FOREIGN else "sociedad de otra empresa")
                cont.rows_pending_mapping += 1
                continue
            if rec.mapping_status != M_MAPPED:
                rec.mapping_status = M_MAPPED
                self._anotar_tocada(objeto, rec.source_key)

            if objeto in promotion.STAGED_ONLY:
                self._estado(rec, P_STAGED_ONLY)
            elif objeto in promotion.COMPOSED:
                self._estado(rec, P_READY)        # la compone el paso de su documento
            elif await promotion.promote_simple(self.db, objeto, rec, ctx, self.actor_id):
                cont.rows_promoted += 1
        await self.db.flush()

    @staticmethod
    def _estado(rec: SapInboundRecord, estado: str) -> None:
        for campo, valor in (("promotion_status", estado), ("error_code", None),
                             ("error_message", None)):
            if getattr(rec, campo) != valor:
                setattr(rec, campo, valor)

    @staticmethod
    def _retener(rec: SapInboundRecord, motivo: str) -> None:
        for campo, valor in (("mapping_status", M_PENDING_MAPPING),
                             ("promotion_status", P_PENDING),
                             ("error_code", ErrorCode.SAP_MAPPING_PENDING.value),
                             ("error_message", motivo)):
            if getattr(rec, campo) != valor:
                setattr(rec, campo, valor)

    async def _promover_traslados(self, ctx: MappingContext, cont: _Contadores) -> None:
        pendientes = (await self.db.execute(
            select(SapInboundRecord.source_key).where(
                SapInboundRecord.company_id == ctx.company_id,
                SapInboundRecord.object_type == HanaObject.TRANSFER_ORDER.value,
                SapInboundRecord.is_current.is_(True),
                SapInboundRecord.promotion_status.in_((P_READY, P_BLOCKED)),
            ))).scalars().all()
        documentos = set(self._tocadas_sto) | {k.split("|")[1] for k in pendientes}
        for ebeln in sorted(documentos):
            cont.rows_promoted += await promotion.promote_transfer_order(
                self.db, ctx.company_id, self.cfg.client, ebeln, self.actor_id)
        await self.db.flush()

    async def _promover_ordenes_de_compra(
            self, ctx: MappingContext, jobs: dict[HanaObject, SapInboundSyncJob]) -> None:
        """Compone las OC una vez que cabecera y posiciones de esta pasada están en RAW.

        Si la cabecera o las posiciones fallaron no se compone nada: una OC armada con la mitad
        de sus datos tendría una cantidad que `BR-18` tomaría por buena.
        """
        cabeceras_job = jobs.get(HanaObject.PURCHASE_ORDER)
        posiciones_job = jobs.get(HanaObject.PURCHASE_ORDER_ITEM)
        if cabeceras_job is None or posiciones_job is None:
            return
        if JOB_FAILED in (cabeceras_job.status, posiciones_job.status) or \
                JOB_SKIPPED in (cabeceras_job.status, posiciones_job.status):
            return
        try:
            async with self.db.begin_nested():
                condicion = SapInboundRecord.promotion_status.in_((P_READY, P_BLOCKED))
                if self._tocadas_oc:
                    claves = [f"{self.cfg.client}|{e}" for e in self._tocadas_oc]
                    condicion = condicion | SapInboundRecord.source_key.in_(claves)
                cabeceras = (await self.db.execute(
                    select(SapInboundRecord).where(
                        SapInboundRecord.company_id == ctx.company_id,
                        SapInboundRecord.object_type == HanaObject.PURCHASE_ORDER.value,
                        SapInboundRecord.is_current.is_(True),
                        SapInboundRecord.validation_status == V_VALID,
                        SapInboundRecord.mapping_status == M_MAPPED,
                        condicion,
                    ).order_by(SapInboundRecord.source_key))).scalars().all()
                promovidas = 0
                for cabecera in cabeceras:
                    promovidas += await promotion.promote_purchase_order(
                        self.db, cabecera, self.actor_id)
                await self.db.flush()
            cabeceras_job.rows_promoted = (cabeceras_job.rows_promoted or 0) + promovidas
        except Exception as exc:  # noqa: BLE001
            logger.exception("Fallo componiendo órdenes de compra")
            await self.db.refresh(cabeceras_job)
            self._cerrar(cabeceras_job, JOB_FAILED, ErrorCode.SAP_INTERNAL_ERROR,
                         f"Fallo interno al promover: {type(exc).__name__}")

    async def _avanzar_watermarks(self, job: SapInboundSyncJob, definicion: QueryDefinition,
                                  ctx: MappingContext, cont: _Contadores) -> None:
        """Solo aquí, dentro del savepoint y después de persistir: si algo falla antes, la
        marca no existe; si falla después, el rollback se la lleva con las filas."""
        valor = cont.ventana[1] if definicion.strategy == WINDOW else \
            _ahora().isoformat(timespec="seconds")
        if definicion.strategy == SNAPSHOT:
            cont.ventana = (None, valor)
        for ambito, leidas in cont.por_ambito.items():
            marca = await self._watermark(job.company_id, definicion.object_type, ambito)
            if marca is None:
                marca = SapInboundWatermark(
                    company_id=job.company_id, source_system=SOURCE_SYSTEM,
                    object_type=definicion.object_type.value, scope_key=ambito,
                    watermark_value=valor)
                self.db.add(marca)
            else:
                if definicion.strategy == SNAPSHOT and cont.ventana[0] is None:
                    cont.ventana = (marca.watermark_value, valor)
                marca.watermark_value = valor
            marca.last_success_at = _ahora()
            marca.last_record_count = leidas
        await self.db.flush()

    # ── Lecturas ──────────────────────────────────────────────────────────────

    async def list_jobs(self, limit: int = 20, offset: int = 0,
                        object_type: str | None = None) -> tuple[list[SapInboundSyncJob], int]:
        donde = [self._de_la_empresa(SapInboundSyncJob.company_id)]
        if object_type:
            donde.append(SapInboundSyncJob.object_type == object_type)
        total = (await self.db.execute(
            select(func.count()).select_from(SapInboundSyncJob).where(*donde))).scalar() or 0
        filas = (await self.db.execute(
            select(SapInboundSyncJob).where(*donde)
            .order_by(SapInboundSyncJob.id.desc()).offset(offset).limit(limit))).scalars().all()
        return list(filas), total

    async def list_records(self, *, object_type: str | None = None,
                           validation_status: str | None = None,
                           mapping_status: str | None = None,
                           promotion_status: str | None = None, only_errors: bool = False,
                           limit: int = 50, offset: int = 0
                           ) -> tuple[list[SapInboundRecord], int]:
        donde = [self._de_la_empresa(SapInboundRecord.company_id),
                 SapInboundRecord.is_current.is_(True)]
        for columna, valor in ((SapInboundRecord.object_type, object_type),
                               (SapInboundRecord.validation_status, validation_status),
                               (SapInboundRecord.mapping_status, mapping_status),
                               (SapInboundRecord.promotion_status, promotion_status)):
            if valor:
                donde.append(columna == valor)
        if only_errors:
            donde.append(SapInboundRecord.error_code.is_not(None))
        total = (await self.db.execute(
            select(func.count()).select_from(SapInboundRecord).where(*donde))).scalar() or 0
        filas = (await self.db.execute(
            select(SapInboundRecord).where(*donde)
            .order_by(SapInboundRecord.object_type, SapInboundRecord.source_key)
            .offset(offset).limit(limit))).scalars().all()
        return list(filas), total

    async def list_errors(self, limit: int = 50, offset: int = 0
                          ) -> tuple[list[SapInboundRecord], list[SapInboundSyncJob]]:
        registros, _ = await self.list_records(only_errors=True, limit=limit, offset=offset)
        jobs = (await self.db.execute(
            select(SapInboundSyncJob).where(
                self._de_la_empresa(SapInboundSyncJob.company_id),
                SapInboundSyncJob.status.in_((JOB_FAILED, JOB_PARTIAL)),
            ).order_by(SapInboundSyncJob.id.desc()).offset(offset).limit(limit))).scalars().all()
        return registros, list(jobs)

    # ── Mappings ──────────────────────────────────────────────────────────────

    async def list_mappings(self) -> list[SapEntityMapping]:
        return list((await self.db.execute(
            select(SapEntityMapping).where(
                self._de_la_empresa(SapEntityMapping.company_id),
            ).order_by(SapEntityMapping.entity_type, SapEntityMapping.sap_key))).scalars().all())

    async def _mapping(self, entity_type: str, sap_key: str) -> SapEntityMapping | None:
        return (await self.db.execute(
            select(SapEntityMapping).where(
                SapEntityMapping.source_system == SOURCE_SYSTEM,
                SapEntityMapping.client == self.cfg.client,
                SapEntityMapping.entity_type == entity_type,
                SapEntityMapping.sap_key == sap_key))).scalar_one_or_none()

    async def upsert_mapping(self, *, entity_type: str, sap_key: str,
                             parent_sap_key: str | None = None, farm_id: int | None = None,
                             house_id: int | None = None,
                             business_unit_code: str | None = None) -> SapEntityMapping:
        """Declara a qué empresa pertenece una clave SAP. Siempre la empresa efectiva.

        Enlazar una sociedad (`BUKRS`) con un inquilino decide qué datos de SAP verá: solo lo
        hace la autoridad global situada en esa empresa (`Q5`). Centros y almacenes los declara
        quien opera la integración, pero únicamente bajo una sociedad ya suya.
        """
        company_id = self._require_company_id()
        if not self.cfg.client:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                "SAP_HANA_CLIENT no está configurado: no se puede mapear.")
        from ....masters.models import Farm, House
        from ....tenancy import verificar_pertenencia

        conflicto = HTTPException(
            status.HTTP_409_CONFLICT,
            "La clave SAP no puede asignarse a esta empresa.")
        if entity_type == ENTITY_COMPANY_CODE:
            if not self.current_user.get("is_super_admin"):
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    "Enlazar una sociedad SAP con una empresa requiere autoridad global.")
            if self.cfg.company_codes and sap_key not in self.cfg.company_codes:
                raise conflicto
            parent_sap_key = farm_id = house_id = None
        else:
            if not parent_sap_key:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    "parent_sap_key es obligatorio para centros y almacenes.")
            tipo_padre = ENTITY_COMPANY_CODE if entity_type == ENTITY_PLANT else ENTITY_PLANT
            padre = await self._mapping(tipo_padre, parent_sap_key)
            if padre is None or padre.company_id != company_id or not padre.is_active:
                raise conflicto
            if entity_type == ENTITY_PLANT:
                house_id = None
            else:
                farm_id = None
                if not sap_key.startswith(parent_sap_key + "/"):
                    raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                                        "La clave de un almacén es WERKS/LGORT.")
        await verificar_pertenencia(self.db, Farm, farm_id, company_id, "Granja")
        await verificar_pertenencia(self.db, House, house_id, company_id, "Galpón")

        existente = await self._mapping(entity_type, sap_key)
        if existente is not None and existente.company_id != company_id:
            raise conflicto               # una clave SAP, una sola empresa
        if existente is None:
            existente = SapEntityMapping(
                source_system=SOURCE_SYSTEM, client=self.cfg.client, entity_type=entity_type,
                sap_key=sap_key, company_id=company_id, created_by_id=self.actor_id)
            self.db.add(existente)
        existente.parent_sap_key = parent_sap_key
        existente.farm_id = farm_id
        existente.house_id = house_id
        existente.business_unit_code = business_unit_code or None
        existente.is_active = True
        await self.db.flush()
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.CONFIG_CHANGE,
            modulo=AuditModule.SAP, entity_type="sap_entity_mapping",
            entity_id=str(existente.id), company_id=company_id,
            new_values={"entity_type": entity_type, "client": self.cfg.client,
                        "sap_key": sap_key, "parent_sap_key": parent_sap_key,
                        "farm_id": farm_id, "house_id": house_id})
        return existente

    async def delete_mapping(self, mapping_id: int) -> None:
        company_id = self._require_company_id()
        mapeo = (await self.db.execute(
            select(SapEntityMapping).where(
                SapEntityMapping.id == mapping_id,
                SapEntityMapping.company_id == company_id))).scalar_one_or_none()
        if mapeo is None:
            # Ajeno o inexistente: indistinguibles para quien no tiene derecho a saberlo.
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Mapping no encontrado")
        if mapeo.entity_type == ENTITY_COMPANY_CODE and not self.current_user.get(
                "is_super_admin"):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Desenlazar una sociedad SAP requiere autoridad global.")
        tipo_hijo = {ENTITY_COMPANY_CODE: ENTITY_PLANT,
                     ENTITY_PLANT: ENTITY_STORAGE_LOCATION}.get(mapeo.entity_type)
        if tipo_hijo is not None:
            hijos = (await self.db.execute(
                select(func.count()).select_from(SapEntityMapping).where(
                    SapEntityMapping.company_id == company_id,
                    SapEntityMapping.client == mapeo.client,
                    SapEntityMapping.entity_type == tipo_hijo,
                    SapEntityMapping.parent_sap_key == mapeo.sap_key))).scalar() or 0
            if hijos:
                raise HTTPException(status.HTTP_409_CONFLICT,
                                    "Tiene mappings dependientes; elimínelos primero.")
        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.CONFIG_CHANGE,
            modulo=AuditModule.SAP, entity_type="sap_entity_mapping",
            entity_id=str(mapeo.id), company_id=company_id,
            previous_values={"entity_type": mapeo.entity_type, "client": mapeo.client,
                             "sap_key": mapeo.sap_key}, new_values={"deleted": True})
        await self.db.delete(mapeo)
        await self.db.flush()

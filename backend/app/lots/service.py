"""
Lot service with business rules for lot lifecycle management.
"""
from datetime import date, datetime, time, timezone


def _dia(valor: datetime | date) -> date:
    """Día del calendario de un valor que puede venir como fecha o como instante."""
    return valor.date() if isinstance(valor, datetime) else valor


def _fecha_de_negocio(valor: datetime | date) -> datetime:
    """Un día del calendario anclado a medianoche UTC, listo para una columna con zona.

    `R-75`. Vale para cualquier fecha de negocio del lote, no solo la de inicio: `end_date`
    es la misma columna `DateTime(timezone=True)` y arrastraba el mismo desfase.
    """
    return datetime.combine(_dia(valor), time.min, tzinfo=timezone.utc)


def _inicio_declarado(valor: datetime | date | None) -> datetime:
    """Inicio del ciclo, anclado a medianoche UTC.

    `GA-REM-028 AC01/AC02`. La columna es `DateTime(timezone=True)` y la base corre en
    `CET`, de modo que una fecha sin zona se guardaba a medianoche local y volvía como el
    **día anterior** en UTC. Afectaba también al valor por omisión: un lote creado hoy se
    leía como iniciado ayer.

    Anclar el día declarado a medianoche UTC hace que la petición, la persistencia y la
    respuesta hablen del mismo día del calendario, que es lo que `§46` exige. No se cambia
    el tipo de la columna: eso sería una migración que `R-47` no necesita.
    """
    if valor is None:
        valor = date.today()
    return _fecha_de_negocio(valor)
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..masters.models import BirdTypeEnum, Lot, LotStatus, SexEnum
from ..tenancy import verificar_pertenencia
from ..operations.validators import (
    BusinessRuleViolation,
    validate_lot_closure,
    validate_lot_records_approved,
)
from ..operations.models import (
    OperationalEvent, EventType, EventStatus,
    BirdMovement, FeedMovement, EggMovement,
)
from . import models, schemas
from ..masters.service import MasterService


# ============================================================
# `R-153` · `OD-25 (B)` — el lote de abuelas nace al aprobar la importación
# ============================================================


def _fecha_de_llegada_del_plan(valor: Any) -> date:
    """Fecha de llegada declarada en el plan (`extra_data.import_plan.arrival_date`).

    Se acepta fecha, instante o texto ISO — el JSONB guarda el texto tal como llegó. Si no
    puede leerse, la aprobación **no** crea el lote: se levanta `BR-22` y la transacción
    revierte entera (aprobación incluida), que es la atomicidad que exige `OD-25`.
    """
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.fromisoformat(valor.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                return date.fromisoformat(valor[:10])
            except ValueError:
                pass
    raise BusinessRuleViolation(
        "La importación no tiene fecha de llegada válida para crear el lote", "BR-22",
    )


def _sexo_del_plan(filas: list) -> SexEnum | None:
    """Sexo del lote a partir de las filas ♂/♀ declaradas; mixto si vienen ambos."""
    machos = any(getattr(s, "value", s) == "male" and int(q or 0) > 0 for s, q in filas)
    hembras = any(getattr(s, "value", s) == "female" and int(q or 0) > 0 for s, q in filas)
    if machos and hembras:
        return SexEnum.MIXED
    if machos:
        return SexEnum.MALE
    if hembras:
        return SexEnum.FEMALE
    return None


async def _bloquear_secuencia(db: AsyncSession, clave: str) -> None:
    """Lock asesor transaccional de PostgreSQL; en otros dialectos no hay nada que bloquear."""
    try:
        dialecto = db.get_bind().dialect.name
    except Exception:  # pragma: no cover — sesión sin bind (pruebas unitarias puras)
        dialecto = ""
    if dialecto == "postgresql":
        await db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:clave))"),
                         {"clave": clave})


async def _siguiente_codigo_de_lote_gp(db: AsyncSession, company_id: int, anio: int, *,
                                       global_: bool) -> str:
    """`L-GP-{año}-{nn}`: siguiente consecutivo del año — de la empresa o, si una colisión
    real lo exige, contra el máximo global (la unicidad de `lot_code` es global en la base)."""
    prefijo = f"L-GP-{anio}-"
    consulta = select(Lot.lot_code).where(Lot.lot_code.like(f"{prefijo}%"))
    if not global_:
        consulta = consulta.where(Lot.company_id == company_id)
    codigos = (await db.execute(consulta)).scalars().all()
    mayor = 0
    for codigo in codigos:
        sufijo = codigo[len(prefijo):]
        if sufijo.isdigit():
            mayor = max(mayor, int(sufijo))
    return f"{prefijo}{mayor + 1:02d}"


async def crear_lote_de_importacion_si_procede(db: AsyncSession, event: Any,
                                               current_user: dict[str, Any]):
    """Crea el lote de abuelas al aprobar una importación que no lo traía; no-op en el legado.

    Invariante (`R-153`): la **aprobación** es lo único que convierte una importación en un
    lote real — una devuelta o rechazada no lo deja, y si se aprueba después, nace entonces.
    No **puebla**: la recepción sigue siendo la única entrada de aves (`R-152`, `R-130`).
    Con lote preasignado (flujo legado), no hace nada: mismo resultado que `R-152`.
    """
    if getattr(event, "lot_id", None) is not None:
        return None
    if getattr(event, "event_type", None) != EventType.GRANDPARENT_IMPORT:
        return None

    plan = (event.extra_data or {}).get("import_plan") or {}
    llegada = _fecha_de_llegada_del_plan(plan.get("arrival_date"))
    filas = (await db.execute(
        select(BirdMovement.sex, BirdMovement.quantity)
        .where(BirdMovement.event_id == event.id)
    )).all()
    sexo = _sexo_del_plan(filas)
    anio = llegada.year

    # Un solo lote por (empresa, año) se está numerando a la vez.
    await _bloquear_secuencia(db, f"lote-gp:{event.company_id}:{anio}")

    lote: Lot | None = None
    for intento in range(4):
        codigo = await _siguiente_codigo_de_lote_gp(db, event.company_id, anio,
                                                    global_=intento > 0)
        candidato = Lot(
            company_id=event.company_id,
            farm_id=event.farm_id,
            house_id=event.house_id,
            lot_code=codigo,
            bird_type=BirdTypeEnum.GRANDPARENT,
            sex=sexo,
            status=LotStatus.ACTIVE,
            activation_type="normal",
            start_date=_fecha_de_negocio(llegada),
        )
        db.add(candidato)
        try:
            async with db.begin_nested():
                await db.flush()
        except IntegrityError:
            if intento >= 3:
                raise
            # Colisión real contra otra empresa (unicidad global): se reintenta contra el
            # máximo global, bajo el lock del año compartido.
            await _bloquear_secuencia(db, f"lote-gp:{anio}:global")
            continue
        lote = candidato
        break
    if lote is None:  # pragma: no cover — inalcanzable: el último intento re-lanza
        raise BusinessRuleViolation("No se pudo asignar el código del lote de abuelas", "BR-22")

    event.lot_id = lote.id
    await db.flush()

    from ..audit.helpers import audit_accion
    from ..audit.models import AuditAction, AuditModule

    await audit_accion(
        db, usuario=current_user, accion=AuditAction.CREATED, modulo=AuditModule.LOTS,
        entity_type="lot", entity_id=lote.id, company_id=event.company_id, lot_id=lote.id,
        new_values={"lot_code": lote.lot_code, "origin": "grandparent_import_approval"},
    )
    return lote


class LotService:
    """Handles lot CRUD, activation, closure, and balance queries."""

    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")
        self.is_super_admin = current_user.get("is_super_admin", False)
        self._unidades_cache: Optional[list[str]] = None

    async def _unidades(self) -> list[str]:
        """El alcance de lectura productiva de quien pregunta (`OD-16`). Una vez por servicio.

        La autoridad global lee por las **habilitadas** de la empresa (la concesión no se le
        exige; la habilitación jamás se salta) — `GA-FE-02-D`.
        """
        if self._unidades_cache is None:
            from ..business_units.service import unidades_de_alcance_productivo

            self._unidades_cache = await unidades_de_alcance_productivo(
                self.db, current_user=self.current_user, company_id=self.company_id
            )
        return self._unidades_cache

    async def _exigir_unidad_operativa(self, unidad: Optional[str]) -> None:
        """`GA-REM-040-H` · `R-163`: la habilitación de la empresa es absoluta al escribir.

        `unidad` es el código canónico del lote (`lot.bird_type`, o `data.bird_type` en el alta;
        `None` = pendiente). Para el actor de empresa las superficies por `id` ya responden `404`
        fuera de su alcance (fase 3): aquí solo cambia el alta, que no pasaba por ningún
        alcance. Para la autoridad global se cierra la exención de **habilitación** que la fase 3
        declaró para lecturas y que nunca fue una autorización para escribir (`OD-16.f`). La
        decisión es la función compartida con `operations`; el contrato de `lots` es `403`:
        la unidad es un catálogo público de cuatro códigos, no hay nada que no enumerar.
        """
        from fastapi import HTTPException, status as _st

        from ..business_units.service import AccesoDeUnidadDenegado, exigir_unidad_operativa

        try:
            await exigir_unidad_operativa(
                self.db, current_user=self.current_user, company_id=self.company_id,
                unidad=unidad, efectivas=await self._unidades())
        except AccesoDeUnidadDenegado as exc:
            raise HTTPException(status_code=_st.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    @staticmethod
    def _codigo(lot) -> Optional[str]:
        tipo = getattr(lot, "bird_type", None)
        return getattr(tipo, "value", tipo) if tipo is not None else None

    async def get_lots(
        self, skip: int = 0, limit: int = 20, search: str = "",
        farm_id: Optional[int] = None, status: Optional[str] = None,
    ) -> tuple[list[Lot], int]:
        """List lots with filters and company isolation."""
        master_service = MasterService(self.db, Lot, self.current_user,
                                       unidades=await self._unidades())
        filters = {}
        if farm_id:
            filters["farm_id"] = farm_id
        if status:
            filters["status"] = status
        return await master_service.get_all(
            skip=skip, limit=limit, search=search,
            search_fields=["lot_code"],
            filters=filters,
            order_by="lot_code",
        )

    async def get_lot(self, lot_id: int) -> Lot:
        """Get single lot with phases and opening balance eager loaded."""
        master_service = MasterService(self.db, Lot, self.current_user,
                                       unidades=await self._unidades())
        return await master_service.get_by_id(lot_id)

    async def _curva_del_lote(
        self, genetic_line_id: Optional[int], weight_curve_id: Optional[int]
    ) -> Optional[int]:
        """La versión de curva que le corresponde a un lote nuevo. `AC09`, `AC10`.

        Sin línea genética no hay curva posible, y no se inventa ninguna: el motor
        devolverá `NO_REFERENCE`, que es la respuesta honesta (`AC19`).
        """
        from ..masters.curves import version_activa
        from ..masters.models import GeneticWeightCurve

        if weight_curve_id is None:
            if genetic_line_id is None:
                return None
            activa = await version_activa(self.db, genetic_line_id)
            return activa.id if activa else None

        curva = (await self.db.execute(
            select(GeneticWeightCurve).where(GeneticWeightCurve.id == weight_curve_id)
        )).scalar_one_or_none()
        if curva is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Curva de peso no encontrada",
            )
        # `AC10`. Juzgar un Ross 308 contra la tabla de un Cobb 500 produce un veredicto
        # con toda la apariencia de ser correcto y ninguna de las garantías.
        if curva.genetic_line_id != genetic_line_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La curva de peso pertenece a otra línea genética",
            )
        return curva.id

    async def create_lot(self, data: schemas.LotCreate) -> Lot:
        """Create a new lot."""
        existing = await self.db.execute(
            select(Lot).where(Lot.lot_code == data.lot_code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un lote con ese código",
            )

        # Validate farm belongs to user's company (or is global)
        if data.farm_id:
            from ..masters.models import Farm
            farm_result = await self.db.execute(select(Farm).where(Farm.id == data.farm_id))
            farm = farm_result.scalar_one_or_none()
            if farm and farm.company_id is not None and farm.company_id != self.company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="La granja no pertenece a su compañía",
                )

        # `GA-FE-06-A` · `R182-SEC-AC01`. `GA-REM-039` añadió el área al lote, pero quedó
        # fuera de las comprobaciones de pertenencia que `GA-REM-002` (`R-42`/`R-59`),
        # `R-139` y `R-179` extienden a toda referencia que el cliente puede enviar: el
        # área de **otra empresa** se aceptaba (`201`) y quedaba ligada al lote. Se usa el
        # validador canónico de catálogos — `company_id` nulo = compartida; ajena = se
        # comporta como inexistente (`BR-07`), sin distinguir «no existe» de «no es tuyo».
        #
        # `GA-FE-07` · `OD-21`: además, un área **dada de baja lógica** no puede usarse
        # para referencias nuevas — `exigir_activo` es la extensión de ese mismo validador
        # (el resto de callers de `R-179` conservan su contrato sin cambios).
        if getattr(data, "area_id", None) is not None:
            from ..masters.models import Area
            from ..tenancy import verificar_catalogo_de_empresa

            await verificar_catalogo_de_empresa(
                self.db, Area, data.area_id, self.company_id, "Área",
                exigir_activo=True)

        # `R-203`. Galpón y línea genética son referencias **estructurales**: la misma
        # clase que el área y el mismo contrato (`BR-07`, detalle neutro — el ajeno se
        # comporta como inexistente, sin distinguir «no existe» de «no es tuyo»). El
        # galpón no tiene `company_id` propio —cuelga de una granja—, así que su tenencia
        # se resuelve **por la granja**. Sin empresa efectiva, fail-closed.
        if data.house_id is not None:
            from ..masters.models import Farm, House
            from ..operations.validators import BusinessRuleViolation

            empresa_del_galpon = (await self.db.execute(
                select(Farm.company_id).join(House, House.farm_id == Farm.id)
                .where(House.id == data.house_id))).scalar_one_or_none()
            if empresa_del_galpon is None or empresa_del_galpon != self.company_id:
                raise BusinessRuleViolation("Galpón no encontrado", "BR-07")

        if data.genetic_line_id is not None:
            from ..masters.models import GeneticLine
            from ..tenancy import verificar_catalogo_de_empresa

            await verificar_catalogo_de_empresa(
                self.db, GeneticLine, data.genetic_line_id, self.company_id,
                "Línea genética")

        # `GA-REM-037` / `OD-06`. La curva estándar contra la que se juzgará este lote se
        # fija ahora y no se recalcula: es lo que separa una referencia histórica de una
        # que cambia bajo los pies del dato ya registrado (`AC07`, `AC08`).
        weight_curve_id = await self._curva_del_lote(
            data.genetic_line_id, getattr(data, "weight_curve_id", None)
        )
        # `GA-REM-040-H` · `AC-L02…L07`: `bird_type` es el dato de dominio que fija la cadena
        # del lote; el servidor lo contrasta con el alcance **antes** de `db.add`. Sin esto,
        # cualquier actor creaba lotes en cualquier cadena, apagada o no concedida, y la
        # autoridad global sin contexto los creaba sin empresa.
        await self._exigir_unidad_operativa(
            getattr(data.bird_type, "value", data.bird_type) if data.bird_type is not None else None)

        lot = Lot(
            company_id=self.company_id,
            lot_code=data.lot_code,
            farm_id=data.farm_id,
            house_id=data.house_id,
            genetic_line_id=data.genetic_line_id,
            weight_curve_id=weight_curve_id,
            area_id=getattr(data, "area_id", None),
            # `GA-REM-038` enmienda B. Se ancla a medianoche UTC con la misma convención que
            # `start_date` y `end_date` (`R-75`): es una fecha de negocio, no un instante.
            planned_close_date=(
                _fecha_de_negocio(data.planned_close_date)
                if getattr(data, "planned_close_date", None) else None
            ),
            breed_id=data.breed_id,
            bird_type=data.bird_type,
            sex=data.sex,
            status="active",
            activation_type="normal",
            # `GA-REM-028` / `R-47`. La fecha que envía quien registra el lote se
            # descartaba y se ponía la de hoy, de modo que un lote ya en marcha nacía con
            # edad cero: `age_days`, el índice productivo y la ganancia diaria salían mal,
            # y `BR-06` rechazaba cualquier evento retroactivo. Es lo que bloqueaba `P-11`.
            #
            # `RR-09`: `start_date` es el inicio del ciclo según el negocio y lo aporta el
            # usuario; `created_at` —que el servidor sigue fijando— es el alta en el
            # software. Para un lote incorporado, las dos difieren legítimamente.
            #
            # Omitirla mantiene el comportamiento de siempre: hoy.
            start_date=_inicio_declarado(data.start_date),
        )
        self.db.add(lot)
        await self.db.flush()
        await self.db.refresh(lot)
        # `GA-REM-032 AC02`. El alta de un lote no pasa por `MasterService`, así que la
        # instrumentación de los maestros no la alcanzaba: sin esto, crear un lote seguiría
        # sin dejar rastro.
        from ..audit.helpers import audit_accion
        from ..audit.models import AuditAction, AuditModule

        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.CREATED,
            modulo=AuditModule.LOTS, entity_type="lot", entity_id=lot.id,
            company_id=lot.company_id, lot_id=lot.id,
            new_values={"lot_code": lot.lot_code,
                        "bird_type": str(getattr(lot.bird_type, "value", lot.bird_type))},
        )
        return lot

    async def update_lot(self, lot_id: int, data: schemas.LotUpdate) -> Lot:
        """Update lot fields."""
        master_service = MasterService(self.db, Lot, self.current_user,
                                       unidades=await self._unidades())
        # `GA-REM-040-H` · `AC-L08`: el lote se resuelve como siempre (`404` por unidad para el
        # actor) y después se exige la habilitación, que a la autoridad global no le exigía nadie.
        lote_actual = await master_service.get_by_id(lot_id)
        await self._exigir_unidad_operativa(self._codigo(lote_actual))
        # `GA-FE-06-A` · `R182-SEC-AC02`. La edición pasa por `MasterService.update`, cuyo
        # `_PADRES_TENANT` no incluye `area_id`: mover un lote al área de otra empresa era la
        # misma escritura entre inquilinos que crearlo ahí. Se valida **antes** de tocar el
        # objeto — una negativa no deja mutación parcial ni auditoría de éxito.
        #
        # `GA-FE-07` · `OD-21` (matriz H1–H5): **cambiar la referencia es una referencia
        # nueva** — exige área activa y de la empresa. Omitir el campo, reenviar el mismo id
        # o despejar a `null` **no** es referencia nueva: la historia se conserva y una baja
        # lógica del área no invalida las ediciones ajenas al área.
        campos = data.model_dump(exclude_unset=True)
        if campos.get("area_id") is not None and campos["area_id"] != lote_actual.area_id:
            from ..masters.models import Area
            from ..tenancy import verificar_catalogo_de_empresa

            await verificar_catalogo_de_empresa(
                self.db, Area, campos["area_id"], self.company_id, "Área",
                exigir_activo=True)

        # `R-203`: mismo contrato que el alta para galpón y línea genética. Solo cuando
        # el valor **cambia** (reenviar el mismo id o `null` no es referencia nueva —
        # misma semántica que el área, `OD-21`).
        if (campos.get("house_id") is not None
                and campos["house_id"] != lote_actual.house_id):
            from ..masters.models import Farm, House
            from ..operations.validators import BusinessRuleViolation

            empresa_del_galpon = (await self.db.execute(
                select(Farm.company_id).join(House, House.farm_id == Farm.id)
                .where(House.id == campos["house_id"]))).scalar_one_or_none()
            if empresa_del_galpon is None or empresa_del_galpon != self.company_id:
                raise BusinessRuleViolation("Galpón no encontrado", "BR-07")

        if (campos.get("genetic_line_id") is not None
                and campos["genetic_line_id"] != lote_actual.genetic_line_id):
            from ..masters.models import GeneticLine
            from ..tenancy import verificar_catalogo_de_empresa

            await verificar_catalogo_de_empresa(
                self.db, GeneticLine, campos["genetic_line_id"], self.company_id,
                "Línea genética")
        return await master_service.update(lot_id, data)

    async def close_lot(self, lot_id: int) -> dict:
        """G-09: Close a lot with final summary (BR-05)."""
        master_service = MasterService(self.db, Lot, self.current_user,
                                       unidades=await self._unidades())
        lot = await master_service.get_by_id(lot_id)
        await self._exigir_unidad_operativa(self._codigo(lot))  # `AC-L08`, antes de toda regla

        if lot.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden cerrar lotes activos",
            )

        # `R-74` / `GA-REM-029 AC05`. `BR-05` exige pesaje y alimento antes de cerrar, sin
        # los cuales el resumen final no tiene base para el FCR. La guarda existía, pero
        # colgaba del evento `lot_closure`, que **no cierra el lote**: este endpoint es el
        # único sitio del backend que asigna `status = "closed"`. Vigilaba la puerta
        # equivocada, y el audit la daba por vigente justamente aquí.
        await validate_lot_closure(self.db, lot_id)

        # `R-76` / `GA-REM-036`. `docs/12 §6 R7`: un lote no puede cerrarse con registros sin
        # aprobar. Estaba escrita en la documentación del ciclo de revisión y no existía aquí,
        # de modo que un lote se cerraba con todos sus eventos en `registered`.
        #
        # Va **antes** de tocar `status` y `end_date`: una negativa no puede dejar el cierre a
        # medias. Es una regla distinta de `BR-05` y se cita como `R7`, que es como la norma
        # la llama; no se amplía `BR-05` ni se inventa un `BR-` nuevo.
        await validate_lot_records_approved(self.db, lot_id, self.company_id)

        # Calculate final summary
        # Total mortality
        mort_q = select(func.coalesce(func.sum(BirdMovement.quantity), 0)).join(
            OperationalEvent, BirdMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.event_type == EventType.MORTALITY_RECORDING,
        )
        mort_result = await self.db.execute(mort_q)
        total_mortality = mort_result.scalar() or 0

        # Total feed consumed
        feed_q = select(func.coalesce(func.sum(FeedMovement.quantity_kg), 0.0)).join(
            OperationalEvent, FeedMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
        )
        feed_result = await self.db.execute(feed_q)
        total_feed_kg = round(feed_result.scalar() or 0.0, 2)

        # Total eggs produced (if breeder)
        egg_q = select(func.coalesce(func.sum(EggMovement.quantity), 0)).join(
            OperationalEvent, EggMovement.event_id == OperationalEvent.id
        ).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.event_type == EventType.EGG_COLLECTION,
        )
        egg_result = await self.db.execute(egg_q)
        total_eggs = egg_result.scalar() or 0

        # Approved events count
        events_q = select(func.count(OperationalEvent.id)).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
        )
        events_result = await self.db.execute(events_q)
        total_events = events_result.scalar() or 0

        approved_q = select(func.count(OperationalEvent.id)).where(
            OperationalEvent.lot_id == lot_id,
            OperationalEvent.company_id == self.company_id,
            OperationalEvent.status.in_([
                EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
            ]),
        )
        approved_result = await self.db.execute(approved_q)
        approved_events = approved_result.scalar() or 0

        # Age in days
        # `R-73`. Restaba un `datetime` de un `date` y reventaba con `TypeError`, de modo
        # que **el cierre de lote respondía 500 siempre**: `start_date` nunca es nulo. Es la
        # misma confusión entre fecha de negocio y marca temporal que originó `R-47`, y por
        # eso se resuelve con él (`GA-REM-028 AC07`): la edad es la única consumidora
        # alcanzable de `start_date`, y sin esto el criterio no puede comprobarse.
        age_days = (date.today() - _dia(lot.start_date)).days if lot.start_date else 0

        summary = {
            "lot_id": lot_id,
            "lot_code": lot.lot_code if hasattr(lot, 'lot_code') else f"L-{lot_id}",
            "age_days": age_days,
            "total_mortality": total_mortality,
            "total_feed_kg": total_feed_kg,
            "total_eggs": total_eggs,
            "total_events": total_events,
            "approved_events": approved_events,
            "status": "closed",
            "end_date": str(date.today()),
        }

        lot.status = "closed"
        # `R-75`. Escribir `date.today()` en una columna con zona lo guardaba a medianoche
        # **local**, de modo que el lote cerrado hoy se releía como cerrado ayer: el resumen
        # decía una fecha y el registro otra. Es el mismo desfase que `GA-REM-028` corrigió
        # en `start_date`, que quedó sin aplicar al campo hermano.
        lot.end_date = _fecha_de_negocio(date.today())
        await self.db.flush()
        await self.db.refresh(lot)

        return summary

    # ============================================================
    # Manual Activation (Opening Balance)
    # ============================================================

    async def activate_manual(self, data: schemas.OpeningBalanceCreate) -> models.OpeningBalance:
        """
        Activate a lot manually with opening balances.
        Used for lots that already exist before system adoption.
        """
        # Validate lot exists
        lot = await self.db.execute(select(Lot).where(Lot.id == data.lot_id))
        lot = lot.scalar_one_or_none()
        if not lot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")

        # `AC-R67-11`. Hasta aquí lo único que impedía activar el lote de otra empresa era
        # carecer del permiso `lots:create`; quien lo tuviera en su propia empresa podía
        # fijar el saldo de apertura de un lote ajeno. Existir no es pertenecer: se usa la
        # misma comprobación que el resto del sistema (`GA-REM-002 AC10`).
        # `GA-REM-002-C` / `R-139` · `OD-14.c/d`: sin rama por `is_super_admin`. La
        # pertenencia se exige a todos y falla cerrada sin empresa efectiva (`AC26`); la
        # autoridad global fija saldos solo desde una empresa situada.
        await verificar_pertenencia(self.db, Lot, data.lot_id, self.company_id, "Lote")
        # `GA-REM-040` fase 3. La comprobación de empresa no basta: el lote de otra
        # cadena de la **misma** empresa también es ajeno. Se usa el mismo camino
        # acotado que el detalle, de modo que la respuesta es idéntica —`404`— y no
        # revela que el lote existe. `get_lot` acota por empresa para todos y por unidad
        # solo para quien no es global: la exención de visibilidad de unidad se preserva.
        # `GA-REM-040-H` · `AC-L08`: verla no es operarla; la habilitación se exige a todos.
        await self._exigir_unidad_operativa(self._codigo(await self.get_lot(data.lot_id)))

        # Validate no existing opening balance
        existing = await self.db.execute(
            select(models.OpeningBalance).where(models.OpeningBalance.lot_id == data.lot_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este lote ya tiene un balance de apertura registrado",
            )

        # `docs/02 §3.9.2` exige «Se evita doble conteo» y nada lo implementaba: un lote
        # que ya tuviera eventos de recepción y recibiera además un saldo de apertura
        # contaría dos veces las mismas aves. La activación manual sirve para lotes que
        # existían **antes** de la implantación, no para corregir lotes ya operando.
        con_historia = await self.db.execute(
            select(OperationalEvent.id)
            .where(
                OperationalEvent.lot_id == data.lot_id,
                OperationalEvent.status != EventStatus.CANCELLED,
            )
            .limit(1)
        )
        if con_historia.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El lote ya tiene operaciones registradas: activarlo manualmente "
                    "contaría dos veces las mismas aves"
                ),
            )

        # Business rules for opening balance
        if data.accumulated_mortality_male > data.initial_male_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mortalidad acumulada machos no puede exceder población inicial",
            )
        if data.accumulated_mortality_female > data.initial_female_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mortalidad acumulada hembras no puede exceder población inicial",
            )

        ob = models.OpeningBalance(
            lot_id=data.lot_id,
            activation_date=data.activation_date,
            phase_at_activation_id=data.phase_at_activation_id,
            age_days=data.age_days,
            initial_male_count=data.initial_male_count,
            initial_female_count=data.initial_female_count,
            accumulated_mortality_male=data.accumulated_mortality_male,
            accumulated_mortality_female=data.accumulated_mortality_female,
            accumulated_culls_male=data.accumulated_culls_male,
            accumulated_culls_female=data.accumulated_culls_female,
            accumulated_feed_kg=data.accumulated_feed_kg,
            current_avg_weight=data.current_avg_weight,
            accumulated_egg_production=data.accumulated_egg_production,
            accumulated_eggs_to_hatchery=data.accumulated_eggs_to_hatchery,
            accumulated_chicks_hatched=data.accumulated_chicks_hatched,
            accumulated_broiler_received=data.accumulated_broiler_received,
            activation_reason=data.activation_reason,
            support_document_url=data.support_document_url,
            is_manual_activation=True,
            activated_by_id=self.current_user["id"],
        )
        self.db.add(ob)

        # Mark lot as manually activated
        lot.activation_type = "manual"
        # Misma normalización que en el alta: la columna es `DateTime(timezone=True)` y la
        # base corre en `CET`, de modo que una fecha sin zona se guardaba a medianoche local
        # y volvía como el día anterior. La semántica no cambia —`docs/02 §3.9` pide la
        # «fecha real de inicio» y eso es lo que se guarda—, solo deja de derivar un día.
        lot.start_date = _inicio_declarado(data.activation_date)

        await self.db.flush()
        await self.db.refresh(ob)
        return ob

    async def get_opening_balance(self, lot_id: int) -> Optional[models.OpeningBalance]:
        """Saldo de apertura de un lote **alcanzable**.

        Consultaba por `lot_id` sin comprobar pertenencia alguna —ni siquiera de empresa—, de
        modo que el lote quedaba abierto por la puerta de al lado: proteger el detalle y
        dejar el sub-recurso libre no protege nada. Pasa por `get_lot`, que aplica empresa y
        unidad, y un lote inalcanzable produce el mismo `404` que produciría su detalle.
        """
        await self.get_lot(lot_id)
        result = await self.db.execute(
            select(models.OpeningBalance).where(models.OpeningBalance.lot_id == lot_id)
        )
        return result.scalar_one_or_none()

    async def get_lot_phases(self, lot_id: int) -> list[models.LotPhase]:
        """Fases de un lote **alcanzable**. Mismo caso que el saldo de apertura."""
        await self.get_lot(lot_id)
        result = await self.db.execute(
            select(models.LotPhase)
            .where(models.LotPhase.lot_id == lot_id)
            .order_by(models.LotPhase.start_date)
        )
        return list(result.scalars().all())

    async def add_phase(self, data: schemas.LotPhaseCreate) -> models.LotPhase:
        """Transición de fase con cierre de la anterior — `R-191`.

        El contrato de la UI (`phase_id` resuelto por código) se vuelve completo: la fase
        activa se cierra (`end_date = start_date`) **bajo bloqueo del lote** —una sola
        activa incluso con transiciones concurrentes, sin migración—, las poblaciones
        ausentes (0/0) se derivan del saldo por sexo, y las transiciones inválidas se
        rechazan sin dejar rastro: lote no activo, misma fase ya activa, fecha anterior al
        inicio de la fase vigente (`BR-23`). El aislamiento por empresa y unidad sigue
        primero (`AC-L08`, `R-203`).
        """
        lote = await self.get_lot(data.lot_id)
        await self._exigir_unidad_operativa(self._codigo(lote))  # `AC-L08`

        # Bloqueo pesimista del lote: serializa transiciones del mismo lote (la fila de la
        # fase activa no sirve como cerrojo cuando aún no existe o va a cambiar).
        await self.db.execute(
            select(models.Lot).where(models.Lot.id == data.lot_id).with_for_update()
        )

        estado = getattr(lote.status, "value", lote.status)
        if estado != "active":
            raise BusinessRuleViolation("El lote no está activo", "BR-23")

        valor = lambda v: getattr(v, "value", v)  # noqa: E731
        activa = (await self.db.execute(
            select(models.LotPhase).where(models.LotPhase.lot_id == data.lot_id,
                                         models.LotPhase.is_active.is_(True))
        )).scalar_one_or_none()
        if activa is not None:
            if activa.phase_id == data.phase_id:
                raise BusinessRuleViolation("El lote ya está en esa fase", "BR-23")
            if data.start_date < valor(activa.start_date):
                raise BusinessRuleViolation(
                    "La fecha de inicio es anterior a la fase vigente", "BR-23")
            activa.is_active = False
            activa.end_date = data.start_date
        _ = valor

        campos = data.model_dump()
        if campos.get("start_population_male", 0) == 0 and campos.get("start_population_female", 0) == 0:
            # `R-191`: sin poblaciones declaradas se derivan del saldo vivo por sexo.
            from ..operations.validators import get_current_bird_balance_by_sex

            machos, hembras = await get_current_bird_balance_by_sex(self.db, data.lot_id)
            campos["start_population_male"] = machos
            campos["start_population_female"] = hembras
        campos["is_active"] = True
        phase = models.LotPhase(**campos)
        self.db.add(phase)
        await self.db.flush()

        from sqlalchemy.orm import selectinload

        return (await self.db.execute(
            select(models.LotPhase)
            .options(selectinload(models.LotPhase.phase))
            .where(models.LotPhase.id == phase.id)
        )).scalar_one()

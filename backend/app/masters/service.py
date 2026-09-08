"""
Generic CRUD service for master data entities.
Multi-company aware: auto-filters by company_id for non-super-admin users.
"""
from typing import Any, Optional, Type

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import Base
from ..audit.models import AuditAction


def _serializable(valor: Any) -> Any:
    """Lo que cabe en una columna JSON; el resto se guarda por su representación."""
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    return str(valor)


def _limpio(datos: dict | None) -> dict | None:
    return {k: _serializable(v) for k, v in datos.items()} if datos else None


class MasterService:
    """Generic CRUD service for any SQLAlchemy model, with multi-company support."""

    def __init__(
        self,
        db: AsyncSession,
        model: Type[Base],
        current_user: Optional[dict[str, Any]] = None,
        unidades: Optional[list[str]] = None,
    ):
        self.db = db
        self.model = model
        self.current_user = current_user or {}
        self.is_super_admin = self.current_user.get("is_super_admin", False)
        self.user_company_id = self.current_user.get("company_id")
        #: Unidades de negocio efectivas del usuario (`GA-REM-040` fase 3). `None` significa
        #: «esta llamada no acota por unidad»; una lista vacía significa «ninguna», que es
        #: distinto y da cero filas. Lo resuelve quien construye el servicio, porque
        #: resolverlo es una consulta y este constructor es síncrono.
        self.unidades = unidades

    def _apply_company_filter(self, query):
        """
        Apply company_id filter unless:
        - User is Super Admin (scope all)
        - Model doesn't have company_id column
        """
        if self.is_super_admin:
            return query  # No filter — sees all companies
        if not self.user_company_id:
            return query  # No company assigned — return empty or filter by id
        if hasattr(self.model, "company_id"):
            query = query.where(self.model.company_id == self.user_company_id)
        return query

    def _apply_business_unit_filter(self, query):
        """Acota por unidad de negocio. `GA-REM-040 AC-C08` / `T-040-09`.

        Vive junto al filtro de empresa y **se aplica donde se aplica aquél**: si el de
        empresa no actúa —Super Administrador, o modelo sin `company_id`—, éste tampoco.
        Separarlos daría dos alcances distintos en la misma consulta y nadie sabría cuál
        manda.

        El Super Administrador queda fuera igual que del filtro de empresa: su semántica
        está certificada en `GA-REM-002` y esta fase no la reabre. Queda declarado en la
        evidencia como excepción, no como descuido.
        """
        from ..business_units.scope import predicado

        if self.unidades is None or self.is_super_admin:
            return query
        condicion = predicado(self.model, self.unidades)
        return query if condicion is None else query.where(condicion)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str = "",
        search_fields: Optional[list[str]] = None,
        filters: Optional[dict[str, Any]] = None,
        order_by: str = "id",
    ) -> tuple[list[Any], int]:
        """Get paginated list with search, filters, and company isolation."""
        query = select(self.model)

        # Company isolation
        query = self._apply_company_filter(query)
        # Unidad de negocio. Antes del recuento y de la paginación: si fuera después, el
        # total contaría filas ocultas —revelándolas por diferencia— y la primera página
        # llegaría con huecos donde estaban las ajenas.
        query = self._apply_business_unit_filter(query)

        # Text search
        if search and search_fields:
            search_conditions = []
            for field in search_fields:
                col = getattr(self.model, field, None)
                if col is not None:
                    search_conditions.append(col.ilike(f"%{search}%"))
            if search_conditions:
                query = query.where(or_(*search_conditions))

        # Extra filters
        if filters:
            for key, value in filters.items():
                col = getattr(self.model, key, None)
                if col is not None and value is not None:
                    query = query.where(col == value)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Order, paginate
        order_col = getattr(self.model, order_by, self.model.id)
        query = query.order_by(order_col).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total

    async def get_by_id(self, item_id: int) -> Any:
        """Get single item by ID, respecting company isolation."""
        query = self._apply_company_filter(select(self.model))
        query = self._apply_business_unit_filter(query)
        query = query.where(self.model.id == item_id)
        result = await self.db.execute(query)
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} no encontrado",
            )
        return item

    #: Claves foráneas estructurales de los maestros: definen de quién es el dato.
    #: Los catálogos con `company_id` anulable quedan fuera a proposito — su diseño
    #: admite el uso compartido entre empresas.
    _PADRES_TENANT = {"farm_id": "Farm", "hatchery_id": "Hatchery"}

    async def _verificar_padres(self, item_data: dict) -> None:
        """El recurso padre debe pertenecer a la misma compañía (`GA-REM-002 AC10`).

        Sin esto, un galpón podía crearse bajo la granja de otra empresa: el hijo quedaba
        asignado a una compañía y colgando de la estructura de otra. Es la misma clase de
        defecto que `R-42`, en el árbol de maestros (`R-59`).
        """
        from ..tenancy import verificar_pertenencia
        from . import models as masters_models

        for campo, nombre_modelo in self._PADRES_TENANT.items():
            valor = item_data.get(campo)
            if valor is None:
                continue
            await verificar_pertenencia(
                self.db, getattr(masters_models, nombre_modelo), valor,
                self.user_company_id, nombre_modelo,
            )

    async def _auditar(self, accion, item, previos=None, nuevos=None) -> None:
        """`GA-REM-032 AC02`. Alta, edición y baja lógica de un maestro o un lote.

        Los listeners solo vigilan el ciclo del evento operativo, de modo que crear una
        granja o editar un lote no dejaba rastro alguno. Vive aquí, en el servicio común de
        los maestros, y no repartido por diecinueve routers.
        """
        from ..audit.helpers import audit_accion
        from ..audit.models import AuditModule
        from .models import Lot

        await audit_accion(
            self.db, usuario=self.current_user, accion=accion,
            modulo=AuditModule.LOTS if self.model is Lot else AuditModule.MASTERS,
            entity_type=self.model.__name__.lower(), entity_id=item.id,
            company_id=getattr(item, "company_id", None) or self.user_company_id,
            previous_values=_limpio(previos), new_values=_limpio(nuevos),
        )

    async def create(self, data: Any) -> Any:
        """Create a new item. Auto-assigns company_id from current user."""
        item_data = data.model_dump()

        # Auto-assign company_id if model has it and user has one
        if hasattr(self.model, "company_id") and "company_id" in item_data:
            if item_data["company_id"] is None and self.user_company_id:
                item_data["company_id"] = self.user_company_id

        await self._verificar_padres(item_data)

        item = self.model(**item_data)
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        await self._auditar(AuditAction.CREATED, item, nuevos=item_data)
        return item

    async def update(self, item_id: int, data: Any) -> Any:
        """Update an existing item. Respects company isolation."""
        item = await self.get_by_id(item_id)
        update_data = data.model_dump(exclude_unset=True)
        # Mover un maestro bajo un padre ajeno es la misma escritura entre inquilinos que
        # crearlo ahi (`R-59`).
        await self._verificar_padres(update_data)
        previos = {k: _serializable(getattr(item, k, None)) for k in update_data}
        for key, value in update_data.items():
            setattr(item, key, value)
        await self.db.flush()
        await self.db.refresh(item)
        await self._auditar(AuditAction.UPDATED, item,
                            previos=previos, nuevos=update_data)
        return item

    async def deactivate(self, item_id: int) -> None:
        """Soft delete: set is_active=False. Respects company isolation."""
        item = await self.get_by_id(item_id)
        item.is_active = False
        await self.db.flush()
        await self._auditar(AuditAction.DELETED, item)

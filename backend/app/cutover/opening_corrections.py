"""GA-REQ-061 · T14 · C6 — correcciones formales del Opening (AC59-65).

Un opening APPLIED **no se edita ni se elimina directamente** (AC59/60): la
única vía es esta corrección, que **conserva el original** en su propia fila
(`old_value`/`new_value`/`delta`, AC61/63), exige **razón** (AC62) y queda
**auditada** (AC64). Nunca toca los eventos post-cutover (AC65): el saldo se
recalcula por fórmula con componentes etiquetados (`10.000 → 9.900 ⇒ 9.865`).

Permiso: el canónico del framework de correcciones (`corrections:correct` /
`corrections:read`, AC42).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_accion
from ..audit.models import AuditAction, AuditModule
from ..database import get_db
from ..dependencies import require_permission
from ..lots.models import OpeningBalance
from ..masters.models import Lot
from ..transaction import RutaTransaccional
from . import schemas
from .models import OpeningBalanceCorrection

router = APIRouter(route_class=RutaTransaccional, prefix="/opening-balances", tags=["Cutover"])

#: Lista blanca de campos corregibles (AC63: before/after/delta por campo).
CAMPOS_CORREGIBLES = (
    "initial_male_count",
    "initial_female_count",
    "accumulated_mortality_male",
    "accumulated_mortality_female",
    "accumulated_culls_male",
    "accumulated_culls_female",
)


class OpeningCorrectionService:
    def __init__(self, db: AsyncSession, current_user: dict):
        self.db = db
        self.current_user = current_user

    def _empresa(self) -> int:
        empresa = self.current_user.get("effective_company_id") or self.current_user.get("company_id")
        if not empresa:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Se requiere una empresa efectiva para corregir openings.")
        return int(empresa)

    async def _opening_propio(self, opening_id: int) -> OpeningBalance:
        """Fail-closed: un opening de otra empresa se comporta como inexistente."""
        opening = (await self.db.execute(
            select(OpeningBalance).where(OpeningBalance.id == opening_id))).scalar_one_or_none()
        if opening is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opening no encontrado")
        lote = (await self.db.execute(select(Lot).where(Lot.id == opening.lot_id))).scalar_one_or_none()
        if lote is None or lote.company_id != self._empresa():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opening no encontrado")
        return opening

    async def corregir(self, opening_id: int, data: schemas.OpeningCorrectionCreate) -> OpeningBalanceCorrection:
        opening = await self._opening_propio(opening_id)
        if data.field not in CAMPOS_CORREGIBLES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"CORRECTION_FIELD_INVALID: '{data.field}' no es un campo corregible")
        if data.new_value < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="CORRECTION_VALUE_INVALID: el valor no puede ser negativo")

        viejo = int(getattr(opening, data.field) or 0)
        nuevo = int(data.new_value)
        delta = nuevo - viejo
        setattr(opening, data.field, nuevo)

        correccion = OpeningBalanceCorrection(
            opening_id=opening.id,
            field=data.field,
            old_value=str(viejo),
            new_value=str(nuevo),
            delta=str(delta),
            reason=data.reason,
            requested_by_id=int(self.current_user["id"]),
            applied_at=datetime.now(timezone.utc),
        )
        self.db.add(correccion)
        await self.db.flush()

        await audit_accion(
            self.db, usuario=self.current_user, accion=AuditAction.CORRECT,
            modulo=AuditModule.CUTOVER, entity_type="opening_balance",
            entity_id=str(opening.id), company_id=self._empresa(), lot_id=opening.lot_id,
            previous_values={data.field: viejo}, new_values={data.field: nuevo},
            change_reason=data.reason,
        )
        await self.db.commit()
        await self.db.refresh(correccion)
        return correccion

    async def listar(self, opening_id: int) -> list[OpeningBalanceCorrection]:
        await self._opening_propio(opening_id)
        resultado = await self.db.execute(
            select(OpeningBalanceCorrection)
            .where(OpeningBalanceCorrection.opening_id == opening_id)
            .order_by(OpeningBalanceCorrection.id))
        return list(resultado.scalars().all())


@router.post("/{opening_id}/corrections", response_model=schemas.OpeningCorrectionRead, status_code=201)
async def crear_correccion(
    opening_id: int,
    data: schemas.OpeningCorrectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("corrections", "correct")),
):
    """Corrección formal: conserva el original, exige razón, audita y no toca el post-cutover."""
    return await OpeningCorrectionService(db, current_user).corregir(opening_id, data)


@router.get("/{opening_id}/corrections", response_model=schemas.OpeningCorrectionList)
async def listar_correcciones(
    opening_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("corrections", "read")),
):
    """Historial de correcciones del opening (el original permanece visible)."""
    return {"items": await OpeningCorrectionService(db, current_user).listar(opening_id)}

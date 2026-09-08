"""Configurar unidades de negocio en las pruebas — `GA-REM-040` fase 3.

Desde la fase 3, un usuario sin unidades concedidas **no ve dato productivo**: es lo que
`OD-09.c` decidió y lo que el filtro por fila aplica. Las suites escritas antes de esta
capacidad crean usuarios sin concederles nada, y con razón —entonces no existía—, de modo que
sus sujetos se quedan sin ver ni sus propios lotes.

Esto no es un rodeo al control: es **configurar la empresa**, que es lo que un cliente real hará
en su alta. La alternativa —dejar que la ausencia de concesión signifique acceso total— es
exactamente el `fail open` que esta capacidad existe para impedir.

Se usa donde la prueba mide **otra cosa** —el cierre de un lote, un `KPI`, un flujo de
revisión— y necesita un sujeto que pueda trabajar. Las pruebas que miden el aislamiento por
unidad conceden a mano, unidad por unidad, porque ahí la concesión **es** el objeto de estudio.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


async def habilitar_y_conceder_todo(database_url: str, *, company_id: int,
                                    user_ids: list[int]) -> None:
    """Habilita las cuatro cadenas a la empresa y se las concede a esos usuarios.

    Idempotente: repetirla no duplica ni falla. Respeta el camino de escritura sancionado
    —`conceder_unidad`—, de modo que la concesión queda acotada a la empresa igual que la
    haría la administración de la fase 7.
    """
    from app.auth.models import User
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit, UserBusinessUnit
    from app.business_units.service import conceder_unidad

    motor = create_async_engine(database_url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            unidades = (await s.execute(select(BusinessUnit))).scalars().all()
            habilitaciones = {}
            for unidad in unidades:
                fila = (await s.execute(select(CompanyBusinessUnit).where(
                    CompanyBusinessUnit.company_id == company_id,
                    CompanyBusinessUnit.business_unit_id == unidad.id))).scalar_one_or_none()
                if fila is None:
                    fila = CompanyBusinessUnit(company_id=company_id,
                                               business_unit_id=unidad.id, is_enabled=True)
                    s.add(fila)
                    await s.flush()
                elif not fila.is_enabled:
                    fila.is_enabled = True
                habilitaciones[unidad.id] = fila

            for user_id in user_ids:
                usuario = (await s.execute(
                    select(User).where(User.id == user_id))).scalar_one_or_none()
                if usuario is None or usuario.company_id != company_id:
                    continue
                for fila in habilitaciones.values():
                    ya = (await s.execute(select(UserBusinessUnit).where(
                        UserBusinessUnit.user_id == user_id,
                        UserBusinessUnit.company_business_unit_id == fila.id,
                        UserBusinessUnit.revoked_at.is_(None)))).scalar_one_or_none()
                    if ya is None:
                        await conceder_unidad(s, user=usuario, company_business_unit=fila)
            await s.commit()
    finally:
        await motor.dispose()

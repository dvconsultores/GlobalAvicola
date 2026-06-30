"""Boost live-test data coverage for multi-company readiness.

Run:
    cd backend
    PYTHONPATH=. python3 seeds/live_data_boost.py
"""

import asyncio
import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.lots.models  # noqa: F401 - register mappers
from app.auth.models import User
from app.database import async_session
from app.integrations.sap.models import SapReference, SapReferenceType
from app.masters.models import BirdTypeEnum, Breed, Company, Farm, Hatchery, House, Lot, LotStatus, SexEnum
from app.operations.models import (
    BirdMovement,
    EggMovement,
    EventStatus,
    EventType,
    FeedMovement,
    HatcheryParams,
    OperationalEvent,
)


logging.basicConfig(level=logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)


BOOST_TAG = "LIVE_BOOST"


def _build_stage_sap_refs(company_id: int) -> list[dict]:
    company_key = f"C{company_id:03d}"
    return [
        # Purchase orders across the 6 process stages
        {
            "ref_type": SapReferenceType.PURCHASE_ORDER,
            "sap_code": f"PO-{company_key}-GPR-0001",
            "description": "OC Progenitoras Cria - recepcion de abuelas",
            "quantity": 5600,
            "unit": "UN",
            "extra_data": {"stage": "grandparent_rearing", "seed": BOOST_TAG},
        },
        {
            "ref_type": SapReferenceType.PURCHASE_ORDER,
            "sap_code": f"PO-{company_key}-GPP-0001",
            "description": "OC Progenitoras Produccion - alimento postura",
            "quantity": 12000,
            "unit": "KG",
            "extra_data": {"stage": "grandparent_production", "seed": BOOST_TAG},
        },
        {
            "ref_type": SapReferenceType.PURCHASE_ORDER,
            "sap_code": f"PO-{company_key}-BRR-0001",
            "description": "OC Reproductoras Cria - reposicion de aves",
            "quantity": 6200,
            "unit": "UN",
            "extra_data": {"stage": "breeder_rearing", "seed": BOOST_TAG},
        },
        {
            "ref_type": SapReferenceType.PURCHASE_ORDER,
            "sap_code": f"PO-{company_key}-BRP-0001",
            "description": "OC Reproductoras Produccion - alimento fase pico",
            "quantity": 15000,
            "unit": "KG",
            "extra_data": {"stage": "breeder_production", "seed": BOOST_TAG},
        },
        {
            "ref_type": SapReferenceType.PURCHASE_ORDER,
            "sap_code": f"PO-{company_key}-HAT-0001",
            "description": "OC Incubadora - insumos de incubacion",
            "quantity": 9000,
            "unit": "UN",
            "extra_data": {"stage": "hatchery", "seed": BOOST_TAG},
        },
        {
            "ref_type": SapReferenceType.PURCHASE_ORDER,
            "sap_code": f"PO-{company_key}-BRO-0001",
            "description": "OC Engorde - alimento crecimiento",
            "quantity": 24000,
            "unit": "KG",
            "extra_data": {"stage": "broiler", "seed": BOOST_TAG},
        },
        # Transfer orders for egg/chick logistics between stages
        {
            "ref_type": SapReferenceType.TRANSFER_ORDER,
            "sap_code": f"STO-{company_key}-GPP-HAT-01",
            "description": "Transferencia huevo fertil GP a Incubadora",
            "quantity": 12000,
            "unit": "UN",
            "extra_data": {"stage": "grandparent_production", "seed": BOOST_TAG},
        },
        {
            "ref_type": SapReferenceType.TRANSFER_ORDER,
            "sap_code": f"STO-{company_key}-BRP-HAT-01",
            "description": "Transferencia huevo fertil BR a Incubadora",
            "quantity": 11000,
            "unit": "UN",
            "extra_data": {"stage": "breeder_production", "seed": BOOST_TAG},
        },
        {
            "ref_type": SapReferenceType.TRANSFER_ORDER,
            "sap_code": f"STO-{company_key}-HAT-BRO-01",
            "description": "Transferencia pollito de Incubadora a Engorde",
            "quantity": 19000,
            "unit": "UN",
            "extra_data": {"stage": "hatchery", "seed": BOOST_TAG},
        },
    ]


async def _get_company(session: AsyncSession, name: str) -> Company | None:
    result = await session.execute(select(Company).where(Company.name == name))
    return result.scalar_one_or_none()


async def _get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def _get_any_company_user(session: AsyncSession, company_id: int) -> User | None:
    result = await session.execute(
        select(User).where(User.company_id == company_id).order_by(User.id.asc())
    )
    return result.scalars().first()


async def _get_farm_houses(session: AsyncSession, company_id: int) -> list[tuple[Farm, House]]:
    farms = (
        await session.execute(
            select(Farm).where(Farm.company_id == company_id).order_by(Farm.id.asc())
        )
    ).scalars().all()
    pairs: list[tuple[Farm, House]] = []
    for farm in farms:
        houses = (
            await session.execute(
                select(House).where(House.farm_id == farm.id).order_by(House.id.asc())
            )
        ).scalars().all()
        for house in houses:
            pairs.append((farm, house))
    return pairs


async def _get_first_breed_id(session: AsyncSession) -> int | None:
    result = await session.execute(select(Breed.id).order_by(Breed.id.asc()))
    return result.scalars().first()


async def _get_first_hatchery_id(session: AsyncSession, company_id: int) -> int | None:
    result = await session.execute(
        select(Hatchery.id).where(Hatchery.company_id == company_id).order_by(Hatchery.id.asc())
    )
    return result.scalars().first()


async def _ensure_sap_ref(
    session: AsyncSession,
    company_id: int,
    imported_by_id: int | None,
    ref_type: SapReferenceType,
    sap_code: str,
    description: str,
    quantity: float,
    unit: str,
    extra_data: dict | None = None,
) -> None:
    exists = await session.execute(
        select(SapReference.id).where(
            SapReference.company_id == company_id,
            SapReference.ref_type == ref_type,
            SapReference.sap_code == sap_code,
        )
    )
    if exists.scalar_one_or_none():
        return

    session.add(
        SapReference(
            company_id=company_id,
            ref_type=ref_type,
            sap_code=sap_code,
            description=description,
            quantity=quantity,
            unit=unit,
            extra_data=extra_data,
            imported_by_id=imported_by_id,
        )
    )


async def _ensure_stage_sap_refs(
    session: AsyncSession,
    company_id: int,
    imported_by_id: int | None,
) -> None:
    for ref in _build_stage_sap_refs(company_id):
        await _ensure_sap_ref(
            session,
            company_id,
            imported_by_id,
            ref["ref_type"],
            ref["sap_code"],
            ref["description"],
            ref["quantity"],
            ref["unit"],
            extra_data=ref.get("extra_data"),
        )


async def _ensure_lot(
    session: AsyncSession,
    *,
    company_id: int,
    farm_id: int,
    house_id: int,
    breed_id: int | None,
    lot_code: str,
    bird_type: BirdTypeEnum,
    status: LotStatus,
    days_ago_start: int,
) -> Lot:
    existing = await session.execute(select(Lot).where(Lot.lot_code == lot_code))
    lot = existing.scalar_one_or_none()
    if lot:
        if lot.company_id != company_id:
            lot.company_id = company_id
        if lot.status != status:
            lot.status = status
        return lot

    start_date = date.today() - timedelta(days=days_ago_start)
    end_date = date.today() - timedelta(days=1) if status == LotStatus.CLOSED else None

    lot = Lot(
        company_id=company_id,
        farm_id=farm_id,
        house_id=house_id,
        breed_id=breed_id,
        lot_code=lot_code,
        bird_type=bird_type,
        sex=SexEnum.MIXED,
        status=status,
        activation_type="manual",
        start_date=start_date,
        end_date=end_date,
    )
    session.add(lot)
    await session.flush()
    return lot


async def _ensure_event(
    session: AsyncSession,
    *,
    company_id: int,
    lot: Lot,
    farm_id: int,
    house_id: int,
    event_type: EventType,
    status: EventStatus,
    registered_by_id: int,
    reviewed_by_id: int | None,
    approved_by_id: int | None,
    hatchery_id: int | None = None,
    breed_id: int | None = None,
    days_ago: int = 1,
) -> None:
    marker = f"{BOOST_TAG}:{company_id}:{lot.lot_code}:{event_type.value}:{status.value}"
    existing = await session.execute(
        select(OperationalEvent.id).where(
            OperationalEvent.company_id == company_id,
            OperationalEvent.observations == marker,
        )
    )
    if existing.scalar_one_or_none():
        return

    event = OperationalEvent(
        company_id=company_id,
        lot_id=lot.id,
        farm_id=farm_id,
        house_id=house_id,
        event_type=event_type,
        event_date=date.today() - timedelta(days=days_ago),
        status=status,
        registered_by_id=registered_by_id,
        reviewed_by_id=reviewed_by_id,
        approved_by_id=approved_by_id,
        observations=marker,
    )
    session.add(event)
    await session.flush()

    if event_type == EventType.BIRD_RECEPTION:
        session.add(
            BirdMovement(
                event_id=event.id,
                sex="mixed",
                quantity=1500,
                avg_weight=42.0,
                breed_id=breed_id,
            )
        )
    elif event_type == EventType.FEED_REGISTRATION:
        session.add(FeedMovement(event_id=event.id, quantity_kg=600.0, sacks_count=12))
    elif event_type in (EventType.EGG_COLLECTION, EventType.EGG_DISPATCH):
        session.add(EggMovement(event_id=event.id, egg_type="fertile", quantity=1200))
    elif event_type == EventType.INCUBATION_LOAD:
        session.add(
            HatcheryParams(
                event_id=event.id,
                hatchery_id=hatchery_id,
                temperature=37.5,
                humidity=55.0,
                quantity_loaded=1200,
            )
        )
    elif event_type == EventType.MORTALITY_RECORDING:
        session.add(BirdMovement(event_id=event.id, sex="mixed", quantity=22, avg_weight=900.0))


async def _ensure_company3_operational_data(session: AsyncSession) -> None:
    company = await _get_company(session, "Avícola Del Sur C.A.")
    if not company:
        return

    pairs = await _get_farm_houses(session, company.id)
    if not pairs:
        return

    actor = await _get_user_by_username(session, "operador_sur")
    if not actor:
        actor = await _get_any_company_user(session, company.id)
    if not actor:
        return

    reviewer = await _get_user_by_username(session, "supervisor_sur") or actor
    breed_id = await _get_first_breed_id(session)
    hatchery_id = await _get_first_hatchery_id(session, company.id)

    await _ensure_stage_sap_refs(session, company.id, actor.id)

    lot_defs = [
        ("L-DS-LIVE-GP-01", BirdTypeEnum.GRANDPARENT, LotStatus.ACTIVE, 45),
        ("L-DS-LIVE-BR-01", BirdTypeEnum.BREEDER, LotStatus.ACTIVE, 40),
        ("L-DS-LIVE-BO-01", BirdTypeEnum.BROILER, LotStatus.ACTIVE, 30),
        ("L-DS-LIVE-BO-02", BirdTypeEnum.BROILER, LotStatus.ACTIVE, 20),
        ("L-DS-LIVE-HIST-00", BirdTypeEnum.BROILER, LotStatus.CLOSED, 120),
    ]

    lots: list[Lot] = []
    for idx, (code, bird_type, status, days_ago) in enumerate(lot_defs):
        farm, house = pairs[idx % len(pairs)]
        lot = await _ensure_lot(
            session,
            company_id=company.id,
            farm_id=farm.id,
            house_id=house.id,
            breed_id=breed_id,
            lot_code=code,
            bird_type=bird_type,
            status=status,
            days_ago_start=days_ago,
        )
        lots.append(lot)

    event_defs = [
        (lots[0], EventType.BIRD_RECEPTION, EventStatus.APPROVED, 6),
        (lots[1], EventType.FEED_REGISTRATION, EventStatus.REGISTERED, 5),
        (lots[1], EventType.EGG_COLLECTION, EventStatus.PENDING_REVIEW, 4),
        (lots[2], EventType.EGG_DISPATCH, EventStatus.IN_REVIEW, 3),
        (lots[2], EventType.INCUBATION_LOAD, EventStatus.CORRECTED, 2),
        (lots[3], EventType.MORTALITY_RECORDING, EventStatus.REJECTED, 1),
    ]

    for lot, event_type, status, days_ago in event_defs:
        await _ensure_event(
            session,
            company_id=company.id,
            lot=lot,
            farm_id=lot.farm_id,
            house_id=lot.house_id,
            event_type=event_type,
            status=status,
            registered_by_id=actor.id,
            reviewed_by_id=reviewer.id,
            approved_by_id=reviewer.id if status == EventStatus.APPROVED else None,
            hatchery_id=hatchery_id,
            breed_id=breed_id,
            days_ago=days_ago,
        )


async def _ensure_company1_missing_statuses_and_types(session: AsyncSession) -> None:
    company = await _get_company(session, "Avícola Global C.A.")
    if not company:
        return

    actor = await _get_user_by_username(session, "web.supervisor")
    if not actor:
        actor = await _get_any_company_user(session, company.id)
    if not actor:
        return

    await _ensure_stage_sap_refs(session, company.id, actor.id)

    lot_result = await session.execute(
        select(Lot).where(Lot.company_id == company.id, Lot.status == LotStatus.ACTIVE).order_by(Lot.id.asc())
    )
    lot = lot_result.scalars().first()
    if not lot:
        return

    hatchery_id = await _get_first_hatchery_id(session, company.id)
    breed_id = await _get_first_breed_id(session)

    await _ensure_event(
        session,
        company_id=company.id,
        lot=lot,
        farm_id=lot.farm_id,
        house_id=lot.house_id,
        event_type=EventType.EGG_DISPATCH,
        status=EventStatus.PENDING_REVIEW,
        registered_by_id=actor.id,
        reviewed_by_id=actor.id,
        approved_by_id=None,
        hatchery_id=hatchery_id,
        breed_id=breed_id,
        days_ago=2,
    )

    await _ensure_event(
        session,
        company_id=company.id,
        lot=lot,
        farm_id=lot.farm_id,
        house_id=lot.house_id,
        event_type=EventType.INCUBATION_LOAD,
        status=EventStatus.IN_REVIEW,
        registered_by_id=actor.id,
        reviewed_by_id=actor.id,
        approved_by_id=None,
        hatchery_id=hatchery_id,
        breed_id=breed_id,
        days_ago=1,
    )


async def main() -> int:
    print("Live data boost: ensuring readiness coverage...")
    async with async_session() as session:
        try:
            await _ensure_company1_missing_statuses_and_types(session)
            await _ensure_company3_operational_data(session)
            await session.commit()
            print("Live data boost completed.")
            return 0
        except Exception as exc:  # pragma: no cover
            await session.rollback()
            print(f"Live data boost failed: {exc}")
            return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

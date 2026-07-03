"""Readiness check for live functional testing data.

Run:
    cd backend
    PYTHONPATH=. python3 seeds/live_readiness_check.py
"""

import asyncio
import logging
from collections import defaultdict

from sqlalchemy import func, select, text

import app.lots.models  # noqa: F401 - register LotPhase/OpeningBalance mappers
from app.auth.models import User
from app.database import async_session
from app.integrations.sap.models import SapReference
from app.masters.models import Company, Lot
from app.operations.models import OperationalEvent


logging.basicConfig(level=logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)


MIN_ACTIVE_LOTS_PER_COMPANY = 4
MIN_COMPANIES_WITH_OPERATIONAL_DATA = 2
MIN_PURCHASE_ORDERS_PER_COMPANY = 6
MIN_TRANSFER_ORDERS_PER_COMPANY = 3

REQUIRED_EVENT_STATUSES = {
    "REGISTERED",
    "PENDING_REVIEW",
    "IN_REVIEW",
    "CORRECTED",
    "APPROVED",
    "REJECTED",
}

REQUIRED_EVENT_TYPES = {
    "BIRD_RECEPTION",
    "FEED_REGISTRATION",
    "EGG_COLLECTION",
    "EGG_DISPATCH",
    "INCUBATION_LOAD",
    "MORTALITY_RECORDING",
}

REQUIRED_SAP_REF_TYPES = {
    "PURCHASE_ORDER",
    "TRANSFER_ORDER",
}

REQUIRED_PURCHASE_ORDER_STAGES = {
    "grandparent_rearing",
    "grandparent_production",
    "breeder_rearing",
    "breeder_production",
    "hatchery",
    "broiler",
}


def _print_check(ok: bool, label: str, details: str = "") -> None:
    prefix = "PASS" if ok else "FAIL"
    print(f"[{prefix}] {label}")
    if details:
        print(f"       {details}")


async def main() -> int:
    async with async_session() as session:
        companies = (
            await session.execute(select(Company.id, Company.name).order_by(Company.id))
        ).all()

        company_metrics: dict[int, dict[str, int]] = {}
        for company_id, _ in companies:
            users = (
                await session.execute(
                    select(func.count(User.id)).where(User.company_id == company_id)
                )
            ).scalar() or 0
            lots = (
                await session.execute(
                    select(func.count(Lot.id)).where(Lot.company_id == company_id)
                )
            ).scalar() or 0
            events = (
                await session.execute(
                    select(func.count(OperationalEvent.id)).where(
                        OperationalEvent.company_id == company_id
                    )
                )
            ).scalar() or 0
            sap_refs = (
                await session.execute(
                    select(func.count(SapReference.id)).where(
                        SapReference.company_id == company_id
                    )
                )
            ).scalar() or 0

            company_metrics[company_id] = {
                "users": users,
                "lots": lots,
                "events": events,
                "sap_refs": sap_refs,
            }

        lot_status_rows = (
            await session.execute(
                text(
                    """
                    SELECT company_id, status::text, count(*)
                    FROM lots
                    GROUP BY company_id, status::text
                    """
                )
            )
        ).all()

        event_status_rows = (
            await session.execute(
                text(
                    """
                    SELECT company_id, status::text, count(*)
                    FROM operational_events
                    GROUP BY company_id, status::text
                    """
                )
            )
        ).all()

        event_type_rows = (
            await session.execute(
                text(
                    """
                    SELECT company_id, event_type::text, count(*)
                    FROM operational_events
                    GROUP BY company_id, event_type::text
                    """
                )
            )
        ).all()

        sap_ref_rows = (
            await session.execute(
                text(
                    """
                    SELECT company_id, ref_type::text, count(*)
                    FROM sap_references
                    GROUP BY company_id, ref_type::text
                    """
                )
            )
        ).all()

        sap_po_stage_rows = (
            await session.execute(
                text(
                    """
                    SELECT company_id, COALESCE(extra_data->>'stage', '') AS stage, count(*)
                    FROM sap_references
                    WHERE ref_type::text = 'PURCHASE_ORDER'
                    GROUP BY company_id, COALESCE(extra_data->>'stage', '')
                    """
                )
            )
        ).all()

        users_without_role = (
            await session.execute(
                select(func.count(User.id)).where(User.company_id.is_not(None), User.role_id.is_(None))
            )
        ).scalar() or 0

    lot_status_map: dict[int, dict[str, int]] = defaultdict(dict)
    for company_id, status, count in lot_status_rows:
        lot_status_map[company_id][str(status)] = count

    event_status_map: dict[int, dict[str, int]] = defaultdict(dict)
    for company_id, status, count in event_status_rows:
        event_status_map[company_id][str(status)] = count

    event_type_map: dict[int, dict[str, int]] = defaultdict(dict)
    for company_id, event_type, count in event_type_rows:
        event_type_map[company_id][str(event_type)] = count

    sap_ref_map: dict[int, dict[str, int]] = defaultdict(dict)
    for company_id, ref_type, count in sap_ref_rows:
        sap_ref_map[company_id][str(ref_type)] = count

    sap_po_stage_map: dict[int, dict[str, int]] = defaultdict(dict)
    for company_id, stage, count in sap_po_stage_rows:
        stage_key = str(stage).strip()
        if stage_key:
            sap_po_stage_map[company_id][stage_key] = count

    print("=" * 72)
    print("Global Avicola - Live Test Data Readiness")
    print("=" * 72)

    print("\nCompany inventory:")
    company_name_map = {cid: name for cid, name in companies}
    for cid, _ in companies:
        m = company_metrics[cid]
        print(
            f"- company_id={cid} name={company_name_map[cid]} "
            f"users={m['users']} lots={m['lots']} events={m['events']} sap_refs={m['sap_refs']}"
        )

    checks_failed = 0

    has_min_companies = len(companies) >= 2
    _print_check(has_min_companies, "At least 2 companies are registered", f"found={len(companies)}")
    if not has_min_companies:
        checks_failed += 1

    companies_with_oper_data = [
        cid
        for cid, metrics in company_metrics.items()
        if metrics["lots"] > 0 and metrics["events"] > 0 and metrics["sap_refs"] > 0
    ]
    enough_companies_with_oper_data = (
        len(companies_with_oper_data) >= MIN_COMPANIES_WITH_OPERATIONAL_DATA
    )
    _print_check(
        enough_companies_with_oper_data,
        "Operational data exists in at least 2 companies",
        f"companies_with_oper_data={companies_with_oper_data}",
    )
    if not enough_companies_with_oper_data:
        checks_failed += 1

    roles_ok = users_without_role == 0
    _print_check(roles_ok, "No users without role", f"users_without_role={users_without_role}")
    if not roles_ok:
        checks_failed += 1

    # Company-specific checks for all companies that have at least one assigned user
    target_companies = [cid for cid, metrics in company_metrics.items() if metrics["users"] > 0]
    for cid in target_companies:
        cname = company_name_map[cid]
        active_lots = lot_status_map.get(cid, {}).get("ACTIVE", 0)
        has_closed = lot_status_map.get(cid, {}).get("CLOSED", 0) > 0

        lots_ok = active_lots >= MIN_ACTIVE_LOTS_PER_COMPANY
        _print_check(
            lots_ok,
            f"{cname}: at least {MIN_ACTIVE_LOTS_PER_COMPANY} active lots",
            f"active_lots={active_lots}",
        )
        if not lots_ok:
            checks_failed += 1

        closed_ok = has_closed
        _print_check(
            closed_ok,
            f"{cname}: at least 1 closed lot",
            f"closed_lots={lot_status_map.get(cid, {}).get('CLOSED', 0)}",
        )
        if not closed_ok:
            checks_failed += 1

        statuses_present = set(event_status_map.get(cid, {}).keys())
        missing_statuses = sorted(REQUIRED_EVENT_STATUSES - statuses_present)
        statuses_ok = not missing_statuses
        _print_check(
            statuses_ok,
            f"{cname}: required event statuses coverage",
            "missing=" + (", ".join(missing_statuses) if missing_statuses else "none"),
        )
        if not statuses_ok:
            checks_failed += 1

        event_types_present = set(event_type_map.get(cid, {}).keys())
        missing_event_types = sorted(REQUIRED_EVENT_TYPES - event_types_present)
        event_types_ok = not missing_event_types
        _print_check(
            event_types_ok,
            f"{cname}: required event types coverage",
            "missing=" + (", ".join(missing_event_types) if missing_event_types else "none"),
        )
        if not event_types_ok:
            checks_failed += 1

        sap_types_present = set(sap_ref_map.get(cid, {}).keys())
        missing_sap_types = sorted(REQUIRED_SAP_REF_TYPES - sap_types_present)
        sap_ok = not missing_sap_types
        _print_check(
            sap_ok,
            f"{cname}: required SAP references coverage",
            "missing=" + (", ".join(missing_sap_types) if missing_sap_types else "none"),
        )
        if not sap_ok:
            checks_failed += 1

        purchase_orders = sap_ref_map.get(cid, {}).get("PURCHASE_ORDER", 0)
        po_ok = purchase_orders >= MIN_PURCHASE_ORDERS_PER_COMPANY
        _print_check(
            po_ok,
            f"{cname}: at least {MIN_PURCHASE_ORDERS_PER_COMPANY} purchase orders",
            f"purchase_orders={purchase_orders}",
        )
        if not po_ok:
            checks_failed += 1

        po_stages_present = set(sap_po_stage_map.get(cid, {}).keys())
        missing_po_stages = sorted(REQUIRED_PURCHASE_ORDER_STAGES - po_stages_present)
        po_stage_ok = not missing_po_stages
        _print_check(
            po_stage_ok,
            f"{cname}: purchase order stage coverage",
            "missing=" + (", ".join(missing_po_stages) if missing_po_stages else "none"),
        )
        if not po_stage_ok:
            checks_failed += 1

        transfer_orders = sap_ref_map.get(cid, {}).get("TRANSFER_ORDER", 0)
        sto_ok = transfer_orders >= MIN_TRANSFER_ORDERS_PER_COMPANY
        _print_check(
            sto_ok,
            f"{cname}: at least {MIN_TRANSFER_ORDERS_PER_COMPANY} transfer orders",
            f"transfer_orders={transfer_orders}",
        )
        if not sto_ok:
            checks_failed += 1

    print("\n" + "-" * 72)
    if checks_failed == 0:
        print("READY: live testing dataset meets minimum coverage.")
    else:
        print(f"NOT READY: {checks_failed} blocking checks failed.")
    print("-" * 72)

    return 0 if checks_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

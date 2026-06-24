"""Dashboard service — mobile operator KPIs and admin KPIs."""
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..operations.models import EventStatus, EventType, OperationalEvent


class DashboardService:
    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")

    async def get_mobile_dashboard(self) -> dict:
        """Quick KPIs for operators on mobile."""
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        today_events = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.registered_by_id == self.current_user["id"],
                OperationalEvent.created_at >= today,
            )
        )
        pending_review = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.registered_by_id == self.current_user["id"],
                OperationalEvent.status == EventStatus.RETURNED,
            )
        )
        approved_today = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.registered_by_id == self.current_user["id"],
                OperationalEvent.status == EventStatus.APPROVED,
                OperationalEvent.updated_at >= today,
            )
        )

        return {
            "today_events": today_events.scalar() or 0,
            "pending_corrections": pending_review.scalar() or 0,
            "approved_today": approved_today.scalar() or 0,
            "quick_actions": [
                {"label": "Registrar Alimento", "path": "/operations/new?type=feed_registration", "icon": "🌾"},
                {"label": "Registrar Mortalidad", "path": "/operations/new?type=mortality_recording", "icon": "💀"},
                {"label": "Registrar Pesaje", "path": "/operations/new?type=weight_recording", "icon": "⚖️"},
                {"label": "Recolección Huevos", "path": "/operations/new?type=egg_collection", "icon": "🥚"},
            ],
        }

    async def get_admin_dashboard(self) -> dict:
        """Admin/supervisor KPIs."""
        # Total events by status
        status_counts = await self.db.execute(
            select(OperationalEvent.status, func.count().label("cnt")).where(
                OperationalEvent.company_id == self.company_id,
            ).group_by(OperationalEvent.status)
        )
        status_dist = {row.status.value: row.cnt for row in status_counts.fetchall()}

        # Pending review
        pending = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.status.in_([EventStatus.REGISTERED, EventStatus.PENDING_REVIEW]),
            )
        )

        # Pending approval
        pending_approval = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.status == EventStatus.CORRECTED,
            )
        )

        # Events by type (top 5)
        type_counts = await self.db.execute(
            select(OperationalEvent.event_type, func.count().label("cnt")).where(
                OperationalEvent.company_id == self.company_id,
            ).group_by(OperationalEvent.event_type).order_by(func.count().desc()).limit(5)
        )
        top_types = {row.event_type.value: row.cnt for row in type_counts.fetchall()}

        # Events last 7 days
        from datetime import datetime, timedelta, timezone
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        last_week = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.created_at >= seven_days_ago,
            )
        )

        return {
            "total_events": sum(status_dist.values()),
            "by_status": status_dist,
            "pending_review": pending.scalar() or 0,
            "pending_approval": pending_approval.scalar() or 0,
            "top_event_types": top_types,
            "last_7_days": last_week.scalar() or 0,
            "lots_by_type": await self._get_lots_by_type(),
            "mortality_trend": await self._get_mortality_trend(),
        }

    async def _get_lots_by_type(self) -> dict:
        """Count active lots grouped by bird_type."""
        from ..masters.models import Lot
        rows = await self.db.execute(
            select(Lot.bird_type, func.count().label("cnt"))
            .where(Lot.company_id == self.company_id, Lot.status == "active")
            .group_by(Lot.bird_type)
        )
        return {str(row.bird_type): row.cnt for row in rows.fetchall()}

    async def _get_mortality_trend(self) -> list[dict]:
        """Weekly mortality totals for the last 8 weeks."""
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import cast, Integer, extract
        now = datetime.now(timezone.utc)
        eight_weeks_ago = now - timedelta(weeks=8)
        rows = await self.db.execute(
            select(
                extract("isoyear", OperationalEvent.event_date).label("yr"),
                extract("week", OperationalEvent.event_date).label("wk"),
                func.sum(OperationalEvent.total_count).label("total"),
            )
            .where(
                OperationalEvent.company_id == self.company_id,
                OperationalEvent.event_type == EventType.MORTALITY_RECORDING,
                OperationalEvent.event_date >= eight_weeks_ago,
            )
            .group_by("yr", "wk")
            .order_by("yr", "wk")
        )
        return [
            {"week": f"S{int(r.wk)}", "mortality": int(r.total or 0)}
            for r in rows.fetchall()
        ]

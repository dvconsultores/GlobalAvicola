"""Dashboard service — mobile operator KPIs and admin KPIs."""
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..operations.models import EventStatus, EventType, OperationalAlert, OperationalEvent


class DashboardService:
    def __init__(self, db: AsyncSession, current_user: dict[str, Any]):
        self.db = db
        self.current_user = current_user
        self.company_id = current_user.get("company_id")
        self._unidades_cache = None

    async def _lotes(self):
        """Subconsulta de lotes alcanzables (`OD-16`: también para la autoridad global).

        `GA-REM-040` fase 4 · `GA-FE-02-D`. El panel es el agregado de empresa por
        excelencia: sus contadores y su tendencia sumaban toda la compañía, y `lots_by_type`
        llegaba a **nombrar** las cadenas ajenas con su recuento — una fuga de dimensión,
        que no enseña ninguna fila y sin embargo dice que existen y cuántas hay. La
        autoridad global quedaba exenta (fase 3); `OD-16` la somete a la misma puerta: su
        alcance son las unidades **habilitadas** de la empresa, así que con todo apagado
        los agregados son cero y con una encendida solo ella suma.
        """
        if self._unidades_cache is None:
            from ..business_units.service import unidades_de_alcance_productivo

            self._unidades_cache = await unidades_de_alcance_productivo(
                self.db, current_user=self.current_user, company_id=self.company_id
            )
        from ..business_units.scope import lotes_alcanzables

        return lotes_alcanzables(self.company_id, self._unidades_cache)

    async def get_mobile_dashboard(self) -> dict:
        """Quick KPIs for operators on mobile."""
        # `GA-REM-040` fase 4: los agregados del panel cuentan solo sobre lotes
        # alcanzables. Un evento **sin lote** no contribuye — misma decisión que la fase 3
        # tomó con el lote sin cadena: `OD-10.c` lo manda a «pendiente de clasificar», que
        # es la fase 6, y hasta entonces lo seguro es que no sume. Queda declarado.
        _lotes = await self._lotes()
        _ambito = [] if _lotes is None else [OperationalEvent.lot_id.in_(_lotes)]
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        today_events = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                *_ambito,
                OperationalEvent.registered_by_id == self.current_user["id"],
                OperationalEvent.created_at >= today,
            )
        )
        pending_review = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                *_ambito,
                OperationalEvent.registered_by_id == self.current_user["id"],
                OperationalEvent.status == EventStatus.RETURNED,
            )
        )
        approved_today = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                *_ambito,
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
        # `GA-REM-040` fase 4: los agregados del panel cuentan solo sobre lotes
        # alcanzables. Un evento **sin lote** no contribuye — misma decisión que la fase 3
        # tomó con el lote sin cadena: `OD-10.c` lo manda a «pendiente de clasificar», que
        # es la fase 6, y hasta entonces lo seguro es que no sume. Queda declarado.
        _lotes = await self._lotes()
        _ambito = [] if _lotes is None else [OperationalEvent.lot_id.in_(_lotes)]
        # Total events by status
        status_counts = await self.db.execute(
            select(OperationalEvent.status, func.count().label("cnt")).where(
                OperationalEvent.company_id == self.company_id,
                *_ambito,
            ).group_by(OperationalEvent.status)
        )
        status_dist = {row.status.value: row.cnt for row in status_counts.fetchall()}

        # Pending review
        pending = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                *_ambito,
                OperationalEvent.status.in_([EventStatus.REGISTERED, EventStatus.PENDING_REVIEW]),
            )
        )

        # Pending approval
        pending_approval = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                *_ambito,
                OperationalEvent.status == EventStatus.CORRECTED,
            )
        )

        # Events by type (top 5)
        type_counts = await self.db.execute(
            select(OperationalEvent.event_type, func.count().label("cnt")).where(
                OperationalEvent.company_id == self.company_id,
                *_ambito,
            ).group_by(OperationalEvent.event_type).order_by(func.count().desc()).limit(5)
        )
        top_types = {row.event_type.value: row.cnt for row in type_counts.fetchall()}

        # Events last 7 days
        from datetime import datetime, timedelta, timezone
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        last_week = await self.db.execute(
            select(func.count()).select_from(OperationalEvent).where(
                OperationalEvent.company_id == self.company_id,
                *_ambito,
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
            "active_alerts": await self._get_active_alerts(),
        }

    async def _get_lots_by_type(self) -> dict:
        """Lotes activos por cadena, **solo de las cadenas alcanzables**.

        Acotar el total y dejar la dimensión suelta no protege nada: el grupo lleva el
        nombre de la cadena ajena y su recuento. Se filtran los grupos, no se ocultan
        después.
        """
        from ..masters.models import Lot
        consulta = (
            select(Lot.bird_type, func.count().label("cnt"))
            .where(Lot.company_id == self.company_id, Lot.status == "active")
        )
        lotes = await self._lotes()
        if lotes is not None:
            consulta = consulta.where(Lot.id.in_(lotes))
        rows = await self.db.execute(consulta.group_by(Lot.bird_type))
        # `R-216`: claves = **valor** del enum (`'broiler'`), no `str()` — `str()` de un
        # `(str, Enum)` producía `'BirdTypeEnum.BROILER'` y `DashboardPage`, que busca
        # `'broiler'`, mostraba **0** en las cuatro tarjetas mientras la suma era
        # correcta. El contrato queda fijado por `test_r216_lots_by_type_contract.py`.
        return {row.bird_type.value: row.cnt for row in rows.fetchall()}

    async def _get_mortality_trend(self) -> list[dict]:
        """Weekly mortality totals for the last 8 weeks."""
        # `GA-REM-040` fase 4: los agregados del panel cuentan solo sobre lotes
        # alcanzables. Un evento **sin lote** no contribuye — misma decisión que la fase 3
        # tomó con el lote sin cadena: `OD-10.c` lo manda a «pendiente de clasificar», que
        # es la fase 6, y hasta entonces lo seguro es que no sume. Queda declarado.
        _lotes = await self._lotes()
        _ambito = [] if _lotes is None else [OperationalEvent.lot_id.in_(_lotes)]
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import extract
        from ..operations.models import BirdMovement
        now = datetime.now(timezone.utc)
        eight_weeks_ago = now - timedelta(weeks=8)
        rows = await self.db.execute(
            select(
                extract("isoyear", OperationalEvent.event_date).label("yr"),
                extract("week", OperationalEvent.event_date).label("wk"),
                func.sum(BirdMovement.quantity).label("total"),
            )
            .join(BirdMovement, BirdMovement.event_id == OperationalEvent.id)
            .where(
                OperationalEvent.company_id == self.company_id,
                *_ambito,
                OperationalEvent.event_type == EventType.MORTALITY_RECORDING,
                # `GA-REM-022` (R-141): mismo conjunto filtrado que el detalle
                # certificado — cancelados fuera de la tendencia.
                OperationalEvent.status.in_([
                    EventStatus.APPROVED, EventStatus.CONSOLIDATED,
                    EventStatus.SENT_TO_SAP, EventStatus.SAP_CONFIRMED,
                ]),
                OperationalEvent.event_date >= eight_weeks_ago,
            )
            .group_by("yr", "wk")
            .order_by("yr", "wk")
        )
        return [
            {"week": f"S{int(r.wk)}", "mortality": int(r.total or 0)}
            for r in rows.fetchall()
        ]

    async def _get_active_alerts(self) -> list[dict]:
        """Return last 10 unresolved alerts for the company."""
        # `GA-REM-040` fase 4: los agregados del panel cuentan solo sobre lotes
        # alcanzables. Un evento **sin lote** no contribuye — misma decisión que la fase 3
        # tomó con el lote sin cadena: `OD-10.c` lo manda a «pendiente de clasificar», que
        # es la fase 6, y hasta entonces lo seguro es que no sume. Queda declarado.
        _lotes = await self._lotes()
        if _lotes is None:
            # `R-204` · fail-closed: sin resolutor de alcance no se sirve ninguna alerta.
            return []
        rows = await self.db.execute(
            select(
                OperationalAlert.id,
                OperationalAlert.lot_id,
                OperationalAlert.alert_type,
                OperationalAlert.severity,
                OperationalAlert.message,
                OperationalAlert.actual_value,
                OperationalAlert.created_at,
            )
            .where(
                OperationalAlert.company_id == self.company_id,
                # `R-204` · `OD-16`: solo alertas de lotes alcanzables — el `_ambito`
                # se calculaba y **no se aplicaba**, y el panel nombraba lotes de
                # unidades no concedidas.
                OperationalAlert.lot_id.in_(_lotes),
                OperationalAlert.is_resolved == False,  # noqa: E712
            )
            .order_by(OperationalAlert.created_at.desc())
            .limit(10)
        )
        return [
            {
                "id": r.id,
                "lot_id": r.lot_id,
                "alert_type": r.alert_type,
                "severity": r.severity,
                "message": r.message,
                "actual_value": r.actual_value,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows.fetchall()
        ]

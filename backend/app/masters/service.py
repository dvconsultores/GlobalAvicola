"""
Generic CRUD service for master data entities.
Multi-company aware: auto-filters by company_id for non-super-admin users.
"""
from typing import Any, Optional, Type

from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import Base


class MasterService:
    """Generic CRUD service for any SQLAlchemy model, with multi-company support."""

    def __init__(
        self,
        db: AsyncSession,
        model: Type[Base],
        current_user: Optional[dict[str, Any]] = None,
    ):
        self.db = db
        self.model = model
        self.current_user = current_user or {}
        self.is_super_admin = self.current_user.get("is_super_admin", False)
        self.user_company_id = self.current_user.get("company_id")

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
        query = query.where(self.model.id == item_id)
        result = await self.db.execute(query)
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} no encontrado",
            )
        return item

    async def create(self, data: Any) -> Any:
        """Create a new item. Auto-assigns company_id from current user."""
        item_data = data.model_dump()

        # Auto-assign company_id if model has it and user has one
        if hasattr(self.model, "company_id") and "company_id" in item_data:
            if item_data["company_id"] is None and self.user_company_id:
                item_data["company_id"] = self.user_company_id

        item = self.model(**item_data)
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def update(self, item_id: int, data: Any) -> Any:
        """Update an existing item. Respects company isolation."""
        item = await self.get_by_id(item_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def deactivate(self, item_id: int) -> None:
        """Soft delete: set is_active=False. Respects company isolation."""
        item = await self.get_by_id(item_id)
        item.is_active = False
        await self.db.flush()

"""
REST API router for master data entities.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from . import models, schemas
from .service import MasterService

router = APIRouter(prefix="/masters", tags=["Masters"])


# Helper to create CRUD endpoints for a master entity
def register_crud(
    prefix: str,
    model,
    create_schema,
    read_schema,
    update_schema=None,
    search_fields: Optional[list[str]] = None,
):
    """Register standard CRUD endpoints for a master entity using add_api_route."""

    async def list_items(
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        search: str = Query(""),
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        service = MasterService(db, model, current_user)
        items, total = await service.get_all(
            skip=skip, limit=limit, search=search,
            search_fields=search_fields or ["name"],
        )
        return [read_schema.model_validate(item) for item in items]

    async def create_item(
        data: create_schema,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        service = MasterService(db, model, current_user)
        item = await service.create(data)
        return read_schema.model_validate(item)

    async def get_item(
        item_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        service = MasterService(db, model, current_user)
        item = await service.get_by_id(item_id)
        return read_schema.model_validate(item)

    async def deactivate_item(
        item_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        service = MasterService(db, model, current_user)
        await service.deactivate(item_id)

    # Register routes with unique names
    router.add_api_route(f"/{prefix}", list_items, methods=["GET"], response_model=list[read_schema], name=f"list_{prefix}")
    router.add_api_route(f"/{prefix}", create_item, methods=["POST"], response_model=read_schema, status_code=201, name=f"create_{prefix}")
    router.add_api_route(f"/{prefix}/{{item_id}}", get_item, methods=["GET"], response_model=read_schema, name=f"get_{prefix}")
    router.add_api_route(f"/{prefix}/{{item_id}}", deactivate_item, methods=["DELETE"], status_code=204, name=f"delete_{prefix}")

    if update_schema:
        async def update_item(
            item_id: int,
            data: update_schema,
            db: AsyncSession = Depends(get_db),
            current_user: dict = Depends(get_current_user),
        ):
            service = MasterService(db, model, current_user)
            item = await service.update(item_id, data)
            return read_schema.model_validate(item)

        router.add_api_route(f"/{prefix}/{{item_id}}", update_item, methods=["PUT"], response_model=read_schema, name=f"update_{prefix}")


# ============================================================
# Register CRUD for all master entities
# ============================================================

register_crud("companies", models.Company, schemas.CompanyCreate, schemas.CompanyRead, schemas.CompanyUpdate, ["name", "tax_id"])
register_crud("farms", models.Farm, schemas.FarmCreate, schemas.FarmRead, schemas.FarmUpdate, ["name", "code", "location"])
register_crud("houses", models.House, schemas.HouseCreate, schemas.HouseRead, schemas.HouseUpdate, ["name"])
register_crud("hatcheries", models.Hatchery, schemas.HatcheryCreate, schemas.HatcheryRead, schemas.HatcheryUpdate, ["name", "code"])
register_crud("incubators", models.Incubator, schemas.IncubatorCreate, schemas.IncubatorRead, None, ["name"])
register_crud("hatchers", models.Hatcher, schemas.HatcherCreate, schemas.HatcherRead, None, ["name"])
register_crud("genetic-lines", models.GeneticLine, schemas.GeneticLineCreate, schemas.GeneticLineRead, None, ["name", "code", "supplier"])
register_crud("breeds", models.Breed, schemas.BreedCreate, schemas.BreedRead, None, ["name"])
register_crud("productive-phases", models.ProductivePhase, schemas.ProductivePhaseCreate, schemas.ProductivePhaseRead, None, ["name", "code"])
register_crud("suppliers", models.Supplier, schemas.SupplierCreate, schemas.SupplierRead, None, ["name", "sap_code"])
register_crud("feed-types", models.FeedType, schemas.FeedTypeCreate, schemas.FeedTypeRead, None, ["name", "code"])
register_crud("vaccines", models.Vaccine, schemas.VaccineCreate, schemas.VaccineRead, None, ["name", "laboratory"])
register_crud("medications", models.Medication, schemas.MedicationCreate, schemas.MedicationRead, None, ["name", "laboratory"])
register_crud("mortality-causes", models.MortalityCause, schemas.MortalityCauseCreate, schemas.MortalityCauseRead, None, ["name", "category"])
register_crud("cull-causes", models.CullCause, schemas.CullCauseCreate, schemas.CullCauseRead, None, ["name", "category"])
register_crud("transports", models.Transport, schemas.TransportCreate, schemas.TransportRead, None, ["name", "plate"])
register_crud("processing-plants", models.ProcessingPlant, schemas.ProcessingPlantCreate, schemas.ProcessingPlantRead, None, ["name", "location"])
register_crud("rejection-reasons", models.RejectionReason, schemas.RejectionReasonCreate, schemas.RejectionReasonRead, None, ["name", "category"])
register_crud("correction-types", models.CorrectionType, schemas.CorrectionTypeCreate, schemas.CorrectionTypeRead, None, ["name"])


# ============================================================
# Special endpoints
# ============================================================

@router.get("/farms/{farm_id}/houses", response_model=list[schemas.HouseRead])
async def get_houses_by_farm(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get houses belonging to a specific farm. Validates farm belongs to user's company."""
    company_id = current_user.get("company_id")
    is_super_admin = current_user.get("is_super_admin", False)
    # Verify farm belongs to user's company (super admins bypass)
    if not is_super_admin and company_id is not None:
        farm_check = await db.execute(
            select(models.Farm).where(models.Farm.id == farm_id, models.Farm.company_id == company_id)
        )
        if not farm_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Granja no encontrada")
    result = await db.execute(
        select(models.House).where(models.House.farm_id == farm_id)
    )
    return [schemas.HouseRead.model_validate(h) for h in result.scalars().all()]


@router.get("/hatcheries/{hatchery_id}/incubators", response_model=list[schemas.IncubatorRead])
async def get_incubators_by_hatchery(
    hatchery_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get incubators belonging to a specific hatchery. Validates hatchery belongs to user's company."""
    company_id = current_user.get("company_id")
    is_super_admin = current_user.get("is_super_admin", False)
    # Verify hatchery belongs to user's company (super admins bypass)
    if not is_super_admin and company_id is not None:
        hatchery_check = await db.execute(
            select(models.Hatchery).where(models.Hatchery.id == hatchery_id, models.Hatchery.company_id == company_id)
        )
        if not hatchery_check.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Incubadora no encontrada")
    result = await db.execute(
        select(models.Incubator).where(models.Incubator.hatchery_id == hatchery_id)
    )
    return [schemas.IncubatorRead.model_validate(i) for i in result.scalars().all()]

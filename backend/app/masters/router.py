"""
REST API router for master data entities.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..transaction import RutaTransaccional
from ..dependencies import get_current_user, require_permission
from . import curves, models, schemas
from .service import MasterService

router = APIRouter(route_class=RutaTransaccional, prefix="/masters", tags=["Masters"])


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
        response: Response,
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        search: str = Query(""),
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(require_permission("masters", "read")),
    ):
        service = MasterService(db, model, current_user)
        items, total = await service.get_all(
            skip=skip, limit=limit, search=search,
            search_fields=search_fields or ["name"],
        )
        # `GA-REM-033 AC01` / `R-89`. El total se calculaba y se tiraba, de modo que la
        # interfaz mostraba el tamaño de la página donde promete «resultados». Viaja en
        # cabecera y no en el cuerpo: 43 puntos del frontend leen este endpoint como lista, y
        # un defecto de contador no justifica cambiarlos todos.
        response.headers["X-Total-Count"] = str(total)
        response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
        return [read_schema.model_validate(item) for item in items]

    async def create_item(
        data: create_schema,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(require_permission("masters", "create")),
    ):
        service = MasterService(db, model, current_user)
        item = await service.create(data)
        return read_schema.model_validate(item)

    async def get_item(
        item_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(require_permission("masters", "read")),
    ):
        service = MasterService(db, model, current_user)
        item = await service.get_by_id(item_id)
        return read_schema.model_validate(item)

    async def deactivate_item(
        item_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(require_permission("masters", "delete")),
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
            current_user: dict = Depends(require_permission("masters", "update")),
        ):
            service = MasterService(db, model, current_user)
            item = await service.update(item_id, data)
            return read_schema.model_validate(item)

        router.add_api_route(f"/{prefix}/{{item_id}}", update_item, methods=["PUT"], response_model=read_schema, name=f"update_{prefix}")


# ============================================================
# Register CRUD for all master entities
# ============================================================

# `GA-REM-033` enmienda A / `R-127`. El catálogo responde con `CompanyCatalogRead`, una
# proyección explícita sin `sap_config` (`OD-18`). Con `CompanyRead(CompanyBase)` la fila
# entera viajaba y, al ser la columna `String`, una configuración poblada rompía el listado.
register_crud("companies", models.Company, schemas.CompanyCreate, schemas.CompanyCatalogRead, schemas.CompanyUpdate, ["name", "tax_id"])
register_crud("farms", models.Farm, schemas.FarmCreate, schemas.FarmRead, schemas.FarmUpdate, ["name", "code", "location"])
register_crud("houses", models.House, schemas.HouseCreate, schemas.HouseRead, schemas.HouseUpdate, ["name"])
register_crud("hatcheries", models.Hatchery, schemas.HatcheryCreate, schemas.HatcheryRead, schemas.HatcheryUpdate, ["name", "code"])
register_crud("incubators", models.Incubator, schemas.IncubatorCreate, schemas.IncubatorRead, schemas.IncubatorUpdate, ["name"])
register_crud("hatchers", models.Hatcher, schemas.HatcherCreate, schemas.HatcherRead, schemas.HatcherUpdate, ["name"])
# `GA-REM-039` / `OD-08`. El área es dato maestro configurable: los nombres los pone el
# cliente y ninguno viene sembrado.
register_crud("areas", models.Area, schemas.AreaCreate, schemas.AreaRead, schemas.AreaUpdate, ["name", "code"])
register_crud("genetic-lines", models.GeneticLine, schemas.GeneticLineCreate, schemas.GeneticLineRead, schemas.GeneticLineUpdate, ["name", "code", "supplier"])
register_crud("breeds", models.Breed, schemas.BreedCreate, schemas.BreedRead, schemas.BreedUpdate, ["name"])
register_crud("productive-phases", models.ProductivePhase, schemas.ProductivePhaseCreate, schemas.ProductivePhaseRead, schemas.ProductivePhaseUpdate, ["name", "code"])
register_crud("suppliers", models.Supplier, schemas.SupplierCreate, schemas.SupplierRead, schemas.SupplierUpdate, ["name", "sap_code"])
register_crud("feed-types", models.FeedType, schemas.FeedTypeCreate, schemas.FeedTypeRead, schemas.FeedTypeUpdate, ["name", "code"])
register_crud("vaccines", models.Vaccine, schemas.VaccineCreate, schemas.VaccineRead, schemas.VaccineUpdate, ["name", "laboratory"])
register_crud("medications", models.Medication, schemas.MedicationCreate, schemas.MedicationRead, schemas.MedicationUpdate, ["name", "laboratory"])
register_crud("mortality-causes", models.MortalityCause, schemas.MortalityCauseCreate, schemas.MortalityCauseRead, schemas.MortalityCauseUpdate, ["name", "category"])
register_crud("cull-causes", models.CullCause, schemas.CullCauseCreate, schemas.CullCauseRead, schemas.CullCauseUpdate, ["name", "category"])
register_crud("transports", models.Transport, schemas.TransportCreate, schemas.TransportRead, schemas.TransportUpdate, ["name", "plate"])
register_crud("processing-plants", models.ProcessingPlant, schemas.ProcessingPlantCreate, schemas.ProcessingPlantRead, schemas.ProcessingPlantUpdate, ["name", "location"])
register_crud("rejection-reasons", models.RejectionReason, schemas.RejectionReasonCreate, schemas.RejectionReasonRead, schemas.RejectionReasonUpdate, ["name", "category"])
register_crud("correction-types", models.CorrectionType, schemas.CorrectionTypeCreate, schemas.CorrectionTypeRead, schemas.CorrectionTypeUpdate, ["name"])


# ============================================================
# Special endpoints
# ============================================================

@router.get("/farms/{farm_id}/houses", response_model=list[schemas.HouseRead])
async def get_houses_by_farm(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("masters", "read")),
):
    """Get houses belonging to a specific farm. Validates farm belongs to user's company."""
    company_id = current_user.get("company_id")
    # `GA-REM-002-C` / `R-139` · `OD-14.c`: la granja debe ser de la empresa efectiva, para
    # todos. Sin empresa efectiva no hay granja alcanzable (`R-116`, `OD-14.d`).
    if company_id is None:
        raise HTTPException(status_code=404, detail="Granja no encontrada")
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
    current_user: dict = Depends(require_permission("masters", "read")),
):
    """Get incubators belonging to a specific hatchery. Validates hatchery belongs to user's company."""
    company_id = current_user.get("company_id")
    # `GA-REM-002-C` / `R-139` · `OD-14.c`: ídem `get_houses_by_farm`, con la planta.
    if company_id is None:
        raise HTTPException(status_code=404, detail="Incubadora no encontrada")
    hatchery_check = await db.execute(
        select(models.Hatchery).where(models.Hatchery.id == hatchery_id, models.Hatchery.company_id == company_id)
    )
    if not hatchery_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Incubadora no encontrada")
    result = await db.execute(
        select(models.Incubator).where(models.Incubator.hatchery_id == hatchery_id)
    )
    return [schemas.IncubatorRead.model_validate(i) for i in result.scalars().all()]


# ============================================================
# Curvas estándar de peso · `GA-REM-037` / `OD-06`
# ============================================================
# No pasan por `register_crud` porque la carga no es un alta: es una importación atómica
# con informe de rechazo por fila (`AC06`), y la activación es exclusiva por línea.

@router.get("/genetic-lines/{genetic_line_id}/weight-curves",
            response_model=list[schemas.WeightCurveRead])
async def list_weight_curves(
    genetic_line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("masters", "read")),
):
    """Versiones de curva de una línea genética."""
    await curves._linea_del_usuario(db, genetic_line_id, current_user)
    result = await db.execute(
        select(models.GeneticWeightCurve)
        .where(models.GeneticWeightCurve.genetic_line_id == genetic_line_id)
        .order_by(models.GeneticWeightCurve.created_at.desc())
    )
    return [schemas.WeightCurveRead.model_validate(c) for c in result.scalars().all()]


@router.post("/weight-curves", response_model=schemas.WeightCurveRead, status_code=201)
async def create_weight_curve(
    data: schemas.WeightCurveCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("masters", "create")),
):
    """Carga una versión de curva con su tabla completa. Todo o nada."""
    curva = await curves.crear_version(db, data, current_user)
    return schemas.WeightCurveRead.model_validate(curva)


@router.get("/weight-curves/{curve_id}", response_model=schemas.WeightCurveRead)
async def get_weight_curve(
    curve_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("masters", "read")),
):
    curva = (await db.execute(
        select(models.GeneticWeightCurve).where(models.GeneticWeightCurve.id == curve_id)
    )).scalar_one_or_none()
    if curva is None:
        raise HTTPException(status_code=404, detail="Curva no encontrada")
    # La tenencia se comprueba sobre la línea, que es donde vive.
    await curves._linea_del_usuario(db, curva.genetic_line_id, current_user)
    return schemas.WeightCurveRead.model_validate(curva)


@router.put("/weight-curves/{curve_id}/activate", response_model=schemas.WeightCurveRead)
async def activate_weight_curve(
    curve_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("masters", "update")),
):
    """Hace de esta versión la que tomarán los lotes nuevos. No toca los existentes."""
    curva = (await db.execute(
        select(models.GeneticWeightCurve).where(models.GeneticWeightCurve.id == curve_id)
    )).scalar_one_or_none()
    if curva is None:
        raise HTTPException(status_code=404, detail="Curva no encontrada")
    await curves._linea_del_usuario(db, curva.genetic_line_id, current_user)
    await curves.activar(db, curva)
    await db.refresh(curva)
    return schemas.WeightCurveRead.model_validate(curva)

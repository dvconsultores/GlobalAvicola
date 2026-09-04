from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..transaction import RutaTransaccional
from ..dependencies import get_current_user, require_permission
from ..main import limiter, rate_limit  # S-05: rate limiting
from .schemas import (
    LoginRequest,
    PasswordChangeRequest,
    RefreshRequest,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    SwitchCompanyRequest,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from .service import AuthService

router = APIRouter(route_class=RutaTransaccional)


# ------------------- Auth Endpoints -------------------

@router.post("/login", response_model=TokenResponse, tags=["Auth"])
@rate_limit("5/minute")  # S-05: Anti brute-force (dev: no-op, prod: active)
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).login(data)


@router.post("/refresh", response_model=TokenResponse, tags=["Auth"])
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).refresh_token(data.refresh_token)


@router.get("/me", response_model=UserRead, tags=["Auth"])
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_read = await AuthService(db).get_user(current_user["id"])
    user_read.is_super_admin = current_user.get("is_super_admin", False)
    return user_read


@router.post("/switch-company", response_model=TokenResponse, tags=["Auth"])
async def switch_company(
    data: SwitchCompanyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Super-admin only: issue new tokens scoped to a different company."""
    return await AuthService(db).switch_company(data.company_id, current_user)


# ------------------- User Endpoints -------------------

@router.get("/users", response_model=list[UserRead], tags=["Users"])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "read")),
):
    return await AuthService(db).get_users(skip=skip, limit=limit, search=search)


@router.post("/users", response_model=UserRead, status_code=201, tags=["Users"])
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "create")),
):
    return await AuthService(db).create_user(data)


@router.get("/users/{user_id}", response_model=UserRead, tags=["Users"])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "read")),
):
    return await AuthService(db).get_user(user_id)


@router.put("/users/{user_id}", response_model=UserRead, tags=["Users"])
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "update")),
):
    return await AuthService(db).update_user(user_id, data)


@router.post("/users/{user_id}/password", status_code=204, tags=["Users"])
async def change_password(
    user_id: int,
    data: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Cambia la contraseña de un usuario.

    Endpoint dedicado (`GA-REM-012`). Enviar `password` a `PUT /users/{id}` devolvía
    `200` sin cambiar nada: `P0-13`.
    """
    await AuthService(db).change_password(user_id, data, current_user)


@router.delete("/users/{user_id}", status_code=204, tags=["Users"])
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "delete")),
):
    await AuthService(db).deactivate_user(user_id)


# ------------------- Role Endpoints -------------------

@router.get("/roles", response_model=list[RoleRead], tags=["Roles"])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "read")),
):
    return await AuthService(db).get_roles()


@router.post("/roles", response_model=RoleRead, status_code=201, tags=["Roles"])
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "create")),
):
    return await AuthService(db).create_role(data)


@router.put("/roles/{role_id}", response_model=RoleRead, tags=["Roles"])
async def update_role(
    role_id: int,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "update")),
):
    return await AuthService(db).update_role(role_id, data)

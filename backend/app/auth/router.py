from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..transaction import RutaTransaccional
from ..dependencies import get_current_user, require_permission
from ..main import limiter, rate_limit  # S-05: rate limiting
from .schemas import (
    SessionRead,
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


@router.post("/logout", status_code=204, tags=["Auth"])
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db),
                 current_user: dict = Depends(get_current_user)):
    """`GA-REM-003` · AC04: revoca el refresh token presentado.

    Exige sesión (`AC08b` — la superficie anónima son solo login y refresh) y el
    servicio comprueba que el refresh pertenece **al propio titular**: cerrar la
    sesión de otro no es una operación de usuario. Tampoco hay ventana ciega: si el
    access expiró, el interceptor renueva primero — y si el refresh ya no vale, no
    había nada que revocar.
    """
    await AuthService(db).logout(data.refresh_token, current_user)


@router.get("/me", response_model=SessionRead, tags=["Auth"])
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """La sesión — `GA-REM-040` fase 8 · `T-040-20` · enmienda E.

    **Compone; no calcula.** Cada campo sale de un resolutor ya certificado:

    ```
    empresa efectiva        `get_current_user`, que aplica `OD-11`
    capacidades             el `RBAC` que ya resolvió esa misma dependencia
    habilitadas             `unidades_habilitadas`
    concedidas              `unidades_concedidas`
    efectivas               `unidades_efectivas_por_id`
    ```

    Ninguna decisión de seguridad se toma aquí, y por eso no hay ni un `if` sobre roles,
    empresas o comodines. La sesión **informa al cliente**; lo que protege sigue siendo que
    la ruta deniegue (`AC-H10`).
    """
    from ..business_units.service import (
        unidades_concedidas, unidades_efectivas_por_id, unidades_habilitadas,
    )

    base = await AuthService(db).get_user(current_user["id"])
    empresa = current_user.get("company_id")

    # `is_super_admin` lo asigna el endpoint y no el servicio: `get_user` lee la fila y la
    # fila no sabe nada de comodines. Al componer la sesión perdí esta línea y `/me` empezó a
    # decir que nadie era administrador — lo cazó `test_get_me`, que llevaba ahí desde el
    # principio.
    base.is_super_admin = bool(current_user.get("is_super_admin"))

    return SessionRead(
        **base.model_dump(),
        effective_company_id=empresa,
        permissions=sorted(f"{modulo}:{accion}"
                           for modulo, accion in (current_user.get("permissions") or set())),
        company_business_units=await unidades_habilitadas(db, empresa),
        granted_business_units=await unidades_concedidas(
            db, user_id=current_user["id"], company_id=empresa),
        effective_business_units=await unidades_efectivas_por_id(
            db, user_id=current_user["id"], company_id=empresa),
    )


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
    return await AuthService(db).get_users(skip=skip, limit=limit, search=search, actor=current_user)


@router.post("/users", response_model=UserRead, status_code=201, tags=["Users"])
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "create")),
):
    return await AuthService(db).create_user(data, actor=current_user)


@router.get("/users/{user_id}", response_model=UserRead, tags=["Users"])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "read")),
):
    return await AuthService(db).get_user(user_id, actor=current_user)


@router.put("/users/{user_id}", response_model=UserRead, tags=["Users"])
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "update")),
):
    return await AuthService(db).update_user(user_id, data, actor=current_user)


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
    await AuthService(db).deactivate_user(user_id, actor=current_user)


# ------------------- Role Endpoints -------------------

@router.get("/roles/permissions-catalog", tags=["Roles"])
async def get_permissions_catalog(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "read")),
):
    """`GA-REM-034 AC01`. Módulos y acciones que se pueden conceder.

    Va **antes** de `/roles` a propósito: una ruta con segmento fijo debe declararse antes que
    cualquier otra que pudiera capturarla.
    """
    return AuthService(db).get_permission_catalog()


@router.get("/roles", response_model=list[RoleRead], tags=["Roles"])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "read")),
):
    return await AuthService(db).get_roles(actor=current_user)


@router.post("/roles", response_model=RoleRead, status_code=201, tags=["Roles"])
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "create")),
):
    return await AuthService(db).create_role(data, current_user)


@router.put("/roles/{role_id}", response_model=RoleRead, tags=["Roles"])
async def update_role(
    role_id: int,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("users", "update")),
):
    return await AuthService(db).update_role(role_id, data, current_user)

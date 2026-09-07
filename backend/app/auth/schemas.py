from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ------------------- Auth -------------------

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


# ------------------- User -------------------

class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    phone: Optional[str] = None
    role_id: Optional[int] = None
    company_id: Optional[int] = None
    view_type: str = "web"
    #: `GA-REM-039` / `OD-08`. Área funcional. Nulable: hay usuarios anteriores.
    area_id: Optional[int] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class PasswordChangeRequest(BaseModel):
    """Cambio de contraseña — `GA-REM-012`, regla `RR-05`.

    Endpoint dedicado y no un campo más de `UserUpdate`: enviar `password` a
    `PUT /users/{id}` era aceptado con `200` y descartado en silencio (`P0-13`), y
    admitirlo allí sin control abriría además un vector de toma de cuentas.

    `current_password` es obligatoria cuando el titular cambia la suya y se omite cuando
    un administrador restablece la de otro. La comprobación vive en el servicio, que es
    quien sabe quién pide qué.
    """

    model_config = {"extra": "forbid"}

    current_password: Optional[str] = None
    # RR-05: política única de longitud mínima 8, idéntica en alta, cambio y
    # restablecimiento. El `min_length=6` del login no es una política: restringe un
    # intento de autenticación, no la creación de un secreto.
    new_password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Edición de los datos de un usuario. **No** incluye la contraseña.

    `extra="forbid"` convierte en error explícito lo que antes era un descarte
    silencioso: `ProfilePage` enviaba `{password}` aquí, recibía `200` y mostraba
    «contraseña actualizada» sin que nada cambiara (`P0-13`). La contraseña se cambia por
    `POST /users/{id}/password`.
    """

    model_config = {"extra": "forbid"}

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    #: `GA-REM-039` / `OD-08`. Sin esto un usuario nace sin área y no puede ganarla nunca —
    #: el mismo patrón de `R-93`, donde un rol no podía cambiar sus permisos.
    area_id: Optional[int] = None
    view_type: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: int
    view_type: str
    is_active: bool
    is_super_admin: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    company_name: Optional[str] = None

    model_config = {"from_attributes": True}


class SwitchCompanyRequest(BaseModel):
    company_id: int = Field(..., gt=0)


# ------------------- Role -------------------

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permissions: list["PermissionCreate"] = []


class RoleUpdate(BaseModel):
    """`GA-REM-034 AC02` / `R-93`.

    `permissions` faltaba, de modo que un rol nacía con los suyos y **no podía cambiarlos
    nunca**: `docs/02 §3.1.3` pide «CRUD de roles con permisos granulares» y sin esto se
    quedaba en «alta con permisos granulares».

    Cuando viaja, **sustituye** el conjunto entero —la misma semántica que ya tiene el alta—.
    Es la única que permite **quitar** un permiso, que es la mitad de administrarlos.
    Omitirlo deja los permisos intactos, para que editar el nombre no los borre.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[list["PermissionCreate"]] = None


class PermissionCatalog(BaseModel):
    """`GA-REM-034 AC01` / `R-94`.

    Sin esto, una interfaz de roles tendría que repetir a mano los módulos y las acciones, y
    quedarían desincronizados el día que se añada un módulo. Se derivan de las fuentes de
    verdad: el enum de acciones y los módulos que el enforcement reconoce.
    """
    modules: list[str]
    actions: list[str]


class RoleRead(RoleBase):
    id: int
    is_active: bool
    created_at: datetime
    permissions: list["PermissionRead"] = []

    model_config = {"from_attributes": True}


# ------------------- Permission -------------------

class PermissionCreate(BaseModel):
    module: str
    action: str  # read, create, update, delete, review, correct, approve, reject, send_sap
    scope_type: str = "all"
    scope_id: Optional[int] = None


class PermissionRead(PermissionCreate):
    id: int

    model_config = {"from_attributes": True}

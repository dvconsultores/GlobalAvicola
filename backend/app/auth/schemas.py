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
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


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

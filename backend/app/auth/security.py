from datetime import datetime, timezone, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..audit.context import set_current_audit_user

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)

# ═══════════════════════════════════════════
# Password utilities
# ═══════════════════════════════════════════

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ═══════════════════════════════════════════
# JWT Token utilities (multi-company aware)
# ═══════════════════════════════════════════

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    # PyJWT requires 'sub' to be a string
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    if "company_id" in to_encode and to_encode["company_id"] is not None:
        to_encode["company_id"] = str(to_encode["company_id"])
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    if "company_id" in to_encode and to_encode["company_id"] is not None:
        to_encode["company_id"] = str(to_encode["company_id"])
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


# ═══════════════════════════════════════════
# Current User dependency (multi-company)
# ═══════════════════════════════════════════

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    FastAPI dependency: validates JWT and loads FULL user from DB.
    Returns dict with: id, username, first_name, last_name, email,
    company_id, role_id, role_name, is_super_admin.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
        )

    payload = decode_token(credentials.credentials)

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido: falta subject")

    user_id = int(user_id_str)

    # Lazy import to avoid circular dependency
    from .models import Permission, PermissionAction, Role, User

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")

    # Determine if Super Admin (has permission with module="*" and scope_type="all")
    is_super_admin = False
    role_id = user.role_id
    role_name = None

    permisos: set[tuple[str, str]] = set()

    if user.role:
        role_name = user.role.name
        if user.role.permissions:
            for perm in user.role.permissions:
                accion = perm.action.value if hasattr(perm.action, "value") else str(perm.action)
                permisos.add((perm.module, accion))
                # `R-199` · `OD-13.c`: la autoridad global exige el permiso **en un rol
                # de sistema** (`company_id IS NULL`); en un rol de inquilino el comodín
                # no es la capacidad — un permiso suelto no la concede.
                if (perm.module == "*" and perm.scope_type == "all"
                        and user.role.company_id is None):
                    is_super_admin = True

    # R-48: contexto de compania.
    #
    # Para un usuario normal manda **siempre** la base: un token no puede reclamar una
    # compania ajena, y esa propiedad es la que hace que el aislamiento multiempresa se
    # sostenga (verificado en `test_rbac.py`).
    #
    # El Super Admin es el caso distinto. No pertenece a ninguna compania —asi lo siembra
    # el sistema— y `switch-company` existe precisamente para que pueda situarse en una.
    # Ese endpoint emitia el token con la compania elegida y aqui se descartaba, de modo
    # que el cambio no tenia ningun efecto: con RBAC activo eso dejaba a **nadie** en
    # condiciones de crear un lote, porque solo el Super Admin tiene `lots:create` y no
    # tenia compania en la que crearlo.
    #
    # Honrar el claim solo para quien ya puede operar sobre cualquier compania no concede
    # ningun privilegio nuevo: unicamente acota donde escribe.
    # `OD-11` / `GA-REM-040 AC-C09`…`AC-C14`: la regla vive en `app/tenancy.py`, no aquí.
    # Estaba escrita en este punto desde `R-48` y era correcta, pero solo era invocable
    # desde una petición: un servicio o una tarea de fondo tenían que reimplementarla. Y
    # comprobaba la autoridad del actor sin comprobar que la empresa de destino siguiera
    # existiendo y activa, cosa que puede dejar de ser cierta con la sesión ya abierta.
    from ..tenancy import resolver_empresa_efectiva

    company_id = await resolver_empresa_efectiva(
        db, user=user, reclamada=payload.get("company_id"), puede_cambiar=is_super_admin
    )

    user_dict = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "company_id": company_id,
        "role_id": role_id,
        "role_name": role_name,
        "is_super_admin": is_super_admin,
        # GA-REM-002: los permisos viajan en el contexto para que la autorizacion se
        # decida en el backend. Antes se cargaban solo para deducir `is_super_admin` y
        # se descartaban, de modo que el unico control real vivia en la interfaz.
        "permissions": permisos,
    }

    # Store user in context variable for audit listeners
    set_current_audit_user(user_dict)

    return user_dict


def require_company(current_user: dict = Depends(get_current_user)) -> int:
    """
    Ensures user belongs to a company. Raises 403 if not.
    Returns company_id (always, even for super admin in non-masters endpoints).
    """
    company_id = current_user.get("company_id")
    if company_id is None and not current_user.get("is_super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no asignado a ninguna empresa",
        )
    return company_id


# ═══════════════════════════════════════════════════════════════════════════
# Autorizacion — GA-REM-002
# ═══════════════════════════════════════════════════════════════════════════

def tiene_permiso(current_user: dict, modulo: str, accion: str) -> bool:
    """Decide si el usuario puede ejecutar `accion` sobre `modulo`.

    El Super Admin —quien tiene el permiso comodin `("*", ...)` con alcance `all`— pasa
    siempre. Para el resto se admite el comodin de modulo, de modo que un rol puede
    declarar `("*", "read")` sin enumerar los modulos uno a uno.
    """
    if current_user.get("is_super_admin"):
        return True
    permisos = current_user.get("permissions") or set()
    return (modulo, accion) in permisos or ("*", accion) in permisos


def require_permission(modulo: str, accion: str):
    """Dependencia que exige un permiso concreto.

    Sin cabecera de autorizacion el resultado es 401 —lo produce `get_current_user`—; con
    sesion valida pero sin permiso, 403. Esa distincion importa: decirle a un cliente
    «no estas autenticado» cuando si lo esta le hace reintentar el login en balde.

    La autorizacion se decide aqui y no en la interfaz. Ocultar un boton no es un control
    de seguridad: quien invoque el endpoint con `curl` lo alcanza igual.
    """

    def _dependencia(current_user: dict = Depends(get_current_user)) -> dict:
        if not tiene_permiso(current_user, modulo, accion):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido: {modulo}:{accion}",
            )
        return current_user

    # Marca legible para el verificador de cobertura (AC08).
    _dependencia.__ga_permission__ = (modulo, accion)  # type: ignore[attr-defined]
    return _dependencia

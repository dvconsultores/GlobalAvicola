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

    if user.role:
        role_name = user.role.name
        if user.role.permissions:
            for perm in user.role.permissions:
                if perm.module == "*" and perm.scope_type == "all":
                    is_super_admin = True
                    break

    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "company_id": user.company_id,
        "role_id": role_id,
        "role_name": role_name,
        "is_super_admin": is_super_admin,
    }


def get_company_filter(current_user: dict = Depends(get_current_user)) -> int | None:
    """
    Returns the company_id to filter by.
    Super Admin → None (no filter, sees all companies).
    Regular user → their company_id.
    """
    if current_user.get("is_super_admin"):
        return None  # No filter
    return current_user.get("company_id")


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

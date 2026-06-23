from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Permission, PermissionAction, Role, User
from .security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from .schemas import (
    LoginRequest,
    PermissionCreate,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- Auth ----

    async def login(self, data: LoginRequest) -> TokenResponse:
        result = await self.db.execute(
            select(User).where(User.username == data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta desactivada. Contacte al administrador.",
            )

        # Build token payload with multi-company data
        token_data = {
            "sub": user.id,
            "username": user.username,
            "company_id": user.company_id,
            "role_id": user.role_id,
            "view_type": user.view_type or "web",
        }
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=30 * 60,
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no es refresh token",
            )

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")

        token_data = {"sub": user.id, "username": user.username}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=30 * 60,
        )

    # ---- User CRUD ----

    async def get_users(self, skip: int = 0, limit: int = 20, search: str = "") -> list[UserRead]:
        query = select(User)
        if search:
            query = query.where(
                (User.username.ilike(f"%{search}%"))
                | (User.email.ilike(f"%{search}%"))
                | (User.first_name.ilike(f"%{search}%"))
            )
        query = query.offset(skip).limit(limit).order_by(User.id)
        result = await self.db.execute(query)
        users = result.scalars().all()
        return [UserRead.model_validate(u) for u in users]

    async def get_user(self, user_id: int) -> UserRead:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return UserRead.model_validate(user)

    async def create_user(self, data: UserCreate) -> UserRead:
        existing = await self.db.execute(select(User).where((User.username == data.username) | (User.email == data.email)))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario o email ya existe")

        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            username=data.username,
            phone=data.phone,
            hashed_password=hash_password(data.password),
            role_id=data.role_id,
            company_id=data.company_id,
            view_type=data.view_type or "web",
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return UserRead.model_validate(user)

    async def update_user(self, user_id: int, data: UserUpdate) -> UserRead:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        await self.db.flush()
        await self.db.refresh(user)
        return UserRead.model_validate(user)

    async def deactivate_user(self, user_id: int) -> None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        user.is_active = False
        await self.db.flush()

    # ---- Role CRUD ----

    async def get_roles(self) -> list[RoleRead]:
        result = await self.db.execute(select(Role).where(Role.is_active == True))
        roles = result.scalars().all()
        return [RoleRead.model_validate(r) for r in roles]

    async def create_role(self, data: RoleCreate) -> RoleRead:
        role = Role(name=data.name, description=data.description)
        self.db.add(role)
        await self.db.flush()

        for perm_data in data.permissions:
            permission = Permission(
                role_id=role.id,
                module=perm_data.module,
                action=PermissionAction(perm_data.action),
                scope_type=perm_data.scope_type,
                scope_id=perm_data.scope_id,
            )
            self.db.add(permission)

        await self.db.flush()
        await self.db.refresh(role)
        return RoleRead.model_validate(role)

    async def update_role(self, role_id: int, data: RoleUpdate) -> RoleRead:
        result = await self.db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(role, key, value)

        await self.db.flush()
        await self.db.refresh(role)
        return RoleRead.model_validate(role)

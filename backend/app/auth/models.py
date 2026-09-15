import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("roles.id"), nullable=True)
    #: `GA-REM-039` / `OD-08`. El área funcional a la que pertenece. Nulable: hay usuarios
    #: anteriores a esta spec, y asignarles un área por su rol sería fabricar dato.
    area_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("areas.id"), nullable=True, index=True)
    view_type: Mapped[str] = mapped_column(String(10), default="web")  # "mobile" or "web"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="users", lazy="selectin")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship("User", back_populates="role", lazy="selectin")
    permissions: Mapped[list["Permission"]] = relationship("Permission", back_populates="role", lazy="selectin")


class PermissionAction(str, enum.Enum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    REVIEW = "review"
    CORRECT = "correct"
    APPROVE = "approve"
    REJECT = "reject"
    SEND_SAP = "send_sap"
    # `GA-REQ-061` · T14: acciones del cutover (la matriz de seguridad las nombra así).
    VALIDATE = "validate"
    SUBMIT = "submit"
    APPLY = "apply"


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"))
    module: Mapped[str] = mapped_column(String(100))
    action: Mapped[PermissionAction] = mapped_column(Enum(PermissionAction))
    scope_type: Mapped[str] = mapped_column(String(50), default="all")  # all, company, farm
    scope_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    role: Mapped["Role"] = relationship("Role", back_populates="permissions")


class RevokedToken(Base):
    """Refresh tokens revocados por `logout` — `GA-REM-003` · AC04.

    Denylist por `jti` con TTL: la fila vive hasta la expiración del refresh (7 días)
    y la purga es oportunista en cada inserción. El almacén en memoria se descartó en
    revisión de spec: multi-instancia lo vuelve una lotería.
    """

    __tablename__ = "revoked_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

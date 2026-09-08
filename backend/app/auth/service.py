from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Permission, PermissionAction, Role, User
from ..masters.models import Company
from .security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from .schemas import (
    LoginRequest,
    PasswordChangeRequest,
    PermissionCreate,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)


def _claims_de(user: User, company_id: int | None = None) -> dict:
    """Claims del token a partir del usuario en base de datos.

    Un único sitio para el login, la renovación y el cambio de empresa: mientras
    estuvieron duplicados, la renovación se quedó atrás y emitía la mitad de los campos
    (`GA-REM-003`).

    `company_id` permite conservar un contexto desplazado por `switch-company`. Sin él, un
    Super Admin que estuviera trabajando en otra empresa volvía en silencio a la suya al
    renovar la sesión, a los treinta minutos y sin aviso (`R-54`).
    """
    return {
        "sub": user.id,
        "username": user.username,
        "company_id": user.company_id if company_id is None else company_id,
        "role_id": user.role_id,
        "view_type": user.view_type or "web",
    }


from ..audit.helpers import audit_accion
from ..audit.models import AuditAction, AuditModule


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Inquilino en la administración de usuarios — `GA-REM-002` enmienda B ──
    #
    # `AC11` exige que la comprobación de pertenencia sea **una** función reutilizable y no
    # una copia por servicio. Estos dos localizadores son ese sitio para `users`: listar,
    # leer, editar y desactivar pasan por ellos, de modo que añadir mañana una quinta ruta
    # no obliga a acordarse de nada.

    class AutoridadInsuficiente(Exception):
        """El actor no puede administrar usuarios en ninguna empresa concreta."""

    @staticmethod
    def _contexto(actor: dict | None) -> tuple[int | None, bool]:
        """`(empresa efectiva, autoridad global)` del actor.

        La empresa **no se recibe del cliente**: llega ya resuelta por `OD-11` dentro de
        `current_user`, que la deriva de la persistida salvo cambio de contexto autorizado.
        Un parámetro de consulta o una reclamación en el token no la mueven.

        `None` en la empresa significa **no hay empresa efectiva**, y solo la autoridad
        global —`("*", …, "all")`, que es como `docs/02 §3.1.4` define al Super
        Administrador— puede operar sin ella. Para cualquier otro actor eso es denegar:
        `fail-closed`, nunca «sin empresa, todas las empresas».
        """
        if actor is None:
            return None, False
        return actor.get("company_id"), bool(actor.get("is_super_admin"))

    def _acotar(self, consulta, actor: dict | None):
        """Añade el predicado de inquilino a una consulta sobre `users`. `AC13`.

        Se aplica **en la consulta**, de modo que paginación, orden y búsqueda operen ya
        sobre el conjunto acotado. Filtrar después de traer las filas dejaría el total
        contando lo ajeno, que revela por diferencia lo que el filtro escondía.
        """
        empresa, global_ = self._contexto(actor)
        if global_:
            # `docs/02 §3.1.4`, literal: «Super Admin (rol con `module="*"`,
            # `scope_type="all"`) ve TODAS las compañías». Es la misma exención que
            # `get_company_filter` aplica en el resto del producto y que `MasterService`
            # respeta; acotarla solo aquí habría hecho que `/users` se comportara distinto
            # de `/masters` sin que ninguna norma lo pidiera.
            #
            # Esto **no** es la fuga que cierra esta enmienda. El actor del hallazgo es el
            # administrador **acotado** a una empresa, y para él el filtro de abajo es
            # obligatorio. Si el propietario quiere además que situarse con `switch-company`
            # acote a la autoridad global, es una decisión de producto que afecta a todos los
            # servicios y no solo a éste: queda registrada como `R-126`.
            return consulta
        if empresa is not None:
            return consulta.where(User.company_id == empresa)
        # `fail-closed`: sin empresa efectiva y sin autoridad global no se administra nada.
        # Nunca «sin empresa, todas las empresas».
        raise self.AutoridadInsuficiente(
            "no hay empresa efectiva sobre la que administrar usuarios")

    async def _usuario_alcanzable(self, user_id: int, actor: dict | None) -> User | None:
        """El usuario, **si el actor tiene derecho a alcanzarlo**. `AC13` · `AC14`.

        Devuelve `None` cuando no lo tiene, y quien llama responde `404`: la convención de
        `AC05` es que un recurso ajeno se comporte como inexistente, porque distinguir «no
        existe» de «no es tuyo» ya filtra información.

        Es un **localizador**, no una comprobación posterior. La diferencia es el orden:
        aquí el objetivo se resuelve dentro de la empresa antes de que exista nada que
        mutar, en vez de traerlo global y descubrir la discrepancia con la fila ya en la
        mano.
        """
        try:
            consulta = self._acotar(select(User).where(User.id == user_id), actor)
        except self.AutoridadInsuficiente:
            return None
        return (await self.db.execute(consulta)).scalar_one_or_none()

    async def _rol_asignable(self, role_id: int | None, actor: dict | None) -> bool:
        """¿Puede este actor asignar ese rol? `OD-13.c` · `AC-R05` · `AC-R06`.

        ```
        autoridad global            cualquiera
        rol de inquilino            solo si es de SU empresa
        plantilla de sistema        sí, salvo que confiera autoridad global
        ```

        La tercera línea es la que evita convertir la norma en un bloqueo: **los seis roles
        del producto tienen `company_id NULL`**, de modo que prohibirlos todos dejaría a un
        administrador de empresa sin poder asignar nada. Lo que se protege es la autoridad
        global, no la existencia de un catálogo compartido (`OD-13.c`).
        """
        if role_id is None:
            return True
        empresa, global_ = self._contexto(actor)
        if actor is None or global_:
            return True
        rol = (await self.db.execute(
            select(Role).where(Role.id == role_id))).scalar_one_or_none()
        if rol is None:
            return False
        if rol.company_id is None:
            # Plantilla de producto: asignable salvo que reparta autoridad global.
            return not await self._es_autoridad_global(role_id)
        return rol.company_id == empresa

    async def _rol_administrable(self, role_id: int, actor: dict | None):
        """El rol, **si el actor puede administrarlo**. `AC-R03` · `AC-R04`.

        Un actor de empresa administra los roles de su empresa. Las plantillas de sistema
        las **ve** —las necesita para elegir— y no las edita: `OD-13.e`.
        """
        rol = (await self.db.execute(
            select(Role).where(Role.id == role_id))).scalar_one_or_none()
        if rol is None:
            return None
        empresa, global_ = self._contexto(actor)
        if actor is None or global_:
            return rol
        return rol if rol.company_id == empresa else None

    async def _es_autoridad_global(self, role_id: int | None) -> bool:
        """¿Ese rol concede alcance sobre **todas** las compañías? `AC15`.

        La forma la fija `docs/02 §3.1.4`: «rol con `module="*"`, `scope_type="all"`». No se
        mira el nombre del rol — `GA-REM-040 AC-F05` ya dejó dicho lo que valen los nombres.
        """
        if role_id is None:
            return False
        return (await self.db.execute(
            select(Permission.id).where(Permission.role_id == role_id,
                                        Permission.module == "*",
                                        Permission.scope_type == "all").limit(1)
        )).scalar_one_or_none() is not None

    # ---- Auth ----

    async def login(self, data: LoginRequest) -> TokenResponse:
        result = await self.db.execute(
            select(User).where(User.username == data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.hashed_password):
            # `GA-REM-032 AC01`. El intento fallido sobre una cuenta existente es lo primero
            # que un auditor busca, y no se registraba. Nunca se guarda la credencial
            # intentada: auditar el fallo conservando la contraseña sería peor que no
            # auditarlo. Un usuario inexistente no puede atribuirse a ninguna empresa y
            # queda sin registro (`R-83`).
            if user is not None:
                await audit_accion(
                    self.db, usuario={"id": user.id, "company_id": user.company_id},
                    accion=AuditAction.LOGIN_FAILED, modulo=AuditModule.AUTH,
                    entity_type="user", entity_id=user.id,
                    comments="Credenciales incorrectas",
                )
                # El 401 provoca el `rollback` de la petición (`GA-REM-026`), que se
                # llevaría por delante este registro. La auditoría de una acción
                # **rechazada** tiene que sobrevivir al rechazo: si no, el único rastro que
                # queda de un intento de acceso es ninguno. Se confirma aquí, y solo aquí,
                # porque en esta rama no hay ninguna otra escritura pendiente.
                await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta desactivada. Contacte al administrador.",
            )

        # El login parte siempre de la compañía del usuario: es una sesión nueva y no
        # arrastra ningún contexto anterior.
        await audit_accion(                                   # `GA-REM-032 AC01`
            self.db, usuario={"id": user.id, "company_id": user.company_id},
            accion=AuditAction.LOGIN, modulo=AuditModule.AUTH,
            entity_type="user", entity_id=user.id,
        )

        token_data = _claims_de(user)
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=30 * 60,
        )

    async def _es_super_admin(self, user: User) -> bool:
        """Comodín `("*", …)` con alcance `all`, la misma señal que usa `get_current_user`."""
        from .models import Permission, Role

        resultado = await self.db.execute(
            select(Permission.id)
            .join(Role, Role.id == Permission.role_id)
            .where(
                Role.id == user.role_id,
                Permission.module == "*",
                Permission.scope_type == "all",
            )
            .limit(1)
        )
        return resultado.scalar_one_or_none() is not None

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no es refresh token",
            )

        # R-43: `sub` viaja como cadena en el JWT y aquí se comparaba tal cual contra
        # `User.id`, que es entero. PostgreSQL rechazaba la comparación
        # (`operator does not exist: integer = character varying`) y **el refresco nunca
        # funcionó**: toda sesión moría al expirar el token de acceso, a los 30 minutos.
        # `get_current_user` sí convertía (`security.py:93`); esta ruta se quedó atrás.
        bruto = payload.get("sub")
        try:
            user_id = int(bruto)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: subject no reconocido",
            ) from None
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")

        # GA-REM-003: el contexto se reconstruye desde la base, que es la fuente de
        # verdad, y no se copian los claims del token anterior. Antes se emitía
        # `{sub, username}` a secas y el frontend perdía vista y compañía al renovar.
        #
        # R-54: la única excepción es el contexto de empresa que `switch-company` hubiera
        # fijado, y solo para quien puede tenerlo. Sin esto, un Super Admin que estuviera
        # trabajando en otra empresa volvía a la suya en silencio a los treinta minutos.
        # Para el resto manda la base, que es lo que sostiene el aislamiento
        # multiempresa: un token no reclama compañías ajenas.
        contexto = None
        reclamada = payload.get("company_id")
        if reclamada is not None and str(reclamada) != str(user.company_id):
            if await self._es_super_admin(user):
                contexto = int(reclamada)

        token_data = _claims_de(user, contexto)
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=30 * 60,
        )

    # ---- User CRUD ----

    async def get_users(self, skip: int = 0, limit: int = 20, search: str = "",
                        actor: dict | None = None) -> list[UserRead]:
        """Los usuarios de la empresa efectiva. `AC13` · `R-114`.

        El predicado de inquilino va **antes** que la búsqueda y la paginación: si fuera
        después, la primera página llegaría con huecos donde estaban los ajenos y el
        recuento los delataría por diferencia.
        """
        try:
            query = self._acotar(select(User), actor)
        except self.AutoridadInsuficiente as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=str(exc)) from exc
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

    async def get_user(self, user_id: int, actor: dict | None = None) -> UserRead:
        """Un usuario de la empresa efectiva. `AC13` · `R-114`.

        `actor` nulo omite el filtro **a propósito y solo para `/me`**, donde el sujeto es el
        propio titular y no hay inquilino ajeno que proteger. Toda ruta de administración lo
        pasa.
        """
        if actor is None:
            user = (await self.db.execute(
                select(User).where(User.id == user_id))).scalar_one_or_none()
        else:
            user = await self._usuario_alcanzable(user_id, actor)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        data = UserRead.model_validate(user)
        if user.company_id:
            company_result = await self.db.execute(
                select(Company.name).where(Company.id == user.company_id)
            )
            data.company_name = company_result.scalar_one_or_none()
        return data

    async def create_user(self, data: UserCreate, actor: dict | None = None) -> UserRead:
        """Alta de usuario **en la empresa efectiva**. `AC14` · `R-118`.

        La empresa se **resuelve**, no se recibe. `company_id` venía del cuerpo y el router
        obtenía el actor sin llegar a pasarlo, de modo que un administrador de A creaba
        usuarios en B. Para un actor acotado la reclamación del cliente se ignora; solo la
        autoridad global sin contexto puede declarar en qué empresa nace el usuario.
        """
        existing = await self.db.execute(select(User).where((User.username == data.username) | (User.email == data.email)))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario o email ya existe")

        empresa, global_ = self._contexto(actor)
        if actor is None or global_:
            # La autoridad global **sí** declara la empresa de destino. Aprovisionar usuarios
            # en varias empresas es su trabajo, y quitárselo no cerraría ningún `P0`: el
            # actor del hallazgo es el administrador **acotado**, para el que la empresa se
            # impone justo debajo. Situarse con `switch-company` acota lo que **ve**; no le
            # retira la autoridad de crear donde declare.
            company_id = data.company_id if data.company_id is not None else empresa
        elif empresa is not None:
            company_id = empresa
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No hay empresa efectiva en la que crear el usuario")

        if not await self._rol_asignable(data.role_id, actor):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ese rol no es asignable desde la administración de esta empresa")

        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            username=data.username,
            phone=data.phone,
            hashed_password=hash_password(data.password),
            role_id=data.role_id,
            company_id=company_id,
            view_type=data.view_type or "web",
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return UserRead.model_validate(user)

    async def update_user(self, user_id: int, data: UserUpdate,
                          actor: dict | None = None) -> UserRead:
        """Edición de un usuario de la empresa efectiva. `AC14` · `AC15` · `R-114` · `R-117`.

        El orden **es** parte de la regla:

        ```
        objetivo dentro de la empresa  →  validación de rol  →  mutación
        ```

        Antes se traía el usuario globalmente y se le aplicaban los campos en bucle, `role_id`
        incluido. Eso permitía, por la ruta documentada de edición, que un administrador de la
        empresa A convirtiera a un usuario de la B en Super Administrador: fuga de inquilino y
        modificación de autoridad a la vez.
        """
        if actor is None:
            user = (await self.db.execute(
                select(User).where(User.id == user_id))).scalar_one_or_none()
        else:
            user = await self._usuario_alcanzable(user_id, actor)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

        update_data = data.model_dump(exclude_unset=True)

        # `AC15`. Se comprueba **antes** de tocar la fila: una denegación no puede dejar
        # medio usuario escrito.
        if ("role_id" in update_data
                and not await self._rol_asignable(update_data["role_id"], actor)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ese rol no es asignable desde la administración de esta empresa")
        for key, value in update_data.items():
            setattr(user, key, value)

        await self.db.flush()
        await self.db.refresh(user)
        return UserRead.model_validate(user)

    async def change_password(
        self, user_id: int, data: "PasswordChangeRequest", current_user: dict
    ) -> None:
        """Cambia la contraseña de un usuario — `GA-REM-012`, regla `RR-05`.

        Dos caminos, con reglas distintas y deliberadas:

        * **el titular cambia la suya**: debe aportar la contraseña actual y acertarla;
        * **un administrador restablece la de otro**: no necesita la anterior —no la
          conoce— pero sí autorización.

        Cualquier otro caso es un 403. Hoy la autorización se apoya en `is_super_admin`,
        la única señal disponible: `GA-REM-002` la sustituirá por el permiso
        `users:update` cuando exista el enforcement de RBAC.

        Nunca responde con éxito sin haber cambiado nada: ese silencio era `P0-13`.
        """
        from ..audit.helpers import _insert_audit_log
        from ..audit.models import AuditAction, AuditModule

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

        es_el_titular = current_user["id"] == user_id
        es_administrador = bool(current_user.get("is_super_admin"))

        if not es_el_titular and not es_administrador:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene autorización para cambiar la contraseña de otro usuario",
            )

        if es_el_titular:
            if not data.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Debe aportar su contraseña actual para cambiarla",
                )
            if not verify_password(data.current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La contraseña actual no es correcta",
                )

        user.hashed_password = hash_password(data.new_password)
        await self.db.flush()

        # La auditoría registra el hecho y los dos usuarios implicados. Nunca la
        # contraseña ni su hash.
        await _insert_audit_log(
            db=self.db,
            user_id=current_user["id"],
            # La compañía del titular, no la de quien actúa: un administrador puede
            # restablecer la contraseña de un usuario de otra empresa. `0` no vale como
            # relleno — es una clave foránea y no existe la compañía 0 (`R-37`).
            company_id=user.company_id or current_user.get("company_id"),
            action=AuditAction.UPDATED,
            entity_type="user_password",
            entity_id=str(user_id),
            module=AuditModule.AUTH,
            comments=(
                "Cambio de contraseña propia" if es_el_titular
                else f"Restablecimiento de la contraseña del usuario {user_id} por un administrador"
            ),
        )

    async def deactivate_user(self, user_id: int, actor: dict | None = None) -> None:
        """Baja de un usuario de la empresa efectiva. `AC14`.

        Misma clase de mutación por identificador que `update_user`, y por tanto la misma
        regla: dar de baja a alguien de otro inquilino es tan grave como editarlo.
        """
        if actor is None:
            user = (await self.db.execute(
                select(User).where(User.id == user_id))).scalar_one_or_none()
        else:
            user = await self._usuario_alcanzable(user_id, actor)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        user.is_active = False
        await self.db.flush()

    async def switch_company(self, company_id: int, current_user: dict) -> "TokenResponse":
        """Issue new tokens scoped to a different company. Super-admin only."""
        from .schemas import TokenResponse as TR
        if not current_user.get("is_super_admin"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo super administradores pueden cambiar de empresa")
        company_result = await self.db.execute(
            select(Company.id).where(Company.id == company_id, Company.is_active == True)
        )
        if not company_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada o inactiva")
        user_id = current_user["id"]
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        # `OD-11 §6` / `AC-I06`. Situarse en otra empresa decide sobre qué datos se opera
        # después, y hasta aquí no quedaba constancia de que hubiera ocurrido. Va en `P-09`,
        # con el mismo insertor que el resto, y no en un registro paralelo.
        await audit_accion(
            self.db, usuario={"id": user.id, "company_id": user.company_id},
            accion=AuditAction.CONTEXT_SWITCHED, modulo=AuditModule.AUTH,
            entity_type="company", entity_id=company_id,
            company_id=company_id,
            previous_state=str(user.company_id) if user.company_id else None,
            new_state=str(company_id),
        )

        # El mismo constructor que el login y la renovación, con el contexto desplazado.
        token_data = _claims_de(user, company_id)
        return TR(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=30 * 60,
        )

    # ---- Role CRUD ----

    #: Módulos que el enforcement reconoce, recogidos de las llamadas a `require_permission`.
    #: Se enumeran aquí y no en el frontend para que no puedan desincronizarse.
    MODULOS = [
        # `GA-REM-040 §5` fase 7: «el plano de control tiene permisos propios». Administrar
        # qué cadenas opera una empresa y quién accede a ellas no es administrar usuarios ni
        # editar un maestro, y reutilizar el módulo de otro habría atado dos autoridades que
        # el propietario puede querer repartir entre personas distintas.
        "approvals", "audit", "business_units", "corrections", "dashboard", "lots",
        "masters", "operations", "reports", "review", "sap", "users",
    ]

    def get_permission_catalog(self) -> dict[str, list[str]]:
        """`GA-REM-034 AC01`. Qué se puede conceder, desde la fuente de verdad."""
        return {
            "modules": list(self.MODULOS),
            "actions": [a.value for a in PermissionAction],
        }

    async def get_roles(self, actor: dict | None = None) -> list[RoleRead]:
        """Los roles de la empresa efectiva **más** las plantillas de sistema. `AC-R01`.

        `OD-13.b`: `company_id NULL` es una plantilla de producto, compartida por todos los
        clientes; `company_id` concreto es un rol de un inquilino. El actor de empresa ve las
        primeras y las suyas, nunca las de otra empresa.

        Verlas no es poder asignarlas ni editarlas — de eso se ocupan `_rol_asignable` y
        `_rol_administrable`.
        """
        consulta = select(Role).where(Role.is_active == True)
        empresa, global_ = self._contexto(actor)
        if actor is not None and not global_:
            if empresa is None:
                # `fail-closed`, igual que en usuarios y maestros.
                consulta = consulta.where(Role.id.is_(None))
            else:
                consulta = consulta.where(
                    (Role.company_id == empresa) | (Role.company_id.is_(None)))
        roles = (await self.db.execute(consulta)).scalars().all()
        return [RoleRead.model_validate(r) for r in roles]

    async def create_role(self, data: RoleCreate, current_user: dict | None = None) -> RoleRead:
        """Crea un rol **en la empresa efectiva del actor**. `AC-R02` · `OD-13.e`.

        `RoleCreate` no acepta `company_id` y no se le añade: la empresa sale del actor, no
        del cuerpo. La autoridad global crea plantillas de sistema (`company_id NULL`), que
        es lo que las semillas del producto han hecho siempre.
        """
        empresa, global_ = self._contexto(current_user)
        role = Role(name=data.name, description=data.description,
                    company_id=None if (current_user is None or global_) else empresa)
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
        # `GA-REM-032 AC03`. «Quién concedió esto y cuándo» no tenía respuesta: ni el alta de
        # un rol ni el cambio de sus permisos dejaban rastro. Se emite **después** de
        # persistir los permisos, para que el registro diga lo concedido y no lo pedido.
        await audit_accion(
            self.db, usuario=current_user, accion=AuditAction.PERMISSION_CHANGE,
            modulo=AuditModule.USERS, entity_type="role", entity_id=role.id,
            new_values={"nombre": role.name,
                        "permisos": [f"{p.module}:{p.action}" for p in (data.permissions or [])]},
        )
        return RoleRead.model_validate(role)

    async def update_role(self, role_id: int, data: RoleUpdate, current_user: dict | None = None) -> RoleRead:
        """Edita un rol que el actor pueda administrar. `AC-R03` · `AC-R04`.

        El objetivo se resuelve **dentro** del alcance antes de mutar nada, igual que en
        `update_user`: una plantilla de sistema o un rol de otra empresa se comportan como
        inexistentes para un actor de empresa.
        """
        role = await self._rol_administrable(role_id, current_user)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rol no encontrado")

        # `permissions` se excluye del asignador genérico: es una relación y se sustituye
        # abajo. Asignarle una lista de diccionarios revienta el mapeador.
        update_data = data.model_dump(exclude_unset=True, exclude={"permissions"})
        for key, value in update_data.items():
            setattr(role, key, value)

        # `GA-REM-034 AC02` / `R-93`. Sustituye el conjunto entero cuando viaja: se retiran
        # los que sobran y se crean los que faltan. Omitirlo deja los permisos intactos.
        if data.permissions is not None:
            await self.db.execute(
                sa_delete(Permission).where(Permission.role_id == role.id)
            )
            for perm in data.permissions:
                self.db.add(Permission(
                    role_id=role.id, module=perm.module,
                    action=PermissionAction(perm.action),
                    scope_type=perm.scope_type, scope_id=perm.scope_id,
                ))

        await self.db.flush()
        await self.db.refresh(role, ["permissions"])
        await audit_accion(                                   # `GA-REM-032 AC03`
            self.db, usuario=current_user, accion=AuditAction.PERMISSION_CHANGE,
            modulo=AuditModule.USERS, entity_type="role", entity_id=role.id,
            new_values={"nombre": role.name},
        )
        return RoleRead.model_validate(role)

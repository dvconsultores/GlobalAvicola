from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Permission, PermissionAction, Role, User
from ..masters.models import Company
from .security import (create_access_token, create_refresh_token, decode_token,
                      hash_password, tiene_permiso, verify_password)
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
        empresa, _ = self._contexto(actor)
        # `OD-14.c`: `/users` es superficie de **inquilino**, y lo es para todos. La
        # autoridad global no queda exenta: elige empresa con `switch-company` y opera en
        # ella. Antes esta rama devolvía la consulta sin acotar para el Super Administrador,
        # que es lo que `R-126` vino a decidir y `OD-14` decidió.
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
        # `R-199`: un rol de inquilino nunca confiere autoridad global; asignar uno con el
        # comodín repartiría la escalada en vez de fabricarla, y también se deniega.
        return rol.company_id == empresa and not await self._es_autoridad_global(role_id)

    async def _exigir_rol_activo(self, role_id: int | None) -> None:
        """`AC-RL-03` · `DR-1`: un rol **inactivo** no se asigna.

        Asignarlo reintroduciría por la puerta de atrás el usuario sin capacidades que
        `AC-RL-01` acaba de evitar al impedir la baja del rol en uso: la persona entraría al
        sistema sin poder hacer nada y sin saber por qué.

        Es una comprobación **distinta** de `_rol_asignable` —aquella decide de quién es el
        rol y qué autoridad reparte— y por eso se llama después y por separado. La de aquí
        solo mira `is_active`.
        """
        if role_id is None:
            return
        rol = (await self.db.execute(
            select(Role).where(Role.id == role_id))).scalar_one_or_none()
        if rol is not None and not rol.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El rol está inactivo y no puede asignarse")

    # ── Regla de subconjunto — `DR-3` (`AC-ES-01` · `AC-ES-02`) ──
    #
    # «Nadie asigna un rol ni concede permisos que él mismo no posea», con la autoridad
    # global exenta. Sin esto, `users:create` basta para fabricarse cualquier capacidad:
    # basta crear un rol con `("*", …)` —o con el permiso que se quiera— y asignárselo a
    # un cómplice o a uno mismo. Administrar el acceso dejaba de ser administrar y pasaba
    # a ser elevarse.

    def _no_cubiertos(self, actor: dict | None, pares) -> list[str]:
        """Qué `"modulo:accion"` de `pares` **no** están en poder del actor.

        La comprobación es `tiene_permiso`, la **misma** función que decide cada ruta del
        producto. Una segunda implementación de la misma regla acabaría concediendo lo que
        la primera deniega, y el comodín se comporta aquí como allí: `("*", "read")` en
        poder del actor cubre `lots:read`, y un rol que **reparte** `("*", "read")` exige
        tener el comodín (`AC-ES-01`, «el comodín exige comodín»).

        `actor` nulo significa que no hay nadie a quien exigirle nada —el camino de las
        semillas y de los servicios invocados sin petición—, y la autoridad global está
        exenta por `DR-3`.
        """
        if actor is None or actor.get("is_super_admin"):
            return []
        faltan = {f"{modulo}:{accion}" for modulo, accion in pares
                  if not tiene_permiso(actor, modulo, accion)}
        return sorted(faltan)

    @staticmethod
    def _mensaje_de_escalada(prefijo: str, faltan: list[str]) -> str:
        """El detalle del `403`: qué se denegó, con nombres, y recortado.

        Con muchos permisos fuera del subconjunto el mensaje se haría ilegible; cinco y unos
        puntos suspensivos dicen lo mismo. El resto queda en el asiento de auditoría.
        """
        return f"{prefijo}: " + ", ".join(faltan[:5]) + ("…" if len(faltan) > 5 else "")

    async def _exigir_subconjunto_de_rol(self, role_id: int | None,
                                         actor: dict | None) -> None:
        """`AC-ES-01` · el rol **destino** no puede repartir lo que el actor no tiene.

        Se comprueban los pares `(módulo, acción)` del rol, no su nombre ni su empresa: lo
        que se reparte es la capacidad. `role_id` nulo —un usuario sin rol— no reparte nada
        y no hay nada que comprobar.
        """
        if role_id is None:
            return
        filas = (await self.db.execute(
            select(Permission.module, Permission.action)
            .where(Permission.role_id == role_id))).all()
        pares = [(modulo, getattr(accion, "value", accion)) for modulo, accion in filas]
        faltan = self._no_cubiertos(actor, pares)
        if not faltan:
            return
        await self._registrar_rechazo_de_autoridad(
            actor=actor, role_id=role_id,
            motivo="rechazado: escalada de permisos (asignación de rol)")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=self._mensaje_de_escalada(
                "No puede asignar un rol con permisos que usted no posee", faltan))

    async def _exigir_permisos_cubiertos(self, nuevos, actor, *, role_id: int | None,
                                         motivo: str) -> None:
        """`AC-ES-02` · conceder exige poseer. Retirar no se comprueba nunca.

        `nuevos` son solo los pares que se **añaden** al rol: quitar un permiso reduce lo
        que el rol reparte y no puede ser una escalada, de modo que prohibirlo dejaría roles
        heredados imposibles de sanear. Reenviar el mismo conjunto —lo que la interfaz hace
        al guardar— tampoco añade nada y no exige nada.
        """
        faltan = self._no_cubiertos(actor, nuevos)
        if not faltan:
            return
        await self._registrar_rechazo_de_autoridad(actor=actor, role_id=role_id,
                                                   motivo=motivo)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=self._mensaje_de_escalada(
                "No puede conceder permisos que usted no posee", faltan))

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
                # `R-199` · `OD-13.c`: la capacidad exige el permiso **en un rol de
                # sistema**; un rol de inquilino con el comodín no la confiere.
                Role.company_id.is_(None),
                # `UAT-ADMIN-RBAC` · `AC-RL-02` · `DR-1`: un rol inactivo **no** confiere
                # autoridad global. Es la misma señal que `get_current_user` ya ignora
                # estando el rol apagado; aquí se cierra la otra mitad de la regla.
                Role.is_active.is_(True),
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

        # `GA-REM-003` · AC04: un refresh revocado por `logout` no vuelve a emitir.
        # La denylist es por `jti` (token, no usuario): cerrar sesión en un sitio no
        # cierra las demás sesiones — eso es lo que un usuario espera de «cerrar
        # sesión».
        from .models import RevokedToken

        jti = payload.get("jti")
        if jti and (await self.db.execute(
            select(RevokedToken.id).where(RevokedToken.jti == jti).limit(1)
        )).scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revocado",
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

    async def logout(self, refresh_token: str, actor: dict) -> None:
        """`GA-REM-003` · AC04: revoca el refresh token presentado (denylist `jti`).

        Idempotente y sin oráculo: un token irrecuperable o ya revocado no produce
        error — no hay nada que revocar, y distinguir casos daría una señal legible
        para un atacante. La revocación es **del propio titular**: el `sub` del
        refresh debe ser el actor; cerrar sesiones ajenas no es una operación de
        usuario (y con un refresh robado, además, habría sido un cierre de sesión
        a distancia gratis).

        La revocación es **por token**, no por usuario: cerrar sesión aquí no derriba
        las demás sesiones. «Cerrar todas» sería otra operación y otra decisión.
        """
        from datetime import datetime, timezone

        from sqlalchemy import delete as sa_delete

        from .models import RevokedToken

        try:
            payload = decode_token(refresh_token)
        except HTTPException:
            return
        if payload.get("type") != "refresh":
            return
        jti = payload.get("jti")
        if not jti:
            return
        try:
            user_id = int(payload.get("sub"))
        except (TypeError, ValueError):
            return
        if user_id != actor.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autoriza revocar la sesión de otro usuario",
            )

        user = (await self.db.execute(
            select(User).where(User.id == user_id))).scalar_one_or_none()
        if user is None:
            return

        # TTL: la fila vive hasta la expiración del refresh; la purga es oportunista —
        # una tabla de revocación que crece sin límite es deuda, no mecanismo.
        ahora = datetime.now(timezone.utc)
        await self.db.execute(
            sa_delete(RevokedToken).where(RevokedToken.expires_at < ahora))
        existe = (await self.db.execute(
            select(RevokedToken.id).where(RevokedToken.jti == jti).limit(1)
        )).scalar_one_or_none()
        if existe is None:
            self.db.add(RevokedToken(
                jti=jti, user_id=user.id,
                expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            ))
        await self.db.flush()

        # `GA-REM-003` · AC06 (parte): el logout deja asiento, con la empresa del
        # dueño del token — es a quien pertenece la sesión que termina.
        await audit_accion(
            self.db, usuario={"id": user.id, "company_id": user.company_id},
            accion=AuditAction.LOGOUT, modulo=AuditModule.AUTH,
            entity_type="user", entity_id=user.id,
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
        # `UAT-ADMIN-RBAC` · `AC-ID-01` · `AC-ID-03`. La identidad se normaliza **antes** de
        # compararla y de persistirla, y cada unicidad se comprueba por separado.
        #
        # Antes había una sola consulta con `OR` y `scalar_one_or_none`: cuando el `username`
        # era de un usuario y el `email` de otro, llegaban dos filas y la petición moría con
        # `MultipleResultsFound` (`500`). El administrador no sabía qué estaba ocupado y el
        # `OR` obligaba a adivinar qué campo corregir.
        #
        # `lower()` porque el login se escribe a mano: `PA_X` y `pa_x` no pueden ser dos
        # identidades distintas (`AC-ID-03`). Los índices únicos de la base siguen siendo
        # sensibles a mayúsculas — **sin migración**, como fija el §4.3 de la spec.
        username = data.username.strip()
        email = str(data.email).strip()
        if len(username) < 3:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El nombre de usuario debe tener al menos 3 caracteres")

        ocupado = (await self.db.execute(
            select(User.id).where(func.lower(User.username) == username.lower()).limit(1)
        )).first()
        if ocupado is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="El nombre de usuario ya está en uso")
        ocupado = (await self.db.execute(
            select(User.id).where(func.lower(User.email) == email.lower()).limit(1)
        )).first()
        if ocupado is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="El correo electrónico ya está en uso")

        empresa, global_ = self._contexto(actor)
        if actor is None:
            company_id = data.company_id
        elif empresa is not None:
            # `OD-14.c`: el alta es superficie de inquilino como cualquier otra. La empresa
            # sale del contexto **también para la autoridad global**: declarar una empresa
            # distinta de aquella en la que se está situado sería operar sobre un inquilino
            # sin estar en él, que es lo que `OD-14.d` prohíbe.
            company_id = empresa
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No hay empresa efectiva en la que crear el usuario")

        if not await self._rol_asignable(data.role_id, actor):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ese rol no es asignable desde la administración de esta empresa")

        # `UAT-ADMIN-RBAC` · `AC-RL-03` · `DR-1`: además de asignable, el rol tiene que
        # estar vivo. Va detrás de lo anterior y antes del `db.add`, de modo que un rechazo
        # no deja fila.
        await self._exigir_rol_activo(data.role_id)

        # `UAT-ADMIN-RBAC` · `AC-ES-01` · `DR-3`: además de asignable y de estar vivo, el
        # rol no puede repartir capacidades que el actor no posea. Es la puerta del alta: sin
        # esta comprobación, `users:create` bastaba para crear a alguien con el rol que
        # concedía lo que el actor no tenía — o para crearse a uno mismo la cuenta cómplice.
        await self._exigir_subconjunto_de_rol(data.role_id, actor)

        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=email,
            username=username,
            phone=data.phone,
            hashed_password=hash_password(data.password),
            role_id=data.role_id,
            company_id=company_id,
            view_type=data.view_type or "web",
        )
        self.db.add(user)
        try:
            await self.db.flush()
        except IntegrityError:
            # Red de seguridad, no la regla: entre la comprobación de arriba y este `flush`
            # cabe otra alta simultánea. Sin capturarlo, la carrera terminaba en `500`.
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="El usuario o el correo ya existen") from None
        await self.db.refresh(user)

        # `P1-12-REOPEN` (`E-13` · T-05): el alta escribe su fila — sin secretos.
        if actor is not None:
            await audit_accion(
                self.db, usuario=actor, accion=AuditAction.CREATED, modulo=AuditModule.USERS,
                entity_type="user", entity_id=str(user.id), company_id=company_id,
                new_values={"username": user.username, "role_id": user.role_id,
                            "company_id": company_id, "view_type": user.view_type},
            )
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

        # `UAT-ADMIN-RBAC` · `AC-ES-03` · `DR-3`. Administrar el acceso **no** autoriza a
        # modificar el propio: quien puede `users:update` podría, si no, darse el rol que le
        # faltaba, y quien puede darse de baja podría dejar la superficie sin administrador.
        # La autoridad global **no** queda exenta —tampoco ella cambia su rol ni se
        # desactiva sola—, que es la mitad de `DR-3` que no admite excepción.
        #
        # Reenviar el **mismo** `role_id` no es un cambio y sigue permitido: la interfaz lo
        # envía siempre al guardar, y bloquearlo dejaría la fila propia sin poder editarse.
        if actor is not None and actor.get("id") == user.id:
            if "role_id" in update_data and update_data["role_id"] != user.role_id:
                await self._registrar_rechazo_de_autoridad(
                    actor=actor, role_id=update_data["role_id"],
                    motivo="rechazado: auto-cambio de rol")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Administrar el acceso no autoriza a modificar el propio rol")
            if update_data.get("is_active") is False:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puede desactivarse a sí mismo")

        # `AC15`. Se comprueba **antes** de tocar la fila: una denegación no puede dejar
        # medio usuario escrito.
        if ("role_id" in update_data
                and not await self._rol_asignable(update_data["role_id"], actor)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ese rol no es asignable desde la administración de esta empresa")

        # `UAT-ADMIN-RBAC` · `AC-RL-03` · `DR-1`: el rol nuevo tiene que estar vivo — pero
        # **solo si cambia**. Re-guardar el rol inactivo que ya está asignado no se
        # re-valida: si no, la fila quedaría imposible de editar (un usuario heredado no
        # podría ni cambiar su nombre).
        if "role_id" in update_data and update_data["role_id"] != user.role_id:
            await self._exigir_rol_activo(update_data["role_id"])
            # `AC-ES-01` · `DR-3`: el cambio de rol también **reparte** permisos, y no
            # puede repartir los que el actor no tiene. Reenviar el rol ya asignado no
            # reparte nada nuevo y no se comprueba (la UI lo manda siempre).
            await self._exigir_subconjunto_de_rol(update_data["role_id"], actor)

        # `UAT-ADMIN-RBAC` · `AC-ID-02` · `AC-ID-02b`. Dos defectos que acababan en `500` en
        # el mismo sitio, y las dos comprobaciones van aquí por la misma razón que la del
        # rol: una petición rechazada no deja medio usuario escrito.
        #
        # * un `null` viajaba hasta la base y moría en el `NOT NULL` — es un `422`, no un
        #   fallo del servidor;
        # * un correo ya usado por otro llegaba también a la base, y el `IntegrityError` de
        #   `ix_users_email` se propagaba sin capturar.
        if "email" in update_data:
            if update_data["email"] is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="El correo electrónico no puede ser nulo")
            email = str(update_data["email"]).strip()
            # La comprobación de duplicado solo tiene sentido si el correo **cambia**. Con
            # datos antiguos pueden existir dos correos que solo difieren en mayúsculas (el
            # índice de la base distingue mayúsculas, el producto no): reenviar el propio
            # correo sin tocarlo no puede chocar contra el otro, o el administrador no
            # podría guardar ningún otro campo de esa fila.
            if email.lower() != (user.email or "").strip().lower():
                # `lower()` y `strip()`: la unicidad es del producto, no del índice.
                de_otro = (await self.db.execute(
                    select(User.id).where(
                        User.id != user.id,
                        func.lower(User.email) == email.lower(),
                    ).limit(1)
                )).first()
                if de_otro is not None:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                        detail="El correo electrónico ya está en uso")
            update_data["email"] = email

        # `role_id` y `area_id` **sí** admiten nulo —desasignar rol o área es una operación
        # legítima—; estos cinco no, porque la fila no los admite y el cliente no debe poder
        # provocar un `500` con un `null`.
        for campo in ("first_name", "last_name", "view_type", "is_active"):
            if campo in update_data and update_data[campo] is None:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail=f"{campo} no puede ser nulo")

        # `UAT-ADMIN-RBAC` · `AC-ID-05` · `AR-07`. Desactivar es la mitad destructiva de la
        # administración de usuarios y ya tenía su propio permiso en `DELETE /users/{id}`.
        # Admitirla por `PUT` con `users:update` era la misma capacidad por otra puerta —
        # `users:update` es también lo que autoriza a renombrar. Reactivar no destruye nada
        # y sigue exigiendo solo `users:update`, que el router ya comprueba.
        #
        # Va antes de mutar: una denegación no deja medio usuario escrito.
        if (update_data.get("is_active") is False and actor is not None
                and not tiene_permiso(actor, "users", "delete")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Desactivar un usuario exige el permiso users:delete")

        cambios = {clave: {"old": getattr(user, clave, None), "new": valor}
                   for clave, valor in update_data.items()}
        for key, value in update_data.items():
            setattr(user, key, value)

        try:
            await self.db.flush()
        except IntegrityError:
            # Carrera entre la comprobación y el `flush`: mismo contrato (`409`), nunca `500`.
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="El correo electrónico ya está en uso") from None
        await self.db.refresh(user)

        # `P1-12-REOPEN` (`E-13` · T-05): la edición deja fila con el diff — sin secretos.
        if actor is not None and cambios:
            await audit_accion(
                self.db, usuario=actor, accion=AuditAction.UPDATED, modulo=AuditModule.USERS,
                entity_type="user", entity_id=str(user.id), company_id=user.company_id,
                previous_values={k: v["old"] for k, v in cambios.items()},
                new_values={k: v["new"] for k, v in cambios.items()},
            )
        return UserRead.model_validate(user)

    async def change_password(
        self, user_id: int, data: "PasswordChangeRequest", current_user: dict
    ) -> None:
        """Cambia la contraseña de un usuario — `GA-REM-012`, regla `RR-05`.

        Dos caminos, con reglas distintas y deliberadas:

        * **el titular cambia la suya**: debe aportar la contraseña actual y acertarla;
        * **un administrador restablece la de otro**: no necesita la anterior —no la
          conoce— pero sí autorización (`users:update`) **y ámbito**: `R-202` resolvió
          que el objetivo vive en la empresa efectiva del actor (`_usuario_alcanzable`,
          fail-closed sin contexto) — la capacidad global suelta ya no basta.

        Un objetivo fuera del ámbito se comporta como inexistente (404); sin
        `users:update` (y sin ser el titular), `403`.

        Nunca responde con éxito sin haber cambiado nada: ese silencio era `P0-13`.
        """
        from ..audit.helpers import _insert_audit_log
        from ..audit.models import AuditAction, AuditModule

        es_el_titular = current_user["id"] == user_id

        if es_el_titular:
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        else:
            # `R-202` · `AC-R202-01…04`: la resolución del objetivo va **primero** y
            # dentro del ámbito — sin empresa efectiva no hay ámbito (4xx) y un objetivo
            # de otra empresa se comporta como inexistente.
            user = await self._usuario_alcanzable(user_id, current_user)
            if user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
            if not tiene_permiso(current_user, "users", "update"):
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

        # `UAT-ADMIN-RBAC` · `AC-ID-06` · `AR-10`: aceptar como «nueva» la contraseña vigente
        # deja creer al usuario que cambió algo que no cambió — el mismo silencio de `P0-13`
        # por otra puerta, y además hace parecer que un restablecimiento surtió efecto. Vale
        # para los dos caminos: el titular y el restablecimiento por un administrador.
        if verify_password(data.new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La nueva contraseña debe ser distinta de la actual")

        user.hashed_password = hash_password(data.new_password)
        await self.db.flush()

        # La auditoría registra el hecho y los dos usuarios implicados. Nunca la
        # contraseña ni su hash.
        await _insert_audit_log(
            db=self.db,
            user_id=current_user["id"],
            # `R-202` · `AC-R202-06`: la empresa **efectiva del actor** — el objetivo ya se
            # resolvió dentro de su ámbito (para el titular coinciden). `0` no vale como
            # relleno — es una clave foránea y no existe la compañía 0 (`R-37`).
            company_id=current_user.get("company_id") or user.company_id,
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
        # `UAT-ADMIN-RBAC` · `AC-ES-03` · `DR-3`. Darse de baja uno mismo deja la superficie
        # sin el administrador que la estaba usando, y `users:delete` —el permiso de la baja—
        # no convierte ese permiso en derecho a retirarse del sistema. La regla es la misma
        # que en `update_user` y no exime a la autoridad global.
        if actor is not None and actor.get("id") == user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede desactivarse a sí mismo")
        user.is_active = False
        await self.db.flush()

        # `P1-12-REOPEN` (`E-13` · T-05): la baja deja fila.
        if actor is not None:
            await audit_accion(
                self.db, usuario=actor, accion=AuditAction.DELETED, modulo=AuditModule.USERS,
                entity_type="user", entity_id=str(user.id), company_id=user.company_id,
                new_values={"is_active": False},
            )

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
        # `GA-REQ-061` · T14: el cutover es una capacidad operativa con permisos propios
        # (`cutover:{create,validate,approve,apply}`); no se reutiliza el módulo de otro.
        "cutover",
        # `GA-REM-040 §5` fase 7: «el plano de control tiene permisos propios». Administrar
        # qué cadenas opera una empresa y quién accede a ellas no es administrar usuarios ni
        # editar un maestro, y reutilizar el módulo de otro habría atado dos autoridades que
        # el propietario puede querer repartir entre personas distintas.
        "approvals", "audit", "business_units", "corrections", "dashboard", "lots",
        "masters", "operations", "reports", "reversals", "review", "sap", "users",
    ]

    #: `R-199` · `AC08`. Alcances admitidos; `docs/02 §3.1.4` no define otros.
    SCOPE_TYPES = ("all", "company", "farm")

    def _validar_permisos(self, permisos, *, rol_de_inquilino: bool) -> None:
        """`R-199` · catálogo cerrado + invariante del comodín global.

        `OD-13.c`: la autoridad global —`("*", scope_type="all")`, `docs/02 §3.1.4`— no se
        fabrica desde una superficie de empresa. El catálogo es del producto: un módulo,
        una acción o un alcance fuera de él se rechazan (`422`) antes de tocar la base.
        """
        acciones = [a.value for a in PermissionAction]
        for perm in permisos:
            if perm.module != "*" and perm.module not in self.MODULOS:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Módulo fuera del catálogo: {perm.module!r}")
            accion = getattr(perm.action, "value", perm.action)
            if accion not in acciones:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Acción fuera del catálogo: {accion!r}")
            if perm.scope_type not in self.SCOPE_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Alcance fuera del catálogo: {perm.scope_type!r}")
            if rol_de_inquilino and perm.module == "*" and perm.scope_type == "all":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="La autoridad global no se concede desde la administración de una empresa")

    async def _registrar_rechazo_de_autoridad(self, *, actor: dict | None,
                                              role_id: int | None,
                                              motivo: str = ("rechazado: autoridad global "
                                                             "desde una superficie de empresa")
                                              ) -> None:
        """`C-05`: el intento denegado de fabricar autoridad deja asiento.

        Mismo patrón que `LOGIN_FAILED`: el `403` provoca el rollback de la petición y el
        registro debe sobrevivir al rechazo — se confirma aquí, solo aquí, y solo cuando no
        hay otra escritura pendiente (la validación corre antes de tocar la base). Sin
        empresa efectiva no hay asiento posible (`audit_logs.company_id` es `NOT NULL`).

        `motivo` dice **qué** se intentó: la autoridad global desde una empresa (`R-199`),
        la escalada de permisos por asignación o por concesión, o el auto-cambio de rol
        (`DR-3`). Un mismo `403` por cuatro reglas distintas que dejara el mismo texto no
        serviría para reconstruir un incidente.
        """
        empresa, _ = self._contexto(actor)
        if actor is None or empresa is None:
            return
        await audit_accion(
            self.db, usuario=actor, accion=AuditAction.PERMISSION_CHANGE,
            modulo=AuditModule.USERS, entity_type="role", entity_id=role_id,
            company_id=empresa,
            comments=motivo,
        )
        await self.db.commit()

    def get_permission_catalog(self) -> dict[str, list[str]]:
        """`GA-REM-034 AC01`. Qué se puede conceder, desde la fuente de verdad."""
        return {
            "modules": list(self.MODULOS),
            "actions": [a.value for a in PermissionAction],
        }

    async def get_roles(self, actor: dict | None = None,
                        include_inactive: bool = False) -> list[RoleRead]:
        """Los roles de la empresa efectiva **más** las plantillas de sistema. `AC-R01`.

        `OD-13.b`: `company_id NULL` es una plantilla de producto, compartida por todos los
        clientes; `company_id` concreto es un rol de un inquilino. El actor de empresa ve las
        primeras y las suyas, nunca las de otra empresa.

        Verlas no es poder asignarlas ni editarlas — de eso se ocupan `_rol_asignable` y
        `_rol_administrable`.

        `AC-RL-04` · `DR-1`: los inactivos solo aparecen **bajo petición** (`include_inactive`).
        Un rol apagado desaparecía de la única lista que existe y quedaba irrecuperable: no
        había forma de volver a encontrarlo para reactivarlo. El flag abre esa puerta y
        **nada más**: el filtro de empresa y plantillas de abajo no depende de él, porque
        usarlo para «quitar el filtro» mezclaría inquilinos.
        """
        consulta = select(Role)
        if not include_inactive:
            consulta = consulta.where(Role.is_active == True)
        empresa, _ = self._contexto(actor)
        if actor is not None:
            # `OD-14.c`: las plantillas de sistema son control global y se ven siempre; los
            # roles de inquilino exigen contexto, también para la autoridad global.
            if empresa is None:
                consulta = consulta.where(Role.company_id.is_(None))
            else:
                consulta = consulta.where(
                    (Role.company_id == empresa) | (Role.company_id.is_(None)))
        roles = (await self.db.execute(consulta)).scalars().all()
        return [RoleRead.model_validate(r) for r in roles]

    async def _nombre_de_rol_ocupado(self, nombre: str, *, empresa: int | None,
                                     excluir_id: int | None = None) -> bool:
        """¿Ese nombre de rol ya está tomado en el ámbito del actor? `AC-ID-04` · `AR-06`.

        ```
        `empresa` NULL   plantilla de producto   solo choca con otras plantillas
        `empresa` = X    rol de inquilino        choca con las plantillas y con los de X
        ```

        La segunda línea es la que impide que un rol de empresa repita el nombre de una
        plantilla que **ve** —el listado ofrecería dos entradas indistinguibles— sin
        prohibirle nombrar los suyos como quiera. Los inactivos cuentan: la ambigüedad no
        depende de que el rol esté vivo.

        La comparación es `lower(trim(...))`, que es lo que hace que «con espacios» y «con
        otra capitalización» sean el mismo nombre. Vive en el servicio y no en un índice
        único porque esta spec **no lleva migración** (`§4.3`).
        """
        objetivo = nombre.strip().lower()
        consulta = select(Role.id).where(func.lower(func.trim(Role.name)) == objetivo)
        if empresa is None:
            consulta = consulta.where(Role.company_id.is_(None))
        else:
            consulta = consulta.where(
                or_(Role.company_id.is_(None), Role.company_id == empresa))
        if excluir_id is not None:
            consulta = consulta.where(Role.id != excluir_id)
        return (await self.db.execute(consulta.limit(1))).first() is not None

    async def create_role(self, data: RoleCreate, current_user: dict | None = None) -> RoleRead:
        """Crea un rol **en la empresa efectiva del actor**. `AC-R02` · `OD-13.e`.

        `RoleCreate` no acepta `company_id` y no se le añade: la empresa sale del actor, no
        del cuerpo. La autoridad global crea plantillas de sistema (`company_id NULL`), que
        es lo que las semillas del producto han hecho siempre.
        """
        empresa, global_ = self._contexto(current_user)
        # `AC-ID-04` · `AR-06`. El nombre se valida **antes** de `db.add`, igual que los
        # permisos: una denegación no deja fila. La autoridad global crea plantillas de
        # sistema, de modo que su ámbito de nombres es el de las plantillas.
        nombre = data.name.strip()
        if not nombre:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="El nombre del rol es obligatorio")
        # `UAT-ADMIN-RBAC` · `AC-RL-05` · `DR-2`: un rol sin permisos no es un rol, es una
        # entrada de catálogo que solo sirve para dejar a alguien dentro del sistema sin
        # poder hacer nada. Se comprueba **antes** del duplicado y antes del `db.add`: el
        # rechazo no deja fila.
        if not data.permissions:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="El rol debe tener al menos un permiso")
        if await self._nombre_de_rol_ocupado(
                nombre, empresa=None if (current_user is None or global_) else empresa):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Ya existe un rol con ese nombre")
        # `R-199` · `T-02`: validar **antes** de `db.add` — una denegación no deja fila.
        try:
            self._validar_permisos(data.permissions or [],
                                   rol_de_inquilino=current_user is not None and not global_)
        except HTTPException as exc:
            if exc.status_code == status.HTTP_403_FORBIDDEN:
                await self._registrar_rechazo_de_autoridad(actor=current_user, role_id=None)
            raise
        # `UAT-ADMIN-RBAC` · `AC-ES-02` · `DR-3`: crear un rol **es** conceder sus permisos.
        # Sin esta comprobación, un administrador de empresa se fabricaba aquí el rol que
        # necesitaba y se lo asignaba después; el catálogo cerrado de `_validar_permisos`
        # impide inventar módulos, no repartir los que ya existen. La autoridad global queda
        # exenta: las plantillas de sistema son suyas por definición.
        if current_user is not None and not global_:
            await self._exigir_permisos_cubiertos(
                [(p.module, getattr(p.action, "value", p.action))
                 for p in (data.permissions or [])],
                current_user, role_id=None,
                motivo="rechazado: escalada de permisos (alta de rol)")

        role = Role(name=nombre, description=data.description,
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

        # `AC-RL-05` · `DR-2`. Un rol sin permisos no es un rol. Va **antes** de `sa_delete`:
        # una edición rechazada deja los permisos como estaban (`AC02`), y no se reescribe
        # el conjunto para luego descubrir que estaba prohibido vaciarlo.
        if data.permissions is not None and len(data.permissions) == 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="El rol debe tener al menos un permiso")

        # `R-199` · `T-02`: validar el conjunto **antes** de `sa_delete` — una denegación
        # deja los permisos intactos (`AC02`).
        if data.permissions is not None:
            try:
                self._validar_permisos(data.permissions,
                                       rol_de_inquilino=role.company_id is not None)
            except HTTPException as exc:
                if exc.status_code == status.HTTP_403_FORBIDDEN:
                    await self._registrar_rechazo_de_autoridad(actor=current_user,
                                                               role_id=role.id)
                raise

        # `UAT-ADMIN-RBAC` · `AC-ES-02` · `DR-3`: aquí solo se exige poseer lo que se
        # **añade** (nuevo conjunto − conjunto actual). Retirar reduce lo que el rol reparte
        # y nunca puede ser una escalada — prohibirlo dejaría los roles heredados sin poder
        # sanearse—, y reenviar el mismo conjunto no añade nada: es lo que la interfaz hace
        # al guardar, y la regla no puede convertir el botón de guardar en un bloqueo.
        #
        # Va antes de `sa_delete`: una denegación deja los permisos como estaban (`AC02`).
        if data.permissions is not None and current_user is not None \
                and not current_user.get("is_super_admin"):
            actuales = {(p.module, getattr(p.action, "value", p.action))
                        for p in role.permissions}
            anadidos = [(p.module, getattr(p.action, "value", p.action))
                        for p in data.permissions
                        if (p.module, getattr(p.action, "value", p.action)) not in actuales]
            await self._exigir_permisos_cubiertos(
                anadidos, current_user, role_id=role.id,
                motivo="rechazado: escalada de permisos (edición de rol)")

        # `permissions` se excluye del asignador genérico: es una relación y se sustituye
        # abajo. Asignarle una lista de diccionarios revienta el mapeador.
        update_data = data.model_dump(exclude_unset=True, exclude={"permissions"})

        # `AC-ID-04` · `AR-06`. El renombrado pasa por la misma comprobación que el alta, y
        # **excluye el propio rol**: renombrar `PA_X` a `pa_X` no es chocar consigo mismo.
        if "name" in update_data and update_data["name"] is not None:
            nombre = update_data["name"].strip()
            if not nombre:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="El nombre del rol es obligatorio")
            if nombre.lower() != (role.name or "").strip().lower():
                if await self._nombre_de_rol_ocupado(nombre, empresa=role.company_id,
                                                     excluir_id=role.id):
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                        detail="Ya existe un rol con ese nombre")
            update_data["name"] = nombre

        # `AC-RL-01` · `DR-1`. Un rol que alguien está usando no se da de baja: sus usuarios
        # seguirían entrando con un rol muerto —sin ninguna capacidad y sin saber por qué—,
        # y el administrador tendría que adivinar a quién reasignar. Se cuentan **solo los
        # usuarios activos**: con los dados de baja el rol ya no lo usa nadie, y bloquear
        # también por ellos dejaría roles imposibles de retirar.
        #
        # Va antes de mutar: una negativa no deja medio rol escrito.
        if data.is_active is False and role.is_active:
            n = (await self.db.execute(
                select(func.count(User.id)).where(
                    User.role_id == role.id, User.is_active.is_(True))
            )).scalar_one()
            if n > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(f"El rol tiene {n} usuario(s) activo(s) asignado(s); "
                            f"reasígnelos antes de desactivarlo"))

        # `AC-RL-06` · `AR-09`. El «antes» se captura **antes de mutar**: después, la fila ya
        # no recuerda qué se concedió ni qué se retiró, que es lo único que un auditor puede
        # revisar. Solo cadenas y booleanos — ningún secreto tiene cabida aquí.
        antes = {
            "nombre": role.name,
            "descripcion": role.description,
            "activo": role.is_active,
            "permisos": sorted(
                f"{p.module}:{getattr(p.action, 'value', p.action)}:{p.scope_type}"
                for p in role.permissions),
        }

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
        # `AC-RL-06` · el diff, con las mismas claves que el «antes», y los permisos que
        # entran y salen en claro: eso es lo que se audita de un cambio de permisos.
        despues = {
            "nombre": role.name,
            "descripcion": role.description,
            "activo": role.is_active,
            "permisos": sorted(
                f"{p.module}:{getattr(p.action, 'value', p.action)}:{p.scope_type}"
                for p in role.permissions),
        }
        await audit_accion(                                   # `GA-REM-032 AC03`
            self.db, usuario=current_user, accion=AuditAction.PERMISSION_CHANGE,
            modulo=AuditModule.USERS, entity_type="role", entity_id=role.id,
            previous_values=antes,
            new_values={
                **despues,
                "permisos_agregados": sorted(set(despues["permisos"]) - set(antes["permisos"])),
                "permisos_retirados": sorted(set(antes["permisos"]) - set(despues["permisos"])),
            },
        )
        return RoleRead.model_validate(role)

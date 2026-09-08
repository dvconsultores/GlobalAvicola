"""La administración del acceso por unidad — `GA-REM-040` fase 7 · `T-040-18` · `T-040-19`.

Dos relaciones, y el trabajo de esta fase es **no dejar que se toquen**:

    EMPRESA  → UNIDAD     habilitar y deshabilitar        decisión comercial
    USUARIO  → UNIDAD     conceder y revocar              decisión operativa

```
HABILITAR A LA EMPRESA   ≠  CONCEDER A SUS USUARIOS
CONCEDER A UN USUARIO    ≠  HABILITAR A SU EMPRESA
```

Si habilitar concediera, nadie decidiría nunca quién opera una cadena: habilitarla se lo daría
a toda la plantilla. Y si conceder habilitara, un administrador de usuarios estaría contratando
líneas de producción sin saberlo. Son actos de personas distintas y con consecuencias distintas,
de modo que aquí son funciones distintas, con permisos distintos, y ninguna llama a la otra.

**Y administrar el acceso no es acceder** — `OD-09.b`. Nada de este módulo consulta
`unidades_efectivas` del actor ni la modifica. Quien administra Incubadora sin tenerla concedida
sigue sin ver un solo lote de Incubadora, y eso no es un efecto secundario feliz: es que la
autoridad administrativa y el alcance operativo se leen de sitios distintos y ninguno alimenta
al otro.

Lo que este módulo **no** decide:

    BU-D10      qué pasa con el histórico cuando una empresa cierra una línea. Deshabilitar
                aquí apaga la efectividad y **no toca ni un dato ni una concesión**
                (`AC-A04`), que es lo mínimo que no cierra ninguna puerta.
    RBAC        qué acciones puede ejecutar el usuario. Conceder una cadena no concede
                ninguna acción sobre ella (`AC-B06`).
    EMPRESA     el inquilino de la petición. Viene resuelto de `OD-11` y aquí solo se usa.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..audit.helpers import audit_accion
from ..audit.models import AuditAction, AuditModule
from .models import BusinessUnit, CompanyBusinessUnit, UserBusinessUnit
from .schemas import ConcesionRead, HabilitacionRead
from .service import ConcesionInvalida, conceder_unidad, revocar_unidad


class RecursoDeAdministracionNoEncontrado(LookupError):
    """El usuario, la unidad o la concesión no existen **dentro de la empresa efectiva**.

    Una sola excepción para los tres casos, y a propósito. Distinguir «no existe» de «existe
    pero es de otra empresa» le diría a un administrador de A qué usuarios tiene B, que es
    filtración aunque no venga acompañada de ningún dato.
    """


class AdministracionInvalida(ValueError):
    """La operación es imposible por el estado de la configuración, no por autorización."""


# ── Localización, siempre acotada al inquilino ────────────────────────────────

async def _habilitacion(
    db: AsyncSession, *, company_id: int, code: str
) -> Optional[CompanyBusinessUnit]:
    """La fila de habilitación de **esta** empresa para ese código de unidad.

    El filtro por empresa de aquí es lo único que separa administrar la Incubadora propia de
    administrar la del vecino. Las rutas direccionan por código —nunca por identificador de
    fila— precisamente para que este filtro sea la única forma de llegar a la fila: no hay un
    camino alternativo en el que alguien pueda olvidarlo.
    """
    return (await db.execute(
        select(CompanyBusinessUnit)
        .join(BusinessUnit, BusinessUnit.id == CompanyBusinessUnit.business_unit_id)
        .where(CompanyBusinessUnit.company_id == company_id,
               BusinessUnit.code == code)
    )).scalar_one_or_none()


async def _unidad(db: AsyncSession, code: str) -> Optional[BusinessUnit]:
    """La unidad del catálogo de plataforma. No la crea ni la borra nadie desde aquí."""
    return (await db.execute(
        select(BusinessUnit).where(BusinessUnit.code == code)
    )).scalar_one_or_none()


async def _usuario_de_la_empresa(db: AsyncSession, *, user_id: int, company_id: int):
    """El usuario objetivo, **si pertenece a la empresa efectiva**. `AC-B10` · `AC-A07`.

    Esta comprobación es la que impide que el administrador de A conceda unidades a alguien
    de B. Al escribir la rechazaría también `conceder_unidad`, y las dos hacen falta: sin
    esta, el intento llegaría hasta el momento de la escritura y el mensaje de error diría
    si ese usuario existe.
    """
    from ..auth.models import User

    return (await db.execute(
        select(User).where(User.id == user_id, User.company_id == company_id)
    )).scalar_one_or_none()


# ── `A` · la habilitación de la empresa — `T-040-18` ──────────────────────────

async def listar_habilitaciones(
    db: AsyncSession, *, company_id: int
) -> list[HabilitacionRead]:
    """El catálogo de plataforma con el estado que tiene **en esta empresa**. `AC-A02`.

    Se listan las cuatro siempre, también las que la empresa no tiene habilitadas: quien
    administra necesita ver lo que puede encender, no solo lo encendido. Una unidad sin fila
    de configuración aparece como deshabilitada, que es exactamente lo que el resolutor
    entiende — la ausencia de configuración nunca se lee como permiso.
    """
    filas = (await db.execute(
        select(BusinessUnit, CompanyBusinessUnit.is_enabled)
        .outerjoin(CompanyBusinessUnit,
                   (CompanyBusinessUnit.business_unit_id == BusinessUnit.id)
                   & (CompanyBusinessUnit.company_id == company_id))
        .where(BusinessUnit.is_active.is_(True))
        .order_by(BusinessUnit.code)
    )).all()
    return [HabilitacionRead(code=u.code, name_key=u.name_key,
                             is_enabled=bool(estado))
            for u, estado in filas]


async def fijar_habilitacion(
    db: AsyncSession, *, company_id: int, code: str, habilitada: bool, actor: dict[str, Any]
) -> HabilitacionRead:
    """Habilita o deshabilita una unidad **para la empresa efectiva**. `AC-A03`.

    Y **solo** eso. No concede a nadie, no crea roles, no toca permisos, no reclasifica dato
    y no borra concesiones (`AC-A04`). Deshabilitar apaga la efectividad porque el resolutor
    exige `is_enabled`, no porque aquí se destruya nada:

    ```
    DESHABILITAR   →  las concesiones siguen escritas y dejan de ser efectivas
    REHABILITAR    →  vuelven a serlo, sin volver a concederlas       (`AC-A06`)
    ```

    Esa reversibilidad es deliberada y es lo que deja `BU-D10` intacta. La decisión pendiente
    —qué pasa con el histórico cuando una línea se cierra de verdad— sigue pudiendo resolverse
    en cualquier sentido, porque esta fase no ha borrado nada que una respuesta futura pudiera
    necesitar. Un borrado aquí habría contestado `BU-D10` por omisión.

    Idempotente: fijar el estado que ya se tiene no falla ni duplica. La fila se crea si no
    existía, de modo que «apagada explícitamente» quede distinguible de «nunca configurada»,
    que es la razón de que `is_enabled` sea un campo y no la ausencia de la fila.
    """
    unidad = await _unidad(db, code)
    if unidad is None or not unidad.is_active:
        raise RecursoDeAdministracionNoEncontrado(f"unidad de negocio {code!r}")

    fila = await _habilitacion(db, company_id=company_id, code=code)
    anterior = bool(fila.is_enabled) if fila is not None else False

    if fila is None:
        fila = CompanyBusinessUnit(company_id=company_id, business_unit_id=unidad.id,
                                   is_enabled=habilitada)
        db.add(fila)
    else:
        fila.is_enabled = habilitada
    await db.flush()

    # `AC-I03`. Se emite **después** de persistir, para que el registro diga lo ocurrido y no
    # lo intentado. Una acción denegada no llega hasta aquí y por eso no deja rastro de éxito.
    await audit_accion(
        db, usuario=actor, accion=AuditAction.CONFIG_CHANGE, modulo=AuditModule.CONFIG,
        entity_type="company_business_unit", entity_id=fila.id, company_id=company_id,
        previous_state="enabled" if anterior else "disabled",
        new_state="enabled" if habilitada else "disabled",
        new_values={"business_unit": code, "is_enabled": habilitada},
    )
    return HabilitacionRead(code=unidad.code, name_key=unidad.name_key,
                            is_enabled=bool(fila.is_enabled))


# ── `B` · la concesión al usuario — `T-040-19` ────────────────────────────────

def _proyectar(concesion: UserBusinessUnit, unidad: BusinessUnit,
               habilitacion: CompanyBusinessUnit) -> ConcesionRead:
    """Otorgada y efectiva, separadas. `AC-A05`.

    La efectividad se recompone con las mismas condiciones que `unidades_efectivas` aplica al
    leer. No se consulta al resolutor porque aquí ya están las tres filas en la mano; lo que
    **no** puede pasar es que digan cosas distintas, y de eso se ocupa una prueba dedicada.
    """
    return ConcesionRead(
        user_id=concesion.user_id, code=unidad.code,
        company_id=habilitacion.company_id, granted_at=concesion.created_at,
        revoked_at=concesion.revoked_at,
        is_effective=(concesion.revoked_at is None
                      and bool(habilitacion.is_enabled)
                      and bool(unidad.is_active)),
    )


async def listar_concesiones(
    db: AsyncSession, *, user_id: int, company_id: int
) -> list[ConcesionRead]:
    """Las concesiones de un usuario **bajo la empresa efectiva**. `AC-B07`.

    Se incluyen las revocadas, marcadas: quien administra necesita ver que algo se quitó, y
    borrarlas de la vista convertiría el historial en un agujero. Van con `revoked_at` y con
    `is_effective` en falso, de modo que ninguna pantalla pueda leerlas como vigentes.

    Lo que **no** se incluye es lo de otra empresa. Un usuario que estuvo en A y hoy está en B
    conserva escritas sus concesiones de A —`AC-B11`, son historia— y administrarlo en B no
    las muestra: el filtro es sobre la habilitación, que ya lleva la empresa dentro. Sin esto,
    una concesión de A aparecería junto a las de B y se leería como si valiera aquí.
    """
    filas = (await db.execute(
        select(UserBusinessUnit, BusinessUnit, CompanyBusinessUnit)
        .join(CompanyBusinessUnit,
              CompanyBusinessUnit.id == UserBusinessUnit.company_business_unit_id)
        .join(BusinessUnit, BusinessUnit.id == CompanyBusinessUnit.business_unit_id)
        .where(UserBusinessUnit.user_id == user_id,
               CompanyBusinessUnit.company_id == company_id)
        .order_by(BusinessUnit.code, UserBusinessUnit.id)
    )).all()
    return [_proyectar(c, u, h) for c, u, h in filas]


async def conceder(
    db: AsyncSession, *, user_id: int, company_id: int, code: str, actor: dict[str, Any]
) -> ConcesionRead:
    """Concede una unidad a un usuario de la empresa efectiva. `AC-B01`.

    Tres puertas, y ninguna sobra:

    ```
    el usuario es de esta empresa       si no, 404 — y no se dice si existe en otra
    la unidad está habilitada aquí      si no, no hay nada que conceder  (`§14.4`)
    la concesión no existe ya viva      si no, se devuelve la que hay    (`AC-B10`)
    ```

    La segunda es la que impide que conceder habilite por la puerta de atrás. Conceder una
    cadena que la empresa no ha contratado solo puede acabar de dos maneras: creando una
    concesión inefectiva que nadie entiende, o encendiendo la unidad sin que lo decida quien
    debe. La spec elige la tercera —rechazarlo— y aquí no se encienda nada nunca.

    La escritura la hace `conceder_unidad`, el camino sancionado desde la fase 1, y no una
    copia local: la comprobación de empresa del modelo tiene que aplicarse aunque a esta ruta
    se le olvide, y un segundo camino de escritura sería con el tiempo una segunda política.
    """
    usuario = await _usuario_de_la_empresa(db, user_id=user_id, company_id=company_id)
    if usuario is None:
        raise RecursoDeAdministracionNoEncontrado(f"usuario {user_id}")

    habilitacion = await _habilitacion(db, company_id=company_id, code=code)
    if habilitacion is None:
        raise RecursoDeAdministracionNoEncontrado(f"unidad de negocio {code!r}")
    unidad = await _unidad(db, code)
    if unidad is None or not unidad.is_active:
        raise RecursoDeAdministracionNoEncontrado(f"unidad de negocio {code!r}")

    if not habilitacion.is_enabled:
        # No se habilita de paso. `§7` del contrato de la fase: conceder no configura.
        raise AdministracionInvalida(
            f"la empresa no tiene habilitada la unidad {code!r}; habilítela primero")

    viva = (await db.execute(
        select(UserBusinessUnit).where(
            UserBusinessUnit.user_id == user_id,
            UserBusinessUnit.company_business_unit_id == habilitacion.id,
            UserBusinessUnit.revoked_at.is_(None))
    )).scalar_one_or_none()
    if viva is not None:
        # Idempotente y **sin auditar**: no ha cambiado nada que registrar. Un registro de
        # cambio por una repetición inflaría la auditoría con actos que no ocurrieron.
        return _proyectar(viva, unidad, habilitacion)

    try:
        concesion = await conceder_unidad(db, user=usuario,
                                          company_business_unit=habilitacion)
    except ConcesionInvalida as exc:  # pragma: no cover - la puerta anterior ya lo impide
        raise AdministracionInvalida(str(exc)) from exc

    await audit_accion(
        db, usuario=actor, accion=AuditAction.PERMISSION_CHANGE, modulo=AuditModule.USERS,
        entity_type="user_business_unit", entity_id=concesion.id, company_id=company_id,
        previous_state="none", new_state="granted",
        new_values={"target_user_id": user_id, "business_unit": code},
    )
    return _proyectar(concesion, unidad, habilitacion)


async def revocar(
    db: AsyncSession, *, user_id: int, company_id: int, code: str, actor: dict[str, Any]
) -> ConcesionRead:
    """Revoca una concesión viva. `AC-B05`.

    **Marca, no borra** (`AC-B11` · `OD-09.e`). La fila queda con su fecha, y por eso el
    efecto es inmediato sin ser destructivo: el resolutor exige `revoked_at IS NULL` en cada
    petición, de modo que la siguiente evaluación ya deniega sin esperar a que caduque ningún
    token, y el historial sigue contando quién tuvo qué y hasta cuándo.

    Revocar la unidad tampoco toca lo que el usuario registró mientras la tuvo: `§6.3`
    separa retirar el acceso de borrar el trabajo.
    """
    usuario = await _usuario_de_la_empresa(db, user_id=user_id, company_id=company_id)
    if usuario is None:
        raise RecursoDeAdministracionNoEncontrado(f"usuario {user_id}")

    habilitacion = await _habilitacion(db, company_id=company_id, code=code)
    unidad = await _unidad(db, code)
    if habilitacion is None or unidad is None:
        raise RecursoDeAdministracionNoEncontrado(f"unidad de negocio {code!r}")

    concesion = await revocar_unidad(db, user=usuario, company_business_unit=habilitacion)
    if concesion is None:
        # Revocar lo que ya no está viva no es un éxito silencioso: quien administra pidió un
        # cambio que no ocurrió, y decírselo evita que dé por hecho un acceso ya retirado.
        raise RecursoDeAdministracionNoEncontrado(
            f"concesión viva de {code!r} para el usuario {user_id}")

    await audit_accion(
        db, usuario=actor, accion=AuditAction.PERMISSION_CHANGE, modulo=AuditModule.USERS,
        entity_type="user_business_unit", entity_id=concesion.id, company_id=company_id,
        previous_state="granted", new_state="revoked",
        new_values={"target_user_id": user_id, "business_unit": code},
    )
    return _proyectar(concesion, unidad, habilitacion)

"""Las dos superficies de administración — `GA-REM-040` fase 7 · `AC-F03` · `OD-09.b`.

```
EMPRESA  →  UNIDADES     GET · PATCH enable · PATCH disable
USUARIO  →  UNIDADES     GET · POST conceder · DELETE revocar
```

Tres propiedades que estas rutas sostienen y conviene leer juntas:

**La empresa no se recibe, se resuelve.** Ninguna acepta `company_id`. La empresa efectiva
sale de `OD-11` —la persistida del usuario, salvo contexto de cambio autorizado y válido— y es
la única sobre la que se administra. Un parámetro de empresa habría que validarlo en cada ruta
para que no ampliara el inquilino; no habiéndolo, no hay nada que se pueda olvidar.

**La unidad se direcciona por código.** Nunca por identificador de habilitación. El código
`hatchery` significa una fila distinta en cada empresa, y la que se toca la elige el filtro por
empresa del servicio. Aceptar el identificador de fila habría hecho expresable «la incubadora
de la empresa vecina», y entonces la seguridad dependería de acordarse de rechazarla.

**Administrar no es acceder** (`AC-F04`). Ninguna de estas rutas consulta el alcance operativo
del actor, y ninguna se lo modifica. Quien las usa sin tener la cadena concedida sigue sin ver
un lote de esa cadena: son dos dimensiones que se leen de sitios distintos.

Y no hay atajo por nombre de rol. Un rol llamado «Administrador» sin el permiso declarado
recibe `403` igual que cualquier otro (`AC-F05`).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.security import require_permission
from ..database import get_db
from ..transaction import RutaTransaccional
from . import admin
from .schemas import ConcesionCreate, ConcesionRead, HabilitacionRead

# `GA-REM-026`. La frontera transaccional es de la ruta: conceder y auditar la concesión
# confirman juntos o no confirma ninguno. Sin esto quedaría escrito el acceso sin el registro
# de quién lo dio — que es peor que no haberlo dado.
router = APIRouter(route_class=RutaTransaccional)

#: El módulo `RBAC` propio del plano de control. `GA-REM-040 §5`: «el plano de control tiene
#: permisos propios». No se reutiliza `users` porque habilitar una cadena productiva para la
#: empresa no es administrar a un usuario, y no se reutiliza `masters` porque una unidad de
#: negocio no es un maestro. Las cuatro acciones separan las dos autoridades:
#:
#:     business_units:read     ver la configuración y las concesiones
#:     business_units:update   habilitar y deshabilitar        — la empresa
#:     business_units:create   conceder a un usuario           — el acceso
#:     business_units:delete   revocar a un usuario
#:
#: De modo que se puede autorizar a alguien a repartir acceso entre las líneas ya contratadas
#: sin autorizarle a contratar líneas nuevas.
MODULO = "business_units"


def _empresa_efectiva(current_user: dict) -> int:
    """La empresa sobre la que se administra, o `403`.

    `current_user["company_id"]` ya es la efectiva: `get_current_user` la resuelve con
    `OD-11`. Nulo significa **no hay empresa efectiva** —el Super Administrador global, que se
    siembra sin ninguna— y entonces no se administra nada: «todas las empresas» no es un valor
    por defecto, elegir una es un acto (`OD-11.c`). Quien tenga autoridad global y quiera
    administrar la empresa A se sitúa en ella con `switch-company`, que deja rastro en `P-09`.
    """
    company_id = current_user.get("company_id")
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No hay empresa efectiva sobre la que administrar unidades de negocio",
        )
    return company_id


def _traducir(exc: Exception) -> HTTPException:
    """Los errores del servicio, en el contrato `HTTP` de la casa.

    `404` para lo que no existe **en la empresa efectiva**, sin distinguirlo de lo que existe
    en otra: esa distinción ya sería información sobre el vecino.
    """
    if isinstance(exc, admin.RecursoDeAdministracionNoEncontrado):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, admin.SegregacionDeFunciones):
        # `403` y no `409`: es la misma clase de negativa que `AC15` —«tienes la autoridad y
        # aun así esto no» — y comparte su código para que el cliente no tenga que aprender
        # dos contratos para la misma idea.
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ── `A` · la empresa y sus unidades — `T-040-18` ──────────────────────────────

@router.get("/business-units", response_model=list[HabilitacionRead],
            tags=["Business Units"])
async def listar_unidades_de_la_empresa(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(MODULO, "read")),
):
    """Las cuatro unidades del catálogo con su estado en la empresa efectiva. `AC-A02`."""
    return await admin.listar_habilitaciones(db, company_id=_empresa_efectiva(current_user))


@router.patch("/business-units/{code}/enable", response_model=HabilitacionRead,
              tags=["Business Units"])
async def habilitar_unidad(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(MODULO, "update")),
):
    """Habilita la unidad para la empresa efectiva. `AC-A03`.

    **No concede a nadie.** Después de esto, un usuario sin concesión sigue sin ver un solo
    lote de la cadena: habilitar dice que la empresa la opera, no quién la opera.
    """
    try:
        return await admin.fijar_habilitacion(
            db, company_id=_empresa_efectiva(current_user), code=code,
            habilitada=True, actor=current_user)
    except (admin.RecursoDeAdministracionNoEncontrado, admin.AdministracionInvalida) as exc:
        raise _traducir(exc) from exc


@router.patch("/business-units/{code}/disable", response_model=HabilitacionRead,
              tags=["Business Units"])
async def deshabilitar_unidad(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(MODULO, "update")),
):
    """Deshabilita la unidad para la empresa efectiva. `AC-A03` · `AC-A04`.

    Las concesiones **no se borran**: dejan de ser efectivas y siguen escritas, y rehabilitar
    las devuelve (`AC-A06`). `BU-D10` —qué pasa con el histórico cuando una línea se cierra de
    verdad— sigue pendiente de ratificación, y esta ruta la deja pendiente: no destruye nada
    que una respuesta futura pudiera necesitar.
    """
    try:
        return await admin.fijar_habilitacion(
            db, company_id=_empresa_efectiva(current_user), code=code,
            habilitada=False, actor=current_user)
    except (admin.RecursoDeAdministracionNoEncontrado, admin.AdministracionInvalida) as exc:
        raise _traducir(exc) from exc


# ── `B` · el usuario y sus unidades — `T-040-19` ──────────────────────────────

@router.get("/users/{user_id}/business-units", response_model=list[ConcesionRead],
            tags=["Business Units"])
async def listar_concesiones_de_usuario(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(MODULO, "read")),
):
    """Las concesiones del usuario **bajo la empresa efectiva**. `AC-B07`.

    Otorgada y efectiva van separadas: una concesión viva sobre una unidad deshabilitada
    aparece otorgada y **no** efectiva, que es la verdad y no la mitad de ella.
    """
    company_id = _empresa_efectiva(current_user)
    if await admin._usuario_de_la_empresa(db, user_id=user_id,
                                          company_id=company_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"usuario {user_id}")
    return await admin.listar_concesiones(db, user_id=user_id, company_id=company_id)


@router.post("/users/{user_id}/business-units", response_model=ConcesionRead,
             status_code=status.HTTP_201_CREATED, tags=["Business Units"])
async def conceder_unidad_a_usuario(
    user_id: int,
    data: ConcesionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(MODULO, "create")),
):
    """Concede una unidad habilitada a un usuario de la empresa efectiva. `AC-B01`.

    **No habilita la unidad.** Si la empresa no la tiene habilitada, la concesión se rechaza
    en vez de encenderla: contratar una línea es una decisión comercial que no se toma de
    paso al repartir accesos.
    """
    try:
        return await admin.conceder(
            db, user_id=user_id, company_id=_empresa_efectiva(current_user),
            code=data.code, actor=current_user)
    except (admin.RecursoDeAdministracionNoEncontrado, admin.AdministracionInvalida,
            admin.SegregacionDeFunciones) as exc:
        raise _traducir(exc) from exc


@router.delete("/users/{user_id}/business-units/{code}", response_model=ConcesionRead,
               tags=["Business Units"])
async def revocar_unidad_a_usuario(
    user_id: int,
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission(MODULO, "delete")),
):
    """Revoca la concesión. Efecto inmediato, sin borrar historia. `AC-B05` · `AC-B11`.

    Devuelve la concesión revocada con su fecha en vez de un `204` mudo: quien administra
    necesita poder comprobar **qué** quedó revocado y cuándo, y un cuerpo tipado lo dice sin
    tener que consultar la auditoría.
    """
    try:
        return await admin.revocar(
            db, user_id=user_id, company_id=_empresa_efectiva(current_user),
            code=code, actor=current_user)
    except (admin.RecursoDeAdministracionNoEncontrado, admin.AdministracionInvalida) as exc:
        raise _traducir(exc) from exc

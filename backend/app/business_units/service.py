"""El resolutor central de acceso efectivo — `GA-REM-040` `T-040-05`, `AC-C01`.

Un solo sitio, y por una razón que el propio proyecto ya demostró: el filtro de **empresa** no
está centralizado —`MasterService` lo aplica y los demás servicios lo repiten a mano—, y esa
dispersión es justo lo que hace difícil auditar hoy quién ve qué. Un segundo eje repartido de la
misma forma heredaría el mismo problema.

    ACCESO OPERATIVO EFECTIVO
        =  misma empresa
       AND unidad HABILITADA para la empresa
       AND unidad CONCEDIDA al usuario
       AND unidad activa en el producto

Lo que este módulo **no** hace, y no es un olvido:

    RBAC              `¿puede el usuario ejecutar la acción X?` sigue siendo de `GA-REM-002`.
                      Este resolutor solo contesta `¿está la unidad en su alcance operativo?`,
                      y la cadena completa —inquilino → unidad → RBAC → regla de negocio— se
                      compone fuera.

    CONTROL           `OD-09.a` da a contraloría visibilidad de **toda** la empresa, y
                      explícitamente **no** autoridad operativa. Ese es otro resolutor, de una
                      fase posterior. Meterlo aquí convertiría un permiso de lectura en
                      permiso de escritura sobre las cuatro unidades — que es exactamente el
                      error que `OD-09` se escribió para evitar.

No depende de `Request`: las tareas de fondo y los informes no tienen petición, y si la
exigiera tendrían que reimplementar la regla.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import BusinessUnit, CompanyBusinessUnit, UserBusinessUnit


async def unidades_habilitadas(db: AsyncSession, company_id: Optional[int]) -> list[str]:
    """Las unidades que una empresa tiene habilitadas, por código y ordenadas.

    Nivel de empresa: no necesita usuario, de modo que una tarea de fondo sin sesión puede
    preguntarlo. Una empresa sin fila para una unidad **no** la tiene habilitada: la ausencia
    de configuración nunca se lee como permiso.
    """
    if company_id is None:
        return []

    filas = (await db.execute(
        select(BusinessUnit.code)
        .join(CompanyBusinessUnit,
              CompanyBusinessUnit.business_unit_id == BusinessUnit.id)
        .where(CompanyBusinessUnit.company_id == company_id,
               CompanyBusinessUnit.is_enabled.is_(True),
               BusinessUnit.is_active.is_(True))
    )).scalars().all()
    return sorted(filas)


async def unidades_efectivas(
    db: AsyncSession, user, company_id: Optional[int] = None
) -> list[str]:
    """El alcance operativo de un usuario: lo habilitado **y** concedido, por código.

    Las cuatro condiciones a la vez. Quitar cualquiera de ellas es una de las mutaciones que
    `GA-REM-040 §19` exige que rompa una prueba:

        empresa del usuario     sin ella, un usuario sin empresa heredaría lo de otra
        habilitada              sin ella, revocar a la empresa no revocaría a nadie
        concedida POR ESA       sin ella, pertenecer a la empresa bastaría — `§16` principio 1
          MISMA EMPRESA         y una concesión de la empresa anterior seguiría valiendo
        concesión VIVA          sin ella, volver a una empresa reviviría lo revocado
        activa en el producto   sin ella, una unidad retirada seguiría accesible

    La tercera condición es la que `OD-09.d` corrigió. La concesión apunta a la **habilitación
    de una empresa**, no al catálogo, de modo que exigir `CompanyBusinessUnit.company_id ==
    company_id` deja fuera automáticamente las concesiones de una empresa anterior: existen,
    son historia y no son efectivas.

    **Sin concesiones, la lista está vacía.** Nunca «toda la empresa»: si no conceder nada
    equivaliera a concederlo todo, nadie concedería nunca y la capacidad sería opcional en la
    práctica (`OD-09.c`).

    Se lee de la base en cada llamada, no de un token ni de una caché: así una revocación surte
    efecto en la evaluación siguiente y no cuando caduque la sesión.
    """
    # `OD-11`: la empresa efectiva puede venir dada —un actor autorizado situado en otra
    # empresa— o derivarse de la persistida. Lo que **no** cambia es que las concesiones se
    # buscan dentro de esa empresa y de ninguna otra: situarse en una empresa da contexto,
    # no autoridad sobre sus cadenas (`AC-C14`).
    if company_id is None:
        company_id = getattr(user, "company_id", None)
    return await unidades_efectivas_por_id(db, user_id=user.id, company_id=company_id)


async def unidades_efectivas_por_id(
    db: AsyncSession, *, user_id: Optional[int], company_id: Optional[int]
) -> list[str]:
    """Lo mismo, con identificadores en vez de con el objeto.

    Existe porque el contexto de una petición viaja como diccionario —`current_user`— y no
    como fila del ORM. Una sola consulta con dos puertas, en lugar de dos consultas que
    tarde o temprano dirían cosas distintas.
    """
    if company_id is None or user_id is None:
        # El Super Administrador global se siembra sin empresa. No obtiene acceso operativo a
        # ninguna por esta capacidad: el modelo de inquilino se preserva intacto.
        return []

    filas = (await db.execute(
        select(BusinessUnit.code)
        .join(CompanyBusinessUnit,
              CompanyBusinessUnit.business_unit_id == BusinessUnit.id)
        .join(UserBusinessUnit,
              UserBusinessUnit.company_business_unit_id == CompanyBusinessUnit.id)
        .where(CompanyBusinessUnit.company_id == company_id,
               CompanyBusinessUnit.is_enabled.is_(True),
               UserBusinessUnit.user_id == user_id,
               UserBusinessUnit.revoked_at.is_(None),
               BusinessUnit.is_active.is_(True))
    )).scalars().all()
    return sorted(filas)


async def unidades_concedidas(
    db: AsyncSession, *, user_id: Optional[int], company_id: Optional[int]
) -> list[str]:
    """Las concesiones **vivas** de un usuario en una empresa, estén o no habilitadas.

    `GA-REM-040` enmienda E · `AC-H11`. Es deliberadamente distinta de
    `unidades_efectivas`: aquélla exige además que la empresa tenga la unidad habilitada y
    que siga activa en el producto.

    ```
    CONCEDIDA   la empresa se la dio al usuario y no se la ha quitado
    EFECTIVA    concedida  ∩  habilitada  ∩  activa en el producto
    ```

    Que las dos puedan diferir es justo lo que la sesión tiene que poder contar: una
    concesión sobre una unidad que la empresa apagó **sigue existiendo** —`AC-A04`, apagar no
    revoca— y no da acceso. Sin las dos listas, un cliente no puede distinguir «nunca se lo
    dieron» de «se lo dieron y la empresa cerró esa línea».

    No sustituye a `unidades_efectivas` en ninguna decisión de autorización: esto es para
    **contar**, no para **autorizar**.
    """
    if company_id is None or user_id is None:
        return []

    filas = (await db.execute(
        select(BusinessUnit.code)
        .join(CompanyBusinessUnit,
              CompanyBusinessUnit.business_unit_id == BusinessUnit.id)
        .join(UserBusinessUnit,
              UserBusinessUnit.company_business_unit_id == CompanyBusinessUnit.id)
        .where(CompanyBusinessUnit.company_id == company_id,
               UserBusinessUnit.user_id == user_id,
               UserBusinessUnit.revoked_at.is_(None))
    )).scalars().all()
    return sorted(filas)


async def tiene_acceso(db: AsyncSession, user, code: str) -> bool:
    """¿Está esa unidad dentro del alcance operativo del usuario?

    Se apoya en `unidades_efectivas` en lugar de repetir la consulta. Dos caminos con dos
    implementaciones serían dos políticas, y con el tiempo una se quedaría atrás — que es el
    modo habitual en que un sistema acaba concediendo de más sin que nadie lo decida.
    """
    return code in await unidades_efectivas(db, user)


class ConcesionInvalida(ValueError):
    """Se intentó conceder una unidad que no pertenece a la empresa del usuario."""


async def conceder_unidad(db: AsyncSession, *, user, company_business_unit):
    """Concede a un usuario una unidad **de su propia empresa**. `AC-B10`.

    Es el límite de escritura de la capacidad. Existe ya en la fase 1 y no en la 7 —donde
    vivirá la API de administración— porque la regla que protege es del modelo, no de la
    pantalla: una fila que cruza empresas, si llega a escribirse, acaba encontrando el camino
    a una consulta que la lea mal.

    El resolutor comprueba lo mismo al leer, y las dos comprobaciones hacen falta:

        al escribir   impide que se registre una concesión que nunca debió existir
        al leer       impide que una concesión legítima de ayer siga valiendo cuando el
                      usuario cambió de empresa hoy

    Un usuario **sin empresa** —el super administrador global— no puede recibir ninguna: no
    hay empresa que se la conceda.
    """
    company_id = getattr(user, "company_id", None)
    if company_id is None:
        raise ConcesionInvalida(
            "un usuario sin empresa no puede recibir concesiones de unidad")
    if company_business_unit.company_id != company_id:
        raise ConcesionInvalida(
            f"la habilitación pertenece a la empresa {company_business_unit.company_id} "
            f"y el usuario a la {company_id}")

    concesion = UserBusinessUnit(
        user_id=user.id, company_business_unit_id=company_business_unit.id)
    db.add(concesion)
    await db.flush()
    return concesion


class AccesoDeUnidadDenegado(PermissionError):
    """La unidad pedida no está en el alcance operativo efectivo del usuario."""


async def exigir_acceso_a_unidad(
    db: AsyncSession, *, user, code: str, company_id: Optional[int] = None
) -> None:
    """La guarda central. `AC-C08` · `AC-C16`.

    Lanza si la unidad no está en el alcance efectivo; no devuelve nada si lo está.

    Es una función y no una dependencia de `FastAPI` **a propósito**: las tareas de fondo, los
    informes y las notificaciones tendrán que hacer la misma comprobación, y si viviera atada a
    una petición cada uno reimplementaría la regla. Una regla aplicada en un sitio y ausente en
    otro no es una regla, es una casualidad — la misma lección que `app/tenancy.py` ya había
    aprendido con el filtro de empresa.

    **No sustituye al `RBAC`.** Contesta «¿está esta cadena productiva en su alcance?», no
    «¿puede ejecutar esta acción?». La cadena completa se compone fuera:

        inquilino → unidad de negocio → RBAC → regla de negocio del recurso

    Y no conoce excepciones por nombre de rol. Que alguien se llame «Administrador» o
    «Contralor» no le abre nada aquí: `OD-09.a` da a las funciones de control visibilidad **de
    lectura** sobre la empresa, que es otro resolutor y otra fase.
    """
    efectivas = await unidades_efectivas(db, user, company_id=company_id)
    if code not in efectivas:
        raise AccesoDeUnidadDenegado(
            f"sin acceso operativo a la unidad de negocio {code!r}")


async def revocar_concesiones(db: AsyncSession, *, user) -> int:
    """Marca como historia todas las concesiones vivas de un usuario. `OD-09.e`.

    **Debe invocarse cuando un usuario cambia de empresa.** Es lo que hace que salir deje
    rastro, y sin ese rastro «volvió a la empresa A» sería indistinguible de «nunca salió»:
    la concesión antigua reviviría sola al regresar, que es exactamente lo que `OD-09.e`
    prohíbe. Volver no prueba el mismo cargo ni la misma necesidad operativa.

    No borra. La fila queda, auditable, con la fecha en que dejó de valer — `AC-B11`.

    **Hoy no hay ningún camino que cambie la empresa de un usuario**: `UserUpdate` no acepta
    `company_id`, y `switch-company` desplaza el contexto sin tocar `users.company_id`. Esta
    función existe antes que su llamador a propósito: la fase 7, que traerá esa
    administración, encontrará la regla escrita en vez de tener que deducirla. Mientras tanto
    la garantía vale lo que valga su futuro llamador, y eso queda dicho.

    Devuelve cuántas se revocaron.
    """
    from datetime import datetime, timezone

    from sqlalchemy import update

    resultado = await db.execute(
        update(UserBusinessUnit)
        .where(UserBusinessUnit.user_id == user.id,
               UserBusinessUnit.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    await db.flush()
    return resultado.rowcount or 0


async def revocar_unidad(db: AsyncSession, *, user, company_business_unit):
    """Revoca **una** concesión concreta. `GA-REM-040` fase 7 · `T-040-19`.

    Vive junto a `revocar_concesiones` y no en la capa de administración a propósito: son las
    dos formas de retirar acceso y tienen que significar lo mismo. Si una marcase y la otra
    borrase, «revocado» dependería de por qué camino se llegó, y el historial que `OD-09.e`
    necesita valdría solo la mitad de las veces.

    Devuelve la concesión revocada, o `None` si no había ninguna viva — que no es un error de
    este nivel: quien llama decide si eso es un `404` o un silencio.
    """
    from datetime import datetime, timezone

    concesion = (await db.execute(
        select(UserBusinessUnit).where(
            UserBusinessUnit.user_id == user.id,
            UserBusinessUnit.company_business_unit_id == company_business_unit.id,
            UserBusinessUnit.revoked_at.is_(None))
    )).scalar_one_or_none()
    if concesion is None:
        return None

    concesion.revoked_at = datetime.now(timezone.utc)
    await db.flush()
    return concesion

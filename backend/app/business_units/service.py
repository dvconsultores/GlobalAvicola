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


async def unidades_efectivas(db: AsyncSession, user) -> list[str]:
    """El alcance operativo de un usuario: lo habilitado **y** concedido, por código.

    Las cuatro condiciones a la vez. Quitar cualquiera de ellas es una de las mutaciones que
    `GA-REM-040 §19` exige que rompa una prueba:

        empresa del usuario     sin ella, un usuario sin empresa heredaría lo de otra
        habilitada              sin ella, revocar a la empresa no revocaría a nadie
        concedida POR ESA       sin ella, pertenecer a la empresa bastaría — `§16` principio 1
          MISMA EMPRESA         y una concesión de la empresa anterior seguiría valiendo
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
    company_id = getattr(user, "company_id", None)
    if company_id is None:
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
               UserBusinessUnit.user_id == user.id,
               BusinessUnit.is_active.is_(True))
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

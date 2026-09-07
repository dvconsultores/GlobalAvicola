"""Quién recibe cada notificación interna — `GA-REM-038` enmienda A, decisión `OD-08`.

Un solo sitio. Repartir «consulta administradores aquí, supervisores allá, el originador más
allá» habría hecho que cada evento resolviera a su manera, y con el tiempo discreparían.

`OD-08` nombra **funciones**, no roles. La correspondencia con los roles que existen de verdad
está en `audit/remediation/P14_OD08_ROLE_MAPPING_MATRIX.md`, derivada del catálogo y no
inventada aquí.
"""
from __future__ import annotations

import unicodedata
from typing import Iterable, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

#: Fragmentos de nombre de rol por los que se reconoce cada función de `OD-08`.
#:
#: Por **nombre** y no por identificador: los identificadores dependen del orden de siembra, y
#: `GA-REM-034` permite crear roles nuevos, de modo que fijarlos sería frágil. Sin acentos ni
#: mayúsculas, porque el catálogo los escribe de varias formas.
#:
#: No hay entrada para «gerente del área»: no existe rol de gerencia ni modelo de área. Se
#: declara en la matriz de correspondencia en lugar de sustituirse por otra cosa.
FUNCIONES_OD08 = {
    "administrador": "administrador",   # Administrador de Empresa · Super Administrador
    "contralor": "contralor",           # Contralor Avícola
    "supervisor": "supervisor",         # Supervisor Avícola
}


def _sin_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )


async def _por_funcion(db: AsyncSession, company_id: int) -> set[int]:
    """Usuarios activos **de esa empresa** cuyo rol representa una función de `OD-08`.

    El filtro de empresa no es una comodidad: el Super Administrador se siembra con
    `company_id = None` y su nombre de rol contiene «administrador». Sin esta condición
    recibiría el detalle operativo de todas las empresas, que es la fuga exacta que hay que
    evitar. `OD-08` dice «de la empresa correspondiente».
    """
    from ..auth.models import Role, User

    filas = (await db.execute(
        select(User.id, Role.name)
        .join(Role, Role.id == User.role_id)
        .where(User.company_id == company_id, User.is_active.is_(True))
    )).all()

    fragmentos = tuple(FUNCIONES_OD08.values())
    return {
        user_id for user_id, nombre_rol in filas
        if nombre_rol and any(f in _sin_acentos(nombre_rol) for f in fragmentos)
    }


async def resolver_destinatarios(
    db: AsyncSession,
    *,
    company_id: int,
    originadores: Iterable[Optional[int]] = (),
    explicitos: Iterable[Optional[int]] = (),
) -> list[int]:
    """El conjunto de destinatarios de un evento normativo de `P-14`.

    ```
    explícitos de fuentes anteriores ∪ originador ∪ administradores ∪ contraloría ∪ supervisor
        filtrado por  empresa del evento  y  usuario activo
        DISTINCT por user_id
    ```

    **La unión no resta.** «Notificar al operador» (`docs/02 §3.14`) y «Notificar al rol
    Analista SAP» (`docs/10 §6.2`) siguen exigidos por sus fuentes; `OD-08` amplía y no
    sustituye. Por eso los explícitos entran aparte y no dependen de que su rol case con
    ninguna función.

    **Una persona, un aviso.** Devuelve un conjunto, de modo que quien cumpla varias
    condiciones —originador y administrador, por ejemplo— aparece una sola vez. La
    deduplicación es aquí, en el backend, y no en la pantalla.

    El originador llega como identificador **persistido** —`registered_by_id`—, nunca como
    «el usuario autenticado»: el aviso puede generarse mucho después y por otra persona.
    """
    destinatarios = await _por_funcion(db, company_id)

    # Los explícitos y los originadores se comprueban contra la empresa igual que el resto:
    # un identificador de otra empresa no entra por venir «recomendado».
    candidatos = {u for u in (*originadores, *explicitos) if u is not None}
    if candidatos:
        from ..auth.models import User

        propios = (await db.execute(
            select(User.id).where(
                User.id.in_(candidatos),
                User.company_id == company_id,
                User.is_active.is_(True),
            )
        )).scalars().all()
        destinatarios |= set(propios)

    return sorted(destinatarios)


async def originadores_de_eventos(
    db: AsyncSession, event_ids: Sequence[int]
) -> list[int]:
    """Quiénes registraron esos eventos. Para el aviso de envío SAP, que agrupa varios."""
    if not event_ids:
        return []
    from ..operations.models import OperationalEvent

    return list((await db.execute(
        select(OperationalEvent.registered_by_id)
        .where(OperationalEvent.id.in_(event_ids))
    )).scalars().all())

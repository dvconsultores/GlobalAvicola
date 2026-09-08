"""Acotar una consulta a las unidades de negocio efectivas — `GA-REM-040` `T-040-09`.

    PERTENECER A LA EMPRESA  ES NECESARIO  PERO NO SUFICIENTE

La fase 2 dejó dicho que clasificar una ruta no protege sus filas. Aquí se protegen.

**Por política y no por un filtro universal.** Cada entidad determina su cadena productiva de
una forma distinta —el lote la lleva encima, sus fases la heredan, las entidades de traspaso
tienen dos lados a la vez— y un predicado genérico aplicado a todas las trataría igual. Sería
cómodo de escribir y falso: `SHARED_ENTITY_ROW_SCOPE_MATRIX` documenta catorce entidades de
dieciséis cuya unidad **no** es derivable de forma fiable, y forzar una columna a cada una las
desincronizaría.

Lo que **no** entra aquí, y no es un olvido:

    egg_batches · chick_batches   son traspasos, con origen y destino explícitos. Aplicarles
                                  un predicado de propietario único rompería `P-10`. Su
                                  contrato campo por campo es la fase 5 (`OD-10.a`).

    eventos sin lote              `lot_id` es nulable a propósito. Lo no clasificable va a
                                  «pendiente de clasificar», que es la fase 6 (`OD-10.c`).

    agregados y KPI               la fase 4.
"""
from __future__ import annotations

from typing import Any, Optional, Sequence

from sqlalchemy import false


def predicado(modelo: Any, unidades: Sequence[str]) -> Optional[Any]:
    """El predicado que acota `modelo` a esas unidades, o `None` si no tiene política.

    `None` significa **esta entidad no se acota por unidad en la fase 3**, no «déjala pasar
    sin mirar»: el filtro de empresa y el `RBAC` siguen aplicándose igual. Devolverlo para lo
    que no se sabe acotar es lo contrario de un `fail open`, porque no se afirma nada.

    Una lista de unidades **vacía** produce un predicado que no admite ninguna fila. Es el
    caso del usuario sin concesiones (`OD-09.c`), y tiene que dar cero filas productivas, no
    todas: si no conceder nada equivaliera a concederlo todo, nadie concedería nunca.
    """
    from ..masters.models import BirdTypeEnum, Lot

    if modelo is not Lot:
        return None

    if not unidades:
        return false()

    # `BirdTypeEnum` **no es el control de acceso**: quién puede ver qué lo deciden
    # `business_units`, `company_business_units` y `user_business_units`. El enum es el dato
    # de dominio que dice a qué cadena pertenece el lote, y aquí solo se usa para casar la
    # fila con el alcance ya resuelto. Si mandara el enum, cambiar un valor de dominio
    # cambiaría quién ve qué.
    #
    # `in_` deja fuera los nulos, y es deliberado: un lote sin cadena declarada no se puede
    # atribuir, y `OD-10.c` decidió que lo no clasificable quede **pendiente de clasificar**
    # en lugar de abrirse o borrarse. Esa bandeja es la fase 6; hasta entonces el
    # comportamiento seguro es que no aparezca en la operación.
    tipos = []
    for code in unidades:
        try:
            tipos.append(BirdTypeEnum(code))
        except ValueError:
            # Una unidad del catálogo sin correspondencia en el dominio no casa con ninguna
            # fila. No es un error: es que todavía no hay lotes de esa cadena.
            continue
    return Lot.bird_type.in_(tipos) if tipos else false()


def lotes_alcanzables(company_id, unidades):
    """Subconsulta con los identificadores de lote que el usuario alcanza.

    `GA-REM-040` fase 4. Es la pieza que permite acotar un **agregado** sin recalcular la
    regla: los indicadores y el panel no preguntan «¿de qué cadena es este evento?» —que
    obligaría a un `JOIN` distinto en cada consulta— sino «¿está su lote entre los que este
    usuario alcanza?».

        CONJUNTO AUTORIZADO  →  AGREGAR

    y nunca al revés. Agregar la empresa entera y después descontar lo ajeno deja el total
    correcto y el camino abierto: cualquier consulta que se olvide del descuento vuelve a
    filtrar, y un total que cuenta lo que no se ve lo revela por diferencia.

    Un evento **sin lote** no entra. Es la misma decisión que la fase 3 tomó con el lote sin
    cadena declarada: `OD-10.c` manda lo no clasificable a «pendiente de clasificar», que es
    la fase 6, y hasta entonces lo seguro es que no contribuya. Queda declarado.
    """
    from sqlalchemy import select

    from ..masters.models import Lot

    consulta = select(Lot.id).where(Lot.company_id == company_id)
    condicion = predicado(Lot, unidades)
    return consulta if condicion is None else consulta.where(condicion)

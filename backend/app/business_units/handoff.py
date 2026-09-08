"""El contrato de traspaso entre cadenas — `GA-REM-040` fase 5 · `OD-10.a` · `OD-10.b`.

    VISIBILIDAD DE TRASPASO   ≠   ACCESO A LA UNIDAD AJENA

Participar en un traspaso da lo que el traspaso necesita y nada más. Lo que este módulo
gobierna es **quién puede crear uno y hacia dónde**; qué campos cruzan lo gobiernan las
proyecciones de lectura, que ya eran acotadas.

Tres reglas, y las tres salieron de escribir las pruebas:

    EL ORIGEN ES DEL DESPACHANTE      despachar es operar sobre el lote origen, y exige
                                      tenerlo al alcance. Sin esto se podía salir de un lote
                                      de otra cadena por la puerta del contrato.

    EL DESTINO SE DECLARA             `OD-10.b`. Sin destino, la unidad receptora no puede
                                      saber que un despacho es para ella antes de recibirlo,
                                      y enseñarle todos los pendientes de la empresa
                                      anularía el aislamiento justo donde se protegía.

    EL DESTINO NO EXIGE SU CADENA     y eso es lo que hace que sea un **contrato** y no un
                                      permiso: se dirige a una incubadora sin tenerla
                                      concedida, y no se obtiene acceso a ella.
"""
from __future__ import annotations

from typing import Iterable

#: Qué cadenas pueden ser origen y destino de cada traspaso, según los siete flujos de
#: `audit/remediation/CROSS_MODULE_FLOW_MATRIX.md`. No se inventa ninguna combinación: el
#: huevo fértil va de reproducción a incubación, y el pollito de incubación a cría o engorde.
#:
#: Aceptar un destino fuera de esta tabla escribiría una cadena que `P-10` no puede
#: reconstruir — y la trazabilidad generacional está certificada sobre ella.
FLUJOS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    #                        origen permitido                destino permitido
    "egg_batch": (("grandparent", "breeder"), ("hatchery",)),
    "chick_batch": (("hatchery",), ("breeder", "broiler")),
}


class DestinoInvalido(ValueError):
    """El destino no es válido para este traspaso."""


def _codigo(lote) -> str | None:
    tipo = getattr(lote, "bird_type", None)
    return getattr(tipo, "value", tipo)


def validar_flujo(flujo: str, *, origen, destino) -> None:
    """Comprueba que las dos cadenas son las que el flujo admite.

    Un lote **sin cadena declarada** no sirve como ninguno de los dos lados: no se puede
    afirmar que el traspaso sea válido, y afirmarlo sin saberlo es peor que negarlo.
    `OD-10.c` manda esos lotes a «pendiente de clasificar», que es la fase 6.
    """
    permitidos_origen, permitidos_destino = FLUJOS[flujo]
    o, d = _codigo(origen), _codigo(destino)

    if o not in permitidos_origen:
        raise DestinoInvalido(
            f"el lote origen es de {o!r} y este traspaso sale de "
            f"{' o '.join(permitidos_origen)}")
    if d not in permitidos_destino:
        raise DestinoInvalido(
            f"el lote destino es de {d!r} y este traspaso llega a "
            f"{' o '.join(permitidos_destino)}")


def unidades_del_flujo(flujo: str) -> Iterable[str]:
    """Las cadenas que intervienen. Para la matriz de contrato y la evidencia."""
    origen, destino = FLUJOS[flujo]
    return (*origen, *destino)

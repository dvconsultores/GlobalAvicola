"""La excepción del contrato SAP, declarada — `GA-REM-040` flujo 5 · `OD-12` · `BU-D04`.

**Este módulo no filtra nada, y ésa es exactamente su función.**

Las superficies de SAP **no** se acotan por cadena productiva. Eso es correcto: la
consolidación agrupa el movimiento de las cuatro por definición, y filtrarla la rompería. Pero
hasta `OD-12` esa transversalidad existía **por ausencia** —nadie había puesto el filtro— y

    una excepción que solo existe porque nadie puso el filtro
    es indistinguible de un fallo.

Lo que este módulo aporta es la declaración: dice **cuáles** son esas superficies, **por qué** no
se acotan y **qué** las autoriza. Y una prueba comprueba que la lista declarada coincide con las
rutas reales, de modo que una ruta SAP nueva no se une a la excepción en silencio: quien la añada
tiene que decir que la quiere dentro.

Las cinco condiciones de `OD-12.b` siguen viviendo donde les corresponde, y no se duplican aquí:

    la capacidad explícita      `require_permission("sap", …)` en cada ruta
    la empresa efectiva         `app/tenancy.py`, resuelto en la petición
    el recurso de esa empresa   `SapService._company_filter`, incluidos los accesos por id
    la elegibilidad de negocio  las reglas del propio proceso SAP
    la proyección               los esquemas de lectura, que ya son acotados

Repetirlas aquí sería una comprobación redundante que se desincronizaría con la real. Lo que
faltaba era decir que su conjunto **es** la excepción, no un descuido.

**No existe, y no debe existir, una función genérica de salto de alcance.** Si la hubiera,
acabaría llamándose desde donde nadie la previó. La excepción es de SAP y solo de SAP.
"""
from __future__ import annotations

#: Los permisos que autorizan a operar el contrato. Ya estaban en el catálogo antes de esta
#: decisión: `OD-12 §7` la resolvió con `REUSE`, sin crear ninguno.
CAPACIDADES_SAP: tuple[tuple[str, str], ...] = (
    ("sap", "read"),
    ("sap", "send_sap"),
)

#: Las superficies que operan el contrato y por tanto **atraviesan las cuatro cadenas**.
#:
#: Es la lista de la excepción. Todo lo que esté aquí cruza; todo lo que no, no. Las rutas de
#: configuración de la integración —referencias, diagnóstico— no cruzan nada: no tocan filas de
#: producción, y por eso están clasificadas como plano de control y quedan fuera.
SUPERFICIES_TRANSVERSALES: frozenset[str] = frozenset({
    "/api/v1/sap/consolidate",
    "/api/v1/sap/consolidated",
    "/api/v1/sap/export",
    "/api/v1/sap/payloads",
    "/api/v1/sap/errors",
    "/api/v1/sap/retry",
    "/api/v1/sap/sync/jobs",
})


def es_superficie_transversal(camino: str) -> bool:
    """¿Esta ruta opera el contrato SAP y por tanto cruza cadenas legítimamente?"""
    return camino in SUPERFICIES_TRANSVERSALES

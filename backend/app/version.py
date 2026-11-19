"""Procedencia del build — `SPEC 016 §B`.

`GET /api/v1/version` responde qué artefacto está sirviendo la petición: el `SHA` del commit
con el que se construyó la imagen, cuándo se construyó y en qué entorno corre.

Dos decisiones que la ruta hace explícitas:

**No se le pregunta al repositorio.** La imagen no contiene `.git`, así que inspeccionar el
árbol en tiempo de petición no informaría de lo construido sino de lo que hubiera en el disco
—o de nada—. El `SHA` entra por `build-arg` y se congela en el entorno del contenedor
(`app/config.py`, `GA_GIT_SHA`); aquí solo se lee la configuración.

**Se lee en cada petición, no al importar el módulo**, para que la configuración efectiva sea
la vigente y no una copia tomada al arrancar.

Es pública y de solo lectura: publica tres cadenas que no son datos de negocio. Un operador
que diagnostica un incidente necesita saber qué versión está desplegada antes de tener sesión
—justamente cuando sospecha que el problema es el despliegue.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from .config import settings

router = APIRouter()


class BuildProvenance(BaseModel):
    """Lo único que viaja en la respuesta. Nada se deduce ni se arrastra de `Settings`."""

    git_sha: str
    build_time: str
    environment: str


@router.get("/version", tags=["Health"], response_model=BuildProvenance)
async def version() -> BuildProvenance:
    return BuildProvenance(
        git_sha=settings.GA_GIT_SHA,
        build_time=settings.GA_BUILD_TIME,
        environment=settings.ENVIRONMENT,
    )

"""Los contratos de respuesta de la administración — `GA-REM-040` fase 7 · `AC-F03`.

**Proyecciones declaradas, nunca la entidad.** `R-112` demostró en la fase 5 lo que cuesta
saltarse esto: una ruta devolvía objetos `ORM` crudos y la proyección que la fase daba por
aplicada existía en el fichero sin aplicarse. No filtraba nada por coincidencia —el modelo no
tenía relaciones—, no por contrato.

Aquí importa más que allí. Estas rutas administran **quién accede a qué**, y sus entidades
cuelgan de `users` y de `companies`: devolver la fila entera arrastraría credenciales,
metadatos de sesión y datos de otro inquilino. Por eso ninguna de ellas se serializa sola.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HabilitacionRead(BaseModel):
    """Una unidad del catálogo y **el estado que tiene en la empresa efectiva**.

    Sin `id` de la habilitación a propósito. Quien administra no necesita el identificador de
    la fila: las rutas direccionan por código dentro de su empresa, y no exponerlo evita que
    exista siquiera la tentación de aceptarlo como entrada — que es por donde se cuela una
    habilitación de otro inquilino.
    """

    code: str
    name_key: str
    is_enabled: bool


class ConcesionRead(BaseModel):
    """Una concesión de un usuario, con la diferencia entre **otorgada** y **efectiva**.

    Las dos cosas no coinciden, y confundirlas es el error que esta capacidad existe para
    impedir: una concesión viva sobre una unidad que la empresa ha deshabilitado **está
    otorgada y no es efectiva** (`AC-A05`). Una pantalla que solo mostrara «tiene incubadora»
    mentiría, y quien administra decidiría a ciegas.
    """

    user_id: int
    code: str
    #: Bajo qué empresa se otorgó. `OD-09.d`: la concesión pertenece a usuario + empresa +
    #: unidad, y la fila lo dice sin que haya que mirar dónde está hoy el usuario.
    company_id: int
    granted_at: datetime
    #: Cuándo dejó de valer. `None` es una concesión viva.
    revoked_at: datetime | None = None
    #: Viva **y** con la unidad habilitada **y** activa en el producto.
    is_effective: bool


class ConcesionCreate(BaseModel):
    """Qué unidad se concede. El usuario va en el camino; la empresa **no se acepta**.

    Que la empresa no sea un campo es la decisión de diseño que cierra `AC-B10` en esta
    superficie: no se rechaza una empresa ajena, es que no hay forma de nombrarla. Lo que no
    se puede expresar no hay que acordarse de validarlo.
    """

    code: str = Field(min_length=1, max_length=30)


class CandidatoRead(BaseModel):
    """Un usuario al que se le puede conceder una unidad — enmienda F · `AC-H15` · `R-129`.

    **Lo mínimo para elegir a una persona, y nada de administrarla.** Ni correo, ni teléfono,
    ni rol, ni permisos: el `Administrador de Accesos` no tiene `users:read`, y esta
    proyección existe justamente para que no lo necesite. Cada campo de más sería un pedazo
    de `users:read` con otro nombre.
    """

    user_id: int
    username: str
    #: Nombre y apellido, para reconocer a la persona en un desplegable.
    display_name: str
    #: Si ya tiene esa unidad concedida y viva. Se incluye marcado, no se oculta: ocultarlo
    #: haría indistinguible «nunca se le dio» de «ya la tiene» — la misma confusión que
    #: `AC-H11` separa entre concedidas y efectivas.
    already_granted: bool

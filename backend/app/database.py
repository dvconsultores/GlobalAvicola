from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db(request: Request) -> AsyncSession:
    """Sesión de la petición. **No confirma**: eso es de la capa de ruta.

    `GA-REM-026` / `R-68`. Confirmar aquí, tras el `yield`, ocurría después de que la
    respuesta hubiera salido, de modo que un cliente que leyera de inmediato podía no ver
    lo que acababa de crear. La sesión se publica en `request.state` para que
    `RutaTransaccional` la confirme mientras la respuesta todavía no ha salido.

    La reversión sí se queda aquí: las excepciones se propagan al generador y esta rama ya
    era correcta para errores de dominio, `HTTPException` y fallos inesperados.
    """
    async with async_session() as session:
        request.state.db = session
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

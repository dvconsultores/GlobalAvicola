import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .operations.validators import BusinessRuleViolation

# S-05: Rate limiting — always instantiated, but limits are
# effectively disabled when FEATURE_RATE_LIMIT_ENABLED=false
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_GLOBAL])


def resolve_rate_limit_active(cfg, *, en_contenedor=None, test_env=None) -> bool:
    """G-03/T13: el limitador es obligatorio en el artefacto desplegado.

    El contenedor desplegado puede heredar del servidor un `.env` desactualizado
    (p. ej. `FEATURE_RATE_LIMIT_ENABLED=false` y `ENVIRONMENT=development`) que la
    recreación del contenedor clona. Una protección anti fuerza bruta no debe
    depender de esa herencia. Capas, de mayor a menor precedencia:

    1. `GA_TEST_ENV=1` (guardas de suites locales): manda el flag explícito.
    2. Proceso dentro de un contenedor (`/.dockerenv`): SIEMPRE activo.
    3. Fuera de contenedor: `development`/`test` respetan el flag; el resto ON.
    """
    if test_env is None:
        test_env = os.environ.get("GA_TEST_ENV") == "1"
    if en_contenedor is None:
        en_contenedor = os.path.exists("/.dockerenv")
    if test_env:
        return bool(cfg.FEATURE_RATE_LIMIT_ENABLED)
    if en_contenedor:
        return True
    if cfg.ENVIRONMENT in ("development", "test"):
        return bool(cfg.FEATURE_RATE_LIMIT_ENABLED)
    return True


_limiter_active = resolve_rate_limit_active(settings)


def rate_limit(limit_value: str):
    """Conditional rate limit decorator.
    
    When FEATURE_RATE_LIMIT_ENABLED is false, this is a no-op passthrough.
    When true, applies the slowapi rate limit.
    """
    if _limiter_active:
        return limiter.limit(limit_value)
    else:
        # No-op decorator: just returns the function unchanged
        def noop_decorator(func):
            return func
        return noop_decorator


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    # Register SQLAlchemy audit listeners on startup
    from .audit import register_audit_listeners
    register_audit_listeners()

    # Se desactiva en las pruebas: la suite llama al evaluador directamente para que el
    # resultado sea determinista, y una tarea de fondo compitiendo con ella lo haría
    # depender del reloj.
    from .notifications.sla import vigilar_revisiones_pendientes

    vigilante = None
    if settings.NOTIFICATION_SLA_SCAN_ENABLED and os.environ.get("GA_TEST_ENV") != "1":
        vigilante = asyncio.create_task(vigilar_revisiones_pendientes(
            settings.NOTIFICATION_SLA_SCAN_SECONDS))

    yield

    if vigilante is not None:
        vigilante.cancel()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API REST para la gestión operativa avícola integrada con SAP",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# S-05: Rate limiting handler (only active when feature flag is on)
app.state.limiter = limiter
if _limiter_active:
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# R-26: contrato de error de las reglas de negocio.
#
# `BusinessRuleViolation` señala que la petición es válida pero el dominio la rechaza:
# eso es un 400, no un 500. Hasta ahora solo se convertía en las cinco reglas que caían
# dentro de un `try/except` local de `OperationsService._apply_business_rules`; las otras
# ocho —BR-06, BR-07, BR-08, BR-10, BR-15, BR-17, BR-19 y G-R05— escapaban sin manejar y
# el operador que olvidaba la granja veía «Internal Server Error» en lugar del motivo.
#
# Un manejador tipado y único da un contrato consistente a las 23 reglas y a cualquiera
# que se añada después. Deliberadamente NO se captura `Exception`: un fallo inesperado
# debe seguir siendo un 500, porque esconderlo tras un 400 es peor que el defecto que se
# está corrigiendo.
@app.exception_handler(BusinessRuleViolation)
async def _business_rule_violation_handler(request: Request, exc: BusinessRuleViolation):
    """Traduce una violación de regla de negocio a `400` citando la regla.

    `detail` se mantiene como cadena por compatibilidad con los clientes existentes;
    `rule` se añade para que la interfaz pueda identificar la regla sin analizar el texto.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message, "rule": exc.rule_id or None},
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# S-06: Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT, "version": "0.1.0"}


# Routers will be registered here as modules are built
from .auth.router import router as auth_router
from .masters.router import router as masters_router
from .notifications.router import router as notifications_router
from .lots.router import router as lots_router
from .operations.router import router as ops_router
from .review.router import router as review_router, approval_router, steps_router
from .corrections.router import router as corrections_router
from .audit.router import router as audit_router
from .reports.router import router as reports_router
from .dashboard.router import router as dashboard_router
from .business_units.router import router as business_units_router

# SAP Integration: solo se carga si el feature flag está activo
if settings.FEATURE_SAP_ENABLED:
    from .integrations.sap.router import router as sap_router

app.include_router(auth_router, prefix="/api/v1", tags=["Auth & Users"])
app.include_router(masters_router, prefix="/api/v1", tags=["Masters"])
app.include_router(notifications_router, prefix="/api/v1", tags=["Notifications"])
app.include_router(lots_router, prefix="/api/v1", tags=["Lots"])
app.include_router(ops_router, prefix="/api/v1", tags=["Operations"])
app.include_router(review_router, prefix="/api/v1", tags=["Review"])
app.include_router(approval_router, prefix="/api/v1", tags=["Approvals"])
app.include_router(steps_router, prefix="/api/v1", tags=["Approval Steps"])
app.include_router(corrections_router, prefix="/api/v1", tags=["Corrections"])
from .reversals.router import router as reversals_router  # noqa: E402
app.include_router(reversals_router, prefix="/api/v1", tags=["Reversals"])
from .cutover.router import router as cutover_router  # noqa: E402
from .cutover.opening_corrections import router as opening_corrections_router  # noqa: E402
from .cutover.templates import router as cutover_templates_router  # noqa: E402

app.include_router(cutover_router, prefix="/api/v1", tags=["Cutover"])
app.include_router(opening_corrections_router, prefix="/api/v1", tags=["Cutover"])
app.include_router(cutover_templates_router, prefix="/api/v1", tags=["Cutover"])
app.include_router(audit_router, prefix="/api/v1", tags=["Audit"])
app.include_router(reports_router, prefix="/api/v1", tags=["Reports"])
app.include_router(dashboard_router, prefix="/api/v1", tags=["Dashboard"])
# `GA-REM-040` fase 7. El plano de control de las unidades de negocio: administrar el
# acceso, que no es acceder (`OD-09.b`).
app.include_router(business_units_router, prefix="/api/v1", tags=["Business Units"])

if settings.FEATURE_SAP_ENABLED:
    app.include_router(sap_router, prefix="/api/v1", tags=["SAP Integration"])


# GA-REM-002 AC08: ninguna ruta puede quedarse sin decisión de autorización. Se comprueba
# al importar la aplicación, de modo que un olvido rompe el arranque en lugar de abrir un
# agujero silencioso.
from .authorization_coverage import verificar as _verificar_autorizacion  # noqa: E402

_verificar_autorizacion(app)

# GA-REM-026 AC11: ninguna ruta puede usar la base fuera de la frontera transaccional. Un
# router que olvide `route_class=RutaTransaccional` perdería sus escrituras en silencio;
# esto lo convierte en un fallo de arranque.
from .transaction import verificar as _verificar_transaccion  # noqa: E402

_verificar_transaccion(app)

# GA-REM-040 AC-C15: ninguna ruta puede quedarse sin declarar su relación con la unidad de
# negocio. Es la misma idea que AC08 y por la misma razón: sin la comprobación, cada ruta
# nueva olvidaría la clasificación y la capa se degradaría sola. Clasificar no protege las
# filas —eso es la fase 3—, pero sin clasificar no se sabe siquiera qué hay que proteger.
from .business_units.route_scope import verificar as _verificar_alcance_unidad  # noqa: E402

_verificar_alcance_unidad(app)

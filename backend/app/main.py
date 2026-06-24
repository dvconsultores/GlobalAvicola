from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings

# S-05: Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_GLOBAL])


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API REST para la gestión operativa avícola integrada con SAP",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# S-05: Rate limiting handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
from .lots.router import router as lots_router
from .operations.router import router as ops_router
from .review.router import router as review_router, approval_router, steps_router
from .corrections.router import router as corrections_router
from .integrations.sap.router import router as sap_router
from .audit.router import router as audit_router
from .reports.router import router as reports_router
from .dashboard.router import router as dashboard_router

app.include_router(auth_router, prefix="/api/v1", tags=["Auth & Users"])
app.include_router(masters_router, prefix="/api/v1", tags=["Masters"])
app.include_router(lots_router, prefix="/api/v1", tags=["Lots"])
app.include_router(ops_router, prefix="/api/v1", tags=["Operations"])
app.include_router(review_router, prefix="/api/v1", tags=["Review"])
app.include_router(approval_router, prefix="/api/v1", tags=["Approvals"])
app.include_router(steps_router, prefix="/api/v1", tags=["Approval Steps"])
app.include_router(corrections_router, prefix="/api/v1", tags=["Corrections"])
app.include_router(sap_router, prefix="/api/v1", tags=["SAP Integration"])
app.include_router(audit_router, prefix="/api/v1", tags=["Audit"])
app.include_router(reports_router, prefix="/api/v1", tags=["Reports"])
app.include_router(dashboard_router, prefix="/api/v1", tags=["Dashboard"])

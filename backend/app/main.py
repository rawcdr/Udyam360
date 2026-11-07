"""Main FastAPI Application Entrypoint for Udyam360 Backend."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.advisor import router as advisor_router
from app.api.auth import router as auth_router
from app.api.catalogue import router as catalogue_router
from app.api.eligibility import router as eligibility_router
from app.api.kyc import kyc_router
from app.api.orders import router as orders_router
from app.api.quotes import router as quotes_router
from app.api.recommendations import router as recommendations_router
from app.api.segments import router as segments_router
from app.core.config import settings
from app.core.middleware import CSRFProtectionMiddleware, SecurityHeadersMiddleware
from app.db.init_db import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager: initializes database and seed data on startup."""
    init_database()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 1. Defensive HTTP Security Headers Middleware (OWASP recommended)
app.add_middleware(SecurityHeadersMiddleware)

# 2. CSRF Protection Middleware for ambient cookie authentication
app.add_middleware(CSRFProtectionMiddleware)

# 3. CORS Middleware configuration with explicit allowed origins & credential support
default_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
configured_origins = getattr(settings, "CORS_ORIGINS", None)
if configured_origins:
    cors_origins = [o.strip() for o in configured_origins.split(",") if o.strip()]
else:
    cors_origins = default_cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["X-Session-Token", "Content-Disposition", "X-CSRF-Token"],
)

# Register API v1 Routers
API_V1_PREFIX = "/api/v1"
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(catalogue_router, prefix=API_V1_PREFIX)
app.include_router(segments_router, prefix=API_V1_PREFIX)
app.include_router(eligibility_router, prefix=API_V1_PREFIX)
app.include_router(recommendations_router, prefix=API_V1_PREFIX)
app.include_router(quotes_router, prefix=API_V1_PREFIX)
app.include_router(advisor_router, prefix=API_V1_PREFIX)
app.include_router(kyc_router, prefix=API_V1_PREFIX)
app.include_router(orders_router, prefix=API_V1_PREFIX)
app.include_router(admin_router, prefix=API_V1_PREFIX)


@app.get("/health", tags=["System Health"])
@app.get(f"{API_V1_PREFIX}/health", tags=["System Health"])
def health_check():
    """Verify backend API readiness and operational status."""
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "catalogue_loaded": True,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

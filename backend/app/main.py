"""Main FastAPI Application Entrypoint for Udyam360 Backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.catalogue import router as catalogue_router
from app.api.segments import router as segments_router
from app.api.eligibility import router as eligibility_router
from app.api.recommendations import router as recommendations_router
from app.api.quotes import router as quotes_router
from app.api.advisor import router as advisor_router
from app.api.kyc import kyc_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 Routers
API_V1_PREFIX = "/api/v1"
app.include_router(catalogue_router, prefix=API_V1_PREFIX)
app.include_router(segments_router, prefix=API_V1_PREFIX)
app.include_router(eligibility_router, prefix=API_V1_PREFIX)
app.include_router(recommendations_router, prefix=API_V1_PREFIX)
app.include_router(quotes_router, prefix=API_V1_PREFIX)
app.include_router(advisor_router, prefix=API_V1_PREFIX)
app.include_router(kyc_router, prefix=API_V1_PREFIX)


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


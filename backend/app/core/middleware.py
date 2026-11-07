"""Security and CSRF protection middlewares for Udyam360."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces modern defensive HTTP security headers on all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Standard OWASP defensive headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        # Defensive Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 http://localhost:5173 http://127.0.0.1:5173; "
            "frame-ancestors 'none';"
        )

        # Sensitive paths must prevent downstream browser / proxy caching
        path = request.url.path.lower()
        if any(seg in path for seg in ["/auth", "/kyc", "/admin"]):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        return response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Protects against Cross-Site Request Forgery (CSRF) on cookie-authenticated mutations."""

    EXEMPT_PATHS = {
        "/api/v1/auth/otp/request",
        "/api/v1/auth/otp/verify",
        "/api/v1/auth/admin/login",
        "/api/v1/auth/csrf",
        "/health",
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only check state-changing methods
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            path = request.url.path

            # Skip explicitly exempt authentication endpoints
            if path not in self.EXEMPT_PATHS:
                has_cookie_session = (
                    "udyam360_session" in request.cookies or "udyam360_admin_session" in request.cookies
                )
                
                # CSRF protection applies when requests rely on ambient cookie credentials
                if has_cookie_session:
                    csrf_cookie = request.cookies.get("udyam360_csrf")
                    csrf_header = request.headers.get("X-CSRF-Token")

                    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                        return JSONResponse(
                            status_code=403,
                            content={
                                "detail": "CSRF verification failed: Missing or invalid CSRF token.",
                                "code": "CSRF_FAILED",
                            },
                        )

        return await call_next(request)


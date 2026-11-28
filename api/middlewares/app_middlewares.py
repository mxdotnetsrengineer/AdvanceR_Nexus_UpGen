import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from services.config_service import ConfigService



def register_middlewares(app: FastAPI, global_config: ConfigService | None = None) -> None:
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
    
    raw_origins = (global_config.get("CORS_ALLOWED_ORIGINS") if global_config is not None else ["http://localhost:3000"])
    allowed_origins = (
        [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
        if isinstance(raw_origins, str)
        else list(raw_origins)
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
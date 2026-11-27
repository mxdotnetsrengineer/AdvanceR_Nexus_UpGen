from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import redis.asyncio as redis
from enums.app_enums import AvailableLanguages
from enums.gba.games_enum import AvailableGames
from services.log_service import LogService
from services.error_service import ErrorService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from exceptions.exception_handlers import register_exception_handlers
from api.middlewares.app_middlewares import register_middlewares 
from api.routers.items_router import get_items_facade, router as items_router
from api.routers.config_router import get_config_facade, router as config_router
from facades.items_facade import ItemsFacade
from facades.config_facade import ConfigFacade

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle for shared async resources."""
    global_config: ConfigService = app.state.global_config
    translations_service: TranslationsService = app.state.translations_service
    error_service: ErrorService = app.state.error_service

    # --- STARTUP ---
    # Preload locales into shared cache
    translations_service.preload_locales([lang.name for lang in AvailableLanguages])

    # Initialize shared async Redis connection pool (optional/ready for endpoints)
    redis_client = redis.Redis(
        host=global_config.get("REDIS_HOST", "127.0.0.1"),
        port=int(global_config.get("REDIS_PORT", 6379)),
        db=int(global_config.get("REDIS_DB", 0)),
        decode_responses=True,
    )
    app.state.redis = redis_client

    items_facade = ItemsFacade(
        global_config=global_config,
        error_service=error_service,
        default_game=AvailableGames.ORIGINAL_FIRE_RED,
        redis_client=redis_client,
    )
    app.dependency_overrides[get_items_facade] = lambda: items_facade

    yield

    # Cleanly close async Redis connections on server exit
    if getattr(app.state, "redis", None) is not None:
        await app.state.redis.aclose()

def create_app() -> FastAPI:
    """Build and configure the FastAPI application with injected domain facades."""
    global_config = ConfigService.load_global()
    translations_service = TranslationsService(global_config.get("CURRENT_LANGUAGE", "EN_US"))
    log_service = LogService(translations_service, global_config.get("LOG_TYPE"), keep_history=False)
    error_service = ErrorService(log_service, translations_service)

    internal_error_msg = translations_service.translate(
        "errors.internal_server_error",
        default="An unexpected internal server error occurred.",
    )

    is_prod = str(global_config.get("APP_ENV")).lower() == "prod"

    app = FastAPI(
        title="AdvanceR Nexus UpGen API",
        version="1.0.0",
        description="REST API for GBA Pokémon ROM inspection and randomization.",
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
        lifespan=lifespan
    )

    app.state.global_config = global_config
    app.state.translations_service = translations_service
    app.state.error_service = error_service

    register_exception_handlers(app, internal_error_message=internal_error_msg)
    register_middlewares(app)

    config_facade = ConfigFacade(
        config_service=global_config,
        translations_service=translations_service,
    )

    # Redis Fallback , for tests when lifespan is not executed
    default_items_facade = ItemsFacade(
        global_config=global_config,
        error_service=error_service,
        default_game=AvailableGames.ORIGINAL_FIRE_RED,
    )

    app.dependency_overrides[get_config_facade] = lambda: config_facade
    app.dependency_overrides[get_items_facade] = lambda: default_items_facade

    app.include_router(items_router)
    app.include_router(config_router)

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")
    
    #TODO: app.openapi = custom_openapi

    return app

app = create_app()

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.openapi.utils import get_openapi
from enums.gba.games_enum import AvailableGames
from api.exceptions.exception_handlers import register_exception_handlers
from api.routers.items_router import get_items_facade, router as items_router
from api.routers.config_router import get_config_facade, router as config_router
from services.log_service import LogService
from services.error_service import ErrorService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from api.middlewares.app_middlewares import register_middlewares 
from facades.items_facade import ItemsFacade
from facades.config_facade import ConfigFacade


def create_app() -> FastAPI:
    """Build and configure the FastAPI application with injected domain facades."""
    app = FastAPI(
        title="AdvanceR Nexus UpGen API",
        version="1.0.0",
        description="REST API for GBA Pokémon ROM inspection and randomization.",
    )

    register_middlewares(app)

    global_config = ConfigService.load_global()
    translations_service = TranslationsService(global_config.get("CURRENT_LANGUAGE", "EN_US"))
    log_service = LogService(translations_service, global_config.get("LOG_TYPE"))
    error_service = ErrorService(log_service, translations_service)

    internal_error_msg = translations_service.translate(
        "errors.internal_server_error",
        default="An unexpected internal server error occurred.",
    )

    register_exception_handlers(app, internal_error_message=internal_error_msg)

    config_facade = ConfigFacade(
        config_service=global_config,
        translations_service=translations_service,
    )
    items_facade = ItemsFacade(
        global_config=global_config,
        error_service=error_service,
    )

    app.dependency_overrides[get_config_facade] = lambda: config_facade
    app.dependency_overrides[get_items_facade] = lambda: items_facade

    app.include_router(items_router)
    app.include_router(config_router)

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")
        
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    #app.openapi = custom_openapi

    return app

def replace_references(node,target_ref,compiled_schema):
    if isinstance(node, dict):
        if node.get("$ref") == target_ref:
            node.clear()
            node.update(compiled_schema)
        else:
            for value in node.values():
                replace_references(value,target_ref,compiled_schema)
    elif isinstance(node, list):
        for item in node:
            replace_references(item, target_ref, compiled_schema)

app = create_app()
import sys
import subprocess
import asyncio
import uvicorn
import threading
import webbrowser
import redis.asyncio as redis
from enums.app_enums import AvailableLanguages
from tools.menu import ConsoleMenu
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from grpc_files.grpc_server import run_grpc, test_grpc
from examples.grpc.items import execute_get_all_items
from games.core.games_provider import GamesProvider

def run_fastapi(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start the FastAPI REST server using Uvicorn and open the default browser."""
    url = f"http://{host}:{port}/"
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    uvicorn.run("api.app:app", host=host, port=port, reload=False)

def run_tests(action: str) -> None:
    """Execute the selected Pytest suite directly from the CLI."""
    args_map: dict[str, list[str]] = {
        "pytest_all": [],
        "pytest_unit": ["tests/unit"],
        "pytest_integration": ["tests/integration"],
        "pytest_cov": ["--cov"],
    }
    cmd = [sys.executable, "-m", "pytest", *args_map.get(action, [])]
    subprocess.run(cmd, check=False)

def run_randomizer(game_instance, redis_client: redis.Redis) -> None:
    asyncio.run(_run_randomizer_async(game_instance, redis_client))

async def _run_randomizer_async(game_instance, redis_client: redis.Redis) -> None:
    try:
        await game_instance.process_game()
    finally:
        await redis_client.aclose()

def _create_redis_client(config_service: ConfigService) -> redis.Redis:
    """Instantiate an async Redis client using global configuration settings."""
    return redis.Redis(
        host=config_service.get("REDIS_HOST", "127.0.0.1"),
        port=config_service.get("REDIS_PORT", 6379),
        db=config_service.get("REDIS_DB", 0),
        decode_responses=True,
    )
        
if __name__ == "__main__":
    global_config = ConfigService.load_global()
    raw_lang = global_config.get("CURRENT_LANGUAGE")
    default_lang = AvailableLanguages[raw_lang] if raw_lang in AvailableLanguages.__members__ else AvailableLanguages.EN_US
    
    translator = TranslationsService(default_lang.name)
    menu = ConsoleMenu(translator,default_lang)
    selection = menu.run()

    if selection is None:
        sys.exit(0)

    if selection.action == "randomizer" and selection.game:
        redis_client = _create_redis_client(global_config)
        game_instance = GamesProvider.create(
            game=selection.game,
            language=selection.language,
            redis_client=redis_client,
        )
        run_randomizer(game_instance, redis_client)

    elif selection.action == "grpc_server" and selection.game:
        global_config.set("CURRENT_LANGUAGE", selection.language.name)
        run_grpc(global_config, default_game=selection.game)

    elif selection.action == "fastapi_server":
        run_fastapi()

    elif selection.action.startswith("pytest_"):
        run_tests(selection.action)

    elif selection.action == "grpc_test_loaded":
        test_grpc(
            global_config,
            rpc_handler= execute_get_all_items,
            selected_game=None,
        )

    elif selection.action == "grpc_test_replace" and selection.game:
        test_grpc(
            global_config,
            rpc_handler= execute_get_all_items,
            selected_game=selection.game,
        )

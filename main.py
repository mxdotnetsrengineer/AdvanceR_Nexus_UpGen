import asyncio
import grpc
import redis.asyncio as redis
import os
from pathlib import Path

from enums.gba.games_enum import AvailableGames
from enums.app_enums import AvailableLanguages
from helpers.gba.pokemon.gba_pokemon_helper import GAMES
from tools.menu import ConsoleMenu
from facades.items_facade import ItemsFacade
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from games.core.games_provider import GamesProvider

from grpc_files.generated import items_pb2_grpc, items_pb2
from grpc_files.servicers.items_servicer import ItemsGrpcServicer

MAX_MESSAGE_LENGTH = 48 * 1024 * 1024  # 48MB
BASE_DIR = Path(__file__).resolve().parent

def _create_redis_client(config_service: ConfigService) -> redis.Redis:
    """Instantiate an async Redis client using global configuration settings."""
    return redis.Redis(
        host=config_service.get("REDIS_HOST", "127.0.0.1"),
        port=config_service.get("REDIS_PORT", 6379),
        db=config_service.get("REDIS_DB", 0),
        decode_responses=True,
    )

def _resolve_ssl_path(config_service: ConfigService, config_key: str, default_rel: str) -> Path:
    """Resolve SSL file path from environment variable or config relative to project root."""
    raw_path = os.getenv(config_key) or config_service.get(config_key, default_rel)
    path = Path(raw_path)
    return path if path.is_absolute() else BASE_DIR / path

async def _build_grpc_server(game_instance, port: int = 50051) -> grpc.Server:
    """Configure and serve the async secure gRPC server instance."""
    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", MAX_MESSAGE_LENGTH),
            ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
        ],
    )

    items_facade = ItemsFacade(game_instance.items_service)
    items_pb2_grpc.add_ItemsServiceServicer_to_server(
        ItemsGrpcServicer(items_facade), server
    )

    key_path = _resolve_ssl_path(game_instance.config_service, "GRPC_KEY_PATH", "grpc_files/server.key")
    cert_path = _resolve_ssl_path(game_instance.config_service, "GRPC_CERT_PATH", "grpc_files/server.crt")

    private_key = key_path.read_bytes()
    certificate_chain = cert_path.read_bytes()

    server_credentials = grpc.ssl_server_credentials(
        [(private_key, certificate_chain)]
    )
    server.add_secure_port(f"[::]:{port}", server_credentials)

    await server.start()
    print(f"\nAsync Secure gRPC Server listening on port {port}...")
    await server.wait_for_termination()



def run_randomizer(game_instance) -> None:
    asyncio.run(game_instance.process_game())


def run_grpc(game_instance, port: int = 50051) -> None:
    asyncio.run(_build_grpc_server(game_instance, port))


def test_grpc(
        config_service: ConfigService,
    selected_game: AvailableGames | None = None,
    host: str = "localhost",
    port: int = 50051,
) -> None:
    """Connect to the running gRPC server and test GetAllItems with or without sending a game."""
    target = f"{host}:{port}"
    send_game = selected_game is not None
    mode_label = f"WITH Custom Game ({selected_game.name})" if send_game else "Server Selected Game"
    print(f"\n[TEST - {mode_label}] Connecting to gRPC server at {target}...")

    cert_path = _resolve_ssl_path(config_service, "GRPC_CERT_PATH", "grpc_files/server.crt")
    trusted_certs = cert_path.read_bytes()

    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)

    with grpc.secure_channel(
        target,
        credentials,
        options=[
            ("grpc.max_send_message_length", MAX_MESSAGE_LENGTH),
            ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
        ],
    ) as channel:
        stub = items_pb2_grpc.ItemsServiceStub(channel)

        if send_game:
            game_config = ConfigService.load_for_game(GAMES[int(selected_game.value)])
            raw_game_path = Path(game_config.get("ORIGINAL_GAME"))
            game_path = raw_game_path if raw_game_path.is_absolute() else BASE_DIR / raw_game_path
            game_bytes = game_path.read_bytes()

            request = items_pb2.GetAllItemsRequest(
                game_file=game_bytes,
                game_id=int(selected_game.value),
            )
        else:
            request = items_pb2.GetAllItemsRequest()

        response = stub.GetAllItems(request)

    print(f"\n[TEST] ✅ Total items received via gRPC: {len(response.items)}")
    print("=" * 80)
    for item_id in sorted(response.items.keys()):
        item = response.items[item_id]
        print(
            f"#{item.id:03d} | {item.name:<15} | "
            f"Pocket: {item.pocket:<10} ({item.pocket_id}) | "
            f"Type: {item.item_type:<20} (0x{item.item_type_id:02X}) | Price: ${item.price:5d}"
        )
    print("=" * 80)

if __name__ == "__main__":
    global_config = ConfigService.load_global()
    raw_lang = global_config.get("CURRENT_LANGUAGE")
    default_lang = AvailableLanguages[raw_lang] if raw_lang in AvailableLanguages.__members__ else AvailableLanguages.EN_US
    
    translator = TranslationsService(default_lang.name)
    menu = ConsoleMenu(translator,default_lang)
    selection = menu.run()

    if selection is None:
        exit(0)

    if selection.action == "randomizer" and selection.game:
        redis_client = _create_redis_client(global_config)
        game_instance = GamesProvider.create(
            game=selection.game,
            language=selection.language,
            redis_client=redis_client,
        )
        run_randomizer(game_instance)

    elif selection.action == "grpc_server" and selection.game:
        game_instance = GamesProvider.create(
            game=selection.game,
            language=selection.language,
        )
        run_grpc(game_instance)
        
    elif selection.action == "grpc_test_loaded":
        test_grpc(global_config,selected_game=None)

    elif selection.action == "grpc_test_replace" and selection.game:
        test_grpc(global_config,selected_game=selection.game)
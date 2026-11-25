import asyncio
import os
from collections.abc import Callable
from pathlib import Path
import grpc

from enums.gba.games_enum import AvailableGames
from facades.items_facade import ItemsFacade
from grpc_files.generated import items_pb2_grpc
from grpc_files.servicers.items_servicer import ItemsGrpcServicer
from helpers.gba.pokemon.gba_pokemon_helper import GAMES
from services.config_service import ConfigService
from services.error_service import ErrorService
from services.log_service import LogService
from services.translations_service import TranslationsService

MAX_MESSAGE_LENGTH = 48 * 1024 * 1024  # 48MB
BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_ssl_path(config_service: ConfigService, config_key: str, default_rel: str) -> Path:
    raw_path = os.getenv(config_key) or config_service.get(config_key, default_rel)
    path = Path(raw_path)
    return path if path.is_absolute() else BASE_DIR / path


async def _build_grpc_server(
    global_config: ConfigService,
    default_game: AvailableGames = AvailableGames.ORIGINAL_FIRE_RED,
    port: int = 50051,
) -> grpc.Server:
    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", MAX_MESSAGE_LENGTH),
            ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
        ],
    )

    translator = TranslationsService(global_config.get("CURRENT_LANGUAGE", "EN_US"))
    logger = LogService(translator, global_config.get("LOG_TYPE"))
    error_service = ErrorService(logger, translator)

    items_facade = ItemsFacade(
        global_config=global_config,
        error_service=error_service,
        default_game=default_game,
    )
    items_pb2_grpc.add_ItemsServiceServicer_to_server(
        ItemsGrpcServicer(items_facade), server
    )

    key_path = _resolve_ssl_path(global_config, "GRPC_KEY_PATH", "grpc_files/server.key")
    cert_path = _resolve_ssl_path(global_config, "GRPC_CERT_PATH", "grpc_files/server.crt")

    server_credentials = grpc.ssl_server_credentials(
        [(key_path.read_bytes(), cert_path.read_bytes())]
    )
    server.add_secure_port(f"[::]:{port}", server_credentials)

    await server.start()
    print(f"\nAsync Secure gRPC Server listening on port {port}...")
    await server.wait_for_termination()


def run_grpc(
    global_config: ConfigService,
    default_game: AvailableGames = AvailableGames.ORIGINAL_FIRE_RED,
    port: int = 50051,
) -> None:
    asyncio.run(_build_grpc_server(global_config, default_game=default_game, port=port))


def test_grpc(
    config_service: ConfigService,
    rpc_handler: Callable[[grpc.Channel, bytes | None, int | None], None],
    selected_game: AvailableGames | None = None,
    host: str = "localhost",
    port: int = 50051,
) -> None:
    """Open a secure gRPC channel, optionally load a custom ROM, and delegate the RPC call."""
    translator = TranslationsService(config_service.get("CURRENT_LANGUAGE", "EN_US"))
    logger = LogService(translator, config_service.get("LOG_TYPE"))

    target = f"{host}:{port}"
    send_game = selected_game is not None
    mode_label = f"WITH Custom Game ({selected_game.name})" if send_game else "Server Selected Game"
    print(f"\n[TEST - {mode_label}] Connecting to gRPC server at {target}...")

    game_bytes: bytes | None = None
    game_id: int | None = None

    if send_game:
        try:
            game_config = ConfigService.load_for_game(GAMES[int(selected_game.value)])
        except FileNotFoundError as exc:
            logger.error(translator.translate("errors.game_config_not_found", game_path=str(exc)))
            return

        raw_game_path = Path(game_config.get("ORIGINAL_GAME", ""))
        game_path = raw_game_path if raw_game_path.is_absolute() else BASE_DIR / raw_game_path

        if not game_path.is_file():
            logger.error(translator.translate("errors.game_not_found", game_path=str(game_path)))
            return

        game_bytes = game_path.read_bytes()
        game_id = int(selected_game.value)

    cert_path = _resolve_ssl_path(config_service, "GRPC_CERT_PATH", "grpc_files/server.crt")
    credentials = grpc.ssl_channel_credentials(root_certificates=cert_path.read_bytes())

    try:
        with grpc.secure_channel(
            target,
            credentials,
            options=[
                ("grpc.max_send_message_length", MAX_MESSAGE_LENGTH),
                ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
            ],
        ) as channel:
            rpc_handler(channel, game_bytes, game_id)
    except grpc.RpcError as exc:
        logger.error(f"gRPC Error [{exc.code().name}]: {exc.details()}")

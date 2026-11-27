import asyncio
import os
from collections.abc import Callable
from pathlib import Path
import grpc
from enums.gba.games_enum import AvailableGames
from exceptions.domain_exceptions import ResourceNotFoundError
from facades.items_facade import ItemsFacade
from grpc_files.generated import items_pb2_grpc
from grpc_files.servicers.items_servicer import ItemsGrpcServicer
from services.config_service import ConfigService
from services.error_service import ErrorService
from services.log_service import LogService
from services.file_service import FileService
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

    translator = TranslationsService(global_config.get("CURRENT_LANGUAGE"))
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

    if not key_path.is_file() or not cert_path.is_file():
        error_service.raise_error(
            "errors.tls_certs_not_found",
            ResourceNotFoundError,
            cert_path=str(cert_path),
            key_path=str(key_path),
        )

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
    rpc_handler: Callable[[grpc.Channel, bytes | None, str | None], None],
    selected_game: AvailableGames | None = None,
    host: str = "localhost",
    port: int = 50051,
) -> None:
    """Open a secure gRPC channel, optionally load a custom ROM, and delegate the RPC call."""
    translator = TranslationsService(config_service.get("CURRENT_LANGUAGE"))
    logger = LogService(translator, config_service.get("LOG_TYPE"))
    error_service = ErrorService(logger, translator)

    target = f"{host}:{port}"
    send_game = selected_game is not None
    mode_label = f"WITH Custom Game ({selected_game.name})" if send_game else "Server Selected Game"
    print(f"\n[TEST - {mode_label}] Connecting to gRPC server at {target}...")

    game_bytes: bytes | None = None
    current_game: str | None = None

    if send_game:
        try:
            game_config = ConfigService.load_for_game(selected_game.config_key)
            file_service = FileService(logger, translator, game_config, error_service)
            game_bytes = file_service.open_game_readonly(game_config.get("ORIGINAL_GAME", ""))
            current_game = selected_game.value
        except FileNotFoundError as exc:
            logger.error(translator.translate("errors.game_config_not_found", game_path=str(exc)))
            return
        except ResourceNotFoundError:
            return

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
            rpc_handler(channel, game_bytes, current_game)
    except grpc.RpcError as exc:
        logger.error(f"gRPC Error [{exc.code().name}]: {exc.details()}")

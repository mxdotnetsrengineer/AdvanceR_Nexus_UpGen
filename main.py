import asyncio
import grpc
from settings import init_global_config, init_game_config, current_config
from enums.gba.games_enum import AvailableGames
from enums.app_enums import AvailableLanguages
from helpers.gba.pokemon.gba_pokemon_helper import GAMES
from games.core.games_provider import GamesProvider
from tools.menu import ConsoleMenu

from grcp.generated import items_pb2_grpc, items_pb2
from grcp.servicers.items_servicer import ItemsGrpcServicer

MAX_MESSAGE_LENGTH = 48 * 1024 * 1024  # 48MB


async def __build_grpc_server(game_instance, port: int = 50051) -> grpc.Server:
    """Configure and serve the async secure gRPC server instance."""
    server = grpc.aio.server(
        options=[
            ("grpc.max_send_message_length", MAX_MESSAGE_LENGTH),
            ("grpc.max_receive_message_length", MAX_MESSAGE_LENGTH),
        ],
    )

    items_pb2_grpc.add_ItemsServiceServicer_to_server(
        ItemsGrpcServicer(game_instance.items_service), server
    )

    with open("grcp/server.key", "rb") as f:
        private_key = f.read()
    with open("grcp/server.crt", "rb") as f:
        certificate_chain = f.read()

    server_credentials = grpc.ssl_server_credentials(
        [(private_key, certificate_chain)]
    )
    server.add_secure_port(f"[::]:{port}", server_credentials)

    #serve
    await server.start()
    print(f"\nAsync Secure gRPC Server listening on port {port}...")
    await server.wait_for_termination()



def run_randomizer(game_instance) -> None:
    asyncio.run(game_instance.process_game())


def run_grpc(game_instance, port: int = 50051) -> None:
    asyncio.run(__build_grpc_server(game_instance, port))


def test_grpc(
    selected_game: AvailableGames | None = None,
    host: str = "localhost",
    port: int = 50051,
) -> None:
    """Connect to the running gRPC server and test GetAllItems with or without sending a game."""
    target = f"{host}:{port}"
    send_game = selected_game is not None
    mode_label = f"WITH Custom Game ({selected_game.name})" if send_game else "Server Selected Game"
    print(f"\n[TEST - {mode_label}] Connecting to gRPC server at {target}...")

    with open("grcp/server.crt", "rb") as f:
        trusted_certs = f.read()

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
            game_path = current_config.get("ORIGINAL_GAME")
            with open(game_path, "rb") as f:
                game_bytes = f.read()

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


def setup_game_config(game: AvailableGames, language: AvailableLanguages) -> None:
    """Initialize global configuration and apply the user-selected language."""
    init_game_config(GAMES[int(game.value)])
    if language is not None:
        current_config["CURRENT_LANGUAGE"] = language


if __name__ == "__main__":
    init_global_config()
    raw_lang = current_config.get("CURRENT_LANGUAGE")
    default_lang = AvailableLanguages[raw_lang] if raw_lang in AvailableLanguages.__members__ else AvailableLanguages.EN_US

    menu = ConsoleMenu(default_language=default_lang)
    selection = menu.run()

    if selection is None:
        exit(0)

    if selection.action in ("randomizer", "grpc_server") and selection.game:
        setup_game_config(selection.game, selection.language)
        game_instance = GamesProvider.create(
            game=selection.game,
            game_config=current_config,
        )

        if selection.action == "randomizer":
            run_randomizer(game_instance)
        else:
            run_grpc(game_instance)

    elif selection.action == "grpc_test_loaded":
        test_grpc(selected_game=None)

    elif selection.action == "grpc_test_replace" and selection.game:
        setup_game_config(selection.game, selection.language)
        test_grpc(selected_game=selection.game)
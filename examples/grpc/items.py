import grpc
from enums.gba.games_enum import AvailableGames
from services.config_service import ConfigService
from grpc_files.generated import items_pb2, items_pb2_grpc
from grpc_files.grpc_server import test_grpc


def execute_get_all_items(
    channel: grpc.Channel,
    game_bytes: bytes | None,
    game_id: int | None,
) -> None:
    """Stub execution and console formatting for ItemsService.GetAllItems."""
    stub = items_pb2_grpc.ItemsServiceStub(channel)

    if game_bytes is not None and game_id is not None:
        request = items_pb2.GetAllItemsRequest(
            game_file=game_bytes,
            game_id=game_id,
        )
    else:
        request = items_pb2.GetAllItemsRequest()

    response = stub.GetAllItems(request)

    print(f"\n[TEST] ✔ Total items received via gRPC: {len(response.items)}")
    print("=" * 80)
    for item_id in sorted(response.items.keys()):
        item = response.items[item_id]
        print(
            f"#{item.id:03d} | {item.name:<15} | "
            f"Pocket: {item.pocket:<10} ({item.pocket_id}) | "
            f"Type: {item.item_type:<20} (0x{item.item_type_id:02X}) | Price: ${item.price:5d}"
        )
    print("=" * 80)

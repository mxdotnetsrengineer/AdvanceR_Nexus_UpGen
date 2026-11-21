import grpc
from grcp.generated import items_pb2, items_pb2_grpc
from settings import init_global_config, current_config
from enums.gba.games_enum import AvailableGames
from helpers.gba.pokemon.gba_pokemon_helper import GAMES
from games.core.games_provider import GamesProvider


class ItemsGrpcServicer(items_pb2_grpc.ItemsServiceServicer):
    def __init__(self, items_service):
        self.items_service = items_service

    async def GetAllItems(self, request, context):
        if request.game_file:
            game_file = bytearray(request.game_file)
            target_items_service = self.items_service

            if request.HasField("game_id"):
                try:
                    selected_game = AvailableGames(request.game_id)
                except ValueError:
                    await context.abort(
                        grpc.StatusCode.INVALID_ARGUMENT,
                        f"Invalid game_id: {request.game_id}",
                    )

                init_global_config(GAMES[int(selected_game.value)])
                custom_game_instance = GamesProvider.create(
                    game=selected_game,
                    game_config=current_config,
                )
                target_items_service = custom_game_instance.items_service

            compiled_items = await target_items_service.get_all_items(game_file)

        else:
            server_game_file = self.items_service.memory.game_file
            if not server_game_file:
                await context.abort(
                    grpc.StatusCode.FAILED_PRECONDITION,
                    "No ROM loaded on server and no game_file provided.",
                )

            compiled_items = await self.items_service.get_all_items(server_game_file)

        response_map = {
            item_id: items_pb2.CompiledItemProto(
                id=item.id,
                name=item.name,
                pocket=item.pocket.name,
                pocket_id=item.pocket.value,
                item_type=item.item_type.name,
                item_type_id=item.item_type.value,
                price=item.price,
            )
            for item_id, item in compiled_items.items()
        }

        return items_pb2.GetAllItemsResponse(items=response_map)

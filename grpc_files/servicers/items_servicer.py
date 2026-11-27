import grpc
from models.game_input import GameInput  
from grpc_files.generated import items_pb2, items_pb2_grpc
from exceptions.domain_exceptions import (
    DomainValidationError,
    ResourceNotFoundError,
    RomPreconditionError,
)
from facades.items_facade import ItemsFacade


class ItemsGrpcServicer(items_pb2_grpc.ItemsServiceServicer):
    def __init__(self, items_facade: ItemsFacade):
        self.items_facade = items_facade

    async def GetAllItems(self, request, context):
        raw_file = request.game_file if request.game_file else None
        current_game = request.current_game if request.HasField("current_game") else None

        game_input = GameInput(
            current_game=current_game,
            raw_file=raw_file,
        )

        try:
            compiled_items = await self.items_facade.get_all_items_gba(game_input)
        except DomainValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except ResourceNotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except RomPreconditionError as exc:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))

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

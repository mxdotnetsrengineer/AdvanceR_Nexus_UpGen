from fastapi import APIRouter, Depends
from api.schemas.items_schema import CompiledItemResponse, GetAllItemsResponse
from models.game_api_input import GameAPIInput
from api.dependencies.game_dependencies import parse_game_input
from facades.items_facade import ItemsFacade


router = APIRouter(prefix="/gba/pokemon/items", tags=["Items"])


def get_items_facade() -> ItemsFacade:
    """Dependency placeholder overridden at app startup."""
    raise NotImplementedError("ItemsFacade dependency not configured.")


@router.post("", response_model=GetAllItemsResponse)
async def get_all_items_gba(
    game_input: GameAPIInput = Depends(parse_game_input),
    items_facade: ItemsFacade = Depends(get_items_facade),
) -> GetAllItemsResponse:
    """Extract all compiled items from an uploaded GBA ROM or the configured server ROM."""
    compiled_items = await items_facade.get_all_items_gba(game_input)

    mapped_items = {
        item_id: CompiledItemResponse(
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

    return GetAllItemsResponse(total=len(mapped_items), items=mapped_items)
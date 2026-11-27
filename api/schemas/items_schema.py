from pydantic import BaseModel, ConfigDict


class CompiledItemResponse(BaseModel):
    id: int
    name: str
    pocket: str
    pocket_id: int
    item_type: str
    item_type_id: int
    price: int

class GetAllItemsResponse(BaseModel):
    model_config = ConfigDict(title="All Items Success") 
    total: int
    items: dict[int, CompiledItemResponse]
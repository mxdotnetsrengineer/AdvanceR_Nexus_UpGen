from dataclasses import dataclass
from enums.gba.pokemon.gba_pokemon_enums import ItemPockets, ItemSubCategories

@dataclass
class CompiledItem:
    id: int
    name: str
    pocket: ItemPockets
    price: int
    item_type: ItemSubCategories

    def __str__(self) -> str:
            return (
                f"ID: {self.id:03d} | {self.name:<15} | "
                f"Pocket: {self.pocket.name:<10} ({self.pocket.value}) | "
                f"Type: 0x{self.item_type:02X} | Price: {self.price}"
            )

    @classmethod
    def dict_to_class(cls, item_data: dict) -> CompiledItem:
        return cls(**item_data)
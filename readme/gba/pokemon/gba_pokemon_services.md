# 🎮 GBA Pokémon Domain Services

Detailed breakdown of the `services/gba/pokemon/` domain binary services located under:

* **`gba/pokemon/bank_service.py` (`BankService`):** Parses master pointer tables to reverse engineer map bank hierarchies, map dimensions, and decoded region names.
* **`gba/pokemon/event_service.py` (`EventService`):** Inspects overworld map events, filters item Pokéballs via script opcodes, and repoints them to newly allocated script bytecode.
* **`gba/pokemon/item_service.py` (`ItemService`):** Decodes in-game item names from binary tables and generates valid script bytecode with randomized item IDs.
* **`gba/pokemon/keyboard_service.py` (`GBAKeyboardService`):** Rebuilds both visual UI layouts and logical character byte arrays to inject Spanish characters (`Ñ`, `ñ`, `¡`, `¿`) into naming keyboards.
# 🎮 GBA Pokémon Domain Services

Detailed breakdown of the `services/gba/pokemon/` domain binary services located under:

* **`gba/pokemon/bank_service.py` (`BankService`):** Parses master pointer tables to reverse engineer map bank hierarchies, map dimensions, and decoded region names, and coordinates wild grass encounter randomization across all compiled maps.
* **`gba/pokemon/events_service.py` (`EventsService`):** Inspects overworld map events, filters item Pokéballs via script opcodes, and repoints them to newly allocated script bytecode in free space.
* **`gba/pokemon/item_service.py` (`ItemService`):** Decodes in-game item names from binary tables and generates valid script bytecode with randomized item IDs.
* **`gba/pokemon/keyboard_service.py` (`GBAKeyboardService`):** Rebuilds both visual UI layouts and logical character byte arrays to inject Spanish characters (`Ñ`, `ñ`, `¡`, `¿`) into naming keyboards.
* **`gba/pokemon/stats_service.py` (`StatsService`):** Parses species base stats, BST, names, types, and abilities via `load_all_species()`, recursively traversing evolution tables to assign evolution stages and flag Mega Evolutions.
* **`gba/pokemon/wild_service.py` (`WildService`):** Resolves wild grass encounter slot offsets, tracks already randomized tables, and filters/picks unique species candidates per map.
* **`gba/pokemon/difficulty_service.py` (`DifficultyService`):** Builds BST- and evolution-stage-scaled candidate pools and adjusts wild Pokémon levels (`ADD` / `SUBS`) according to the active difficulty profile.



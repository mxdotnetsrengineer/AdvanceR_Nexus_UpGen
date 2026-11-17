# Changelog

All notable changes to **AdvanceR Nexus UpGen** will be documented in this file.

## [v1.2.0] - 2026-11-16

### Added
- **Pokémon Base Stats & Evolution Line Parser**: Added `StatsService` (`services/gba/pokemon/stats_service.py`) and the `CompiledBaseStats` dataclass model (`models/gba/pokemon/compiled_base_stats.py`) to extract species base stats, BST, names, types, abilities, catch rates, and recursively calculate evolution stages and Mega Evolution flags (`MEGA_EVO_METHODS`).
- **Difficulty-Based Wild Pokémon Randomizer**: Implemented `randomize_banks_wild_encounters` in `BankService` (`services/gba/pokemon/bank_service.py`) alongside `select_wild_species` and `randomize_wild_encounters` in `EventService` (`services/gba/pokemon/event_service.py`) to replace wild grass encounters using difficulty-scaled BST/evolution pools and dynamic level adjustments (`ADD` / `SUBS`).
- **Difficulty & Game Options Configuration**: Updated `settings.py` to load options config and game-specific difficulty profiles and added `DIFFICULTIES` (`easy`, `normal`, `hard`, `inferno`) to `helpers/gba/pokemon/gba_pokemon_helper.py`.
- **Expanded Game & Global Configuration Schemas**: Added pokemon stats, name table, wild encounter, and evolution pointer offsets to `emerald_config.json`, `fire_red_config.json`, and `radical_red_config.json`, plus new flags (`BASE_STATS`, `RANDOMIZE_WILD_POKEMON`, `INCLUDE_MEGA_EVOLUTIONS`) in `feature_flags.json` and `global_config.json`.
- **Low-Level Binary Memory Helpers**: Extended `GBAMemoryService` (`services/gba/memory_service.py`) with more pointer,offsets utilities.

### Changed
- **Asynchronous Execution Pipeline**: Converted `process_game`, `allocate_banks`, and `set_spanish_chars` to `async` methods using `asyncio.gather` in `GBAPokemonGame` (`games/gba/pokemon/gba_pokemon_game.py`) and `asyncio.run` in `main.py` to run map bank allocation and Pokémon species data parsing concurrently.
- **Service Factory & Memory Refactor**: Updated `GBAPokemonCoreFactory` (`games/core/gba_pokemon_core.py`) to inject `StatsService`, refactored `BankService`, `EventService`, and `ItemService` to use the new `GBAMemoryService` helpers, and added `width` and `height` fields to `CompiledMap`.
- **Log Output Gating**: Updated `LogService.raw()` (`services/log_service.py`) and `settings.py` initialization messages to respect the configured `LOG_TYPE` verbosity setting instead of printing unconditionally.

## [v1.1.0] - 2026-11-14

### Added
- **Pokémon Emerald & Emerald Kaizo Support**: Added `EmeraldGame` (`games/gba/pokemon/emerald_game.py`) and new config files (`config/gba/pokemon/emerald_config.json`, `config/gba/pokemon/emerald_kaizo_config.json`) with Hoenn map bank tables, 8-byte map name parsing, item limits, and Spanish keyboard offsets.
- **Abstract Factory & Template Method Architecture**: Created `BaseGame` (`games/base_game.py`), `GamesCore` (`games/core/games_core.py`), `GBAPokemonCoreFactory` (`games/core/gba_pokemon_core.py`), `GamesProvider` (`games/core/games_provider.py`), and the base class `GBAPokemonGame` (`games/gba/pokemon/gba_pokemon_game.py`) to avoid duplicated code across Gen III titles and make it easier to add new consoles later.
- **Feature Flags & Custom Decorators**: Added `config/gba/pokemon/feature_flags.json` and `decorators/app_decorators.py` with `@when_enabled`, `@skip_when_disabled`, `@when_any_enabled` (OR logic), and `@keys_from_str` to toggle execution steps (`ALLOCATE_BANKS`, `ALLOCATE_MAPS`, `MAPS_EVENTS`, `ONLY_DATABASE`, `ADD_SPANISH_CHARS`) cleanly.
- **Bank Table Scanner**: Added `get_core_banks_position` and `inspect_core_banks` to `BankService` (`services/gba/pokemon/bank_service.py`) to locate and verify root map bank pointers across different GBA games versions.

### Changed
- **Shared GBA Pokémon Enums & Helpers**: Renamed and generalized `fire_red_enums.py` and `fire_red_helper.py` to `gba_pokemon_enums.py` (`GBAPokemonKeyIndex`, `GBAPokemonLogicKeyIndex`, `GBAPokemonOthersKeyIndex`, `GBAPokemonOthersLogicKeyIndex`) and `gba_pokemon_helper.py` so all Gen III Pokémon games share the same keyboard layouts and logic tables.
- **Dynamic Map & Keyboard Handling**: Updated `BankService` to calculate map counts per bank using the next bank's header offset and configurable map name sizes (`MAP_NAME_ENTRY_SIZE`, `MAP_NAME_TEXT_OFFSET`), and updated `GBAKeyboardService` to handle multiple keyboard occurrences (`keyboards_ocurrences`).
- **Config & Entry Point Cleanup**: Switched all services to use `ConfigService.get()`, moved games loading into `GBAPokemonCoreFactory.create_memory_service()`, updated `main.py` to load games through `GamesProvider`, and moved the old `CurrentGameFactory` to `deprecated/factory_example.py`.

### Fixed
- **Enum Tuple Bug**: Removed trailing commas in `AvailableGames` (`enums/gba/games_enum.py`) that turned integer values into tuples when running `main.py`.
- **Games File Size & Map Dimension Checks**: Replaced hardcoded `0x1D00000` memory limits with `len(game_file)` and raised the max map size check in `BankService` so large maps don't get skipped early.


## [v1.0.0] - 2026-11-13

### Added
- **Service-Oriented & Factory Architecture**: Introduced `CurrentGameFactory` (`games/current_game.py`) alongside an abstract `GBAGame` base class (`games/gba/gba_game.py`) and concrete `FireRedGame` implementation (`games/gba/pokemon/fire_red_game.py`) to decouple game execution from low-level binary manipulation.
- **Structured Logging & Exception Dispatch System**: Added `LogService` (`services/log_service.py`), `LogLevel` (`enums/logs_enum.py`), and exception/channel mappings (`helpers/logs_helper.py`) to filter console output by severity (`NONE`, `INFO`, `WARNING`, `ERROR`, `ERROR_AND_WARNING`, `ALL`), record execution history, and raise typed Python exceptions (`ValueError`, `FileNotFoundError`, `KeyError`, `RuntimeError`).
- **Core & GBA Domain Services**: Implemented modular service layers including `ConfigService`, `FileService`, `LogService`, `TranslationsService`, `GBAMemoryService`, `BankService`, `EventService`, and `ItemService` to isolate memory pointer resolution, map traversal, event scanning, and item injection.
- **Spanish Naming Screen Localization (`GBAKeyboardService`)**: Added `services/gba/pokemon/keyboard_service.py` along with FireRed keyboard layout tables (`helpers/gba/pokemon/fire_red_helper.py`) and dynamic key index enums (`enums/gba/pokemon/fire_red_enums.py`) to inject Spanish characters (`Ñ`, `ñ`, `¡`, `¿`) into both visual UI matrices and input logic tables.
- **Multi-Language i18n Translation System**: Added JSON locale dictionaries under `translations/EN_US/` and `translations/ES_MX/` (`errors.json`, `messages.json`, `warnings.json`) with key flattening and variable interpolation via `TranslationsService`.
- **Strongly Typed Data Models & Enums**: Created dataclass models (`CompiledBank`, `CompiledMap`, `CompiledEvent`, `GameUIKeyboard`, `GameUIKeyboardLogic`, `UIKeyboardPatch`) under `models/gba/pokemon/` and standardized enums (`AvailableGames`, `AvailableLanguages`, `LogLevel`, and dynamic `@keys_from_str` `IntEnum` generators) under `enums/`.

### Changed
- **Configuration Directory & Schema Expansion**: Migrated configuration files to `config/global_config.json` and `config/gba/pokemon/` (`fire_red_config.json`, `radical_red_config.json`), adding properties for keyboard offsets, UI separators, language selection (`CURRENT_LANGUAGE`), log verbosity (`LOG_TYPE`), and database-only mode (`ONLY_DATABASE`).
- **Entry Point & Settings Refactor**: Streamlined `main.py` to bootstrap games through `CurrentGameFactory` and updated `settings.py` to support localized startup diagnostics and expanded game definitions (`LeafGreen`, `Emerald`, and fan-game variants).
- **Rebrand & Docs**: Updated `README.md` with the new **AdvanceR Nexus UpGen** branding, layered service-oriented architecture documentation, design patterns overview, and complete configuration references.

### Removed
- **Legacy Procedural Helpers**: Replaced monolithic scripts (`helpers/consoles_helper.py`, `helpers/instances_helper.py`, `helpers/map_helper.py`, `helpers/pointers_helper.py`) with the new service, model, and helper hierarchy.

## [v0.1.0] - 2026-11-05

### Added
- **Multi-Game Configuration Architecture**: Implemented JSON based configuration files (`games/fire-red.json`, `games/radical-red.json`, and `games/global_config.json`) alongside `settings.py` to dynamically load ROM offsets, memory boundaries, and randomizer flags.
- **GBA Binary Decryption & Pointer Engine**: Added `helpers/consoles_helper.py` and `helpers/pointers_helper.py` to translate Little Endian GBA memory pointers (`0x08000000` range), decode proprietary GBA character tables, traverse map banks/headers, and locate safe `0xFF` free space blocks for binary injection.
- **Overworld Pokéball Item Randomizer**: Added `helpers/instances_helper.py` and `helpers/map_helper.py` to scan map NPC events, identify ground Pokéball item scripts (filtering out starter Pokéballs), generate valid random items, and repoint custom XSE bytecode scripts into free ROM space.
- **Supported Games**: Added initial randomization support for **Pokémon FireRed (16MB)** and **Pokémon Radical Red v4.1 (32MB)**.
- **Project Documentation & Licensing**: Added `README.md` with quick start instructions using `uv` and full configuration property references, along with an MIT `LICENSE` and Python `.gitignore`.

### Fixed
- **Documentation**: Corrected minor wording and typos.
# Changelog

All notable changes to **AdvanceR Nexus UpGen** will be documented in this file.

## [v1.3.1] - 2026-11-20

### Added
- **Interactive Multi-Language Console Menu (`ConsoleMenu`)**: Created `tools/menu.py` and `tools/user_selection.py` with live locale switching (`EN_US` / `ES_MX`), screen clearing (`__clear_screen`), `ESC` instant exit, and multi-level `Backspace`/`0` back-navigation across execution modes, gRPC tests, and game selection.
- **Redis Caching Layer for Compiled Game Data**: Integrated `redis.asyncio` in `BaseGame` (`games/base_game.py`) and `GBAPokemonGame` (`games/gba/pokemon/gba_pokemon_game.py`) along with `load_from_json` deserializers (`dict_to_class`) across `BankService`, `StatsService`, `ItemService`, `CompiledBank`, `CompiledMap`, `CompiledEvent`, `CompiledBaseStats`, and `CompiledItem` to cache parsed banks, species stats, and items with a 1-hour TTL.
- **Standalone `AppsTranslations` Engine & Menu Locales**: Extracted translation loading and key flattening into `translations/app_translations.py` with `Enum` locale normalization (`__normalize_locale`) and added `menu.json` locale files under `translations/EN_US/` and `translations/ES_MX/`.

### Changed
- **Split Global & Game Configuration Initialization**: Refactored `settings.py` into `init_global_config()` (startup shared/options loading) and `init_game_config()` (game-specific offsets, difficulty, and feature flags) to preserve user-selected menu languages across game loads.
- **Updated Entry Point (`main.py`)**: Replaced hardcoded game execution with `ConsoleMenu` routing for Randomizer, Secure gRPC Server, and gRPC Client test modes.

## [v1.3.0] - 2026-11-19

### Added
- **Game Item Table Parser & Models**: Implemented `CompiledItem` (`models/gba/pokemon/compiled_item.py`), `ItemPockets`, `ItemSubCategories`, and `BankMethods` enums (`enums/gba/pokemon/gba_pokemon_enums.py`), plus `ItemService.get_all_items()` to extract item IDs, names, pockets, subcategories, and prices from GBA Game.
- **Binary Struct Unpacking Helper**: Added `GBAMemoryService.unpack()` (`services/gba/memory_service.py`) wrapping `struct.unpack_from` with bounds validation.

### Changed
- **Service Decoupling & Encapsulation**: Renamed `EventService` to `EventsService` (`services/gba/pokemon/events_service.py`), moved wild encounter orchestration directly into `WildService` (`CompiledWildEvents`), wired services independently via `GBAPokemonCoreFactory` (`games/core/gba_pokemon_core.py`), and standardized internal helper methods with private `__` naming and `# Public Methods` / `# Private Methods` sections across `BankService`, `StatsService`, `ItemService`, `WildService`, and `LogService`.

## [v1.2.2] - 2026-11-18

### Added
- **Secure Async gRPC Server & Items Service**: Added `grcp/protos/items.proto`, PowerShell proto compiler script (`grcp/compile_protos.ps1`), generated protobuf bindings (`grcp/generated/`), and `ItemsGrpcServicer` (`grcp/servicers/items_servicer.py`) exposing `GetAllItems` over TLS (`grpc.aio.server`) with support for both server-loaded Games and custom client-uploaded Games files.
- **gRPC Client Test Runner & Dependencies**: Added `test_grpc` client verification in `main.py` and created `requirements.txt` (`grpcio`, `grpcio-tools`, `cryptography`, `redis`).

## [v1.2.1] - 2026-11-17

### Added
- **Dedicated Wild Encounter & Difficulty Services**: Extracted wild encounter resolution and difficulty tier generation out of `EventService` into modular services: `WildService` (`services/gba/pokemon/wild_service.py`) and `DifficultyService` (`services/gba/pokemon/difficulty_service.py`), wired through `GBAPokemonCoreFactory` (`games/core/gba_pokemon_core.py`).
- **Spanish Keyboard Support for Emerald Kaizo**: Extended `GBAKeyboardService` (`services/gba/pokemon/keyboard_service.py`) to apply Spanish character patches (`Ñ`, `ñ`, `¡`, `¿`) to `AvailableGames.EMERALD_KAIZO` alongside FireRed, Radical Red, and Emerald.
- **Async Support in Flag Decorators**: Updated `_flag_condition` and `when_any_enabled` in `decorators/app_decorators.py` using `inspect.iscoroutinefunction` so decorators seamlessly wrap both synchronous and `async` methods without returning `None` before `await`.
- **Word-Aligned Free Space Scanner & Struct Unpacking**: Added `read_u16_array` (`struct.unpack_from`), `offset_to_pointer`, and 4-byte word-alignment (`align_to_word`) to `GBAMemoryService` (`services/gba/memory_service.py`).
- **Expanded Locale Messages & Warnings**: Added localized keys (`messages.yes`, `messages.no`, `messages.banks.is_bank_table`, `warnings.banks.empty_table_position`, `warnings.banks.pointer_not_found`) across `EN_US` and `ES_MX` translation files.

### Changed
- **Direct Offset Configuration Schema**: Replaced pointer-based config keys (`BANK_TABLE_OFFSET`, `POKEMON_STATS_POINTER_OFFSET`, `POKEMON_NAMES_POINTER_OFFSET`, `WILD_POKEMON_POINTER_OFFSET`) with direct Games offsets (`0x486578` for Emerald/Kaizo and `0x3526a8` for FireRed/Radical Red) and swapped the swapped filenames between `emerald_config.json` and `emerald_kaizo_config.json`.
- **Static & Encapsulated Binary Operations**: Converted `GBAMemoryService` pointer/string utilities into `@staticmethod` / `@classmethod` helpers, tightened bounds checking across `BankService`, `EventService`, `ItemService`, and `StatsService`, and encapsulated internal helper methods with private `__` naming.
- **Inverted Database Flag Decorator**: Replaced `@skip_when_disabled("ONLY_DATABASE")` with `@skip_when_enabled("ONLY_DATABASE")` across `FileService`, `BankService`, `EventService`, and `GBAKeyboardService` for clearer boolean semantics.
- **Updated Default Runtime & Gitignore Rules**: Set default language to `ES_MX` in `config/global_config.json`, and updated `MAX_BANK_SCAN_BYTES` (`0x2000`) and `GBA_POKEMON_III_CHAR_TABLE` in `helpers/gba/pokemon/gba_pokemon_helper.py`.

### Fixed
- **Upper Keyboard Logic Byte Alignment**: Moved the `0x00` spacer byte from the start of row 4 (`T-Z`) to the end of row 3 (`M-S`) in `GBA_POKEMON_NAMING_UPPER_LOGIC` (`helpers/gba/pokemon/gba_pokemon_helper.py`) to match the exact 8-column binary layout in GBA ROMs.
- **Redundant Game Save Call**: Removed duplicate `save_new_game_file` call in `FireRedGame._apply_game_specific_changes()` (`games/gba/pokemon/fire_red_game.py`).

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
- **Multi-Game Configuration Architecture**: Implemented JSON based configuration files (`games/fire-red.json`, `games/radical-red.json`, and `games/global_config.json`) alongside `settings.py` to dynamically load games offsets, memory boundaries, and randomizer flags.
- **GBA Binary Decryption & Pointer Engine**: Added `helpers/consoles_helper.py` and `helpers/pointers_helper.py` to translate Little Endian GBA memory pointers (`0x08000000` range), decode proprietary GBA character tables, traverse map banks/headers, and locate safe `0xFF` free space blocks for binary injection.
- **Overworld Pokéball Item Randomizer**: Added `helpers/instances_helper.py` and `helpers/map_helper.py` to scan map NPC events, identify ground Pokéball item scripts (filtering out starter Pokéballs), generate valid random items, and repoint custom XSE bytecode scripts into free game file space.
- **Supported Games**: Added initial randomization support for **Pokémon FireRed (16MB)** and **Pokémon Radical Red v4.1 (32MB)**.
- **Project Documentation & Licensing**: Added `README.md` with quick start instructions using `uv` and full configuration property references, along with an MIT `LICENSE` and Python `.gitignore`.

### Fixed
- **Documentation**: Corrected minor wording and typos.
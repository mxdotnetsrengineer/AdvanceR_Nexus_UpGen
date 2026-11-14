# Changelog

All notable changes to **AdvanceR UpGeN** will be documented in this file.

## [v1.1.0] - 2026-11-13

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
- **Multi-Game Configuration Architecture**: Implemented JSON-based configuration files (`games/fire-red.json`, `games/radical-red.json`, and `games/global_config.json`) alongside `settings.py` to dynamically load ROM offsets, memory boundaries, and randomizer flags.
- **GBA Binary Decryption & Pointer Engine**: Added `helpers/consoles_helper.py` and `helpers/pointers_helper.py` to translate Little Endian GBA memory pointers (`0x08000000` range), decode proprietary GBA character tables, traverse map banks/headers, and locate safe `0xFF` free space blocks for binary injection.
- **Overworld Pokéball Item Randomizer**: Added `helpers/instances_helper.py` and `helpers/map_helper.py` to scan map NPC events, identify ground Pokéball item scripts (filtering out starter Pokéballs), generate valid random items, and repoint custom XSE bytecode scripts into free ROM space.
- **Supported Games**: Added initial randomization support for **Pokémon FireRed (16MB)** and **Pokémon Radical Red v4.1 (32MB)**.
- **Project Documentation & Licensing**: Added `README.md` with quick start instructions using `uv` and full configuration property references, along with an MIT `LICENSE` and Python `.gitignore`.

### Fixed
- **Documentation**: Corrected minor wording and typos.
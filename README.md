# Objective
This repo is a showcase of how I write clean, scalable, and maintainable Python code in my day-to-day work. Beyond being a fun CLI tool (with a GUI on the way) to randomize and customize classic consoles game files. I am starting with GBA through simple JSON configs, the main goal here is to let recruiters and engineering teams easily review my coding style, architecture decisions, and handling of low-level binary data, all kept simple to run and explore.

# 🎮 AdvanceR Nexus UpGen
**AdvanceR Nexus UpGen** is a modular, extensible Python engine built to parse, reverse engineer and customize binary structures in classic game files. Designed to support multiple consoles and titles through declarative JSON configurations, the project kicks off with **Generation III Pokémon GBA** titles as its initial implementation. Featuring safe Pokéball item randomization via dynamic script repointing and full Spanish character support (`Ñ`, `ñ`, `¡`, `¿`) for in-game naming keyboards.

## 📑 Table of Contents
* [✨ Key Features](#-key-features)
* [🎯 Supported Games](#-supported-games)
* [🚀 Quick Start Guide](#-quick-start-guide)
  * [1. Create the Virtual Environment](#1-create-the-virtual-environment)
  * [2. Activate the Environment](#2-activate-the-environment)
  * [3. Execution](#3-execution)
    * [3.1 Adding a New Game](#31-adding-a-new-game)
* [📁 Project Structure](#-project-structure)
* [⚙️ Configuration Properties](#%EF%B8%8F-configuration-properties-config)
  * [1. Global Config Properties](#1-global-config-properties-configglobal_configjson)
  * [2. Game JSON Properties Example](#2-game-json-properties-example)
  * [3. Custom Dynamic Values](#3-custom-dynamic-values)
* [🏗️ Architecture & Design Patterns](#%EF%B8%8F-architecture--design-patterns)
  * [System Layers](#system-layers)
  * [Design Patterns Used](#design-patterns-used)
    * [1. Abstract Factory & Provider](#1-abstract-factory--factory-provider)
    * [2. Template Method](#2-template-method)
    * [3. Dependency Injection](#3-constructor-dependency-injection-di)
    * [4. Data Transfer Object](#4-data-transfer-object)
    * [5. Strategy / Declarative Configuration](#5-strategy--declarative-configuration-uikeyboardpatch)
    * [6. Metaprogramming / Decorators](#6-custom-decorators--metaprogramming-when_enabled-keys_from_str)
    * [7. Factory Method](#7-factory-method-deprecated)

<h3 align="center">⚫ ⚫ ⚫ ⚫ ⚫ ⚫</h3>

## ✨ Key Features

* **Safe Pokéball Item Randomization (`EventService` & `ItemService`):** Scans map events, inspects script opcodes to ensure the Pokéball holds an item rather than a starter Pokémon, generates new bytecode with a valid random item, and writes it into free space, while updating Game pointers.
* **Pokémon Base Stats & Difficulty-Based Wild Randomizer (`StatsService`, `BankService` & `EventService`, `WildService` & `DifficultyService`):** Parses pokemon base stats, BST, types, abilities, and recursive evolution lines, then randomizes wild grass encounters using difficulty-scaled BST/evolution pools and dynamic level adjustments (`easy`, `normal`, `hard`, `inferno`).
* **Spanish UI & Internal Keyboard Customization (`{Console}KeyboardService`):** Restructures both visual layouts/spacings and logical character tables in game files, relocating `M`/`m` and inserting `Ñ`, `ñ`, `¡`, and `¿` without overflowing binary file boundaries.
* **Map Bank & Header Reverse Engineering (`BankService`):** Reads master binary pointer tables to reconstruct map hierarchies, map dimensions (`width x height`), decoded region names via game specific character tables (starting with Pokémon Gen III), and event counts.
* **Internationalization (`TranslationsService`):** Loads and flattens locale-specific JSON files (`ES_MX`, `EN_US`) for instant lookups.
* **Filterable Logging & Exception System (`LogService`):** Controls console output channels (`NONE`, `INFO`, `WARNING`, `ERROR`, `ERROR_AND_WARNING`, `ALL`) and raises dynamically mapped exceptions based on error keys.

## 🎯 Supported Games

Currently, the engine supports the following **Game Boy Advance (Gen III)** titles via dedicated JSON configuration profiles:

| Platform | Game Title | Version / Base | Status | Supported Features | Extended Features | 
| :--- | :--- | :--- | :--- | :--- |
| **GBA** | **Pokémon FireRed** | USA (v1.0 / v1.1) | ✅ Ready | Item Randomizer, Spanish Keyboard Patch, Wild Pokemon Randomizer | BST-Scaled Wild Randomizer |
| **GBA** | **Pokémon Radical Red** | v4.1 (FireRed Base) | ✅ Ready | Item Randomizer, Spanish Keyboard Patch, Wild Pokemon Randomizer | BST-Scaled Wild Randomizer |
| **GBA** | **Pokémon Emerald** | USA | ✅ Ready | Item Randomizer, Spanish Keyboard Patch |
| **GBA** | **Pokémon Emerald Kaizo** | Emerald USA Base | ✅ Ready | Item Randomizer, Spanish Keyboard Patch |

> 💡 **Interested in Extended Features?**  
> Features like the **BST-Scaled Wild Randomizer** are available for you. If you'd like to get access or learn more about the project, feel free to reach out at the email **[mexican.dotnet.senior.engineer@gmail.com](mailto:mexican.dotnet.senior.engineer@gmail.com)**.

<h3 align="center">
  ⚫ ⚫ ⚫
    <a href="#-table-of-contents" title="Back to Table of Contents">⬆️</a>
  ⚫ ⚫ ⚫
</h3>

## 🚀 Quick Start Guide

To ensure maximum performance and speed when managing Python environments, this project utilizes **`uv`**. *(Requires Python 3.11+ with zero external third-party dependencies).*

### 1. Create the Virtual Environment
Navigate to the root directory of the project and spin up an isolated virtual environment:
```bash
python -m uv venv 
```

### 2. Activate the Environment

Activate the virtual environment depending on your operating system:
* **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```
* **Windows:**
  ```powershell
  .venv\Scripts\activate
  ```

### 3. Execution
1. Place your clean target game file in the root directory.
2. Adjust your main toggles in `config/global_config.json` (and optionally enable `USE_FEATURE_FLAGS` to fine-tune specific pipeline steps in `config/{console}/{series}/feature_flags.json`).
3. Select the target game in `main.py` using `AvailableGames` (e.g., `AvailableGames.ORIGINAL_FIRE_RED` or `AvailableGames.RADICAL_FIRE_RED`) and run:
```bash
python main.py
```

#### 3.1 Adding a New Game
Adding support for a new title only requires updating a few files without touching the core engine:

1. **Register the Enum (`enums/games_enum.py`):** Add a new identifier to `AvailableGames` (e.g., `RUBY = 6`).
2. **Create the Game Profile (`config/{console}/{series}`):** Add a JSON configuration file defining the memory offsets, free space start, and feature flags for the new game, and register it in your game config mapping.
3. **Implement the Game Class (`games/{console}/{series}/`):** Create a new class inheriting from `{console}{series}Game` and override `_apply_game_specific_changes()` if the title requires custom logic.
4. **Register in the Factory (`games/core/{console}_{series}_core.py` & `games/core/games_provider.py`):** Map the new `AvailableGames` enum to its corresponding game class and factory provider.

<h3 align="center">
  ⚫ ⚫ ⚫
    <a href="#-table-of-contents" title="Back to Table of Contents">⬆️</a>
  ⚫ ⚫ ⚫
</h3>

## 📁 Project Structure

The repository is organized by layers and platform domains so new consoles, games, and features can scale independently:

* **`config/`** — Stores declarative JSON configurations split between global runtime flags (`global_config.json`) and console/game specific binary layouts (`config/{console}/{series}/`), allowing new titles to be supported without modifying core logic.
* **`enums/`** — Centralizes strongly typed enumerations for supported titles, languages, logging channels, and dynamically generated keyboard index mappings.
* **`decorators/`** — Contains reusable Python decorators (`app_decorators.py`) to toggle features via config flags (`@when_enabled`, `@skip_when_enabled`, `@when_any_enabled`) and generate enums from strings (`@keys_from_str`).
* **`games/`** — Holds the game classes and the factories that build them:
  * **`base_game.py` (`BaseGame`):** Base abstract class that defines the main structure for any game, regardless of the console.
  * **`core/` (`GamesProvider`, `GamesCore`, `{Console}{Series}CoreFactory`):** Uses the **Abstract Factory** pattern to set up the right services, load the game file into memory, and create the selected game.
  * **`{console}/` (`{Console}Game`, `{Console}{Series}Game`, `FireRedGame`, `EmeraldGame`):** Uses the **Template Method** pattern to share common games logic while keeping game specific changes separate.
* **`deprecated/`** — Preserves removed implementations (such as `factory_example.py`) as architectural reference examples without affecting active runtime paths.
* **`helpers/`** — Holds static reference tables (such as Gen III byte to character mappings), original keyboard matrices, and internal exception-type lookup dictionaries.
* **`models/`** — Defines lightweight `@dataclass` Data Transfer Objects (DTOs) that represent parsed map banks, map headers, overworld events, and declarative keyboard update payloads.
* **`translations/`** — Stores language specific JSON files (`EN_US/`, `ES_MX/`) used by `TranslationsService` to keep user facing text separate from the main logic.
* **`services/`** — The main logic of the app, split between shared utilities and binary handlers for each console:
  * **`config_service.py` (`ConfigService`):** Provides a centralized, clean interface for querying merged runtime configuration values across the application.
  * **`file_service.py` (`FileService`):** Handles safe binary I/O operations for loading clean game files into memory and writing customized outputs to disk.
  * **`log_service.py` (`LogService`):** Filters console logs by level (`INFO`, `WARNING`, `ERROR`, etc.), saves runtime history, and raises mapped exceptions when errors happen.
  * **`translations_service.py` (`TranslationsService`):** Loads, merges, and flattens locale JSON files for instant multi language string resolution.
  * **`{console}/memory_service.py` (`{Console}MemoryService`):** Translates console memory pointers into raw file offsets and tracks available free space for safe binary injection.
  * **`gba/pokemon/` (Domain Services):** gba pokemon series specific binary handlers. See the [GBA Pokémon Services Reference](./readme/gba/pokemon/gba_pokemon_services.md) for a detailed breakdown of each service.
* **Root Files (`main.py`, `settings.py`)** — `settings.py` loads the JSON configs (including optional `feature_flags.json`) and converts hex strings into integers at startup, while `main.py` acts as the entry point that calls `GamesProvider` to build and run the selected game.

<h3 align="center">
  ⚫ ⚫ ⚫
    <a href="#-table-of-contents" title="Back to Table of Contents">⬆️</a>
  ⚫ ⚫ ⚫
</h3>

## ⚙️ Configuration Properties (`config/`)

The system dynamically unifies global configurations, game specific layouts, and randomizer flags at runtime via `init_global_config()`. Hexadecimal string values (properties starting with `0x`) are automatically converted into integers internally to streamline raw binary operations.

### 1. Global Config Properties (`config/global_config.json`)
Establishes logical rules, output behavior, and localization switches enforced across all supported games:

* **`RANDOMIZE_POKEBALLS_ITEMS`** (`bool`): Toggles whether items lying visibly inside overworld Pokéballs on the ground should be randomized.
* **`ADD_SPANISH_CHARS`** (`bool`): When `true`, updates the naming screen UI and logical keyboards to include Spanish characters (`Ñ`, `ñ`, `¡`, `¿`).
* **`ONLY_DATABASE`** (`bool`): When `true`, runs map bank and item reverse engineering in read-only mode without altering or saving a new output game file.
* **`CURRENT_LANGUAGE`** (`str`): Sets the active locale code for console logs and error messages (`"ES_MX"` or `"EN_US"`).
* **`LOG_TYPE`** (`str`): Controls which message channels print to the console (`"NONE"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"ERROR_AND_WARNING"`, or `"ALL"`).
* **`USE_FEATURE_FLAGS`** (`bool`): When `true`, loads extra feature toggles from `config/{console}/{series}/feature_flags.json` (e.g., `ALLOCATE_BANKS`, `ALLOCATE_MAPS`, `MAPS_EVENTS`) to enable or skip specific steps of the process.
* **`RANDOMIZE_WILD_POKEMON`** (`bool`): Toggles whether wild grass Pokémon encounters are randomized based on the selected difficulty profile.
* **`INCLUDE_MEGA_EVOLUTIONS`** (`bool`): When `true`, includes Mega Evolutions when parsing evolution lines and building species data.

### 2. Game JSON Properties Example
Every supported game uses its own JSON profile to define memory offsets, free space limits, and binary layouts. For a complete example of how a game configuration is structured, check out the [FireRed Configuration Reference](./readme/fire_red.md) (`config/gba/pokemon/fire_red_config.json`).

### 3. Custom Dynamic Values
During initialization and execution, the system manages transient runtime state inside `{Console}MemoryService`, rather than persisting them in static JSON files:

* **`game_file`** (`bytearray`): Loaded into memory by `FileService.open_game()` inside `{Console}{Series}CoreFactory.create_memory_service()`. It holds the modified game bytes in memory before saving them to the output file.
* **`free_space_offset`** (`int`): Starts at the offset defined in `FREE_SPACE_START`. Whenever a service writes new data into the game file (such as `EventService` writing randomized Pokéball scripts), this pointer automatically moves forward so consecutive writes never overlap or overwrite existing data.
* **`available_language`** (`bool`): Set inside `current_config` by `init_global_config()` to flag whether the requested `CURRENT_LANGUAGE` is natively supported (`ES_MX` / `EN_US`) or fell back to English.

<h3 align="center">
  ⚫ ⚫ ⚫
    <a href="#-table-of-contents" title="Back to Table of Contents">⬆️</a>
  ⚫ ⚫ ⚫
</h3>

## 🏗️ Architecture & Design Patterns

When refactoring this codebase from procedural helper scripts into an extensible engine, I designed a **Layered Service-Oriented Architecture** with strict separation of concerns, keeping low-level binary manipulation completely decoupled from console and game specific rules.

### System Layers
1. **Entry & Configuration Layer (`main.py`, `settings.py`):** Initializes the application, merges `global_config.json`, game specific JSON layouts, and optional `feature_flags.json`, converts hex strings to integers, and delegates instantiation to `GamesProvider`.
2. **Core Factory & Domain Layer (`games/core/`, `games/`):** Uses `GamesProvider` and `{Console}{Series}CoreFactory` to assemble platform service families, while `BaseGame`, `{Console}Game`, and `{Console}{Series}Game` define the game execution lifecycle for concrete titles (`FireRedGame`, `EmeraldGame`).
3. **Service Layer (`services/`):** Encapsulates all business logic and binary operations split by technical domain (`{Console}MemoryService`, `BankService`, `EventService`, `ItemService`, `StatsService`, `{Console}KeyboardService`) alongside cross-cutting infrastructure services (`ConfigService`, `LogService`, `TranslationsService`, `FileService`).
4. **Models & Data Layer (`models/`, `enums/`, `helpers/`):** Provides strongly typed data structures (`@dataclass`), enumerations, and hexadecimal lookup tables free of side effects.

<h3 align="center">
  ⚫ ⚫ ⚫
    <a href="#-table-of-contents" title="Back to Table of Contents">⬆️</a>
  ⚫ ⚫ ⚫
</h3>

### Design Patterns Used

#### 1. Abstract Factory & Factory Provider
* **Location:** `games/core/games_core.py`, `games/core/{console}_{series}_core.py`, `games/core/games_provider.py`
* **Purpose:** `GamesProvider` selects the appropriate concrete factory (`{Console}{Series}CoreFactory`) based on `AvailableGames`, assembling entire families of platform specific services (`{Console}MemoryService`, `BankService`, `EventService`, `ItemService`, `{Console}KeyboardService`) and loading the game file buffer before instantiating the game. This keeps `main.py` decoupled from object creation and makes adding new consoles (e.g., NDS, GBC) straightforward.

#### 2. Template Method
* **Location:** `games/base_game.py`, `games/{console}/{series}/{console}_{series}_game.py`
* **Purpose:** `{Console}{Series}Game` defines the shared asynchronous processing skeleton inside `process_game()` (concurrently allocating map banks and parsing species stats via `asyncio.gather`, randomizing wild encounters, configuring Spanish keyboards, and saving the modified game file) while exposing a protected `_apply_game_specific_changes()` hook so subclasses (`FireRedGame`, `EmeraldGame`) can add title specific behavior without duplicating code.

#### 3. Constructor Dependency Injection (DI)
* **Location:** All services in `services/` and game classes in `games/`
* **Purpose:** Services never instantiate their own dependencies (e.g., `BankService` receives `ConfigService`, `{Console}MemoryService`, `LogService`, `TranslationsService`, and `EventService` via `__init__`). This prevents circular imports, makes unit testing straightforward, and guarantees all services operate on the exact same in-memory `bytearray` game buffer.

#### 4. Data Transfer Object
* **Location:** `models/{console}/{series}/` (`UIKeyboardPatch`, `GameUIKeyboard`, `GameUIKeyboardLogic`, `CompiledBank`, `CompiledMap`, `CompiledEvent`)
* **Purpose:** Uses `@dataclass` to group complex offset arrays, byte buffers, and map metadata into lightweight, strongly typed objects, eliminating long parameter lists and reducing offset bugs.

#### 5. Strategy / Declarative Configuration (`UIKeyboardPatch`)
* **Location:** `services/{console}/{series}/keyboard_service.py`
* **Purpose:** The keyboard update methods (`_apply_main_keyboards  _patch` and `_apply_others_keyboard_patch`) contain zero hardcoded indices; instead, they execute against a declarative `UIKeyboardPatch` payload specifying which positions to remove, insert, null-pad (`0x00`), and relocate. This makes the algorithm reusable across uppercase, lowercase, and future game targets.

#### 6. Custom Decorators & Metaprogramming (`@when_enabled`, `@keys_from_str`)
* **Location:** `decorators/app_decorators.py`, `enums/{console}/{series}/{console}_{series}_enums.py`
* **Purpose:** Uses custom function decorators (`@when_enabled`, `@skip_when_enabled`, `@when_any_enabled`) to control when service methods run using config flags, keeping the main code clean without extra if checks. Additionally, `@keys_from_str` parses class docstrings to dynamically generate sequential `IntEnum` definitions (`{Console}{Series}KeyIndex`, `{Console}{Series}LogicKeyIndex`), preventing manual indexing errors.

#### 7. Factory Method (Deprecated)
* **Location:** `deprecated/factory_example.py`
* **Purpose:** Kept as a reference example showing the initial single-factory approach (`CurrentGameFactory`) prior to refactoring into the extensible Abstract Factory architecture.
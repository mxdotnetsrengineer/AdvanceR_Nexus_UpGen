# Objective
This repo is a showcase of how I write clean, scalable, and maintainable Python code in my day-to-day work. Beyond being a fun CLI tool (with a GUI on the way) to randomize and customize classic consoles game files. I am starting with GBA through simple JSON configs, the main goal here is to let recruiters and engineering teams easily review my coding style, architecture decisions, and handling of low-level binary data, all kept simple to run and explore.

# 🎮 AdvanceR Nexus UpGen
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=204769)
![Redis](https://img.shields.io/badge/Redis-3670A0?style=for-the-badge&logo=redis&logoColor=204769)
![gRPC](https://img.shields.io/badge/powered_by-gRPC-204769?labelColor=3670A0)
[![License: MIT](https://img.shields.io/badge/License-MIT-204769.svg?labelColor=3670A0)](https://opensource.org/licenses/MIT)

**AdvanceR Nexus UpGen** is a modular, extensible Python engine built to parse, reverse engineer and customize binary structures in classic game files. Designed to support multiple consoles and titles through declarative JSON configurations, the project kicks off with **Generation III Pokémon GBA** titles as its initial implementation. Featuring safe Pokéball item randomization via dynamic script repointing and full Spanish character support (`Ñ`, `ñ`, `¡`, `¿`) for in-game naming keyboards.

## 📑 Table of Contents
* [✨ Key Features](#-key-features)
* [🎯 Supported Games](#-supported-games)
* [🚀 Quick Start Guide](#-quick-start-guide)
  * [1. Create the Virtual Environment](#1-create-the-virtual-environment)
  * [2. Activate the Environment](#2-activate-the-environment)
  * [3. Execution](#3-execution)
    * [3.1 Interactive Console Menu (`ConsoleMenu`)](#31-interactive-console-menu-consolemenu)
    * [3.2 Adding a New Game](#32-adding-a-new-game)
* [📁 Project Structure](#-project-structure)
* [⚙️ Configuration Properties](#%EF%B8%8F-configuration-properties-config)
* [⚡ gRPC & Redis Caching](#-grpc--redis-caching)
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

* **Safe Pokéball Item Randomization (`EventsService` & `ItemService`):** Scans map events, inspects script opcodes to ensure the Pokéball holds an item rather than a starter Pokémon, generates new bytecode with a valid random item, and writes it into free space, while updating Game pointers.
* **Pokémon Base Stats & Difficulty-Based Wild Randomizer (`StatsService`, `BankService` & `EventsService`, `WildService` & `DifficultyService`):** Parses pokemon base stats, BST, types, abilities, and recursive evolution lines, then randomizes wild grass encounters using difficulty-scaled BST/evolution pools and dynamic level adjustments (`easy`, `normal`, `hard`, `inferno`).
* **Spanish UI & Internal Keyboard Customization (`{Console}KeyboardService`):** Restructures both visual layouts/spacings and logical character tables in game files, relocating `M`/`m` and inserting `Ñ`, `ñ`, `¡`, and `¿` without overflowing binary file boundaries.
* **Map Bank & Header Reverse Engineering (`BankService`):** Reads master binary pointer tables to reconstruct map hierarchies, map dimensions (`width x height`), decoded region names via game specific character tables (starting with Pokémon Gen III), and event counts.
* **Internationalization (`TranslationsService`):** Loads and flattens locale-specific JSON files (`ES_MX`, `EN_US`) for instant lookups.
* **Filterable Logging & Exception System (`LogService`):** Controls console output channels (`NONE`, `INFO`, `WARNING`, `ERROR`, `ERROR_AND_WARNING`, `ALL`) and raises dynamically mapped exceptions based on error keys.
* **Interactive Multi-Language Console Menu (`ConsoleMenu`):** Provides a responsive CLI interface (`tools/menu.py`) with real-time language switching (`EN_US` / `ES_MX`), screen clearing, and hotkey navigation (`ESC` to exit, `Backspace` / `0` to go back across steps).
* **Redis Binary Data Caching (`BaseGame` & `{Console}{Series}Game`):** Uses `redis.asyncio` to serialize and cache compiled map banks, species stats, and item tables for 1 hour (`ex=3600`), avoiding redundant files scans on consecutive runs.
* **Secure Async gRPC Server & Client (`grcp/`):** Exposes parsed game data (such as `GetAllItems` in `ItemsGrpcServicer`) over TLS (`grpc.aio.server`) using Protocol Buffers, supporting both server-loaded game and custom client-uploaded game files.

## 🎯 Supported Games

Currently, the engine supports the following **Game Boy Advance (Gen III)** titles via dedicated JSON configuration profiles:

| Platform | Game Title | Version / Base | Status | Supported Features | Extended Features |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GBA** | **Pokémon FireRed** | USA (v1.0 / v1.1) | ✅ Ready | Item Randomizer, Spanish Keyboard Patch, Wild Pokemon Randomizer, gRPC Services | BST-Scaled Wild Randomizer |
| **GBA** | **Pokémon Radical Red** | v4.1 (FireRed Base) | ✅ Ready | Item Randomizer, Spanish Keyboard Patch, Wild Pokemon Randomizer, gRPC Services | BST-Scaled Wild Randomizer |
| **GBA** | **Pokémon Emerald** | USA | ✅ Ready | Item Randomizer, Spanish Keyboard Patch | — |
| **GBA** | **Pokémon Emerald Kaizo** | Emerald USA Base | ✅ Ready | Item Randomizer, Spanish Keyboard Patch | — |

> 💡 **Interested in Extended Features?**  
> Features like the **BST-Scaled Wild Randomizer** are available for you. If you'd like to get access or learn more about the project, feel free to reach out at the email **[mexican.dotnet.senior.engineer@gmail.com](mailto:mexican.dotnet.senior.engineer@gmail.com)**.

<h3 align="center">
  ⚫ ⚫ ⚫
    <a href="#-table-of-contents" title="Back to Table of Contents">⬆️</a>
  ⚫ ⚫ ⚫
</h3>

## 🚀 Quick Start Guide

To ensure maximum performance and speed when managing Python environments, this project utilizes **`uv`**. *(Requires Python 3.11+, a local Redis server on `127.0.0.1:6379`, and dependencies listed in `requirements.txt`).*

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
2. Install dependencies (`uv pip install -r requirements.txt`) and ensure your local Redis instance is running.
3. Adjust your main toggles in `config/global_config.json` (and optionally enable `USE_FEATURE_FLAGS` to fine-tune specific pipeline steps in `config/{console}/{series}/feature_flags.json`).
4. Run `python main.py` and use the interactive `ConsoleMenu` to switch languages, launch the Randomizer, start the secure gRPC server, or run the gRPC test client:

#### 3.1 Interactive Console Menu (`ConsoleMenu`)
Running `python main.py` launches an interactive, multi-language terminal menu (`tools/menu.py`):

* **Execution Flows:** Launch the **Generator & Randomizer**, start the **Secure Async gRPC Server**, or run the **gRPC Client Test** (using either the server-loaded game or uploading a custom game file).
* **Live Locale Switching:** Switch between `EN_US` and `ES_MX` on the fly before selecting a game or execution mode.
* **Keyboard Navigation:** Supports instant `ESC` exit from any screen and `0` / `Backspace` multi-level back navigation.

> 📖 For a complete breakdown of menu flows, keyboard shortcuts, and translation keys, see the [Interactive Console Menu Reference](./readme/menu.md).

#### 3.2 Adding a New Game
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
* **`grcp/`** — Contains Protocol Buffer definitions (`protos/items.proto`), PowerShell compilation scripts (`compile_protos.ps1`), generated bindings (`generated/`), TLS certificates (`server.crt`, `server.key`), and async gRPC servicers (`servicers/items_servicer.py`).
* **`tools/`** — Interactive CLI utilities (`menu.py`, `user_selection.py`) powered by `AppsTranslations` (`translations/app_translations.py`) for multi-language terminal navigation.
* **Root Files (`main.py`, `settings.py`)** — `settings.py` loads the JSON configs (including optional `feature_flags.json`) and converts hex strings into integers at startup, while `main.py` acts as the entry point that calls `GamesProvider` to build and run the selected game.

<h3 align="center">
  ⚫ ⚫ ⚫
    <a href="#-table-of-contents" title="Back to Table of Contents">⬆️</a>
  ⚫ ⚫ ⚫
</h3>

## ⚙️ Configuration Properties (`config/`)

The system unifies global settings, game-specific binary layouts, and feature toggles at runtime via `init_global_config()` and `init_game_config()` (`settings.py`), automatically parsing hexadecimal strings (`0x...`) into integers:

* **`config/global_config.json`:** Global behavior toggles (`RANDOMIZE_POKEBALLS_ITEMS`, `ADD_SPANISH_CHARS`, `RANDOMIZE_WILD_POKEMON`, `ONLY_DATABASE`, `CURRENT_LANGUAGE`, `LOG_TYPE`).
* **`config/{console}/{series}/{game}_config.json`:** Title-specific pointer offsets, table sizes, and free-space boundaries. See the [FireRed Configuration Example](./readme/gba/pokemon/fire_red.md).
* **`config/{console}/{series}/feature_flags.json`:** Optional granular pipeline toggles (`ALLOCATE_BANKS`, `ALLOCATE_MAPS`, `MAPS_EVENTS`).

> 📖 For the full list of global keys and transient runtime state (`game_file`, `free_space_offset`), see the [Configuration Properties Reference](./readme/configuration.md).

<h3 align="center">
  ⚫ ⚫ ⚫
    <a href="#-table-of-contents" title="Back to Table of Contents">⬆️</a>
  ⚫ ⚫ ⚫
</h3>

## ⚡ gRPC & Redis Caching

To support external clients (such as upcoming GUIs) and eliminate redundant binary scans across consecutive runs, **AdvanceR Nexus UpGen** includes a transport and caching layer:

* **Secure Async gRPC (`grcp/`):** Exposes parsed binary structures (such as `GetAllItems` in `ItemsGrpcServicer`) over **HTTP/2 + TLS** (`grpc.aio.server`), supporting both server-loaded game files and dynamic client uploads.
* **Redis Caching (`redis.asyncio`):** Serializes and caches compiled map banks, species stats, and item tables (`game:{GAME_NAME}:*`) with a **1-hour TTL (`ex=3600`)**, reconstructing typed `@dataclass` models via `load_from_json()`.

> 📖 For Protobuf contracts, TLS setup, and cache deserialization details, see the [gRPC & Redis Architecture Reference](./readme/grpc_and_redis.md).


<h3 align="center">
  ⚫ ⚫ ⚫
    <a href="#-table-of-contents" title="Back to Table of Contents">⬆️</a>
  ⚫ ⚫ ⚫
</h3>

## 🏗️ Architecture & Design Patterns

When refactoring this codebase from procedural helper scripts into an extensible engine, I designed a **Layered Service-Oriented Architecture** with strict separation of concerns, keeping low-level binary manipulation completely decoupled from console and game specific rules.

```mermaid
flowchart TD
    subgraph Presentation ["1. Entry & Transport Layer"]
        CLI["ConsoleMenu<br/>(tools/menu.py)"]
        Client["gRPC Client / Future GUI"]
    end

    subgraph Core ["2. Orchestration & Factory Layer"]
        Main["main.py"]
        Config["settings.py<br/>(Global & Game Config)"]
        Provider["GamesProvider<br/>(Abstract Factory)"]
        GRPC["ItemsGrpcServicer<br/>(grpc.aio + TLS)"]
    end

    subgraph Domain ["3. Game Lifecycle & Cache"]
        Game["GBAPokemonGame<br/>(Template Method)"]
        Redis[("Redis Cache<br/>(1h TTL)")]
    end

    subgraph Services ["4. Domain & Binary Services"]
        DomainSvc["Bank / Wild / Item / Stats / Events / Keyboard"]
        Memory["GBAMemoryService<br/>(Pointers & Structs)"]
        GameFile[("Game File<br/>(bytearray)")]
    end

    CLI --> Main
    Client -->|HTTP/2 + Protobuf| GRPC
    Main --> Config
    Main --> Provider
    GRPC --> Provider
    Provider --> Game
    Game <-->|mget / pipeline| Redis
    Game --> DomainSvc
    DomainSvc --> Memory
    Memory --> GameFile
```

### System Layers
1. **Entry, CLI & Transport Layer (`main.py`, `tools/`, `grcp/`, `settings.py`):** Loads global and game-specific JSON configs (`init_global_config` / `init_game_config`), drives user interaction through `ConsoleMenu`, and exposes game services via TLS-secured `grpc.aio` endpoints or local execution.
2. **Core Factory & Domain Layer (`games/core/`, `games/`):** Uses `GamesProvider` and `{Console}{Series}CoreFactory` to assemble platform service families, while `BaseGame`, `{Console}Game`, and `{Console}{Series}Game` define the game execution lifecycle for concrete titles (`FireRedGame`, `EmeraldGame`).
3. **Service Layer (`services/`):** Encapsulates all business logic and binary operations split by technical domain (`{Console}MemoryService`, `BankService`, `EventsService`, `ItemService`, `StatsService`, `{Console}KeyboardService`) alongside cross-cutting infrastructure services (`ConfigService`, `LogService`, `TranslationsService`, `FileService`).
4. **Models & Data Layer (`models/`, `enums/`, `helpers/`):** Provides strongly typed data structures (`@dataclass`), enumerations, and hexadecimal lookup tables free of side effects.

<h3 align="center">
  ⚫ ⚫ ⚫
    <a href="#-table-of-contents" title="Back to Table of Contents">⬆️</a>
  ⚫ ⚫ ⚫
</h3>

### Design Patterns Used

* **Abstract Factory & Provider (`games/core/`):** Decouples game instantiation and platform service assembly from `main.py` (`GamesProvider`, `GBAPokemonCoreFactory`).
* **Template Method (`games/`):** Defines the shared async execution pipeline in `GBAPokemonGame.process_game()` while delegating title-specific hooks to subclasses (`FireRedGame`, `EmeraldGame`).
* **Constructor Dependency Injection (`services/`):** Injects shared services and the in-memory `bytearray` game buffer without tight coupling.
* **Data Transfer Object (`models/`):** Represents parsed banks, maps, events, stats, and items as strongly typed `@dataclass` payloads.
* **Strategy / Declarative Patching (`UIKeyboardPatch`):** Drives keyboard layout transformations from declarative data structures rather than hardcoded indices.
* **Custom Decorators & Metaprogramming (`decorators/`):** Controls pipeline steps via config flags (`@when_enabled`, `@skip_when_enabled`) and generates `IntEnum` definitions dynamically (`@keys_from_str`).

> 📖 For detailed locations, rationale, and architectural trade-offs for each pattern, see the [Design Patterns & Architecture Deep Dive](./readme/architecture.md).

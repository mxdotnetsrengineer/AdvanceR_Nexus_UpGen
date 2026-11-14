# Objective
This repo is a showcase of how I write clean, scalable, and maintainable Python code in my day-to-day work. Beyond being a fun CLI tool (with a GUI on the way) to randomize and customize classic GBA game files through simple JSON configs, the main goal here is to let recruiters and engineering teams easily review my coding style, architecture decisions, and approach to binary reverse engineering—no overly complex setup required.

# 🎮 AdvanceR Nexus UpGen

**AdvanceR Nexus UpGen** is a modular, extensible Python engine built to parse, reverse engineer, and customize binary structures in classic game files. Designed to support multiple consoles and titles through declarative JSON configurations, the project kicks off with **Generation III Pokémon GBA** game files (**Pokémon FireRed** and **Pokémon Radical Red v4.1**) as its initial implementation—featuring safe Pokéball item randomization via dynamic script repointing and full Spanish character support (`Ñ`, `ñ`, `¡`, `¿`) for in-game naming keyboards.

---

## ✨ Key Features

* **Safe Pokéball Item Randomization (`EventService` & `ItemService`):** Scans map events, inspects script opcodes to ensure the Pokéball holds an item rather than a starter Pokémon, generates new bytecode with a valid random item, and writes it into free space, while updating Game pointers.
* **Spanish UI & Internal Keyboard Customization (`GBAKeyboardService`):** Restructures both visual layouts/spacings and logical character tables in *FireRed*-based game files, relocating `M`/`m` and inserting `Ñ`, `ñ`, `¡`, and `¿` without overflowing binary file boundaries.
* **Map Bank & Header Reverse Engineering (`BankService`):** Reads master binary pointer tables to reconstruct map bank hierarchies, map dimensions (`width x height`), decoded region names via Gen III character tables, and event counts.
* **Internationalization (`TranslationsService`):** Loads and flattens locale-specific JSON files (`ES_MX`, `EN_US`) for instant lookups.
* **Filterable Logging & Exception System (`LogService`):** Controls console output channels (`NONE`, `INFO`, `WARNING`, `ERROR`, `ERROR_AND_WARNING`, `ALL`) and raises dynamically mapped exceptions based on error keys.

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
2. Adjust your toggles in `config/global_config.json`.
3. Select the target game in `main.py` using `AvailableGames` (e.g., `AvailableGames.ORIGINAL_FIRE_RED` or `AvailableGames.RADICAL_FIRE_RED`) and run:
```bash
python main.py
```

---

## 📁 Project Structure

The repository is organized by layers and platform domains so new consoles, games, and features can scale independently:

* **`config/`** — Stores declarative JSON configurations split between global runtime flags (`global_config.json`) and console/game-specific binary layouts (`config/gba/pokemon/`), allowing new titles to be supported without modifying core logic.
* **`enums/`** — Centralizes strongly typed enumerations for supported titles, languages, logging channels, and dynamically generated keyboard index mappings.
* **`games/`** — Contains the domain execution layer, including the factory (`CurrentGameFactory`), the abstract console base (`GBAGame`), and concrete game workflows (`FireRedGame`).
* **`helpers/`** — Holds static reference tables (such as Gen III byte-to-character mappings), original keyboard matrices, and internal exception-type lookup dictionaries.
* **`models/`** — Defines lightweight `@dataclass` Data Transfer Objects (DTOs) that represent parsed map banks, map headers, overworld events, and declarative keyboard update payloads.
* **`translations/`** — Houses locale-specific JSON files (`EN_US/`, `ES_MX/`) consumed by the internationalization engine to decouple user-facing messages from business logic.
* **`services/`** — The core business and infrastructure engine of the application, split into cross-cutting utilities and platform-specific binary handlers:
  * **`config_service.py` (`ConfigService`):** Provides a centralized, clean interface for querying merged runtime configuration values across the application.
  * **`file_service.py` (`FileService`):** Handles safe binary I/O operations for loading clean game files into memory and writing customized outputs to disk.
  * **`log_service.py` (`LogService`):** Manages channel-filtered console output (`INFO`, `WARNING`, `ERROR`, etc.), stores runtime log history, and raises dynamically mapped exceptions.
  * **`translations_service.py` (`TranslationsService`):** Loads, merges, and flattens locale JSON files for instant multi-language string resolution.
  * **`gba/memory_service.py` (`GBAMemoryService`):** Translates Little-Endian GBA memory pointers into raw file offsets and tracks available free space for safe binary injection.
  * **`gba/pokemon/bank_service.py` (`BankService`):** Parses master pointer tables to reverse engineer map bank hierarchies, map dimensions, and decoded region names.
  * **`gba/pokemon/event_service.py` (`EventService`):** Inspects overworld map events, filters item Pokéballs via script opcodes, and repoints them to newly allocated script bytecode.
  * **`gba/pokemon/item_service.py` (`ItemService`):** Decodes in-game item names from binary tables and generates valid script bytecode with randomized item IDs.
  * **`gba/pokemon/keyboard_service.py` (`GBAKeyboardService`):** Rebuilds both visual UI layouts and logical character byte arrays to inject Spanish characters (`Ñ`, `ñ`, `¡`, `¿`) into naming keyboards.
* **Root Files (`main.py`, `settings.py`)** — `settings.py` loads and converts hexadecimal JSON values into integers at startup, while `main.py` serves as the clean entry point that triggers the factory and runs the selected game workflow.

---

## ⚙️ Configuration Properties (`config/`)

The system dynamically unifies global configurations, game-specific layouts, and randomizer flags at runtime via `init_global_config()`. Hexadecimal string values (properties starting with `0x`) are automatically converted into integers internally to streamline raw binary operations.

### 1. Global Config Properties (`config/global_config.json`)
Establishes logical rules, output behavior, and localization switches enforced across all supported games:

* **`RANDOMIZE_POKEBALLS_ITEMS`** (`bool`): Toggles whether items lying visibly inside overworld Pokéballs on the ground should be randomized.
* **`ADD_SPANISH_CHARS`** (`bool`): When `true`, updates the naming screen UI and logical keyboards to include Spanish characters (`Ñ`, `ñ`, `¡`, `¿`).
* **`ONLY_DATABASE`** (`bool`): When `true`, runs map bank and item reverse engineering in read-only mode without altering or saving a new output game file.
* **`CURRENT_LANGUAGE`** (`str`): Sets the active locale code for console logs and error messages (`"ES_MX"` or `"EN_US"`).
* **`LOG_TYPE`** (`str`): Controls which message channels print to the console (`"NONE"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"ERROR_AND_WARNING"`, or `"ALL"`).

---

### 2. Game JSON Properties (e.g., `config/gba/pokemon/fire_red_config.json`)
Maps the static physical offsets, pointers, and structural metrics embedded inside the original target game file:

#### Identification & File Paths
* **`GAME_NAME`** (`str`): Descriptive title and file size displayed in initialization logs (e.g., `"Pokemon FireRed (16MB)"`).
* **`ORIGINAL_GAME`** (`str`): Exact filename of the clean input `.gba` game file located in the root directory.
* **`MODIFIED_GAME`** (`str`): Designated output filename for the updated/randomized `.gba` game file.

#### Memory Management & Free Space
* **`MAX_ROM_SIZE`** (`hex str`): Maximum allowed file size limit in bytes for the game binary.
* **`FREE_SPACE_START`** (`hex str`): Starting file offset where unused padding (bytes filled with `0xFF`) is safe to overwrite with newly generated scripts. `GBAMemoryService` tracks `free_space` dynamically from this address so consecutive binary writes never overlap.

#### Map Banks & Map Names
* **`BANK_TABLE_OFFSET`** (`hex str`): Hardcoded physical file offset pointing directly to the root master map bank table.
* **`BANK_TABLE_BANKS_POSITION`** (`int`): Index within the root master table holding the primary pointer to the active map bank list.
* **`MAP_NAMES_TABLE_OFFSET`** (`hex str`): Internal pointer table offset mapping out the text addresses for region/location names.
* **`REGION_MAP_BYTE`** (`int`): Byte offset within each map header (`map_header`) where the `regionMapSectionId` (map name ID) is stored.
* **`GAME_START`** (`hex str`): Base index shift for map names in the text table (e.g., `0x58` aligns entry `0` with *Pallet Town* in *FireRed*).
* **`BANKS_TO_PRINT`** (`int`): Upper limit of map banks the parser loop iterates through during reverse engineering.
* **`MAPS_PER_BANK_TO_PRINT`** (`int`): Maximum number of individual maps evaluated sequentially per bank.

#### Items & Pokéball Events
* **`ITEMS_POINTER_OFFSET`** (`hex str`): File address containing the master pointer to the global item structure table.
* **`ITEM_STRUCT_SIZE`** (`int`): Structural size in bytes occupied by a single item entry inside the GBA memory layout (`44` bytes in Gen III).
* **`MAX_ITEM_ID`** (`int`): Maximum upper index boundary for valid item IDs eligible for randomization (`374` in vanilla *FireRed*; `748` in *Radical Red*).
* **`POKEBALL_SPRITE_ID`** (`int`): Overworld sprite index (`92`) assigned to visible Pokéball items sitting on floor maps.

#### UI & Logical Keyboards
* **`CHARACTER_BYTE_SIZE`** (`int`): Number of bytes per character row/block in the game's naming screen structure.
* **`DEFAULT_UI_KEYBOARD_SEPARATORS`** (`list[str]`): Sequence of hexadecimal control bytes (e.g., `["0xFC", "0x11"]`) preceding each character in the visual table to define spacing and layout formatting.
* **`UPPER_KEYBOARD_CHARS_OFFSET`** (`hex str`): Physical file offset where the uppercase (`A-Z`) logical character array begins.
* **`LOWER_KEYBOARD_CHARS_OFFSET`** (`hex str`): Physical file offset where the lowercase (`a-z`) logical character array begins.
* **`OTHERS_KEYBOARD_CHARS_OFFSET`** (`hex str`): Physical file offset where the numbers and punctuation (`0-9`, `!`, `?`, etc.) logical character array begins.

---

## 🛠️ Custom Dynamic Values

During initialization and execution, the system manages transient runtime state inside `GBAMemoryService` and `current_config` rather than persisting them in static JSON files:

* **`game_file`** (`bytearray`): Loaded in memory by `FileService.open_game()` inside `GBAGame.__init__`, caching the ongoing customized game byte sequence prior to dumping it to the output `.gba` file.
* **`free_space`** (`int`): Initially shadows the address provided in `FREE_SPACE_START`. As `EventService` writes randomized Pokéball scripts, this offset updates as a **self-incrementing dynamic pointer** to ensure consecutive binary writes never overlap or corrupt existing data.
* **`available_language`** (`bool`): Set inside `current_config` by `init_global_config()` to flag whether the requested `CURRENT_LANGUAGE` is natively supported (`ES_MX` / `EN_US`) or fell back to English.

---

## 🏗️ Architecture & Design Patterns

When refactoring this codebase from procedural helper scripts into an extensible engine, I designed a **Layered Service-Oriented Architecture** with strict separation of concerns, keeping low-level binary manipulation completely decoupled from console and game-specific rules.

### System Layers
1. **Entry & Configuration Layer (`main.py`, `settings.py`):** Initializes the application, merges `global_config.json` with game-specific JSON layouts, converts hexadecimal strings to integers, and delegates instantiation to the factory.
2. **Domain / Game Layer (`games/`):** Defines the game processing lifecycle (`GBAGame`) and concrete game workflows (`FireRedGame`), structured by platform (`games/gba/`) so new consoles can be added cleanly.
3. **Service Layer (`services/`):** Encapsulates all business logic and binary operations split by technical domain (`GBAMemoryService`, `BankService`, `EventService`, `ItemService`, `GBAKeyboardService`) alongside cross-cutting infrastructure services (`ConfigService`, `LogService`, `TranslationsService`, `FileService`).
4. **Models & Data Layer (`models/`, `enums/`, `helpers/`):** Provides strongly typed data structures (`@dataclass`), enumerations, and hexadecimal lookup tables free of side effects.

---

### Design Patterns Used

#### 1. Factory Method (`CurrentGameFactory`)
* **Location:** `games/current_game.py`
* **Purpose:** Centralizes the instantiation and dependency wiring of concrete game classes (`FireRedGame`, etc.) based on the `AvailableGames` enum. `main.py` stays completely decoupled from how services are constructed or injected.

#### 2. Constructor Dependency Injection (DI)
* **Location:** All services in `services/` and game classes in `games/`
* **Purpose:** Services never instantiate their own dependencies (e.g., `BankService` receives `ConfigService`, `GBAMemoryService`, `LogService`, `TranslationsService`, and `EventService` via `__init__`). This prevents circular imports, makes unit testing straightforward, and guarantees all services operate on the exact same in-memory `bytearray` game buffer.

#### 3. Template Method (`GBAGame`)
* **Location:** `games/gba/gba_game.py`
* **Purpose:** The abstract base class `GBAGame` defines the shared initialization skeleton (loading the game file into `memory_service.game_file` and exposing `_get_value()`) while enforcing subclasses to implement the abstract `process_game()` hook with game-specific customization steps.

#### 4. Data Transfer Object (DTO)
* **Location:** `models/gba/pokemon/` (`UIKeyboardPatch`, `GameUIKeyboard`, `GameUIKeyboardLogic`, `CompiledBank`, `CompiledMap`, `CompiledEvent`)
* **Purpose:** Uses `@dataclass` to group complex offset arrays, byte buffers, and map metadata into lightweight, strongly typed objects—eliminating long parameter lists and reducing off-by-one offset bugs.

#### 5. Strategy / Declarative Configuration (`UIKeyboardPatch`)
* **Location:** `services/gba/pokemon/keyboard_service.py`
* **Purpose:** The keyboard update methods (`_apply_main_keyboards_patch` and `_apply_others_keyboard_patch`) contain zero hardcoded indices; instead, they execute against a declarative `UIKeyboardPatch` payload specifying which positions to remove, insert, null-pad (`0x00`), and relocate. This makes the algorithm reusable across uppercase, lowercase, and future game targets.

#### 6. Metaprogramming / Enum Class Decorator (`@keys_from_str`)
* **Location:** `enums/gba/pokemon/fire_red_enums.py`
* **Purpose:** Uses a custom class decorator that parses the visual layout docstring (`__doc__`) to dynamically generate sequential `IntEnum` definitions (`FireRedKeyIndex`, `FireRedLogicKeyIndex`), preventing human calculation errors when indexing keys and spaces.
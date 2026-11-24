# 🏗️ Design Patterns & Architecture Deep Dive

**AdvanceR Nexus UpGen** is structured as a **Layered Service-Oriented Architecture** that isolates low-level binary manipulation (`struct`, memory pointers, free-space allocation) from console rules and external transport layers.

## Design Patterns Used

### 1. Abstract Factory & Factory Provider
* **Location:** `games/core/games_core.py`, `games/core/{console}_{series}_core.py`, `games/core/games_provider.py`
* **Purpose:** `GamesProvider` selects the concrete factory (`GBAPokemonCoreFactory`) based on `AvailableGames`, assembling entire families of platform services (`GBAMemoryService`, `BankService`, `EventsService`, `ItemService`, `StatsService`, `WildService`, `GBAKeyboardService`) and loading the game buffer before instantiating the game. This keeps `main.py` decoupled from object creation and simplifies adding new consoles.

### 2. Template Method
* **Location:** `games/base_game.py`, `games/{console}/{series}/{console}_{series}_game.py`
* **Purpose:** `GBAPokemonGame` defines the shared asynchronous processing skeleton inside `process_game()` (concurrently allocating banks and parsing species/items via `asyncio.gather`, applying bank/event/wild modifications, patching Spanish keyboards, and saving the output file) while exposing `_apply_game_specific_changes()` for subclass customization (`FireRedGame`, `EmeraldGame`).

### 3. Constructor Dependency Injection (DI)
* **Location:** All services in `services/` and game classes in `games/`
* **Purpose:** Services receive their dependencies (`ConfigService`, `GBAMemoryService`, `LogService`, `TranslationsService`) via `__init__` rather than instantiating them internally, preventing circular imports and ensuring every service operates on the same in-memory `bytearray` buffer.

### 4. Data Transfer Object (DTO)
* **Location:** `models/{console}/{series}/` (`UIKeyboardPatch`, `GameUIKeyboard`, `GameUIKeyboardLogic`, `CompiledBank`, `CompiledMap`, `CompiledEvent`, `CompiledBaseStats`, `CompiledItem`, `CompiledWildEvents`)
* **Purpose:** Uses `@dataclass` models with `dict_to_class()` deserializers to represent parsed binary structures and Redis cache payloads cleanly.

### 5. Strategy / Declarative Configuration (`UIKeyboardPatch`)
* **Location:** `services/{console}/{series}/keyboard_service.py`
* **Purpose:** Keyboard patch routines execute against a declarative `UIKeyboardPatch` payload specifying indices to remove, insert, null-pad (`0x00`), and relocate, avoiding hardcoded offsets.

### 6. Custom Decorators & Metaprogramming (`@when_enabled`, `@keys_from_str`)
* **Location:** `decorators/app_decorators.py`, `enums/{console}/{series}/{console}_{series}_enums.py`
* **Purpose:** Wraps both sync and `async` service methods (`inspect.iscoroutinefunction`) to toggle execution steps via config flags (`@when_enabled`, `@skip_when_enabled`, `@when_any_enabled`), while `@keys_from_str` dynamically generates sequential `IntEnum` classes from docstrings.

### 7. Factory Method (Deprecated)
* **Location:** `deprecated/factory_example.py`
* **Purpose:** Preserved as an architectural reference illustrating the initial single-factory implementation (`CurrentGameFactory`) prior to migrating to Abstract Factory.

### 8. Facade Pattern
* **Location:** `facades/base_facade.py`, `facades/items_facade.py`, `facades/config_facade.py`
* **Purpose:** Provides a unified entry point for transport layers (FastAPI routers and gRPC servicers) to validate uploaded ROM files, check file size/name constraints, resolve isolated game configurations via `GamesProvider`, and execute synchronous binary parsers off the event loop (`asyncio.to_thread`).

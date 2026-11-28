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

### 6. Custom Decorators (`@when_enabled`, `@skip_when_enabled`, `@when_any_enabled`)
* **Location:** `decorators/app_decorators.py`
* **Purpose:** Wraps both sync and `async` service methods (`inspect.iscoroutinefunction`) to toggle execution steps via config flags (`self.config` or `self.config_service`), supporting `fallback_factory` callables (e.g., `list`) so disabled features preserve return type contracts

### 7. Value Object (`DifficultyConfig`, `DifficultyGroup`, `GameInput`)
* **Location:** `models/difficulty_config.py`, `models/difficulty_group.py`, `models/game_input.py`
* **Purpose:** Encapsulates domain parameters as strongly typed, read-only structures defined by their attribute values rather than identity, replacing raw dictionary lookups across services and transport layers.

### 8. Cache-Aside Pattern (`ItemsFacade`, `GBAPokemonGame`, `FileService`)
* **Location:** `facades/items_facade.py`, `games/gba/pokemon/gba_pokemon_game.py`, `services/file_service.py`
* **Purpose:** Queries Redis (`SHA-256` ROM hash + locale keys) or in-memory `lru_cache` (`mtime_ns`/size keys) before reading the binary ROM; on cache misses, parses the data on a worker thread and populates the cache for subsequent requests.

### 9. Middleware Pipeline & Dependency Injection (`api/middlewares/`, `api/dependencies/`)
* **Location:** `api/middlewares/app_middlewares.py`, `api/dependencies/game_dependencies.py`, `api/app.py`
* **Purpose:** Processes HTTP requests through a composable pipeline (timing metrics, security headers, CORS) and injects validated, chunk-bounded `GameInput` payloads and domain facades into route handlers via FastAPI's `Depends` container.

### 11. Facade Pattern
* **Location:** `facades/base_facade.py`, `facades/items_facade.py`, `facades/config_facade.py`
* **Purpose:** Provides a unified entry point for transport layers (FastAPI routers and gRPC servicers) to validate uploaded ROM files, check file size/name constraints, resolve isolated game configurations via `GamesProvider`, and execute synchronous binary parsers off the event loop (`asyncio.to_thread`).

### 12. Factory Method (Deprecated)
* **Location:** `deprecated/factory_example.py`
* **Purpose:** Preserved as an architectural reference illustrating the initial single-factory implementation (`CurrentGameFactory`) prior to migrating to Abstract Factory.

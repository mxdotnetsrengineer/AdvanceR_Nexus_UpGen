# 📁 Project Structure Reference

**AdvanceR Nexus UpGen** follows a **Layered Service-Oriented Architecture** organized by domain boundaries and transport layers. Each directory has a single responsibility so new consoles, titles, and APIs can be added without modifying existing engine logic.

## 1. Transport & Orchestration Layers

* **`api/`** — REST HTTP API built with FastAPI:
  * **`app.py` (`create_app`):** Application factory that initializes shared services, wires facade dependency overrides, registers middlewares, and mounts routers.
  * **`routers/` (`items_router.py`, `config_router.py`):** Exposes endpoints (`POST /gba/pokemon/items`, `PATCH /config/language`) and maps domain models to Pydantic responses.
  * **`schemas/` (`items_schema.py`, `config_schema.py`):** Pydantic request/response contracts and API-level `StrEnum` selections (`LanguageSelection`).
  * **`dependencies/` (`game_dependencies.py`):** Extracts multipart form fields (`game`, `game_file`) and `app_language` cookies into `GameInput` DTOs.
  * **`middlewares/` (`app_middlewares.py`):** Attaches execution metrics such as the `X-Process-Time` response header.
* **`exceptions/`** — Shared domain error contracts and HTTP translators:
  * **`domain_exceptions.py` & `exception_handlers.py`:** Defines domain exceptions (`DomainValidationError`, `ResourceNotFoundError`, `RomPreconditionError`) shared by REST and gRPC, plus FastAPI HTTP status handlers (`400`, `404`, `412`, `500`).
* **`facades/`** — Unified application facades shared across REST and gRPC transports:
  * **`base_facade.py` (`BaseGameFacade`):** Handles in-memory ROM validation, empty-file checks, filename verification against `ORIGINAL_GAME`, and `MAX_ROM_SIZE` enforcement.
  * **`items_facade.py` (`ItemsFacade`):** Resolves the target game via `GamesProvider` and offloads synchronous binary item extraction to worker threads via `asyncio.to_thread`.
  * **`config_facade.py` (`ConfigFacade`):** Generates localized confirmation messages and cookie expiration metadata (`LANGUAGE_COOKIE_MAX_AGE`).
* **`grpc_files/`** — Binary RPC layer over HTTP/2 + TLS:
  * **`protos/` & `compile_protos.ps1`:** Protocol Buffer definitions (`items.proto`) and PowerShell compilation script.
  * **`generated/`:** Auto-generated Python protobuf and gRPC stub modules (`items_pb2.py`, `items_pb2_grpc.py`).
  * **`servicers/` (`items_servicer.py`):** Async `ItemsGrpcServicer` delegating `GetAllItems` requests through `ItemsFacade` and translating exceptions to gRPC status codes.
  * **`grpc_server.py` (`run_grpc`, `test_grpc`):** Configures and starts the async TLS gRPC server (`port 50051`) and provides the secure client test runner.

## 2. Core Domain & Game Factories

* **`games/`** — Game lifecycle definitions and Abstract Factory builders:
  * **`base_game.py` (`BaseGame`):** Abstract base class defining the execution contract (`process_game()`) and optional async Redis client injection.
  * **`core/` (`GamesProvider`, `GamesCore`, `{Console}{Series}CoreFactory`):** Assembles platform-specific service families, loads ROM bytes (from disk or memory), and instantiates concrete game classes.
  * **`{console}/` (`{Console}Game`, `{Console}{Series}Game`, `FireRedGame`, `EmeraldGame`):** Implements the **Template Method** pattern for shared Gen III randomization, Redis caching (`__load_from_cache` / `__save_to_cache`), and title-specific overrides.
* **`services/`** — Core infrastructure and console-specific binary handlers:
  * **`config_service.py` (`ConfigService`):** Loads isolated global (`load_global()`) and game configurations (`load_for_game()`) with recursive `BASE_CONFIG` inheritance, circular-loop detection, and automatic `0x` hex-to-int parsing.
  * **`file_service.py` (`FileService`):** Resolves paths relative to project root and performs safe binary ROM reads and writes.
  * **`log_service.py` (`LogService`):** Filters console output by verbosity level (`NONE`, `INFO`, `WARNING`, `ERROR`, `ERROR_AND_WARNING`, `ALL`) and stores execution logs.
  * **`error_service.py` (`ErrorService`):** Translates localized error keys, records them via `LogService`, and raises typed `DomainException` subclasses.
  * **`translations_service.py` (`TranslationsService`):** Loads, caches, and flattens locale JSON dictionaries (`EN_US`, `ES_MX`) with dynamic variable interpolation.
  * **`{console}/memory_service.py` (`{Console}MemoryService`):** Converts GBA memory pointers (`0x08000000` range) to file offsets, unpacks Little Endian structs, and scans word-aligned `0xFF` free space.
  * **`gba/pokemon/` (Domain Services):** Binary parsers and randomizers (`BankService`, `EventsService`, `ItemService`, `StatsService`, `WildService`, `DifficultyService`, `GBAKeyboardService`). See the [GBA Pokémon Services Reference](./gba/pokemon/gba_pokemon_services.md).

## 3. Configuration, Data Models & Tooling

* **`config/`** — Declarative JSON configurations split into `global_config.json`, `options/`, and console/series layouts (`config/gba/pokemon/`) supporting `BASE_CONFIG` inheritance and `feature_flags.json`.
* **`translations/`** — Localized JSON dictionaries (`EN_US/`, `ES_MX/`) separating user-facing messages, menu labels, warnings, and errors from business logic.
* **`models/`** — Lightweight `@dataclass` Data Transfer Objects (`GameInput`, `CompiledBank`, `CompiledMap`, `CompiledEvent`, `CompiledBaseStats`, `CompiledItem`, `CompiledWildEvents`, `UIKeyboardPatch`).
* **`enums/`** — Strongly typed enumerations (`AvailableGames`, `GameSelection`, `AvailableLanguages`, `LogLevels`, item pockets/subcategories, and keyboard index enums).
* **`decorators/`** — Reusable decorators (`app_decorators.py`) for config-driven feature toggling (`@when_enabled`, `@skip_when_enabled`, `@when_any_enabled`) and dynamic `IntEnum` generation (`@keys_from_str`).
* **`helpers/`** — Static lookup tables, Gen III byte-to-character mappings, original keyboard matrices, and log channel mappings.
* **`tools/`** — Interactive terminal UI (`menu.py`, `user_selection.py`) powered by `TranslationsService` for multi-language CLI navigation.
* **`tests/`** — Automated `pytest` suite (`conftest.py`, `unit/test_memory.py`, `unit/test_facades.py`, `integration/test_config_router.py`) covering binary pointer math, Gen III string decoding, facade validations, and FastAPI cookie endpoints.
* **`examples/`** — Standalone client usage scripts for testing the REST API (`examples/api/items.py`) and gRPC service (`examples/grpc/items.py`).
* **`deprecated/`** — Preserves early architectural iterations (`factory_example.py`) for historical reference without impacting active code.
* **Root Entry Point (`main.py`)** — Bootstraps `ConfigService.load_global()` and routes execution across `ConsoleMenu`, the local Randomizer (`run_randomizer`), the FastAPI REST server (`run_fastapi`), the secure gRPC server/clients (`run_grpc`, `test_grpc`), and the Pytest runner (`run_tests`).


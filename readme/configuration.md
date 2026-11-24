# ⚙️ Configuration Properties Reference

**AdvanceR Nexus UpGen** manages configuration through isolated `ConfigService` instances (`services/config_service.py`) instead of global mutable state:
1. `ConfigService.load_global()` — Loads `config/global_config.json` and `config/options/options_config.json` at startup.
2. `ConfigService.load_for_game(game_key, language)` — Recursively resolves `BASE_CONFIG` inheritance (e.g., `emerald_kaizo` -> `emerald`, `radical_red` -> `fire_red`), merges difficulty profiles, and applies optional feature flags.

All string values prefixed with `0x` are automatically parsed into base-16 integers via `_parse_hex_values()`.

## 1. Global Config Properties (`config/global_config.json`)

* **`RANDOMIZE_POKEBALLS_ITEMS`** (`bool`): Toggles whether items lying visibly inside overworld Pokéballs on the ground should be randomized.
* **`ADD_SPANISH_CHARS`** (`bool`): When `true`, updates the naming screen UI and logical keyboards to include Spanish characters (`Ñ`, `ñ`, `¡`, `¿`).
* **`ONLY_DATABASE`** (`bool`): When `true`, runs map bank and item reverse engineering in read-only mode without altering or saving a new output game file.
* **`CURRENT_LANGUAGE`** (`str`): Sets the active locale code for console logs and error messages (`"ES_MX"` or `"EN_US"`).
* **`LOG_TYPE`** (`str`): Controls which message channels print to the console (`"NONE"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"ERROR_AND_WARNING"`, or `"ALL"`).
* **`USE_FEATURE_FLAGS`** (`bool`): When `true`, loads extra feature toggles from `config/{console}/{series}/feature_flags.json` (`ALLOCATE_BANKS`, `ALLOCATE_MAPS`, `MAPS_EVENTS`).
* **`RANDOMIZE_WILD_POKEMON`** (`bool`): Toggles whether wild grass Pokémon encounters are randomized based on the selected difficulty profile.
* **`INCLUDE_MEGA_EVOLUTIONS`** (`bool`): When `true`, includes Mega Evolutions when parsing evolution lines and building species data.
* **`GRPC_CERT_PATH` / `GRPC_KEY_PATH`** (`str`): Relative or absolute paths to the TLS certificate and private key used by the gRPC server (`grpc_files/server.crt`, `grpc_files/server.key`).
* **`REDIS_HOST` / `REDIS_PORT` / `REDIS_DB`** (`str` / `int`): Connection parameters for the async Redis cache client (`"127.0.0.1"`, `6379`, `0`).
* **`LANGUAGE_COOKIE_MAX_AGE`** (`int`): Expiration time in seconds for the HTTP-only `app_language` cookie set by the FastAPI `/config/language` endpoint (default `604800` / 7 days).

## 2. Transient Runtime State

During initialization and execution, the system manages transient state in memory rather than persisting it to JSON files:

* **`game_file`** (`bytearray`): Loaded by `FileService.open_game()` inside `{Console}{Series}CoreFactory._create_memory_service()`. Holds the modified binary buffer before writing it to disk.
* **`free_space_offset`** (`int`): Starts at `FREE_SPACE_START`. Whenever a service injects new bytecode (such as `EventsService` writing randomized Pokéball scripts), this pointer advances automatically so consecutive writes never overlap.
* **`available_language`** (`bool`): Set inside `current_config` by `init_global_config()` to indicate whether `CURRENT_LANGUAGE` is natively supported (`ES_MX` / `EN_US`).

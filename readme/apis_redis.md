# ⚡ gRPC & Redis Caching Architecture

To support external frontends (such as upcoming desktop or web GUIs) and avoid re-scanning unchanged binary files across consecutive runs, **AdvanceR Nexus UpGen** provides an async TLS gRPC API and a Redis caching layer.

## 1. Secure Async gRPC Server (`grpc_files/`)

The server runs on `grpc.aio.server` over **HTTP/2 + TLS** on port `50051` with a `48MB` message size limit (`MAX_MESSAGE_LENGTH`) to accommodate full 16MB and 32MB GBA game payloads.

### Protobuf Contract (`grpc_files/protos/items.proto`)
* **`ItemsService.GetAllItems`:** Unary RPC accepting `GetAllItemsRequest` (`bytes game_file`, `optional int32 game_id`) and returning `GetAllItemsResponse` (`map<int32, CompiledItemProto>`).
* **Operating Modes (`grpc_files/servicers/items_servicer.py`):**
  1. **Server-Loaded Game File:** When `game_file` is omitted, queries the game buffer already loaded in memory on the server.
  2. **Client Game File Override:** When `game_file` and `game_id` are provided, initializes that title's configuration via `GamesProvider` and parses the uploaded bytes on demand.

### Local Setup Commands
1. **Compile `.proto` definitions (PowerShell):**
   ```powershell
   .\grpc_files\compile_protos.ps1
   ```
2. **Do not forget to generate local TLS credentials (`grpc_files/server.crt` & `grpc_files/server.key`):**

## 2. Redis Binary Data Caching (`redis.asyncio`)

`BaseGame` (`games/base_game.py`) initializes an async Redis client (`127.0.0.1:6379`) to cache compiled binary structures extracted from unmodified game files:

* **Cache Keys & Expiration:** Stores serialized JSON arrays under `game:{GAME_NAME}:banks`, `game:{GAME_NAME}:stats`, and `game:{GAME_NAME}:items` with a **1-hour TTL (`ex=3600`)**.
* **Fast DTO Deserialization (`dict_to_class`):** On subsequent runs, `GBAPokemonGame` queries all three keys via `mget` inside `__load_from_cache()` (and persists newly parsed data via `__save_to_cache()`), reconstructing typed `@dataclass` hierarchies (`CompiledBank`, `CompiledMap`, `CompiledEvent`, `CompiledBaseStats`, `CompiledItem`) through `load_from_json()`.

## 3. REST FastAPI Layer (`api/` & `facades/`)

Built with FastAPI (`api/app.py`) to provide standard HTTP/JSON endpoints alongside gRPC:
* **`POST /gba/pokemon/items` (`api/routers/items_router.py`):** Accepts multipart form data (`game`, optional `game_file` ROM upload) and the `app_language` cookie via `parse_game_input`, returning all compiled items as JSON via `ItemsFacade`.
* **`PATCH /config/language` (`api/routers/config_router.py`):** Updates the active locale (`EN_US` / `ES_MX`) and sets an `httponly`, `samesite="lax"` cookie (`app_language`) configured via `LANGUAGE_COOKIE_MAX_AGE`.
* **Exception Translation & Middleware:** Maps `DomainException` subclasses (`DomainValidationError` -> `400`, `ResourceNotFoundError` -> `404`, `RomPreconditionError` -> `412`) in `exceptions/exception_handlers.py` and attaches `X-Process-Time` headers via `api/middlewares/app_middlewares.py`.
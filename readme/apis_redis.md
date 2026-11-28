# ⚡ gRPC & Redis Caching Architecture

To support external frontends (such as upcoming desktop or web GUIs) and avoid re-scanning unchanged binary files across consecutive runs, **AdvanceR Nexus UpGen** provides an async TLS gRPC API and a Redis caching layer.

## 1. Secure Async gRPC Server (`grpc_files/`)

The server runs on `grpc.aio.server` over **HTTP/2 + TLS** on port `50051` with a `48MB` message size limit (`MAX_MESSAGE_LENGTH`) to accommodate full 16MB and 32MB GBA game payloads.

### Protobuf Contract (`grpc_files/protos/items.proto`)
* **`ItemsService.GetAllItems`:** Unary RPC accepting `GetAllItemsRequest` (`bytes game_file`, `optional string current_game`) and returning `GetAllItemsResponse` (`map<int32, CompiledItemProto>`).
* **Operating Modes (`grpc_files/servicers/items_servicer.py`):**
  1. **Server-Loaded Game File:** When `game_file` is omitted, queries the game buffer already loaded in memory on the server using `default_game`.
  2. **Client Game File Override:** When `game_file` and `current_game` are provided, initializes that title's configuration via `GamesProvider` and parses the uploaded bytes on demand.

### Local Setup Commands
1. **Compile `.proto` definitions (PowerShell):**
   ```powershell
   .\tools\compile_protos.ps1
   ```
2. **Generate local self-signed TLS credentials (`grpc_files/server.crt` & `grpc_files/server.key`):**
   ```powershell
   python tools/generate_certificate.py
   ```

## 2. Multi-Layer & Redis Caching (`redis.asyncio`)

Both `GBAPokemonGame` (`games/gba/pokemon/gba_pokemon_game.py`) and `ItemsFacade` (`facades/items_facade.py`) connect to an async Redis pool (`127.0.0.1:6379`) to eliminate redundant binary parsing:

* **Cache Keys & Expiration:** Stores serialized JSON arrays under `game:{GAME_NAME}:{ROM_SHA256}:{LOCALE}:banks`, `:stats`, and `:items` (or `server_default` when using the server's local ROM) with a **1-hour TTL (`ex=3600`)**.
* **Fast DTO Deserialization (`dict_to_class`):** On cache hits, `ItemsFacade` returns items directly without spawning a worker thread, while `GBAPokemonGame` hydrates `CompiledBank`, `CompiledMap`, `CompiledEvent`, `CompiledBaseStats`, and `CompiledItem` models via `mget` and `load_from_json()`.
* **In-Memory Caching:** `FileService.open_game_readonly()` caches unmodified ROM bytes via `lru_cache` (keyed by path, `mtime_ns`, and file size), `WildService` caches encounter slot offsets, and `TranslationsService` shares flattened locales via `_SHARED_CACHE`.

## 3. REST FastAPI Layer (`api/` & `facades/`)

Built with FastAPI (`api/app.py`) to provide standard HTTP/JSON endpoints alongside gRPC:
* **`POST /gba/pokemon/items` (`api/routers/items_router.py`):** Accepts multipart form data (`game`, optional `game_file` ROM upload) and the `app_language` cookie via `parse_game_input`, streaming uploads in `1MB` chunks up to `GLOBAL_MAX_UPLOAD_MB` (`32MB` default) and returning compiled items via `ItemsFacade`.
* **`PATCH /config/language` (`api/routers/config_router.py`):** Updates the active locale (`EN_US` / `ES_MX`) and sets an `httponly`, `samesite="lax"` cookie (`app_language`, automatically marked `Secure` over HTTPS) configured via `LANGUAGE_COOKIE_MAX_AGE`.
* **Security & Exception Middleware:** Applies `CORSMiddleware`, HTTP security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`), automatic `/docs` and `/openapi.json` lockdown when `APP_ENV=prod`, and centralized domain-to-HTTP exception mapping (`400`, `404`, `412`, `500`)..
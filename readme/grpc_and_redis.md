# ⚡ gRPC & Redis Caching Architecture

To support external frontends (such as upcoming desktop or web GUIs) and avoid re-scanning unchanged binary files across consecutive runs, **AdvanceR Nexus UpGen** provides an async TLS gRPC API and a Redis caching layer.

## 1. Secure Async gRPC Server (`grcp/`)

The server runs on `grpc.aio.server` over **HTTP/2 + TLS** on port `50051` with a `48MB` message size limit (`MAX_MESSAGE_LENGTH`) to accommodate full 16MB and 32MB GBA game payloads.

### Protobuf Contract (`grcp/protos/items.proto`)
* **`ItemsService.GetAllItems`:** Unary RPC accepting `GetAllItemsRequest` (`bytes game_file`, `optional int32 game_id`) and returning `GetAllItemsResponse` (`map<int32, CompiledItemProto>`).
* **Operating Modes (`grcp/servicers/items_servicer.py`):**
  1. **Server-Loaded Game File:** When `game_file` is omitted, queries the game buffer already loaded in memory on the server.
  2. **Client Game File Override:** When `game_file` and `game_id` are provided, initializes that title's configuration via `GamesProvider` and parses the uploaded bytes on demand.

### Local Setup Commands
1. **Compile `.proto` definitions (PowerShell):**
   ```powershell
   .\grcp\compile_protos.ps1
   ```
2. **Do not forget to generate local TLS credentials (`grcp/server.crt` & `grcp/server.key`):**

## 2. Redis Binary Data Caching (`redis.asyncio`)

`BaseGame` (`games/base_game.py`) initializes an async Redis client (`127.0.0.1:6379`) to cache compiled binary structures extracted from unmodified game files:

* **Cache Keys & Expiration:** Stores serialized JSON arrays under `game:{GAME_NAME}:banks`, `game:{GAME_NAME}:stats`, and `game:{GAME_NAME}:items` with a **1-hour TTL (`ex=3600`)**.
* **Fast DTO Deserialization (`dict_to_class`):** On subsequent runs, `GBAPokemonGame.process_game()` queries all three keys via `mget` and reconstructs typed `@dataclass` hierarchies (`CompiledBank`, `CompiledMap`, `CompiledEvent`, `CompiledBaseStats`, `CompiledItem`) through `load_from_json()`.

# 🖥️ Interactive Console Menu (`ConsoleMenu`)

The CLI entry point of **AdvanceR Nexus UpGen** is powered by `ConsoleMenu` (`tools/menu.py`), a self-contained terminal interface that decouples user interaction from game instantiation and gRPC transport logic.

## 🧭 Navigation Flow

When `python main.py` starts, `init_global_config()` loads the default locale (`CURRENT_LANGUAGE`) and passes it to `ConsoleMenu`, which loops until the user completes a selection (`UserSelection`) or exits:

1. **Start App (`randomizer` / `grpc_server`):**
   * **Step 1 — Execution Mode:** Choose between **Generator & Randomizer** (modifies and saves the ROM) or **Start gRPC Server** (serves parsed game data over TLS on port `50051`).
   * **Step 2 — Game Selection:** Dynamically lists all titles registered in `AvailableGames` (`ORIGINAL_FIRE_RED`, `RADICAL_FIRE_RED`, `LEAF_GREEN`, `CUSTOM_LEAF_GREEN`, `EMERALD`, `EMERALD_KAIZO`).
2. **Test gRPC Client (`grpc_test_loaded` / `grpc_test_replace`):**
   * **Use Server Loaded Game:** Queries `GetAllItems` against whichever game file is currently loaded in the running gRPC server.
   * **Replace Server Game:** Prompts for a target game from `AvailableGames`, reads its bytes from disk, and streams them to the server alongside `game_id`.
3. **Start Rest API Server (`fastapi_server`):**
   * Immediately returns `UserSelection(action="fastapi_server")`, launching the FastAPI application via Uvicorn on `http://127.0.0.1:8000` and automatically opening the default browser at `/` (redirecting to `/docs`).
4. **Run Tests (`pytest_all` / `pytest_unit` / `pytest_integration` / `pytest_cov`):**
   * Opens a sub-menu to run **All Tests**, **Unit Tests Only**, **Integration Tests Only**, or **All Tests with Coverage Report** via `pytest.main()`.
5. **Change Language:**
   * Displays all locales defined in `AvailableLanguages` (`EN_US`, `ES_MX`), marks the active language, and immediately reloads UI strings via `TranslationsService.set_locale()`.

## ⌨️ Hotkeys & Terminal Controls

`ConsoleMenu` reads standard input character-by-character (`msvcrt.getwch` on Windows, `termios`/`tty` on Unix) to support responsive keyboard navigation without external dependencies:

| Key | Scope | Behavior |
| :--- | :--- | :--- |
| **`1` – `N` + `Enter`** | All screens | Confirms the selected option (supports multi-digit numbers). |
| **`0` + `Enter`** | Sub-menus | Raises `_GoBackException` to return to the previous step. |
| **`Backspace`** | Sub-menus (empty input) | Deletes typed characters if the buffer is non-empty, or returns to the previous step when empty. |
| **`ESC`** | Any screen | Raises `_ExitMenuException` to clear the terminal and exit cleanly (`return None`). |

## 📦 Output Payload (`UserSelection`)

Once a flow finishes, `ConsoleMenu.run()` returns a lightweight `@dataclass` (`tools/user_selection.py`) to `main.py`:

## 🌐 Localization (`menu.json`)

Menu labels, prompts, and navigation hints are stored separately from application logs inside `translations/{LOCALE}/menu.json` and flattened at runtime by `TranslationsService ` (`services/translations_service.py`), supporting dynamic variable interpolation (`{lang}`, `{label}`).
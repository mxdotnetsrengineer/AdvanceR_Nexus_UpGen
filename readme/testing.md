# 🧪 Automated Testing Guide (`Pytest`)

**AdvanceR Nexus UpGen** includes an automated test suite built with **Pytest** (`pytest`, `pytest-asyncio`, `pytest-cov`, and `httpx`) to validate low-level GBA binary operations, domain facade orchestration, and FastAPI HTTP endpoints without requiring real ROM files or external Redis instances.

---

## 1. Running Tests

You can execute the test suite either through the interactive terminal menu or directly via CLI commands.

### Option A: From `ConsoleMenu` (`python main.py`)
1. Run `python main.py`.
2. Select **`4. Run Tests (Pytest)`** from the main menu.
3. Choose the desired execution mode:
   * **`1. All Tests (Unit & Integration)`** (`pytest -v`)
   * **`2. Unit Tests Only`** (`pytest tests/unit -v`)
   * **`3. Integration Tests Only`** (`pytest tests/integration -v`)
   * **`4. All Tests with Coverage Report`** (`pytest --cov`)

### Option B: Direct CLI Commands
With your virtual environment activated (`.venv`):

```bash
# Run the full test suite
pytest -v

# Run unit tests only
pytest tests/unit -v

# Run integration tests only
pytest tests/integration -v

# Run tests with branch coverage report configured in pyproject.toml
pytest --cov
```

---

## 2. Test Suite Structure (`tests/`)

```text
tests/
├── conftest.py                       # Shared fixtures & synthetic FireRed ROM builder
├── unit/
│   ├── menu/
│   │   └── test_flow.py              # ConsoleMenu navigation & end-to-end difficulty scaling
│   ├── test_memory.py                # Pointer translation, Gen III string decoding & free-space alignment
│   ├── test_facades.py               # ROM validation errors & mocked GamesProvider delegation
│   └── test_translations.py          # Locale key parity & {placeholder} consistency checks
└── integration/
    ├── test_config_router.py         # FastAPI language cookie & invalid locale fallback tests
    └── test_items_router.py          # Multipart ROM upload, size limit & filename validation tests
```

---

## 3. Shared Fixtures (`tests/conftest.py`)

All test modules automatically inherit reusable fixtures defined in `tests/conftest.py`:

| Fixture | Scope | Returns | Description |
| :--- | :--- | :--- | :--- |
| **`translations_service`** | `session` | `TranslationsService` | Provides a shared English (`EN_US`) translation instance across the test run. |
| **`error_service`** | `session` | `ErrorService` | Provides an `ErrorService` backed by a silent `LogService(level="NONE")` so tests assert raised `DomainException`s cleanly without polluting stdout. |
| **`api_client`** | `module` | `TestClient` | Wraps `create_app()` in a FastAPI `TestClient` (powered by `httpx`) for testing HTTP routes, status codes, and response headers/cookies. |
| **`fake_gba_rom`** | `function` | `bytearray` | Allocates a fresh `64KB` (`0x10000` bytes) in-memory buffer initialized with `0xFF` free-space bytes for isolated binary read/write tests. |
| **`synthetic_firered_rom`** | `function` | `tuple[bytearray, dict]` | Builds a compact 4KB synthetic GBA ROM with valid item, stats, bank, event, and wild tables alongside matching offset overrides. |
| **`firered_test_config`** | `function` | `tuple[ConfigService, bytearray, Path]` | Merges real FireRed config settings with synthetic ROM offsets and a temporary output path (`tmp_path`) for isolated randomizer tests. |

---

## 4. Writing New Tests

Follow these conventions when expanding the test suite so tests remain fast, isolated, and easy to maintain:

### Where to Place Tests
* **`tests/unit/test_<module>.py`:** Place isolated tests for services, binary helpers, models, and facades here. Mock external dependencies (`GamesProvider`, file I/O, or Redis) so unit tests run purely in memory.
* **`tests/integration/test_<router>.py`:** Place end-to-end HTTP or transport tests here to verify request parsing, dependency injection, status codes, and response headers/cookies.

### How to Inject Fixtures
Declare any fixture name from `tests/conftest.py` directly as a parameter in your test function signature—Pytest resolves and injects it automatically:

```python
def test_example_with_fixtures(fake_gba_rom, translations_service, error_service):
    # Each fixture is ready to use without manual setup
    #... Your tests Code
```

### Common Assertion Patterns
* **Value & Structure Checks (`assert`):** Verify return values, dictionary keys, or decoded strings directly:
  ```python
  assert result == expected_value
  assert "app_language=ES_MX" in response.headers.get("set-cookie", "")
  ```
* **Domain Exception Checks (`pytest.raises`):** Verify that invalid inputs trigger the expected `DomainException` subclass and error message:
  ```python
  with pytest.raises(DomainValidationError) as exc_info:
      await facade.get_all_items_gba(invalid_input)

  assert "empty" in str(exc_info.value).lower()
  ```
* **Async Functions (`@pytest.mark.asyncio`):** Decorate any `async def test_...` function when testing asynchronous facades or services:
  ```python
  @pytest.mark.asyncio
  async def test_async_operation(error_service):
      result = await some_async_call()
      assert result is not None
  ```
* **HTTP Endpoints (`api_client`):** Use `api_client` in `tests/integration/` to assert HTTP status codes, JSON payloads, and cookies:
  ```python
  def test_http_endpoint(api_client):
      response = api_client.patch("/config/language", data={"language": "English"})

      assert response.status_code == 200
      assert response.json()["language"] == "EN_US"
  ```
```

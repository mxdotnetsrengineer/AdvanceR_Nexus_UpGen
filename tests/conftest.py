import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from services.translations_service import TranslationsService
from services.log_service import LogService
from services.error_service import ErrorService
from services.config_service import ConfigService
from api.app import create_app

def _format_test_label(test_name: str, mode: str) -> str:
    if mode == "NAME":
        clean = test_name.removeprefix("test_").replace("_", " ")
        return clean.capitalize()
    return test_name


def pytest_configure(config: pytest.Config) -> None:
    raw_mode = ConfigService.load_global().get("PYTEST_OUTPUT_MODE")
    config._output_mode = str(raw_mode).strip().upper()


@pytest.hookimpl(tryfirst=True)
def pytest_report_teststatus(report: pytest.TestReport, config: pytest.Config):
    if report.when != "call":
        return None

    module_path, test_name = report.nodeid.split("::", 1)

    terminal = config.pluginmanager.get_plugin("terminalreporter")
    if terminal is not None:
        if module_path != getattr(config, "_last_test_module", None):
            config._last_test_module = module_path
            terminal.write_line("")
            terminal.write_line(f"{module_path}:")

        icon = "✓" if report.passed else "✗" if report.failed else "-"
        color = {"green": True} if report.passed else {"red": True} if report.failed else {}
        output_mode = getattr(config, "_output_mode")
        label = _format_test_label(test_name, output_mode)
        terminal.write_line(f"  {icon} {label}", **color)

    return report.outcome, "", ""

@pytest.fixture(scope="session")
def translations_service() -> TranslationsService:
    """Provide a default English TranslationsService instance."""
    return TranslationsService(default_locale="EN_US")


@pytest.fixture(scope="session")
def error_service(translations_service: TranslationsService) -> ErrorService:
    """Provide an ErrorService instance backed by a silent LogService."""
    logger = LogService(translations_service, level="NONE")
    return ErrorService(logger, translations_service)

@pytest.fixture(scope="module")
def api_client() -> TestClient:
    """Provide a FastAPI TestClient scoped per test module."""
    return TestClient(create_app())

@pytest.fixture
def fake_gba_rom() -> bytearray:
    """Create a 64KB zero-initialized buffer filled with 0xFF free space bytes."""
    return bytearray(b"\xFF" * 0x10000)

@pytest.fixture
def synthetic_firered_rom() -> tuple[bytearray, dict]:
    """Create a compact 4KB synthetic GBA ROM and matching offsets config for unit tests."""
    rom = bytearray(b"\xFF" * 0x1000)
    to_ptr = lambda off: (0x08000000 + off).to_bytes(4, "little")

    # Pointers at 0x00..0x0C: items=0x100, stats=0x200, names=0x300
    rom[0x00:0x04] = to_ptr(0x100)
    rom[0x04:0x08] = to_ptr(0x200)
    rom[0x08:0x0C] = to_ptr(0x300)

    # Items (IDs 1..2 at 0x100)
    for item_id, bytes_name in [(1, b"\xC7\xBB\xCD\xCE\xBF\xCC\xFF"), (2, b"\xCA\xC9\xCE\xC3\xC9\xC8\xFF")]:
        off = 0x100 + (item_id * 44)
        rom[off : off + len(bytes_name)] = bytes_name
        rom[off + 0x10 : off + 0x1C] = b"\x64\x00" + (b"\x00" * 8) + b"\x01\x01"

    # Species (IDs 1..2 at 0x200), Names (at 0x300), Evolutions zeroed (at 0x600)
    rom[0x600:0x680] = b"\x00" * 0x80
    for sp_id, stats, name in [
        (1, b"\x2D\x31\x31\x2D\x41\x41\x00\x00\x2D\x40", b"\xBC\xCF\xC6\xBC\xFF"),
        (2, b"\x27\x34\x2B\x41\x3C\x32\x00\x00\x2D\x40", b"\xBD\xC2\xBB\xCC\xFF"),
    ]:
        rom[0x200 + sp_id * 28 : 0x200 + sp_id * 28 + 10] = stats
        rom[0x300 + sp_id * 11 : 0x300 + sp_id * 11 + len(name)] = name

    # Bank 0 (0x400) -> Map 0 (0x410) -> Layout (0x430) + Events (0x440 -> 0x450 -> Script 0x470)
    rom[0x400:0x404], rom[0x410:0x414] = to_ptr(0x408), to_ptr(0x430)
    rom[0x408:0x40C] = to_ptr(0x410)
    rom[0x410 + 20] = 0x58
    rom[0x430:0x438] = b"\x14\x00\x00\x00\x14\x00\x00\x00"  # width=20, height=20
    rom[0x414:0x418], rom[0x440], rom[0x444:0x448] = to_ptr(0x440), 1, to_ptr(0x450)
    rom[0x451], rom[0x450 + 16 : 0x450 + 20] = 92, to_ptr(0x470)
    rom[0x470:0x47D] = b"\x1A\x00\x80\x01\x00\x1A\x01\x80\x01\x00\x09\x01\x02"

    # Wild table (0x500) -> Info (0x530) -> 2 grass slots (0x540)
    rom[0x500:0x508], rom[0x514:0x516] = b"\x00\x00\x00\x00" + to_ptr(0x530), b"\xFF\xFF"
    rom[0x530:0x538] = b"\x14\x00\x00\x00" + to_ptr(0x540)
    rom[0x540:0x548] = b"\x03\x05\x01\x00\x03\x05\x01\x00"

    overrides = {
        "ITEMS_POINTER_OFFSET": 0x00, "POKEMON_STATS_OFFSET": 0x04, "POKEMON_NAMES_OFFSET": 0x08,
        "POKEMON_EVOLUTIONS_OFFSET": [0x600], "BANK_TABLE_OFFSET": 0x400, "WILD_POKEMON_OFFSET": [0x500],
        "FREE_SPACE_START": 0x700, "MAX_ITEM_ID": 2, "MAX_POKEMON_SPECIES": 3,
        "MAX_BANKS": 1, "MAX_MAPS_PER_BANK": 1, "WILD_GRASS_SLOT_COUNT": 2,
    }
    return rom, overrides

@pytest.fixture
def firered_test_config(tmp_path: Path, synthetic_firered_rom) -> tuple[ConfigService, bytearray, Path]:
    """Load real FireRed ConfigService merged with synthetic ROM offsets."""
    from enums.gba.games_enum import AvailableGames

    rom, overrides = synthetic_firered_rom
    output_path = tmp_path / "randomized.gba"

    config = ConfigService.load_for_game(
        AvailableGames.ORIGINAL_FIRE_RED.config_key,
        language="EN_US",
    )
    for key, val in {
        **overrides,
        "MODIFIED_GAME": str(output_path),
        "LOG_TYPE": "NONE",
    }.items():
        config.set(key, val)

    return config, rom, output_path
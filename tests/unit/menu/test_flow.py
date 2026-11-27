import json
from pathlib import Path
from unittest.mock import patch
import pytest

from enums.app_enums import AvailableLanguages
from enums.gba.games_enum import AvailableGames
from games.core.games_provider import GamesProvider
from services.config_service import BASE_DIR, ConfigService
from tools.menu import ConsoleMenu


def test_menu_option_1_1_returns_randomizer_selection(translations_service):
    menu = ConsoleMenu(translations_service, default_language=AvailableLanguages.EN_US)

    with (
        patch.object(ConsoleMenu, "_clear_screen"),
        patch.object(ConsoleMenu, "_read_input_with_hotkeys", side_effect=["1", "1", "1"]),
    ):
        selection = menu.run()

    assert selection is not None
    assert selection.action == "randomizer"
    assert selection.game == AvailableGames.ORIGINAL_FIRE_RED


@pytest.mark.asyncio
async def test_randomizer_modifies_rom_and_saves_output(tmp_path: Path, synthetic_firered_rom):
    """Verify core ROM modification and file output independent of difficulty settings."""
    rom, overrides = synthetic_firered_rom
    original_bytes = bytes(rom)
    output_path = tmp_path / "randomized.gba"

    config = ConfigService.load_for_game(AvailableGames.ORIGINAL_FIRE_RED.config_key, language="EN_US")
    for key, val in {
        **overrides,
        "CURRENT_DIFFICULTY": None,
        "MODIFIED_GAME": str(output_path),
        "LOG_TYPE": "NONE",
    }.items():
        config.set(key, val)

    game = GamesProvider.create(
        game=AvailableGames.ORIGINAL_FIRE_RED,
        language=AvailableLanguages.EN_US,
        config_service=config,
        game_file=rom,
    )
    await game.process_game()

    saved = output_path.read_bytes()
    assert saved != original_bytes
    assert saved[0x540] == 3  # Without difficulty config, original level (3) is preserved
    new_script_off = int.from_bytes(saved[0x460:0x464], "little") - 0x08000000
    assert new_script_off >= 0x700 and saved[new_script_off] == 0x1A


@pytest.mark.parametrize(
    "difficulty, expected_min_level",
    [
        ("EASY", 5),
        ("NORMAL", 4),
        ("HARD", 3),
        ("INFERNO", 2),
    ],
)
@pytest.mark.asyncio
async def test_randomizer_applies_difficulty_level_scaling(
    firered_test_config,
    monkeypatch,
    difficulty: str,
    expected_min_level: int,
):
    """Verify level scaling across all difficulty profiles when GAME_DIFFICULTY is configured."""
    base_config, rom, output_path = firered_test_config
    if not base_config.get("GAME_DIFFICULTY"):
        pytest.skip()

    monkeypatch.setenv("GAME_DIFFICULTY", difficulty)
    config = ConfigService.load_for_game(
        AvailableGames.ORIGINAL_FIRE_RED.config_key,
        language="EN_US",
    )
    for key, val in base_config.as_dict().items():
        if key not in ("GAME_DIFFICULTY", "CURRENT_DIFFICULTY"):
            config.set(key, val)

    game = GamesProvider.create(
        game=AvailableGames.ORIGINAL_FIRE_RED,
        language=AvailableLanguages.EN_US,
        config_service=config,
        game_file=rom,
    )
    await game.process_game()

    saved = output_path.read_bytes()
    assert saved[0x540] == expected_min_level
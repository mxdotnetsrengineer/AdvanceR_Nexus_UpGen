import pytest
from unittest.mock import MagicMock, patch
from exceptions.domain_exceptions import DomainValidationError
from facades.items_facade import ItemsFacade
from models.game_input import GameInput
from services.config_service import ConfigService


@pytest.mark.asyncio
async def test_facade_raises_validation_error_on_empty_rom(error_service):
    facade = ItemsFacade(
        global_config=ConfigService({"CURRENT_LANGUAGE": "EN_US"}),
        error_service=error_service,
    )
    empty_input = GameInput(
        game_id=0,
        raw_file=b"",
        filename="Pokemon - FireRed Version (USA).gba",
    )

    with pytest.raises(DomainValidationError) as exc_info:
        await facade.get_all_items_gba(empty_input)

    assert "empty" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_facade_delegates_to_items_service_with_mocked_game(error_service, fake_gba_rom):
    mock_game = MagicMock()
    mock_game.config_service.get.return_value = 0x1000000
    mock_game.memory_service.game_file = fake_gba_rom
    mock_game.items_service.get_all_items.return_value = {1: "MASTER BALL"}

    facade = ItemsFacade(
        global_config=ConfigService({"CURRENT_LANGUAGE": "EN_US"}),
        error_service=error_service,
    )

    with patch("facades.base_facade.GamesProvider.create", return_value=mock_game):
        result = await facade.get_all_items_gba(GameInput(game_id=0))

    assert result == {1: "MASTER BALL"}
    mock_game.items_service.get_all_items.assert_called_once_with(fake_gba_rom)
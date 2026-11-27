from unittest.mock import MagicMock, patch


def test_post_items_with_valid_uploaded_rom(api_client):
    mock_game = MagicMock()
    mock_game.config_service.get.return_value = 0x1000000
    mock_game.memory_service.game_file = bytearray(b"\xFF" * 0x1000)
    mock_game.items_service.get_all_items.return_value = {}

    rom_content = b"\x00\x01\x02\x03" * 256
    rom_filename = "Pokemon - FireRed Version (USA).gba"

    with patch("games.core.games_provider.GamesProvider.create", return_value=mock_game) as mock_create:
        response = api_client.post(
            "/gba/pokemon/items",
            data={"game": "fire_red"},
            files={"game_file": (rom_filename, rom_content, "application/octet-stream")},
        )

    assert response.status_code == 200
    assert response.json() == {"total": 0, "items": {}}

    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["game_filename"] == rom_filename
    assert bytes(call_kwargs["game_file"]) == rom_content


def test_post_items_rejects_file_exceeding_global_upload_limit(api_client):
    oversized_content = b"\xFF" * 2048  # 2 KB

    with patch("api.dependencies.game_dependencies._resolve_upload_limits", return_value=(1, 1024)):
        response = api_client.post(
            "/gba/pokemon/items",
            data={"game": "fire_red"},
            files={"game_file": ("Pokemon - FireRed Version (USA).gba", oversized_content, "application/octet-stream")},
        )

    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower()


def test_post_items_rejects_invalid_rom_filename(api_client):
    rom_content = b"\xFF" * 1024

    response = api_client.post(
        "/gba/pokemon/items",
        data={"game": "fire_red"},
        files={"game_file": ("nombre_incorrecto.gba", rom_content, "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "nombre_incorrecto.gba" in response.json()["detail"]
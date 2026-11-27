from unittest.mock import MagicMock, patch


def test_patch_language_sets_httponly_cookie(api_client):
    response = api_client.patch("/config/language", data={"language": "Spanish"})

    assert response.status_code == 200
    assert response.json()["language"] == "ES_MX"
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "app_language=ES_MX" in set_cookie_header
    assert "HttpOnly" in set_cookie_header


def test_invalid_language_cookie_falls_back_safely_on_items_endpoint(api_client):
    mock_game = MagicMock()
    mock_game.config_service.get.return_value = 0x1000000
    mock_game.memory_service.game_file = bytearray(b"\xFF" * 0x1000)
    mock_game.items_service.get_all_items.return_value = {}

    with patch("games.core.games_provider.GamesProvider.create", return_value=mock_game) as mock_create:
        api_client.cookies.set("app_language", "INVALID_LOCALE_999")
        try:
            response = api_client.post("/gba/pokemon/items")
        finally:
            api_client.cookies.clear()

    assert response.status_code == 200
    assert response.json() == {"total": 0, "items": {}}
    assert mock_create.call_args.kwargs["language"] == "EN_US"

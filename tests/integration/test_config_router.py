def test_patch_language_sets_httponly_cookie(api_client):
    response = api_client.patch("/config/language", data={"language": "Spanish"})

    assert response.status_code == 200
    assert response.json()["language"] == "ES_MX"
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "app_language=ES_MX" in set_cookie_header
    assert "HttpOnly" in set_cookie_header
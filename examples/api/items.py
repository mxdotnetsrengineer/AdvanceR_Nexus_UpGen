import json
import urllib.error
import urllib.request

from enums.gba.games_enum import AvailableGames
from examples.api.common import _build_multipart_form

BASE_URL = "http://127.0.0.1:8000"

def get_all_items_fastapi(
    language: str | None = None,
) -> None:
    """Call POST /gba/pokemon/items on the running FastAPI server using AvailableGames."""
    endpoint = f"{BASE_URL.rstrip('/')}/gba/pokemon/items"

    fields: dict[str, str] = {}
    selected_game = AvailableGames.ORIGINAL_FIRE_RED

    body, content_type = _build_multipart_form(fields=fields)

    headers = {"Content-Type": content_type}
    if language:
        headers["Cookie"] = f"app_language={language}"

    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")

    game_label = selected_game.name if selected_game else "Server Default"
    print(f"\n[FastAPI Client] POST {endpoint} (Game: {game_label})")

    try:
        with urllib.request.urlopen(request) as response:
            process_time = response.headers.get("X-Process-Time", "N/A")
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP {exc.code}: {error_body}")
        return
    except urllib.error.URLError as exc:
        print(f"❌ Connection failed (is FastAPI running on {BASE_URL}?): {exc.reason}")
        return

    items: dict[str, dict] = payload.get("items", {})
    total: int = payload.get("total", len(items))

    print(f"[FastAPI Client] ✔ Total items received: {total} | X-Process-Time: {process_time}")
    print("=" * 80)
    for item_id in sorted(items.keys(), key=int):
        item = items[item_id]
        print(
            f"#{item['id']:03d} | {item['name']:<15} | "
            f"Pocket: {item['pocket']:<10} ({item['pocket_id']}) | "
            f"Type: {item['item_type']:<20} (0x{item['item_type_id']:02X}) | Price: ${item['price']:5d}"
        )
    print("=" * 80)
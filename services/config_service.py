import os
import json
from pathlib import Path
from typing import Any
from enums.app_enums import AvailableLanguages

BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigService:
    def __init__(self, config: dict[str, Any]):
        self._config: dict[str, Any] = dict(config)

    def get(self, property_name: str, default: Any = None) -> Any:
        return self._config.get(property_name, default)

    def set(self, property_name: str, value: Any) -> None:
        self._config[property_name] = value

    def as_dict(self) -> dict[str, Any]:
        return dict(self._config)

    @classmethod
    def load_global(cls) -> "ConfigService":
        """Load shared global configuration and user options."""
        raw_data: dict[str, Any] = {}
        global_path = BASE_DIR / "config" / "global_config.json"
        missing_global = not global_path.exists()

        if not missing_global:
            raw_data.update(json.loads(global_path.read_text(encoding="utf-8")))

        options_path = BASE_DIR / "config" / "options" / "options_config.json"
        if options_path.exists():
            raw_data.update(json.loads(options_path.read_text(encoding="utf-8")))

        for key, current_val in raw_data.items():
            env_val = os.getenv(key)
            if env_val is not None:
                if isinstance(current_val, bool):
                    raw_data[key] = env_val.strip().lower() in ("true", "1", "yes")
                elif isinstance(current_val, int):
                    raw_data[key] = int(env_val, 0)
                else:
                    raw_data[key] = env_val

        parsed_data = cls._parse_hex_values(raw_data)
        lang = parsed_data.get("CURRENT_LANGUAGE", "EN_US")

        parsed_data["missing_global"] = missing_global
        parsed_data["available_language"] = lang in AvailableLanguages.__members__

        return cls(parsed_data)

    @classmethod
    def load_for_game(cls, game_key: str, language: str | None = None) -> "ConfigService":
        """Build an isolated configuration instance merging global and game-specific settings."""
        base_config = cls.load_global().as_dict()

        if language is not None:
            base_config["CURRENT_LANGUAGE"] = language

        game_dir = BASE_DIR / "config" / "gba" / "pokemon"
        merged_game_data, parent_key = cls._load_game_hierarchy(game_dir, game_key)
        base_config.update(merged_game_data)

        if language is not None:
            base_config["CURRENT_LANGUAGE"] = language

        # Game difficulty
        difficulty = base_config.get("GAME_DIFFICULTY")
        if difficulty:
            diff_base = BASE_DIR / "config" / "options" / "gba" / "pokemon"
            diff_path = diff_base / game_key / "difficulty" / f"{difficulty}.json"
            if not diff_path.exists() and parent_key:
                diff_path = diff_base / parent_key / "difficulty" / f"{difficulty}.json"

            if diff_path.exists():
                base_config["CURRENT_DIFFICULTY"] = json.loads(diff_path.read_text(encoding="utf-8"))

        # Feature flags
        if base_config.get("USE_FEATURE_FLAGS") is True:
            flags_path = game_dir / "feature_flags.json"
            if flags_path.exists():
                for flag_key, flag_value in json.loads(flags_path.read_text(encoding="utf-8")).items():
                    base_config.setdefault(flag_key, flag_value)

        return cls(cls._parse_hex_values(base_config))

    @classmethod
    def _load_game_hierarchy(
        cls,
        game_dir: Path,
        game_key: str,
        visited: set[str] | None = None,
    ) -> tuple[dict[str, Any], str | None]:
        """Recursively merge parent configurations while preventing circular BASE_CONFIG loops."""
        if visited is None:
            visited = set()

        if game_key in visited:
            chain = " -> ".join([*visited, game_key])
            raise ValueError(f"Circular BASE_CONFIG detected: {chain}")

        visited.add(game_key)
        game_path = game_dir / f"{game_key}_config.json"
        if not game_path.exists():
            raise FileNotFoundError(str(game_path))

        game_data = json.loads(game_path.read_text(encoding="utf-8"))
        parent_key = game_data.get("BASE_CONFIG")

        if parent_key:
            parent_data, _ = cls._load_game_hierarchy(game_dir, parent_key, visited)
            return {**parent_data, **game_data}, parent_key

        return game_data, None
    
    @staticmethod
    def _parse_hex_values(raw_data: dict[str, Any]) -> dict[str, Any]:
        """Convert hex string values ('0x...') into integers."""
        processed: dict[str, Any] = {}
        for key, value in raw_data.items():
            if isinstance(value, str) and value.startswith("0x"):
                processed[key] = int(value, 16)
            else:
                processed[key] = value
        return processed
import json
import os

current_config = {}

def _log_msg(message: str, should_log:bool):
        if should_log:
            print(message)

def _parse_hex_values(raw_data: dict) -> dict:
    """Convert hex string values ('0x...') into integers."""
    processed = {}
    for key, value in raw_data.items():
        if isinstance(value, str) and value.startswith("0x"):
            processed[key] = int(value, 16)
        else:
            processed[key] = value
    return processed


def init_global_config() -> None:
    """Load shared global and user options configuration at application startup."""
    global current_config

    raw_data = {}
    global_path = "config/global_config.json"
    missing_global = False

    if os.path.exists(global_path):
        with open(global_path, "r", encoding="utf-8") as f:
            raw_data.update(json.load(f))
    else:
        missing_global = True

    options_path = "config/options/options_config.json"
    if os.path.exists(options_path):
        with open(options_path, "r", encoding="utf-8") as f:
            raw_data.update(json.load(f))

    current_config.clear()
    current_config.update(_parse_hex_values(raw_data))

    current_config["available_language"] = True
    should_log = current_config.get("LOG_TYPE", "NONE").upper() != "NONE"

    match current_config.get("CURRENT_LANGUAGE"):
        case "ES_MX":
            if missing_global:
                _log_msg("⚠️ Advertencia: No se encontró el archivo compartido global_config.json.", should_log)
            _log_msg("ℹ️ Configuración global inicializada.", should_log)

        case "EN_US" | _ as lang:
            if missing_global:
                _log_msg("⚠️ Warning: Shared global_config.json file not found.", should_log)
            if lang == "EN_US":
                _log_msg("ℹ️ Global configuration initialized.", should_log)
            else:
                current_config["available_language"] = False
                _log_msg("⚠️ Language not supported", should_log)


def init_game_config(game_key: str, language: str | None = None) -> None:
    """Load game-specific configuration, difficulty, and feature flags on top of global config."""
    global current_config

    raw_data = dict(current_config)
    if language is not None:
        raw_data["CURRENT_LANGUAGE"] = language

    game_path = f"config/gba/pokemon/{game_key}_config.json"
    if not os.path.exists(game_path):
        lang = raw_data.get("CURRENT_LANGUAGE", "EN_US")
        error_msg = (
            f"❌ No se encontró la configuración del juego en: {game_path}"
            if lang == "ES_MX"
            else f"❌ Game configuration not found at: {game_path}"
        )
        raise FileNotFoundError(error_msg)

    with open(game_path, "r", encoding="utf-8") as f:
        raw_data.update(json.load(f))

    # Re-apply user-selected language in case game_config defines a default one
    if language is not None:
        raw_data["CURRENT_LANGUAGE"] = language

    # Game options (Difficulty)
    difficulty = raw_data.get("GAME_DIFFICULTY")
    if difficulty:
        difficulty_path = f"config/options/gba/pokemon/{game_key}/difficulty/{difficulty}.json"
        if os.path.exists(difficulty_path):
            with open(difficulty_path, "r", encoding="utf-8") as f:
                raw_data.update({"CURRENT_DIFFICULTY": json.load(f)})

    # Feature flags
    if raw_data.get("USE_FEATURE_FLAGS") is True:
        flags_path = "config/gba/pokemon/feature_flags.json"
        if os.path.exists(flags_path):
            with open(flags_path, "r", encoding="utf-8") as f:
                feature_flags = json.load(f)
                for flag_key, flag_value in feature_flags.items():
                    raw_data.setdefault(flag_key, flag_value)

    current_config.clear()
    current_config.update(_parse_hex_values(raw_data))

    game_name = current_config.get("GAME_NAME", game_key)
    should_log = current_config.get("LOG_TYPE", "NONE").upper() != "NONE"

    if current_config.get("CURRENT_LANGUAGE") == "ES_MX":
        _log_msg(f"ℹ️ Configuración del juego inicializada para: {game_name}", should_log)
    else:
        _log_msg(f"ℹ️ Game configuration initialized for: {game_name}", should_log)
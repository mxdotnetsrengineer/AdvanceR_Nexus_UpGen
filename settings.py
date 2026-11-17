import json
import os

current_config = {}

def _log_msg(message: str, should_log:bool):
        if should_log:
            print(message)

def init_global_config(game_key):
    global current_config

    raw_data = {}
    global_path = "config/global_config.json"

    missing_global = False
    missing_game = False

    if os.path.exists(global_path):
        with open(global_path, "r", encoding="utf-8") as f:
            raw_data.update(json.load(f))
    else:
        missing_global = True

    game_path = f"config/gba/pokemon/{game_key}_config.json"
    if os.path.exists(game_path):
        with open(game_path, "r", encoding="utf-8") as f:
            game_data = json.load(f)
            raw_data.update(game_data)
    else:
        missing_game = True

    options_path = "config/options/options_config.json"
    if os.path.exists(options_path):
        with open(options_path, "r", encoding="utf-8") as f:
            raw_data.update(json.load(f))

    #game_options
    difficulty = raw_data.get("GAME_DIFFICULTY") 
    if difficulty:
        difficulty_path = f"config/options/gba/pokemon/{game_key}/difficulty/{difficulty}.json"
        if os.path.exists(difficulty_path):
            with open(difficulty_path, "r", encoding="utf-8") as f:
                difficulty_data = json.load(f)
                raw_data.update({"CURRENT_DIFFICULTY" : difficulty_data})
    
    # --- FEATURE FLAGS ---
    if raw_data.get("USE_FEATURE_FLAGS") is True:
        flags_path = "config/gba/pokemon/feature_flags.json"  # Ajusta el nombre si es distinto
        if os.path.exists(flags_path):
            with open(flags_path, "r", encoding="utf-8") as f:
                feature_flags = json.load(f)
                for flag_key, flag_value in feature_flags.items():
                    raw_data.setdefault(flag_key, flag_value)
    # ------------------------------------------

    processed_config = {}
    for key, value in raw_data.items():
        if isinstance(value, str) and value.startswith("0x"):
            processed_config[key] = int(value, 16)
        else:
            processed_config[key] = value       

    current_config.clear()
    current_config.update(processed_config)
    
    game_name = current_config.get('GAME_NAME', game_key)

    current_config["available_language"] = True;
    should_log = current_config.get("LOG_TYPE", "NONE").upper() != "NONE"

    match current_config.get('CURRENT_LANGUAGE'):
        case "ES_MX":
            if missing_global:
                _log_msg("⚠️ Advertencia: No se encontró el archivo compartido global_config.json.", should_log)
            if missing_game:
                raise FileNotFoundError(f"❌ No se encontró la configuración del juego en: {game_path}")
            _log_msg(f"ℹ️ Configuración global inicializada para: {game_name}", should_log)

        case "EN_US" | _ as lang:
            if missing_global:
                _log_msg("⚠️ Warning: Shared global_config.json file not found.", should_log)
            if missing_game:
                raise FileNotFoundError(f"❌ Game configuration not found at: {game_path}")

            if lang == "EN_US":
                _log_msg(f"ℹ️ Global configuration initialized for: {game_name}", should_log)
            else:
                current_config["available_language"] = False
                _log_msg("⚠️ Language not supported", should_log)
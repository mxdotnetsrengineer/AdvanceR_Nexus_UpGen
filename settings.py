import json
import os

current_config = {}

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
    match current_config.get('CURRENT_LANGUAGE'):
        case "ES_MX":
            if missing_global:
                print("⚠️ Advertencia: No se encontró el archivo compartido global_config.json.")
            if missing_game:
                raise FileNotFoundError(f"❌ No se encontró la configuración del juego en: {game_path}")
            print(f"ℹ️ Configuración global inicializada para: {game_name}")

        case "EN_US" | _ as lang:
            if missing_global:
                print("⚠️ Warning: Shared global_config.json file not found.")
            if missing_game:
                raise FileNotFoundError(f"❌ Game configuration not found at: {game_path}")

            if lang == "EN_US":
                print(f"ℹ️ Global configuration initialized for: {game_name}")
            else:
                current_config["available_language"] = False
                print("⚠️ Language not supported")
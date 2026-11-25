from dataclasses import dataclass
from enums.app_enums import AvailableLanguages 
from enums.gba.games_enum import AvailableGames

@dataclass
class UserSelection:
    action: str  # "randomizer" | "grpc_server" | "grpc_test_loaded" | "grpc_test_replace" | "fastapi_server"
    game: AvailableGames | None = None
    language: AvailableLanguages = AvailableLanguages.EN_US
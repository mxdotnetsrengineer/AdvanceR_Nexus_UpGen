from typing import Any
from abc import ABC, abstractmethod
from enums.gba.games_enum import AvailableGames
from services.log_service import LogService
from services.file_service import FileService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from games.gba.gba_game import GBAGame

class GamesCore(ABC):
    def __init__(
        _self,
        config_service: ConfigService,
        log_service: LogService,
        file_service: FileService,
        translations_service: TranslationsService,
    ):
        _self.config_service = config_service
        _self.log_service = log_service
        _self.file_service = file_service
        _self.translations_service = translations_service

    #Public Methods
    @abstractmethod
    def create_game(self, game: AvailableGames) -> GBAGame:
        pass
    # End Public Methods
    
    #Protected Methods
    @abstractmethod
    def _create_memory_service(_self) -> Any:
        pass
    # End Protected Methods
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
        self,
        config_service: ConfigService,
        log_service: LogService,
        file_service: FileService,
        translations_service: TranslationsService,
    ):
        self.config_service = config_service
        self.log_service = log_service
        self.file_service = file_service
        self.translations_service = translations_service

    @abstractmethod
    def create_memory_service(self) -> Any:
        pass

    @abstractmethod
    def create_keyboard_service(self) -> Any:
        pass

    @abstractmethod
    def create_game(self, game: AvailableGames) -> GBAGame:
        pass
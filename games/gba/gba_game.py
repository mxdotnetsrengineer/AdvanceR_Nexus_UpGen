from typing import Any
from abc import ABC, abstractmethod
from services.log_service import LogService
from services.file_service import FileService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.keyboard_service import GBAKeyboardService

class GBAGame(ABC):
    def __init__(self, game, file_service: FileService, log_service:LogService, memory_service:GBAMemoryService, 
        config_service:ConfigService, keyboard_service:GBAKeyboardService, translations_service: TranslationsService,):
        self.game=game
        self.file_service = file_service
        self.log_service = log_service
        self.config_service = config_service
        self.keyboard_service = keyboard_service
        memory_service.game_file = file_service.open_game(self._get_value("ORIGINAL_GAME"));
        self.memory_service = memory_service
        self.translations_service = translations_service

    # Public Methods
    @abstractmethod
    def process_game(self) -> None:
        pass
    # End Public Methods

    # Protected Methods
    def _get_value(self, property_name: str):
        return self.config_service.get_value(property_name)
    # End Protected Methods
        

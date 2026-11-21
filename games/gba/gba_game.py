from typing import Any
from abc import ABC, abstractmethod
from services.log_service import LogService
from services.file_service import FileService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.item_service import ItemService
from games.base_game import BaseGame

class GBAGame(BaseGame):
    def __init__(self, game, file_service: FileService, log_service:LogService, memory_service:GBAMemoryService, 
        config_service:ConfigService, translations_service: TranslationsService):
        super().__init__(
            game=game,
            file_service=file_service,
            log_service=log_service,
            memory_service=memory_service,
            config_service=config_service,
            translations_service=translations_service
        )
        

import redis.asyncio as redis
from abc import ABC, abstractmethod
from typing import Any
from enums.gba.games_enum import AvailableGames
from services.log_service import LogService
from services.file_service import FileService
from services.config_service import ConfigService
from services.translations_service import TranslationsService

class BaseGame(ABC):
    def __init__(
        _self,
        game: AvailableGames,
        file_service: FileService,
        log_service: LogService,
        memory_service: Any,
        config_service: ConfigService,
        translations_service: TranslationsService,
    ):
        _self.game = game
        _self.file_service = file_service
        _self.log_service = log_service
        _self.config_service = config_service
        _self.translations_service = translations_service
        _self.memory_service = memory_service

        _self.client = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)

    @abstractmethod
    async def process_game(self) -> None:
        pass

    def _get(self, property_name: str):
        return self.config_service.get(property_name)
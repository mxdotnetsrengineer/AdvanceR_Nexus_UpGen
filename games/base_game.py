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
        self,
        game: AvailableGames,
        file_service: FileService,
        log_service: LogService,
        memory_service: Any,
        config_service: ConfigService,
        translations_service: TranslationsService,
        redis_client: redis.Redis | None = None,
    ):
        self.game = game
        self.file_service = file_service
        self.log_service = log_service
        self.config_service = config_service
        self.translations_service = translations_service
        self.memory_service = memory_service
        self.client = redis_client

    @abstractmethod
    async def process_game(self) -> None:
        pass

    def _get(self, property_name: str):
        return self.config_service.get(property_name)
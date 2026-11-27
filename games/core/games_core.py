import redis.asyncio as redis
from typing import Any
from abc import ABC, abstractmethod
from enums.gba.games_enum import AvailableGames
from services.log_service import LogService
from services.file_service import FileService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from services.error_service import ErrorService
from games.gba.gba_game import GBAGame

class GamesCore(ABC):
    def __init__(
        self,
        config_service: ConfigService,
        log_service: LogService,
        file_service: FileService,
        translations_service: TranslationsService,
        error_service: ErrorService,
        redis_client: redis.Redis | None = None
    ):
        self.config_service = config_service
        self.log_service = log_service
        self.error_service = error_service
        self.file_service = file_service
        self.translations_service = translations_service
        self.redis_client = redis_client

    #Public Methods
    @abstractmethod
    def create_game(self, game: AvailableGames, game_file: bytes | bytearray | None = None, readonly: bool = False) -> GBAGame:
        pass
    # End Public Methods
    
    #Protected Methods
    @abstractmethod
    def _create_memory_service(self, game_file: bytes | bytearray | None = None, readonly: bool = False) -> Any:
        pass
    # End Protected Methods
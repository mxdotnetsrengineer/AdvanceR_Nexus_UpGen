import redis.asyncio as redis
from pathlib import Path
from enums.gba.games_enum import AvailableGames
from enums.app_enums import AvailableLanguages
from helpers.gba.pokemon.gba_pokemon_helper import GAMES
from services.log_service import LogService
from services.file_service import FileService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from services.error_service import ErrorService
from games.base_game import BaseGame
from games.core.games_core import GamesCore
from games.core.gba_pokemon_core import GBAPokemonCoreFactory 

class GamesProvider:
    _FACTORY_REGISTRY: dict[AvailableGames, type[GamesCore]] = {
        AvailableGames.ORIGINAL_FIRE_RED: GBAPokemonCoreFactory,
        AvailableGames.RADICAL_FIRE_RED: GBAPokemonCoreFactory,
        AvailableGames.EMERALD: GBAPokemonCoreFactory,
        AvailableGames.EMERALD_KAIZO: GBAPokemonCoreFactory,
    }

    # Public Methods
    @staticmethod
    def create(game: AvailableGames, language: AvailableLanguages | str | None = None, config_service: ConfigService | None = None,
        redis_client: redis.Redis | None = None, game_file: bytearray | None = None, game_filename: str | None = None) -> BaseGame:
        
        resolved_config = config_service or GamesProvider.__resolve_config(game, language)

        
        translations_service = TranslationsService(resolved_config.get("CURRENT_LANGUAGE"))
        log_service = LogService(
            translations_service, resolved_config.get("LOG_TYPE")
        )
        error_service = ErrorService(log_service, translations_service)

        if game_file is not None and game_filename is not None:
            configured_path = resolved_config.get("ORIGINAL_GAME", "")
            expected_filename = Path(configured_path).name
            provided_filename = Path(game_filename).name

            if expected_filename and provided_filename != expected_filename:
                error_service.raise_error(
                    "errors.invalid_game_filename",
                    error_type="value",
                    provided_name=provided_filename,
                    expected_name=expected_filename,
                )

        GamesProvider.__log_config_status(resolved_config, translations_service, log_service, game)

        file_service = FileService(log_service, translations_service, resolved_config,error_service)

        # 2. Factory
        factory_cls = GamesProvider._FACTORY_REGISTRY.get(game)
        if not factory_cls:
            error_service.raise_error("errors.no_game", error_type="value", game=game)

        # 3. Family Build
        factory = factory_cls(
            config_service=resolved_config,
            log_service=log_service,
            file_service=file_service,
            translations_service=translations_service,
            error_service=error_service,
            redis_client=redis_client
        )
        return factory.create_game(game, game_file=game_file)
    # End Public Methods

    # Private Methods
    @staticmethod
    def __resolve_config(
        game: AvailableGames,
        language: AvailableLanguages | str | None = None,
    ) -> ConfigService:
        """Load game configuration or log a localized error if the config file is missing."""
        lang_str = language.name if isinstance(language, AvailableLanguages) else language
        try:
            return ConfigService.load_for_game(GAMES[int(game.value)], language=lang_str)
        except FileNotFoundError as exc:
            fallback_config = ConfigService.load_global()
            fallback_lang = lang_str or fallback_config.get("CURRENT_LANGUAGE", "EN_US")
            translator = TranslationsService(fallback_lang)
            logger = LogService(translator, fallback_config.get("LOG_TYPE"))
            error_service = ErrorService(logger, translator)

            error_service.raise_error(
                "errors.game_config_not_found",
                error_type="file_not_found",
                cause=exc,
                game_path=str(exc),
            )

    @staticmethod
    def __log_config_status(
        config_service: ConfigService,
        translations_service: TranslationsService,
        log_service: LogService,
        game: AvailableGames,
    ) -> None:
        """Log warnings for missing global config or unsupported languages and confirm load."""
        if config_service.get("missing_global"):
            log_service.warning(translations_service.translate("warnings.config.missing_global"))
        else:   
            log_service.info(translations_service.translate("messages.config.global_initialized"))

        if not config_service.get("available_language", True):
            log_service.warning(translations_service.translate("warnings.config.unsupported_language"))

        game_name = config_service.get("GAME_NAME", game.name)
        log_service.info(translations_service.translate("messages.config.game_initialized", game_name=game_name))
    # End Private Methods
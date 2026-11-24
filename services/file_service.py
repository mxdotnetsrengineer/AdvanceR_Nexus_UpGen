from pathlib import Path
from decorators.app_decorators import skip_when_enabled
from services.config_service import ConfigService
from services.error_service import ErrorService
from services.log_service import LogService
from services.translations_service import TranslationsService

BASE_DIR = Path(__file__).resolve().parent.parent


class FileService:
    def __init__(
        self,
        log_service: LogService,
        translations_service: TranslationsService,
        config_service: ConfigService,
        error_service: ErrorService,
    ):
        self.log = log_service
        self.translator = translations_service
        self.config = config_service
        self.errors = error_service

    def open_game(self, game_path: str) -> bytearray:
        resolved_path = self.__resolve_path(game_path)
        if not game_path or not resolved_path.is_file():
            self.errors.raise_error(
                "errors.game_not_found",
                error_type="file_not_found",
                game_path=game_path,
            )

        return bytearray(resolved_path.read_bytes())

    @skip_when_enabled("ONLY_DATABASE")
    def save_new_game_file(self, game_file: bytearray, output_path: str) -> None:
        if game_file is None:
            self.errors.raise_error("errors.no_game_data", error_type="runtime")

        if not output_path:
            self.errors.raise_error("errors.missing_output_path", error_type="key")

        resolved_path = self.__resolve_path(output_path)
        self.log.raw("=" * 80)
        self.log.info(self.translator.translate("messages.decryption_complete"))
        resolved_path.write_bytes(game_file)

    @staticmethod
    def __resolve_path(raw_path: str) -> Path:
        """Resolve relative file paths against the project root directory."""
        path = Path(raw_path)
        return path if path.is_absolute() else BASE_DIR / path
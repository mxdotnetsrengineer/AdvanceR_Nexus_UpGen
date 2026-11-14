import os
from services.translations_service import TranslationsService

class FileService:
    def __init__(
        self,
        log_service: LogService,
        translations_service: TranslationsService,
    ):
        self.log = log_service
        self.translator = translations_service

    # Public Methods
    def open_game(self, game_path: str) -> bytearray:
        if not game_path or not os.path.exists(game_path):
            msg = self.translator.translate("errors.game_not_found", game_path=game_path)
            self.log.error(msg, error_key="file_not_found")

        with open(game_path, "rb") as f:
            return bytearray(f.read())

    def save_new_game_file(self, game_file: bytearray, output_path: str) -> None:
        if game_file is None:
            msg = self.translator.translate("errors.no_game_data")
            self.log.error(msg, error_key="runtime")

        if not output_path:
            msg = self.translator.translate("errors.missing_output_path")
            self.log.error(msg, error_key="key")

        self.log.raw("=" * 80)
        self.log.info(self.translator.translate("messages.decryption_complete"))
        with open(output_path, "wb") as f:
            f.write(game_file)
    # End Public Methods
from pathlib import Path
from functools import lru_cache
from decorators.app_decorators import skip_when_enabled
from exceptions.domain_exceptions import DomainValidationError, ResourceNotFoundError, RomPreconditionError
from services.config_service import ConfigService
from services.error_service import ErrorService
from services.log_service import LogService
from services.translations_service import TranslationsService

BASE_DIR = Path(__file__).resolve().parent.parent
ALLOWED_ROM_EXTENSIONS = {".gba"}

@lru_cache(maxsize=8)
def _read_rom_cached(resolved_path: Path, mtime_ns: int, file_size: int) -> bytes:
    """Lee el archivo ROM una sola vez desde disco y lo mantiene inmutable en RAM."""
    return resolved_path.read_bytes()

class FileService:
    def __init__(
        self,
        log_service: LogService,
        translations_service: TranslationsService,
        config_service: ConfigService,
        error_service: ErrorService,
        roms_dir: Path | None = None,
        output_dir: Path | None = None
    ):
        self.log = log_service
        self.translator = translations_service
        self.config = config_service
        self.errors = error_service
        self._roms_dir = (roms_dir or BASE_DIR).resolve()
        self._output_dir = (output_dir or (BASE_DIR / "output")).resolve()

    def open_game_readonly(self, game_path: str) -> bytes:
        if not game_path:
            self.errors.raise_error(
                "errors.game_not_found",
                ResourceNotFoundError,
                game_path=game_path,
            )

        resolved_path = self._resolve_safe_path(game_path, base_dir=self._roms_dir)
        if resolved_path.suffix.lower() not in ALLOWED_ROM_EXTENSIONS:
            self.errors.raise_error(
                "errors.invalid_rom_extension",
                DomainValidationError,
                game_path=game_path,
            )

        if not resolved_path.is_file():
            self.errors.raise_error(
                "errors.game_not_found",
                ResourceNotFoundError,
                game_path=game_path,
            )

        file_stat = resolved_path.stat()
        return _read_rom_cached(resolved_path, file_stat.st_mtime_ns, file_stat.st_size)

    def open_game(self, game_path: str) -> bytearray:
        return bytearray(self.open_game_readonly(game_path))

    @skip_when_enabled("ONLY_DATABASE")
    def save_new_game_file(self, game_file: bytearray, output_path: str) -> Path:
        if game_file is None:
            self.errors.raise_error("errors.no_game_data", RomPreconditionError)

        if not output_path:
            self.errors.raise_error("errors.missing_output_path", DomainValidationError)

        resolved_path = self._resolve_safe_path(output_path, base_dir=self._output_dir)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        self.log.raw("=" * 80)
        self.log.info(self.translator.translate("messages.decryption_complete"))
        resolved_path.write_bytes(game_file)
        return resolved_path

    def _resolve_safe_output_path(self, raw_path: str) -> Path:
        """Resolve output path safely within the allowed output directory (or explicit absolute path)."""
        candidate = Path(raw_path)
        if candidate.is_absolute():
            return candidate.resolve()

        resolved = (self._output_dir / candidate).resolve()
        if not resolved.is_relative_to(self._output_dir):
            self.errors.raise_error(
                "errors.invalid_output_path",
                DomainValidationError,
                output_path=raw_path,
            )
        return resolved

    def _resolve_safe_path(self, raw_path: str, base_dir: Path) -> Path:
        """Resolve a path safely within `base_dir` (allowing explicit absolute paths for tests/CLI)."""
        candidate = Path(raw_path)
        if candidate.is_absolute():
            return candidate.resolve()

        resolved = (base_dir / candidate).resolve()
        if not resolved.is_relative_to(base_dir):
            self.errors.raise_error(
                "errors.invalid_file_path",
                DomainValidationError,
                file_path=raw_path,
            )
        return resolved
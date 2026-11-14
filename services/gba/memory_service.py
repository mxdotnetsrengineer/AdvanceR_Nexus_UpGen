from services.translations_service import TranslationsService
class GBAMemoryService:
    def __init__(self, translations_service: TranslationsService):
        self.game_file: bytearray | None = None
        self.free_space:int = 0
        self.translator = translations_service
        
    # Public Methods
    def find_free_space(self, size: int, start_offset: int = 0) -> int | None:
        if self.game_file is None:
            msg = self.translator.translate("errors.no_game_loaded")
            self.log.error(msg, error_key="runtime")

        search_bytes = b"\xFF" * size
        index = self.game_file.find(search_bytes, start_offset)
        return index if index != -1 else None

    def gba_pointer_to_file_offset(self, game_file: bytearray, gba_offset: int) -> int | None:
        four_bytes = game_file[gba_offset : gba_offset + 4]
        gba_address = int.from_bytes(four_bytes, byteorder="little")

        if 0x08000000 <= gba_address < 0x0A000000:
            return gba_address - 0x08000000
        return None
    # End Public Methods
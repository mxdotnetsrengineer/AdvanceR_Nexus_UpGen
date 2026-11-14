import copy
from enums.gba.games_enum import AvailableGames
from helpers.gba.pokemon.fire_red_helper import (FIRE_RED_NAMING_UPPER_KEYBOARD, FIRE_RED_NAMING_UPPER_LOGIC, 
    FIRE_RED_NAMING_LOWER_KEYBOARD, FIRE_RED_NAMING_LOWER_LOGIC, FIRE_RED_NAMING_OTHERS_KEYBOARD,FIRE_RED_NAMING_OTHERS_LOGIC)
from models.gba.pokemon.game_ui_keyboard import GameUIKeyboard
from models.gba.pokemon.game_ui_keyboard_logic import GameUIKeyboardLogic
from services.log_service import LogService
from services.file_service import FileService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.bank_service import BankService
from services.gba.pokemon.keyboard_service import GBAKeyboardService
from games.gba.gba_game import GBAGame  

class FireRedGame(GBAGame):
    def __init__(
        self,
        game: AvailableGames,
        file_service: FileService,
        log_service: LogService,
        memory_service: GBAMemoryService,
        config_service : ConfigService,
        bank_service: BankService,
        keyboard_service:GBAKeyboardService,
        translations_service: TranslationsService,
    ):
        # Parent Class
        super().__init__(game,file_service, log_service, memory_service, config_service, keyboard_service,translations_service)
        self.bank_service = bank_service
    
    def process_game(self):
        self.log_service.info(self.translations_service.translate("messages.games.starting_modification",game_name=self._get_value("GAME_NAME")))
        self.bank_service.allocate_banks(self.memory_service.game_file, True)
        
        if not self._get_value("ONLY_DATABASE") and self._get_value("ADD_SPANISH_CHARS"):
            self.keyboard_service.set_spanish_chars(self.memory_service.game_file,
                self.game, GameUIKeyboard(
                    default= copy.deepcopy(FIRE_RED_NAMING_UPPER_KEYBOARD),
                    lower=copy.deepcopy(FIRE_RED_NAMING_LOWER_KEYBOARD),
                    others=copy.deepcopy(FIRE_RED_NAMING_OTHERS_KEYBOARD),
                    logic = GameUIKeyboardLogic(
                        default=FIRE_RED_NAMING_UPPER_LOGIC,
                        lower=FIRE_RED_NAMING_LOWER_LOGIC,
                        others=FIRE_RED_NAMING_OTHERS_LOGIC,
                        offsets = [self._get_value("UPPER_KEYBOARD_CHARS_OFFSET"),self._get_value("LOWER_KEYBOARD_CHARS_OFFSET"),
                            self._get_value("OTHERS_KEYBOARD_CHARS_OFFSET")]
                    )
                ),self._get_value("DEFAULT_UI_KEYBOARD_SEPARATORS"))
        
        if not self._get_value("ONLY_DATABASE"): 
            self.file_service.save_new_game_file(self.memory_service.game_file, self._get_value("MODIFIED_GAME"));

            
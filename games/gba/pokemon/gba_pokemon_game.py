import copy
import asyncio
from enums.gba.games_enum import AvailableGames
from helpers.gba.pokemon.gba_pokemon_helper import (GBA_POKEMON_NAMING_UPPER_KEYBOARD, GBA_POKEMON_NAMING_UPPER_LOGIC, 
    GBA_POKEMON_NAMING_LOWER_KEYBOARD, GBA_POKEMON_NAMING_LOWER_LOGIC, GBA_POKEMON_NAMING_OTHERS_KEYBOARD,GBA_POKEMON_NAMING_OTHERS_LOGIC)
from models.gba.pokemon.game_ui_keyboard import GameUIKeyboard
from models.gba.pokemon.game_ui_keyboard_logic import GameUIKeyboardLogic
from services.log_service import LogService
from services.file_service import FileService
from services.config_service import ConfigService
from services.translations_service import TranslationsService
from services.gba.memory_service import GBAMemoryService
from services.gba.pokemon.bank_service import BankService
from services.gba.pokemon.keyboard_service import GBAKeyboardService
from services.gba.pokemon.stats_service import StatsService
from games.gba.gba_game import GBAGame
class GBAPokemonGame(GBAGame):
    def __init__(
        self,
        game: AvailableGames,
        file_service: FileService,
        log_service: LogService,
        memory_service: GBAMemoryService,
        config_service: ConfigService,
        bank_service: BankService,
        keyboard_service: GBAKeyboardService,
        stats_service: StatsService,
        translations_service: TranslationsService,
    ):
        super().__init__(
            game=game,
            file_service=file_service,
            log_service=log_service,
            memory_service=memory_service,
            config_service=config_service,
            translations_service=translations_service,
        )
        self.bank_service = bank_service
        self.keyboard_service = keyboard_service
        self.stats_service = stats_service

    # Public Methods
    async def process_game(self) -> None:
        self.log_service.info(
            self.translations_service.translate(
                "messages.games.starting_modification",
                game_name=self._get("GAME_NAME"),
            )
        )

        await asyncio.gather(
            self.bank_service.allocate_banks(self.memory_service.game_file),
            self.stats_service.get_all_species_data(self.memory_service.game_file)
        )   

        self.bank_service.randomize_banks_wild_encounters(self.memory_service.game_file, self.stats_service.stats)

        await self.__configure_spanish_keyboard()
        self._apply_game_specific_changes()

        self.file_service.save_new_game_file(
            self.memory_service.game_file,
            self._get("MODIFIED_GAME"),
        )
    # End Public Methods

    # Protected Methods
    def _apply_game_specific_changes(self) -> None:
        pass
    # End Protected Methods

    # Private Methods
    async def __configure_spanish_keyboard(self) -> None:
        keyboard_layout = GameUIKeyboard(
            default=copy.deepcopy(GBA_POKEMON_NAMING_UPPER_KEYBOARD),
            lower=copy.deepcopy(GBA_POKEMON_NAMING_LOWER_KEYBOARD),
            others=copy.deepcopy(GBA_POKEMON_NAMING_OTHERS_KEYBOARD),
            logic=GameUIKeyboardLogic(
                default=GBA_POKEMON_NAMING_UPPER_LOGIC,
                lower=GBA_POKEMON_NAMING_LOWER_LOGIC,
                others=GBA_POKEMON_NAMING_OTHERS_LOGIC,
                offsets=[
                    self._get("UPPER_KEYBOARD_CHARS_OFFSET"),
                    self._get("LOWER_KEYBOARD_CHARS_OFFSET"),
                    self._get("OTHERS_KEYBOARD_CHARS_OFFSET"),
                ],
            ),
        )
        await self.keyboard_service.set_spanish_chars(
            self.memory_service.game_file,
            self.game,
            keyboard_layout,
            self._get("DEFAULT_UI_KEYBOARD_SEPARATORS"),
        )
    # End Private Methods
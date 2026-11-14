from games.gba.pokemon.gb_pokemon_game import GBAPokemonGame 

class FireRedGame(GBAPokemonGame):
    def _apply_game_specific_changes(self) -> None:
        pass
        self.file_service.save_new_game_file(self.memory_service.game_file, self._get("MODIFIED_GAME"));
            

            
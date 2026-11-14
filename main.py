from settings import GAMES, init_global_config, current_config
from enums.gba.games_enum import AvailableGames
from games.current_game import CurrentGameFactory

if __name__ == "__main__":
    current_game = AvailableGames.ORIGINAL_FIRE_RED
    init_global_config(GAMES[int(current_game.value[0])])
    
    game_instance = CurrentGameFactory.create(
        game=current_game, 
        game_config=current_config
    )
    game_instance.process_game()
    
import asyncio
from settings import init_global_config, current_config
from enums.gba.games_enum import AvailableGames
from helpers.gba.pokemon.gba_pokemon_helper import GAMES
from games.core.games_provider import GamesProvider

if __name__ == "__main__":
    current_game = AvailableGames.RADICAL_FIRE_RED
    init_global_config(GAMES[int(current_game.value)])
    
    game_instance = GamesProvider.create(
        game=current_game, 
        game_config=current_config
    )

    asyncio.run(game_instance.process_game())
    
from decorators.app_decorators import keys_from_str
from enum import IntEnum

@keys_from_str
class GBAPokemonKeyIndex:
    """
    A, B, C, D, E, F, SPACE_1, DOT,
    G, H, I, J, K, L, SPACE_2, COMMA,
    M, N, O, P, Q, R, S, SPACE_3
    T, U, V, W, X, Y, Z, SPACE_4
    """

@keys_from_str
class GBAPokemonLogicKeyIndex:
    __doc__ = ", ".join(
        k.name for k in GBAPokemonKeyIndex if not k.name.startswith("SPACE")
    )

@keys_from_str
class GBAPokemonOthersKeyIndex:
     """
    NUM_0, NUM_1, NUM_2, NUM_3, NUM_4, SPACE_1
    NUM_5, NUM_6, NUM_7, NUM_8, NUM_9, SPACE_2
    EXCLAMATION, QUESTION, MALE, FEMALE, SLASH, HYPHEN, SPACE_3
    ELLIPSIS, QUOTE_DOUBLE_OPEN, QUOTE_DOUBLE_CLOSE, QUOTE_SINGLE_OPEN, QUOTE_SINGLE_CLOSE, SPACE_4
    """

@keys_from_str
class GBAPokemonOthersLogicKeyIndex:
    __doc__ = ", ".join(
        k.name for k in GBAPokemonOthersKeyIndex if not k.name.startswith("SPACE")
    )

class ItemPockets(IntEnum):
    ITEMS = 1
    KEY_ITEMS = 2
    POKE_BALLS = 3
    TMS_HMS = 4
    BERRIES = 5
    UNKNOWN = 0

class ItemSubCategories(IntEnum):
    MAIL = 0                  # Mail items (0x00 in FireRed)
    PARTY_CONSUMABLE = 1      # Potions, status healers, vitamins, and evolution stones (0x01)
    FIELD_USE = 2             # Repels, Escape Rope, Bike, Rods (0x02)
    POUCH_OR_TM = 3           # Special pouches and TMs/HMs (0x03)
    PASSIVE_OR_TREASURE = 4   # Passive held items, scarves, and sellable treasures (0x04)
    COMPETITIVE_HELD = 5      # Custom/Special use items (0x05)
    UNKNOWN = 7               # Fallback for custom/unrecognized fan games types
    NONE = 0xFF               # Poké Balls & passive Key Items (no subcategory needed)

class BankMethods(IntEnum):
    RANDOMIZE_POKEBALLS_ITEMS = 1,
    RANDOMIZE_WILD_POKEMONS = 2,
    ALL = 3
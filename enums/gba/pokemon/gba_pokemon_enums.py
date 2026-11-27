from decorators.app_decorators import keys_from_str
from enum import IntEnum, auto

class GBAPokemonKeyIndex(IntEnum):
    A = 0
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    F = auto()
    SPACE_1 = auto()
    DOT = auto()
    G = auto()
    H = auto()
    I = auto()
    J = auto()
    K = auto()
    L = auto()
    SPACE_2 = auto()
    COMMA = auto()
    M = auto()
    N = auto()
    O = auto()
    P = auto()
    Q = auto()
    R = auto()
    S = auto()
    SPACE_3 = auto()
    T = auto()
    U = auto()
    V = auto()
    W = auto()
    X = auto()
    Y = auto()
    Z = auto()
    SPACE_4 = auto()


class GBAPokemonLogicKeyIndex(IntEnum):
    A = 0
    B = auto()
    C = auto()
    D = auto()
    E = auto()
    F = auto()
    DOT = auto()
    G = auto()
    H = auto()
    I = auto()
    J = auto()
    K = auto()
    L = auto()
    COMMA = auto()
    M = auto()
    N = auto()
    O = auto()
    P = auto()
    Q = auto()
    R = auto()
    S = auto()
    T = auto()
    U = auto()
    V = auto()
    W = auto()
    X = auto()
    Y = auto()
    Z = auto()


class GBAPokemonOthersKeyIndex(IntEnum):
    NUM_0 = 0
    NUM_1 = auto()
    NUM_2 = auto()
    NUM_3 = auto()
    NUM_4 = auto()
    SPACE_1 = auto()
    NUM_5 = auto()
    NUM_6 = auto()
    NUM_7 = auto()
    NUM_8 = auto()
    NUM_9 = auto()
    SPACE_2 = auto()
    EXCLAMATION = auto()
    QUESTION = auto()
    MALE = auto()
    FEMALE = auto()
    SLASH = auto()
    HYPHEN = auto()
    SPACE_3 = auto()
    ELLIPSIS = auto()
    QUOTE_DOUBLE_OPEN = auto()
    QUOTE_DOUBLE_CLOSE = auto()
    QUOTE_SINGLE_OPEN = auto()
    QUOTE_SINGLE_CLOSE = auto()
    SPACE_4 = auto()


class GBAPokemonOthersLogicKeyIndex(IntEnum):
    NUM_0 = 0
    NUM_1 = auto()
    NUM_2 = auto()
    NUM_3 = auto()
    NUM_4 = auto()
    NUM_5 = auto()
    NUM_6 = auto()
    NUM_7 = auto()
    NUM_8 = auto()
    NUM_9 = auto()
    EXCLAMATION = auto()
    QUESTION = auto()
    MALE = auto()
    FEMALE = auto()
    SLASH = auto()
    HYPHEN = auto()
    ELLIPSIS = auto()
    QUOTE_DOUBLE_OPEN = auto()
    QUOTE_DOUBLE_CLOSE = auto()
    QUOTE_SINGLE_OPEN = auto()
    QUOTE_SINGLE_CLOSE = auto()

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
    RANDOMIZE_POKEBALLS_ITEMS = 1
    RANDOMIZE_WILD_POKEMONS = 2
    ALL = 3
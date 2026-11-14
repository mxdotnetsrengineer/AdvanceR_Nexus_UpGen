from decorators.app_decorators import keys_from_str

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
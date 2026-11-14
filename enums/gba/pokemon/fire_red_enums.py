from enums.enum_base import keys_from_str

@keys_from_str
class FireRedKeyIndex:
    """
    A, B, C, D, E, F, SPACE_1, DOT,
    G, H, I, J, K, L, SPACE_2, COMMA,
    M, N, O, P, Q, R, S, SPACE_3
    T, U, V, W, X, Y, Z, SPACE_4
    """

@keys_from_str
class FireRedLogicKeyIndex:
    __doc__ = ", ".join(
        k.name for k in FireRedKeyIndex if not k.name.startswith("SPACE")
    )

@keys_from_str
class FireRedOthersKeyIndex:
     """
    NUM_0, NUM_1, NUM_2, NUM_3, NUM_4, SPACE_1
    NUM_5, NUM_6, NUM_7, NUM_8, NUM_9, SPACE_2
    EXCLAMATION, QUESTION, MALE, FEMALE, SLASH, HYPHEN, SPACE_3
    ELLIPSIS, QUOTE_DOUBLE_OPEN, QUOTE_DOUBLE_CLOSE, QUOTE_SINGLE_OPEN, QUOTE_SINGLE_CLOSE, SPACE_4
    """

@keys_from_str
class FireRedOthersLogicKeyIndex:
    __doc__ = ", ".join(
        k.name for k in FireRedOthersKeyIndex if not k.name.startswith("SPACE")
    )
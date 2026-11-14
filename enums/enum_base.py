from enum import IntEnum

def keys_from_str(cls):
    names = cls.__doc__.replace(",", " ").split()
    return IntEnum(cls.__name__, {name: i for i, name in enumerate(names)})
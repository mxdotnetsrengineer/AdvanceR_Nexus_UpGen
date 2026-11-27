from enum import Enum, auto

class AvailableLanguages(Enum):
    EN_US = 0
    ES_MX = 1

class NavAction(Enum):
    BACK = "NAV_BACK"
    EXIT = "NAV_EXIT"
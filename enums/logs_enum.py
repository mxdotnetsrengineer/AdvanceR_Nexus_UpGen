from enum import StrEnum

class LogLevels(StrEnum):
    NONE = "NONE"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    ERROR_AND_WARNING = "ERROR_AND_WARNING"
    ALL = "ALL"
from enums.logs_enum import LogLevel

ERROR_TYPES: dict[str, type[Exception]] = {
    "value": ValueError,
    "type": TypeError,
    "key": KeyError,
    "index": IndexError,
    "file_not_found": FileNotFoundError,
    "runtime": RuntimeError,
    "not_implemented": NotImplementedError,
}

ALLOWED_OUTPUTS: dict[LogLevel, set[str]] = {
    LogLevel.NONE: set(),
    LogLevel.INFO: {"info"},
    LogLevel.WARNING: {"warning"},
    LogLevel.ERROR: {"error"},
    LogLevel.ERROR_AND_WARNING: {"error", "warning"},
    LogLevel.ALL: {"info", "warning", "error"},
}

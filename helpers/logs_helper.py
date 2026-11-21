from enums.logs_enum import LogLevels

ERROR_TYPES: dict[str, type[Exception]] = {
    "value": ValueError,
    "type": TypeError,
    "key": KeyError,
    "index": IndexError,
    "file_not_found": FileNotFoundError,
    "runtime": RuntimeError,
    "not_implemented": NotImplementedError,
}

ALLOWED_OUTPUTS: dict[LogLevels, set[str]] = {
    LogLevels.NONE: set(),
    LogLevels.INFO: {"info"},
    LogLevels.WARNING: {"warning"},
    LogLevels.ERROR: {"error"},
    LogLevels.ERROR_AND_WARNING: {"error", "warning"},
    LogLevels.ALL: {"info", "warning", "error"},
}

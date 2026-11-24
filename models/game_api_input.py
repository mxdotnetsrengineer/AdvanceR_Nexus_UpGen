from dataclasses import dataclass


@dataclass(frozen=True)
class GameAPIInput:
    game_id: int | None = None
    raw_file: bytes | None = None
    filename: str | None = None
    language: str | None = None
from dataclasses import dataclass


@dataclass(frozen=True)
class GameInput:
    current_game: str | None = None
    raw_file: bytes | None = None
    filename: str | None = None
    language: str | None = None

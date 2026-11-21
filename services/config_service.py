from typing import Any

class ConfigService:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    def get(self, property_name: str) -> Any:
        return self.config.get(property_name)

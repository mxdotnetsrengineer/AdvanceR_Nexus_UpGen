from typing import Any

class ConfigService:
    def __init__(self, config: dict[str, Any]):
        self.config = config

   # Public Methods
    def get(self, property_name: str) -> Any:
        return self.config.get(property_name)
    # End Public Methods
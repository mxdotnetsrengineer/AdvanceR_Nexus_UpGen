class ConfigService:
    def __init__(self, config: dict[str, Any]):
        self.config = config

   # Public Methods
    def get_value(self, property_name: str) -> Any:
        return self.config[property_name]
    # End Public Methods
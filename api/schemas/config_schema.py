from pydantic import BaseModel
from enum import StrEnum
from enums.app_enums import AvailableLanguages

class LanguageSelection(StrEnum):
    EN_US = "English"
    ES_MX = "Spanish"

    def to_domain_enum(self) -> AvailableLanguages:
        return AvailableLanguages[self.name]


class UpdateLanguageResponse(BaseModel):
    language: str
    message: str
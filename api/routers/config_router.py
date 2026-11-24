from fastapi import APIRouter, Depends, Form, Response
from api.schemas.config_schema import LanguageSelection, UpdateLanguageResponse
from facades.config_facade import ConfigFacade


router = APIRouter(prefix="/config", tags=["Configuration"])


def get_config_facade() -> ConfigFacade:
    raise NotImplementedError("ConfigFacade dependency not configured.")


@router.patch("/language", response_model=UpdateLanguageResponse)
async def update_language(
    response: Response,
    language: LanguageSelection = Form(...),
    config_facade: ConfigFacade = Depends(get_config_facade),
) -> UpdateLanguageResponse:
    domain_lang = language.to_domain_enum()
    active_lang, message, max_age = config_facade.get_language_cookie_data(domain_lang)

    response.set_cookie(
        key="app_language",
        value=active_lang,
        max_age=max_age,
        httponly=True,
        samesite="lax",
    )

    return UpdateLanguageResponse(language=active_lang, message=message)
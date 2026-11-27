import string
import pytest
from enums.app_enums import AvailableLanguages
from services.translations_service import TranslationsService, DEFAULT_LOCALES_DIR

def _extract_placeholders(template: str) -> set[str]:
    """Extract all {field_name} placeholders from a format string."""
    formatter = string.Formatter()
    return {
        field_name
        for _, field_name, _, _ in formatter.parse(template)
        if field_name is not None
    }

@pytest.fixture(scope="module")
def loaded_locales() -> dict[str, dict[str, str]]:
    service = TranslationsService(default_locale=AvailableLanguages.EN_US.name)
    locales = [lang.name for lang in AvailableLanguages]
    service.preload_locales(locales)

    return {
        locale: service._SHARED_CACHE[(DEFAULT_LOCALES_DIR.resolve(), locale)]
        for locale in locales
    }

def test_all_locales_have_exact_same_keys(loaded_locales: dict[str, dict[str, str]]):
    base_locale = AvailableLanguages.EN_US.name
    base_keys = set(loaded_locales[base_locale].keys())

    for locale, translations in loaded_locales.items():
        if locale == base_locale:
            continue

        current_keys = set(translations.keys())
        missing = base_keys - current_keys
        extra = current_keys - base_keys

        assert not missing, f"Locale '{locale}' is missing keys: {sorted(missing)}"
        assert not extra, f"Locale '{locale}' has extra keys not in '{base_locale}': {sorted(extra)}"


def test_all_locales_have_matching_placeholders(loaded_locales: dict[str, dict[str, str]]):
    base_locale = AvailableLanguages.EN_US.name
    base_translations = loaded_locales[base_locale]

    for locale, translations in loaded_locales.items():
        if locale == base_locale:
            continue

        for key, base_value in base_translations.items():
            target_value = translations.get(key)
            if not isinstance(base_value, str) or not isinstance(target_value, str):
                continue

            base_placeholders = _extract_placeholders(base_value)
            target_placeholders = _extract_placeholders(target_value)

            assert base_placeholders == target_placeholders, (
                f"Placeholder mismatch for key '{key}' between '{base_locale}' "
                f"({base_placeholders}) and '{locale}' ({target_placeholders})"
            )
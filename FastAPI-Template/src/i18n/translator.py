from __future__ import annotations

from core.ctx import CTX_LANG

from .catalog import CATALOG


def get_locale() -> str:
    lang = CTX_LANG.get() or "en"
    if lang.startswith("zh"):
        return "zh"
    return "en"


def t(key: str, **kwargs: object) -> str:
    """Translate a message key using the current request locale.

    Falls back to English, then to the key itself.
    """
    locale = get_locale()
    text = CATALOG.get(locale, {}).get(key)
    if text is None:
        text = CATALOG.get("en", {}).get(key, key)
    try:
        return text.format(**kwargs)
    except Exception:
        return text

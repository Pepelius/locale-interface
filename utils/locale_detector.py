from __future__ import annotations

import re

_ISO_639_1 = {
    "af", "sq", "am", "ar", "hy", "az", "eu", "be", "bn", "bs",
    "bg", "ca", "zh", "hr", "cs", "da", "nl", "en", "eo", "et",
    "fi", "fr", "fy", "gl", "ka", "de", "el", "gu", "ht", "ha",
    "he", "hi", "hu", "is", "id", "ga", "it", "ja", "kn", "kk",
    "ko", "lo", "lv", "lt", "mk", "ms", "ml", "mt", "mr", "mn",
    "my", "ne", "no", "pl", "pt", "ro", "ru", "sr", "sk", "sl",
    "so", "es", "sw", "sv", "ta", "te", "th", "tr", "uk", "ur",
    "uz", "vi", "cy", "yo", "zu",
}

_LOCALE_RE = re.compile(r"^([a-z]{2,3})(?:[_-][A-Za-z]{2,4})?$")


def is_locale_code(name: str) -> bool:
    m = _LOCALE_RE.match(name)
    return bool(m) and m.group(1) in _ISO_639_1


def detect_language_from_filename(stem: str) -> str | None:
    """Extract a locale code from a file stem.

    Handles: "en", "en_US", "messages_en", "strings.en", "en-messages".
    """
    if is_locale_code(stem):
        return stem
    for sep in ("_", "-", "."):
        for part in stem.split(sep):
            if is_locale_code(part):
                return part
    return None

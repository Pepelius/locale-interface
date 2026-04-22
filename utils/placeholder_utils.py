from __future__ import annotations

import re

_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


def extract_placeholders(text: str) -> set[str]:
    return set(_PLACEHOLDER_RE.findall(text))


def validate_consistency(translations: dict[str, str]) -> dict[str, list[str]]:
    """Check all non-empty translations use the same {{variable}} placeholders.

    Returns {lang: [issue_descriptions]} for any mismatches; empty dict if all good.
    """
    non_empty = {lang: t for lang, t in translations.items() if t.strip()}
    if len(non_empty) < 2:
        return {}

    by_lang = {lang: extract_placeholders(t) for lang, t in non_empty.items()}
    ref_placeholders = next(iter(by_lang.values()))

    issues: dict[str, list[str]] = {}
    for lang, placeholders in by_lang.items():
        lang_issues = (
            [f"Missing: {{{{{p}}}}}" for p in ref_placeholders - placeholders]
            + [f"Extra: {{{{{p}}}}}" for p in placeholders - ref_placeholders]
        )
        if lang_issues:
            issues[lang] = lang_issues
    return issues

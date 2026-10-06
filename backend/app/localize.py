"""Per-language merge for admin-authored content (blogs, calendar, events).

Base fields stay canonical; translations are optional and may be filled in
later, one language at a time. Missing translations fall back to base text.
"""
from __future__ import annotations


def merge_lang(data: dict, translations: dict | None, lang: str, fields: list[str]) -> dict:
    if not lang or lang == "en" or not translations:
        return data
    tr = (translations or {}).get(lang) or {}
    for f in fields:
        v = tr.get(f)
        if v:
            data[f] = v
    return data

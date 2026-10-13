#!/usr/bin/env python3
"""Confidential topics that must never become knowledge cards.

Sessions about personnel evaluation or company management (Xtone, PKSHA) are
dropped at extraction, and cards that still mention them fail validation. The
patterns come from confidential_topics.json at the plugin root, plus an optional
personal file at ~/.claude/knowledge-cards/confidential_topics.json.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parents[3] / "confidential_topics.json"
LOCAL_FILE = Path.home() / ".claude" / "knowledge-cards" / "confidential_topics.json"


def default_files() -> list[Path]:
    return [DEFAULT_FILE] + ([LOCAL_FILE] if LOCAL_FILE.is_file() else [])


def load_topics(paths: list[Path] | None = None, require: bool = False) -> list[tuple[str, str, re.Pattern[str]]]:
    """(id, label, compiled pattern) per topic; topics with the same id are merged.

    With require=True an empty result is an error, so a missing or emptied file
    stops extraction instead of silently letting every session through.
    """
    merged: dict[str, tuple[str, list[str]]] = {}
    for path in default_files() if paths is None else paths:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"cannot read confidential topics {path}: {exc}") from None
        for topic in data.get("topics", []) if isinstance(data, dict) else []:
            tid = str(topic.get("id", "")).strip()
            patterns = [str(p) for p in topic.get("patterns", []) if str(p).strip()]
            if not tid or not patterns:
                continue
            label, existing = merged.get(tid, (str(topic.get("label") or tid), []))
            merged[tid] = (label, existing + patterns)
    topics = []
    for tid, (label, patterns) in merged.items():
        try:
            topics.append((tid, label, re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)))
        except re.error as exc:
            raise ValueError(f"bad pattern in confidential topic {tid}: {exc}") from None
    if require and not topics:
        names = ", ".join(str(p) for p in (default_files() if paths is None else paths))
        raise ValueError(f"no confidential topics loaded from {names}; refusing to run without the filter")
    return topics


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", str(text))


def match_topic(text: str, topics) -> str | None:
    """Id of the first confidential topic the text touches, or None."""
    if not text:
        return None
    norm = normalize(text)
    for tid, _, pattern in topics:
        if pattern.search(norm):
            return tid
    return None

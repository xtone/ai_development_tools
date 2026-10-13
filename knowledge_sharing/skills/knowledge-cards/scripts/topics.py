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


def _compile(tid: str, patterns: list[str]) -> re.Pattern[str] | None:
    if not patterns:
        return None
    try:
        return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)
    except re.error as exc:
        raise ValueError(f"bad pattern in confidential topic {tid}: {exc}") from None


def load_topics(paths: list[Path] | None = None, require: bool = False) -> list[tuple]:
    """(id, label, strong pattern, review pattern) per topic; topics with the same id are merged.

    strong (patterns): always excluded. review (review_patterns): words that also have
    ordinary meanings; excluded by default, and only a person who checked the session
    may let it back in. With require=True an empty result is an error, so a missing or
    emptied file stops extraction instead of silently letting every session through.
    """
    merged: dict[str, tuple[str, list[str], list[str]]] = {}
    for path in default_files() if paths is None else paths:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"cannot read confidential topics {path}: {exc}") from None
        for topic in data.get("topics", []) if isinstance(data, dict) else []:
            tid = str(topic.get("id", "")).strip()
            strong = [str(p) for p in topic.get("patterns", []) if str(p).strip()]
            review = [str(p) for p in topic.get("review_patterns", []) if str(p).strip()]
            if not tid or not (strong or review):
                continue
            label, s0, r0 = merged.get(tid, (str(topic.get("label") or tid), [], []))
            merged[tid] = (label, s0 + strong, r0 + review)
    topics = [(tid, label, _compile(tid, strong), _compile(tid, review)) for tid, (label, strong, review) in merged.items()]
    if require and not any(t[2] for t in topics):
        names = ", ".join(str(p) for p in (default_files() if paths is None else paths))
        raise ValueError(f"no confidential topics loaded from {names}; refusing to run without the filter")
    return topics


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", str(text))


def classify(text: str, topics) -> tuple[str, str, str] | None:
    """(topic id, "strong" or "review", matched words) for the first hit; strong words win."""
    if not text:
        return None
    norm = normalize(text)
    for level, index in (("strong", 2), ("review", 3)):
        for topic in topics:
            pattern = topic[index]
            m = pattern.search(norm) if pattern else None
            if m:
                return topic[0], level, m.group(0)
    return None


def match_topic(text: str, topics) -> str | None:
    """Id of the confidential topic the text touches (strong or review words), or None."""
    hit = classify(text, topics)
    return hit[0] if hit else None


def blocked(text: str, topics, allow_review: bool = False, allowed_terms=()) -> tuple[str, str, str] | None:
    """The hit that keeps text out: strong words always; review words unless allowed."""
    hit = classify(text, topics)
    if not hit:
        return None
    if hit[1] == "review" and (allow_review or normalize(hit[2]).lower() in {normalize(t).lower() for t in allowed_terms}):
        # A cleared review word must not hide a strong word later in the text.
        strong_only = [(t[0], t[1], t[2], None) for t in topics]
        return classify(text, strong_only)
    return hit

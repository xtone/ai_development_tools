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


# Markdown / Notion-flavored Markdown that changes how text is displayed but not what it says.
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MARKUP = re.compile(r"<[^>]*>|\\|[*_~`]")


def normalize(text: str) -> str:
    """NFKC, without invisible format characters (zero-width space, BOM, ...) and combining
    marks (variation selectors, ...), so neither can split a word."""
    return "".join(ch for ch in unicodedata.normalize("NFKC", str(text)) if unicodedata.category(ch) not in ("Cf", "Mn"))


def displayed(text: str) -> str:
    """Roughly what Notion shows for the text: links reduced to their label, tags, escapes and
    emphasis marks removed. `取**締**役` and `経<span>営</span>会議` read as the words they spell."""
    return _MARKUP.sub("", _LINK.sub(r"\1", str(text)))


def variants(text: str) -> list[str]:
    """The text as written and as displayed (both normalized); matching runs on each."""
    written = normalize(text or "")
    shown = normalize(displayed(text or ""))
    return [written] if shown == written else [written, shown]


def classify(text: str, topics) -> tuple[str, str, str] | None:
    """(topic id, "strong" or "review", matched words) for the first hit; strong words win.

    The text is checked as written and as displayed, so markup that splits a word on the
    page (a parser differential) does not hide it.
    """
    if not text:
        return None
    forms = variants(text)
    for level, index in (("strong", 2), ("review", 3)):
        for topic in topics:
            pattern = topic[index]
            if not pattern:
                continue
            for form in forms:
                m = pattern.search(form)
                if m:
                    return topic[0], level, m.group(0)
    return None


def match_topic(text: str, topics) -> str | None:
    """Id of the confidential topic the text touches (strong or review words), or None."""
    hit = classify(text, topics)
    return hit[0] if hit else None


def review_words(text: str, topics) -> set[str]:
    """Every review word in the text (as written and as displayed), so a person sees all of them."""
    return {m.group(0) for form in variants(text) for topic in topics if topic[3] for m in topic[3].finditer(form)}


def blocked(text: str, topics, allowed_terms=()) -> tuple[str, str, str] | None:
    """The hit that keeps text out, or None.

    Strong words always block. A review word blocks unless the person allowed that exact
    word; allowed words are blanked out one at a time and the text is checked again, so
    clearing one word never clears a different review word or a strong word next to it.
    """
    allowed = {normalize(t).lower() for t in allowed_terms if str(t).strip()}
    for current in variants(text):
        for _ in range(len(current) + 1):
            hit = classify(current, topics)
            if not hit:
                break
            if hit[1] == "strong" or normalize(hit[2]).lower() not in allowed:
                return hit
            current = re.sub(re.escape(hit[2]), " ", current, flags=re.IGNORECASE)
    return None

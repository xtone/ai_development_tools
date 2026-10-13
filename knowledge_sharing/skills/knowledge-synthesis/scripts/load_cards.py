#!/usr/bin/env python3
"""Normalize knowledge cards read from Notion into the input of a weekly synthesis.

Usage:
  load_cards.py QUERY.json [QUERY2.json ...] --week 2026-W43 --out cards-2026-W43.json

QUERY.json is the result of Notion MCP query-data-sources (SQL) on the cards data
source, saved as is ({"results": [...]}) or as a plain list of rows. Several pages of
results may be given; rows are merged by url.

The output holds the week, metrics, fact cards (for the project table) and opinion
cards (for themes). Authors are replaced by anonymous labels (p1, p2, ...) so the
synthesis can count people per theme without names. Cards that touch a confidential
topic with a strong word are left out and only counted.

Exit code: 0 on success, 2 on input errors.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

CARDS_SCRIPTS = Path(__file__).resolve().parents[2] / "knowledge-cards" / "scripts"
sys.path.insert(0, str(CARDS_SCRIPTS))
try:
    from cards import InputError, load_questions, normalize, questions_by_id, week_info  # noqa: E402
    from topics import classify, default_files, load_topics, review_words  # noqa: E402
except ImportError as exc:  # pragma: no cover - depends on the installed plugin
    print(f"error: knowledge-cards scripts not found at {CARDS_SCRIPTS}: {exc}", file=sys.stderr)
    sys.exit(2)

DEFAULT_QUESTIONS = Path(__file__).resolve().parents[3] / "questions.json"
COLUMNS = {
    "カード": "claim",
    "問い": "question_id",
    "プロジェクト": "projects",
    "極性": "polarity",
    "確度": "confidence",
    "タグ": "tags",
    "文脈": "context",
    "根拠": "evidence",
    "投稿者": "authors",
    "公開範囲": "sensitivity",
}
LIST_FIELDS = ("projects", "tags", "authors")


def _as_list(value) -> list[str]:
    """Notion SQL returns multi-values as JSON strings; MCP rows mode returns lists."""
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return [str(value)]
    return [str(v) for v in parsed] if isinstance(parsed, list) else [str(parsed)]


def read_rows(paths: list[Path]) -> list[dict]:
    rows: dict[str, dict] = {}
    for path in paths:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise InputError(f"cannot read {path}: {exc}") from None
        items = data.get("results", []) if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise InputError(f"{path}: expected a list of rows or {{\"results\": [...]}}")
        for row in items:
            if isinstance(row, dict) and row.get("url"):
                rows[row["url"]] = row
    return list(rows.values())


def normalize_row(row: dict) -> dict:
    card = {"url": row["url"]}
    for column, key in COLUMNS.items():
        value = row.get(column)
        card[key] = _as_list(value) if key in LIST_FIELDS else ("" if value is None else str(value))
    return card


def _text(card: dict) -> str:
    return "\n".join([card["claim"], card["context"], card["evidence"], *card["projects"]])


def load(rows: list[dict], catalog: dict, topics) -> dict:
    by_id = questions_by_id(catalog)
    order = [q["id"] for q in catalog["questions"]]
    labels: dict[str, str] = {}
    cards: list[dict] = []
    excluded = Counter()
    for row in rows:
        card = normalize_row(row)
        if card["question_id"] not in by_id:
            excluded["unknown_question"] += 1
            continue
        hit = classify(_text(card), topics)
        if hit and hit[1] == "strong":
            # Submitted before the filter existed, or edited in Notion: never synthesize it.
            excluded["confidential"] += 1
            continue
        card["review_words"] = sorted(review_words(_text(card), topics))
        author = card.pop("authors")[0] if card["authors"] else ""
        if author and author not in labels:
            labels[author] = f"p{len(labels) + 1}"
        card["person"] = labels.get(author, "p?")
        cards.append(card)

    cards.sort(key=lambda c: (order.index(c["question_id"]), c["url"]))
    kept: list[dict] = []
    seen: dict[tuple, dict] = {}
    for card in cards:
        key = (card["question_id"], tuple(sorted(card["projects"])), card["person"], normalize(card["claim"]))
        if key in seen:
            seen[key].setdefault("duplicates", []).append(card["url"])
            excluded["duplicates"] += 1
            continue
        seen[key] = card
        kept.append(card)

    facts = [c for c in kept if by_id[c["question_id"]]["polarity"] == "fact"]
    opinions = [c for c in kept if by_id[c["question_id"]]["polarity"] != "fact"]
    metrics = {
        "people": len({c["person"] for c in kept}),
        "cards": len(kept),
        "by_question": {q: n for q, n in sorted(Counter(c["question_id"] for c in kept).items(), key=lambda kv: order.index(kv[0]))},
        "by_polarity": dict(sorted(Counter(c["polarity"] for c in kept).items())),
        "observed": sum(1 for c in kept if c["confidence"] == "observed"),
    }
    return {"metrics": metrics, "facts": facts, "opinions": opinions, "excluded": dict(excluded)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize Notion knowledge cards for a weekly synthesis.")
    parser.add_argument("queries", nargs="+", help="saved results of Notion query-data-sources")
    parser.add_argument("--week", required=True, help="2026-W43")
    parser.add_argument("--out", required=True)
    parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS))
    parser.add_argument("--topics", action="append", default=None, help="extra confidential_topics.json")
    args = parser.parse_args(argv)
    try:
        info = week_info(args.week)
        catalog = load_questions(Path(args.questions))
        topics = load_topics(default_files() + [Path(t) for t in args.topics or []], require=True)
        result = {"week": info["week"], "title": info["title"], **load(read_rows([Path(q) for q in args.queries]), catalog, topics)}
    except (InputError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    m = result["metrics"]
    print(
        f"wrote {out}: {m['people']} people, {m['cards']} cards "
        f"({len(result['facts'])} facts, {len(result['opinions'])} opinions); excluded {result['excluded'] or 0}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

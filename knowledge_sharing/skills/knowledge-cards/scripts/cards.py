#!/usr/bin/env python3
"""Knowledge cards: week math, question plan, validation, Markdown round trip and Notion payloads.

Usage:
  cards.py week [--week 2026-W43] [--today YYYY-MM-DD]
  cards.py plan --week 2026-W43 [--ids P1,Q1] [--questions questions.json]
  cards.py validate CARDS.jsonl [--questions questions.json]
  cards.py render CARDS.jsonl --out cards-2026-W43.md [--questions questions.json]
  cards.py parse CARDS.md --base CARDS.jsonl --out CARDS.jsonl
  cards.py dedupe CARDS.jsonl --submitted submitted.jsonl
  cards.py to-notion CARDS.jsonl --week-url URL --author USER_ID|me
  cards.py mark-submitted CARDS.jsonl --submitted submitted.jsonl --results results.json
  cards.py options CARDS.jsonl --schema FETCHED_SCHEMA
  cards.py workdir --kind cards|synthesis|tips [--week 2026-W43] [--root DIR]
  cards.py cleanup RUN_DIR [--root DIR]

Exit code: 0 on success, 1 when validation finds errors, 2 on input errors.
The question catalog defaults to questions.json at the plugin root.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from topics import blocked, default_files, load_topics  # noqa: E402

DEFAULT_QUESTIONS = Path(__file__).resolve().parents[3] / "questions.json"

POLARITIES = ("worked", "failed", "proposal", "question", "fact")
CONFIDENCES = ("observed", "inferred")
SENSITIVITIES = ("internal", "public")
STATUSES = ("draft", "approved", "dropped", "submitted")
EVIDENCE_TYPES = ("prompt", "command", "commit", "pr", "memory", "harness", "session")
REQUIRED = (
    "question_id", "week", "project", "claim", "context",
    "polarity", "confidence", "evidence", "sensitivity", "status",
)
FIELD_ORDER = (
    "card_id", "question_id", "week", "week_range", "author_email", "project", "claim",
    "context", "polarity", "confidence", "evidence", "tags", "sensitivity", "status", "notion_url",
)
CLAIM_MIN, CLAIM_MAX = 20, 80
EXCERPT_MAX = 120  # one readable line per excerpt
EVIDENCE_MAX = 3
CONTEXT_MAX = 160  # about two sentences
PROPERTY_EVIDENCE_MAX = 400
EVIDENCE_LABELS = {
    "prompt": "依頼文", "command": "コマンド", "commit": "commit", "pr": "PR",
    "memory": "memory", "harness": "設定", "session": "セッション",
}
# Notion turns CLAUDE.md and the like into links to a domain; keep them as code in page bodies.
FILENAME_RE = re.compile(r"(?<![`\w./-])([\w.-]+\.(?:md|json|jsonl|py|ts|tsx|js|yml|yaml|sh|toml))(?![`\w])")
NONE_PREFIX = "該当なし"
VAGUE_ENDINGS = ("について", "に関して")
SESSION_REF_RE = re.compile(r"^[\w-]+#[\w-]+$")
WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")

# Markdown labels (cards-<week>.md) and the card keys they hold.
META_KEYS = {
    "id": "card_id",
    "状態": "status",
    "極性": "polarity",
    "確度": "confidence",
    "公開範囲": "sensitivity",
    "プロジェクト": "project",
    "タグ": "tags",
}
EVIDENCE_HEADING = "**根拠**"
EVIDENCE_LINE_RE = re.compile(r"^- (\w+) `([^`]*)`: ?(.*)$")
GUIDE = (
    "<!-- 直したい箇所はそのまま書き換えてください。カードを出さないときは節ごと消すか、"
    "状態を dropped にします。id の無い ### 節を足すと新しいカードになります。"
    "根拠は「- 種類 `参照`: 抜粋」の形で、抜粋の 2 行目以降は 2 字下げます。 -->"
)


class InputError(Exception):
    pass


# ---- weeks -----------------------------------------------------------------


def parse_week(value: str) -> tuple[int, int]:
    m = WEEK_RE.match(value.strip())
    if not m:
        raise InputError(f"week must look like 2026-W43: {value}")
    year, week = int(m.group(1)), int(m.group(2))
    try:
        dt.date.fromisocalendar(year, week, 1)
    except ValueError:
        raise InputError(f"no such ISO week: {value}") from None
    return year, week


def week_info(week_id: str) -> dict:
    year, week = parse_week(week_id)
    monday = dt.date.fromisocalendar(year, week, 1)
    sunday = monday + dt.timedelta(days=6)
    return {
        "week": f"{year}-W{week:02d}",
        "monday": monday.isoformat(),
        "sunday": sunday.isoformat(),
        "title": f"{year}-W{week:02d}（{monday:%m/%d}〜{sunday:%m/%d}）",
    }


def week_of(day: dt.date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def previous_week(today: dt.date) -> str:
    return week_of(today - dt.timedelta(days=7))


def next_week(week_id: str) -> str:
    monday = dt.date.fromisoformat(week_info(week_id)["monday"])
    return week_of(monday + dt.timedelta(days=7))


# ---- questions -------------------------------------------------------------


def load_questions(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InputError(f"cannot read questions: {exc}") from None
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        raise InputError(f"questions file has no questions list: {path}")
    return data


def questions_by_id(catalog: dict) -> dict[str, dict]:
    return {q["id"]: q for q in catalog["questions"]}


def rotation_for(catalog: dict, week_id: str) -> str | None:
    cadence = catalog.get("cadence", {})
    rotation = cadence.get("rotation") or []
    if not rotation:
        return None
    epoch = dt.date.fromisoformat(week_info(cadence.get("rotation_epoch", week_id))["monday"])
    monday = dt.date.fromisoformat(week_info(week_id)["monday"])
    return rotation[((monday - epoch).days // 7) % len(rotation)]


def plan(catalog: dict, week_id: str, ids: list[str] | None = None) -> list[dict]:
    by_id = questions_by_id(catalog)
    if ids:
        unknown = [i for i in ids if i not in by_id]
        if unknown:
            raise InputError(f"unknown question ids: {', '.join(unknown)}")
        chosen = ids
    else:
        chosen = list(catalog.get("cadence", {}).get("weekly", []))
        extra = rotation_for(catalog, week_id)
        if extra and extra not in chosen:
            chosen.append(extra)
    return [by_id[i] for i in chosen]


# ---- cards I/O -------------------------------------------------------------


def read_cards(path: Path) -> list[dict]:
    cards = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise InputError(f"cannot read cards: {exc}") from None
    for lineno, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            card = json.loads(raw)
        except ValueError:
            raise InputError(f"{path}:{lineno}: not valid JSON") from None
        if not isinstance(card, dict):
            raise InputError(f"{path}:{lineno}: a card must be a JSON object")
        cards.append(card)
    return cards


def ordered(card: dict) -> dict:
    out = {k: card[k] for k in FIELD_ORDER if k in card}
    out.update({k: v for k, v in card.items() if k not in out})
    return out


def write_cards(path: Path, cards: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(ordered(c), ensure_ascii=False) + "\n" for c in cards)
    Path(path).write_text(text, encoding="utf-8")


# ---- validation ------------------------------------------------------------


def _claim_errors(claim) -> list[str]:
    if not isinstance(claim, str) or not claim.strip():
        return ["claim is empty"]
    claim = claim.strip()
    errors = []
    if len(claim) > CLAIM_MAX:
        errors.append(f"claim is {len(claim)} chars (max {CLAIM_MAX})")
    if len(claim) < CLAIM_MIN and not claim.startswith(NONE_PREFIX):
        errors.append(f"claim is {len(claim)} chars (min {CLAIM_MIN}); write the conclusion")
    if claim.rstrip("。.").endswith(VAGUE_ENDINGS):
        errors.append("claim ends with について/に関して; write the conclusion instead of the topic")
    return errors


def _evidence_errors(evidence) -> list[str]:
    if not isinstance(evidence, list) or not evidence:
        return ["evidence needs at least one item"]
    errors = []
    if len(evidence) > EVIDENCE_MAX:
        errors.append(f"evidence has {len(evidence)} items (max {EVIDENCE_MAX}); keep the clearest ones")
    for i, ev in enumerate(evidence, 1):
        if not isinstance(ev, dict):
            errors.append(f"evidence[{i}] must be an object")
            continue
        kind = ev.get("type")
        if kind not in EVIDENCE_TYPES:
            errors.append(f"evidence[{i}].type must be one of {', '.join(EVIDENCE_TYPES)}")
        ref = ev.get("ref")
        if not isinstance(ref, str) or not ref.strip():
            errors.append(f"evidence[{i}].ref is empty")
        elif kind == "session" and not SESSION_REF_RE.match(ref):
            errors.append(f"evidence[{i}].ref must look like <session_id>#<uuid> for type session")
        excerpt = ev.get("excerpt", "")
        if not isinstance(excerpt, str):
            errors.append(f"evidence[{i}].excerpt must be a string")
        elif len(excerpt) > EXCERPT_MAX:
            errors.append(f"evidence[{i}].excerpt is {len(excerpt)} chars (max {EXCERPT_MAX}); quote only the part that shows it")
    return errors


def _confidential_errors(card: dict, topics, allowed_terms=()) -> list[str]:
    """Cards about personnel evaluation or company management must not be submitted.

    Strong words always fail. Review words (昇格, 退職, ...) fail unless the user checked the
    card and allowed that exact word with --allow-term.
    """
    texts = [card.get("claim", ""), card.get("context", ""), card.get("project", "")]
    texts += [ev.get("excerpt", "") for ev in card.get("evidence") or [] if isinstance(ev, dict)]
    labels = {t[0]: t[1] for t in topics}
    for text in texts:
        hit = blocked(str(text), topics, allowed_terms=allowed_terms)
        if hit and hit[1] == "strong":
            return [f"touches a confidential topic ({labels[hit[0]]}); drop this card instead of rewording it"]
        if hit:
            return [
                f"touches a confidential topic ({labels[hit[0]]}) by the word '{hit[2]}'; drop the card, or ask the "
                f"user and pass --allow-term '{hit[2]}' only if it is not about personnel or management"
            ]
    return []


def validate(cards: list[dict], catalog: dict, topics=(), allowed_terms=()) -> tuple[list[str], list[str]]:
    by_id = questions_by_id(catalog)
    known_tags = set(catalog.get("tags", []))
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    per_question: dict[tuple[str, str], int] = {}
    live = 0
    for n, card in enumerate(cards, 1):
        label = f"card {n} ({card.get('card_id') or 'no id'})"
        problems = [f"missing {k}" for k in REQUIRED if k not in card]
        qid = card.get("question_id")
        question = by_id.get(qid)
        if "question_id" in card and question is None:
            problems.append(f"unknown question_id {qid}")
        if "claim" in card:
            problems += _claim_errors(card["claim"])
        for key in ("context", "project"):
            if key in card and not str(card[key]).strip():
                problems.append(f"{key} is empty")
        if "evidence" in card:
            problems += _evidence_errors(card["evidence"])
        polarity = card.get("polarity")
        if "polarity" in card:
            if polarity not in POLARITIES:
                problems.append(f"polarity must be one of {', '.join(POLARITIES)}")
            elif question and polarity != question["polarity"] and polarity not in question.get(
                "allowed_polarities", []
            ):
                allowed = [question["polarity"], *question.get("allowed_polarities", [])]
                problems.append(f"polarity {polarity} is not allowed for {qid} ({', '.join(allowed)})")
        for key, values in (("confidence", CONFIDENCES), ("sensitivity", SENSITIVITIES), ("status", STATUSES)):
            if key in card and card[key] not in values:
                problems.append(f"{key} must be one of {', '.join(values)}")
        if "week" in card:
            try:
                parse_week(str(card["week"]))
            except InputError as exc:
                problems.append(str(exc))
        tags = card.get("tags", [])
        if not isinstance(tags, list):
            problems.append("tags must be a list")
        else:
            unknown = [t for t in tags if t not in known_tags]
            if unknown and known_tags:
                warnings.append(
                    f"{label}: tag(s) {', '.join(map(str, unknown))} are not in questions.json; "
                    "they must be added to Notion before submitting (cards.py options)"
                )
        if len(str(card.get("context", ""))) > CONTEXT_MAX:
            warnings.append(f"{label}: context is {len(str(card.get('context', '')))} chars; two sentences "
                            f"(what kind of work, what happened) read best (about {CONTEXT_MAX})")
        card_id = card.get("card_id")
        if card_id:
            if card_id in seen_ids:
                problems.append(f"duplicate card_id {card_id}")
            seen_ids.add(card_id)
        if card.get("status") != "dropped":
            problems += _confidential_errors(card, topics, allowed_terms)
        errors += [f"{label}: {p}" for p in problems]
        if card.get("status") != "dropped":
            live += 1
            key = (str(card.get("author_email", "")), str(qid))
            per_question[key] = per_question.get(key, 0) + 1

    limits = catalog.get("limits", {})
    per_q_limit = limits.get("cards_per_question")
    if per_q_limit:
        for (_, qid), count in sorted(per_question.items(), key=lambda kv: kv[0][1]):
            if count > per_q_limit:
                warnings.append(f"{qid}: {count} cards (aim for at most {per_q_limit} per question)")
    total_limit = limits.get("cards_per_person_per_week")
    if total_limit and live > total_limit:
        warnings.append(f"{live} cards in total (aim for at most {total_limit} a week)")
    return errors, warnings


# ---- Markdown round trip ---------------------------------------------------


def _question_order(catalog: dict, cards: list[dict]) -> list[str]:
    order = [q["id"] for q in catalog["questions"]]
    for card in cards:
        if card.get("question_id") not in order:
            order.append(card.get("question_id"))
    return order


def render(cards: list[dict], catalog: dict) -> str:
    by_id = questions_by_id(catalog)
    visible = [c for c in cards if c.get("status") != "dropped"]
    title = week_info(visible[0]["week"])["title"] if visible else ""
    out = [f"# ナレッジカード {title}".rstrip(), "", GUIDE, ""]
    for qid in _question_order(catalog, visible):
        group = [c for c in visible if c.get("question_id") == qid]
        if not group:
            continue
        text = by_id.get(qid, {}).get("text", "")
        out += [f"## {qid} {text}".rstrip(), ""]
        for card in group:
            tags = ", ".join(card.get("tags") or []) or "-"
            out += [
                f"### {card.get('claim', '')}",
                "",
                f"- id: {card.get('card_id', '')}",
                f"- 状態: {card.get('status', 'draft')}",
                f"- 極性: {card.get('polarity', '')} / 確度: {card.get('confidence', '')}"
                f" / 公開範囲: {card.get('sensitivity', '')}",
                f"- プロジェクト: {card.get('project', '')}",
                f"- タグ: {tags}",
                "",
                str(card.get("context", "")).strip(),
                "",
                EVIDENCE_HEADING,
                "",
            ]
            for ev in card.get("evidence") or []:
                lines = str(ev.get("excerpt", "")).split("\n")
                out.append(f"- {ev.get('type', '')} `{ev.get('ref', '')}`: {lines[0]}".rstrip())
                out += [f"  {line}".rstrip() for line in lines[1:]]
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def _parse_meta(line: str) -> dict:
    meta = {}
    for part in line[2:].split(" / "):
        if ": " in part or part.endswith(":"):
            label, _, value = part.partition(":")
            key = META_KEYS.get(label.strip())
            if key:
                meta[key] = value.strip()
    return meta


def _is_meta(line: str) -> bool:
    """A meta line starts with a known label, so a bulleted context is not mistaken for one."""
    return line.startswith("- ") and line[2:].split(":", 1)[0].strip() in META_KEYS


def _parse_sections(text: str) -> list[dict]:
    """Split cards-<week>.md into card sections with their question id."""
    sections: list[dict] = []
    qid = None
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            qid = line[3:].split()[0] if line[3:].split() else None
            current = None
        elif line.startswith("### "):
            current = {"question_id": qid, "claim": line[4:].strip(), "lines": []}
            sections.append(current)
        elif current is not None:
            current["lines"].append(line)
    return sections


def _section_to_fields(section: dict) -> dict:
    fields: dict = {"question_id": section["question_id"], "claim": section["claim"]}
    lines = section["lines"]
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines) and _is_meta(lines[i]):
        fields.update(_parse_meta(lines[i]))
        i += 1
    context: list[str] = []
    while i < len(lines) and lines[i].strip() != EVIDENCE_HEADING:
        context.append(lines[i])
        i += 1
    fields["context"] = "\n".join(context).strip()
    evidence: list[dict] = []
    for line in lines[i + 1:]:
        m = EVIDENCE_LINE_RE.match(line)
        if m:
            evidence.append({"type": m.group(1), "ref": m.group(2), "excerpt": m.group(3)})
        elif line.startswith("  ") and evidence:
            evidence[-1]["excerpt"] += "\n" + line[2:]
    for ev in evidence:
        ev["excerpt"] = ev["excerpt"].rstrip()
    fields["evidence"] = evidence
    if "tags" in fields:
        fields["tags"] = [t.strip() for t in fields["tags"].split(",") if t.strip() and t.strip() != "-"]
    if "card_id" in fields and not fields["card_id"]:
        del fields["card_id"]
    return fields


def _author_slug(email: str) -> str:
    return email.split("@", 1)[0] if email else "me"


def _next_card_id(cards: list[dict], week: str, qid: str, author: str) -> str:
    prefix = f"{week}/{qid}/{_author_slug(author)}/"
    used = [int(c["card_id"][len(prefix):]) for c in cards
            if str(c.get("card_id", "")).startswith(prefix) and c["card_id"][len(prefix):].isdigit()]
    return f"{prefix}{max(used, default=0) + 1:03d}"


def parse(text: str, base: list[dict]) -> list[dict]:
    """Merge an edited cards-<week>.md back into the cards it was rendered from."""
    by_id = {c.get("card_id"): c for c in base if c.get("card_id")}
    template = base[0] if base else {}
    result: list[dict] = []
    for section in _parse_sections(text):
        fields = _section_to_fields(section)
        original = by_id.get(fields.get("card_id"))
        if original is not None:
            card = {**original, **fields}
        else:
            card = {
                "question_id": fields["question_id"],
                "week": template.get("week"),
                "week_range": template.get("week_range"),
                "author_email": template.get("author_email"),
                "tags": [],
                "sensitivity": "internal",
                "confidence": "observed",
                "status": "draft",
                "notion_url": None,
                **fields,
            }
            taken = {c.get("card_id") for c in base + result}
            if not card.get("card_id") or card["card_id"] in taken:
                card["card_id"] = _next_card_id(base + result, card["week"], card["question_id"],
                                                card.get("author_email") or "")
        result.append(ordered(card))
    kept = {c["card_id"] for c in result}
    for card in base:
        if card.get("card_id") not in kept:
            if card.get("status") != "submitted":
                card = {**card, "status": "dropped"}
            result.append(ordered(card))
    return result


# ---- dedupe, Notion payload, submission record ----------------------------


def normalize(text: str) -> str:
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", text).lower())


def card_key(card: dict) -> str:
    return f"{card.get('question_id')}|{card.get('project')}|{normalize(str(card.get('claim', '')))}"


def read_submitted(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    rows = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(raw)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def dedupe(cards: list[dict], submitted: list[dict]) -> tuple[list[dict], int]:
    done = {row.get("key"): row for row in submitted}
    marked = 0
    out = []
    for card in cards:
        row = done.get(card_key(card))
        if row and card.get("status") in ("draft", "approved"):
            card = {**card, "status": "submitted", "notion_url": row.get("notion_url")}
            marked += 1
        out.append(card)
    return out, marked


def _evidence_text(card: dict) -> tuple[str, str]:
    evidence = card.get("evidence") or []
    excerpts = "\n".join(str(e.get("excerpt", "")) for e in evidence if e.get("excerpt"))
    refs = ", ".join(str(e.get("ref", "")) for e in evidence if e.get("ref"))
    return excerpts[:PROPERTY_EVIDENCE_MAX], refs


def _code_filenames(text: str) -> str:
    return FILENAME_RE.sub(lambda m: f"`{m.group(1)}`", str(text))


def page_body(card: dict) -> str:
    """Card page: the context first; excerpts and refs stay in closed toggles (progressive disclosure)."""
    evidence = [e for e in card.get("evidence") or [] if isinstance(e, dict)]
    excerpts = [
        f"\t- {EVIDENCE_LABELS.get(e.get('type'), e.get('type'))}: {_code_filenames(str(e.get('excerpt', '')).replace(chr(10), ' ').strip())}"
        for e in evidence if str(e.get("excerpt", "")).strip()
    ]
    refs = [f"\t- `{e.get('ref')}`" for e in evidence if e.get("ref")]
    lines = [_code_filenames(str(card["context"]).strip())]
    if excerpts:
        lines += ["<details>", f"<summary>記録の抜粋（{len(excerpts)}）</summary>", *excerpts, "</details>"]
    if refs:
        lines += ["<details>", "<summary>記録の場所（本人が見返す用）</summary>", *refs, "</details>"]
    return "\n".join(lines) + "\n"


def to_notion(cards: list[dict], week_url: str, author: str) -> list[dict]:
    pages = []
    for card in cards:
        if card.get("status") not in ("draft", "approved"):
            continue
        excerpts, refs = _evidence_text(card)
        props = {
            "カード": card["claim"],
            "問い": card["question_id"],
            "週": [week_url],
            "プロジェクト": [card["project"]],
            "極性": card["polarity"],
            "確度": card["confidence"],
            "公開範囲": card["sensitivity"],
            "タグ": list(card.get("tags") or []),
            "文脈": card["context"],
            "根拠": excerpts,
            "根拠参照": refs,
        }
        if author and author != "me":
            props["投稿者"] = [author]
        pages.append({"card_id": card.get("card_id"), "properties": props, "content": page_body(card)})
    return pages


def mark_submitted(cards: list[dict], results: list[dict], now: str) -> tuple[list[dict], list[dict]]:
    urls = {r.get("card_id"): r.get("notion_url") for r in results if r.get("card_id")}
    rows = []
    out = []
    for card in cards:
        if card.get("card_id") in urls and card.get("status") in ("draft", "approved"):
            card = {**card, "status": "submitted", "notion_url": urls[card["card_id"]]}
            rows.append({"key": card_key(card), "card_id": card["card_id"],
                         "notion_url": card["notion_url"], "submitted_at": now})
        out.append(card)
    return out, rows


# ---- multi_select choices ---------------------------------------------------

# Card fields that become multi_select properties. Notion MCP rejects values that are
# not existing choices, so missing ones must be added to the data source first.
OPTION_FIELDS = (("プロジェクト", lambda c: [c.get("project")]), ("タグ", lambda c: list(c.get("tags") or [])))
STATE_RE = re.compile(r"<data-source-state>\s*(\{.*?\})\s*</data-source-state>", re.DOTALL)


def load_schema_state(text: str) -> dict:
    """Read the data source state from Notion fetch output (raw text or the JSON itself)."""
    m = STATE_RE.search(text)
    try:
        state = json.loads(m.group(1) if m else text)
    except ValueError:
        raise InputError("schema must be Notion fetch output with <data-source-state> or its JSON") from None
    if not isinstance(state, dict) or not isinstance(state.get("schema"), dict):
        raise InputError("schema has no properties")
    return state


def _sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def missing_options(cards: list[dict], state: dict) -> dict:
    """Choices used by cards to submit but absent in Notion, and DDL that adds them.

    ALTER COLUMN ... SET replaces the whole list, so every existing choice is repeated
    with its color; leaving one out would delete it.
    """
    live = [c for c in cards if c.get("status") in ("draft", "approved")]
    missing: dict[str, list[str]] = {}
    statements: list[str] = []
    for prop, values_of in OPTION_FIELDS:
        existing = state["schema"].get(prop, {}).get("options", [])
        names = {o.get("name") for o in existing}
        new: list[str] = []
        for card in live:
            for value in values_of(card):
                if value and value not in names and value not in new:
                    new.append(value)
        missing[prop] = new
        if new:
            choices = [f"{_sql_text(o['name'])}:{o.get('color') or 'default'}" for o in existing]
            choices += [f"{_sql_text(v)}:default" for v in new]
            statements.append(f"ALTER COLUMN \"{prop}\" SET MULTI_SELECT({', '.join(choices)})")
    return {"missing": missing, "statements": statements}


# ---- CLI -------------------------------------------------------------------


DEFAULT_ROOT = Path.home() / ".claude" / "knowledge-cards"
RUN_PARENTS = {"cards": "runs", "synthesis": "synthesis"}
STATE_FILES = ("notion-user.json", "allow.txt")
LEGACY_WORK = Path("cards") / ".work"


def _private_dir(path: Path) -> Path:
    path.mkdir(exist_ok=True, mode=0o700)
    return path


def _merge_legacy(legacy: Path, state: Path) -> list[str]:
    """Copy state kept by older versions in <cwd>/cards/.work/ without overwriting newer files."""
    moved = []
    for name in STATE_FILES:
        src, dst = legacy / name, state / name
        if src.is_file() and not dst.exists():
            shutil.copyfile(src, dst)
            moved.append(name)
    src, dst = legacy / "submitted.jsonl", state / "submitted.jsonl"
    if src.is_file():
        have = {json.dumps(r, sort_keys=True) for r in read_submitted(dst)}
        new = [r for r in read_submitted(src) if json.dumps(r, sort_keys=True) not in have]
        if new:
            with dst.open("a", encoding="utf-8") as fh:
                for row in new:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            moved.append(f"submitted.jsonl (+{len(new)})")
    return moved


def workdir(kind: str, week: str | None, root: Path, cwd: Path) -> dict:
    """Create the work directories outside the current repository and return their paths.

    cards:     <root>/runs/<week>/ (deleted after submitting) and <root>/state/ (kept)
    synthesis: <root>/synthesis/<week>/ (deleted after writing to Notion)
    tips:      <root>/tips/.work/ (deliverables stay in the tips output directory)
    """
    root = root.expanduser()
    root.parent.mkdir(parents=True, exist_ok=True)
    root = _private_dir(root)
    if kind == "tips":
        return {"root": str(root), "work": str(_private_dir(_private_dir(root / "tips") / ".work"))}
    if not week:
        raise InputError(f"--week is required for {kind}")
    run = _private_dir(_private_dir(root / RUN_PARENTS[kind]) / week_info(week)["week"])
    out = {"root": str(root), "run": str(run), "work": str(_private_dir(run / ".work"))}
    if kind == "cards":
        state = _private_dir(root / "state")
        out["state"] = str(state)
        legacy = cwd / LEGACY_WORK
        if legacy.is_dir():
            out["legacy"] = str(legacy)
            out["migrated"] = _merge_legacy(legacy, state)
    return out


def cleanup(run: Path, root: Path) -> Path:
    """Delete one run directory. Only <root>/runs/<week> and <root>/synthesis/<week> are accepted."""
    root = root.expanduser().resolve()
    target = Path(os.path.abspath(run.expanduser()))
    if target.is_symlink():
        raise InputError(f"refusing to delete a symlink: {target}")
    resolved = target.resolve()
    if resolved.parent.parent != root or resolved.parent.name not in RUN_PARENTS.values() or not WEEK_RE.match(resolved.name):
        raise InputError(f"refusing to delete {target}: not a run directory under {root}/runs or {root}/synthesis")
    if resolved.exists():
        shutil.rmtree(resolved)
    return resolved


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=1))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Knowledge card helper.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("week", help="ISO week id, Monday, Sunday and title")
    p.add_argument("--week", help="2026-W43 (default: the week before --today)")
    p.add_argument("--today", help="YYYY-MM-DD used as today (for tests)")

    p = sub.add_parser("plan", help="questions to answer this week")
    p.add_argument("--week", required=True)
    p.add_argument("--ids", default="", help="comma-separated question ids that override the cadence")
    p.add_argument("--questions", default=str(DEFAULT_QUESTIONS))

    p = sub.add_parser("validate", help="check cards.jsonl")
    p.add_argument("cards")
    p.add_argument("--questions", default=str(DEFAULT_QUESTIONS))
    p.add_argument("--topics", action="append", default=None,
                   help="extra confidential_topics.json (the plugin's and the personal file are always read)")
    p.add_argument("--allow-term", action="append", default=[],
                   help="review word the user confirmed is not about personnel or management (never strong words)")

    p = sub.add_parser("render", help="cards.jsonl -> cards-<week>.md")
    p.add_argument("cards")
    p.add_argument("--out", required=True)
    p.add_argument("--questions", default=str(DEFAULT_QUESTIONS))

    p = sub.add_parser("parse", help="edited cards-<week>.md -> cards.jsonl")
    p.add_argument("markdown")
    p.add_argument("--base", required=True, help="cards.jsonl the Markdown was rendered from")
    p.add_argument("--out", required=True)

    p = sub.add_parser("dedupe", help="mark cards that were already submitted")
    p.add_argument("cards")
    p.add_argument("--submitted", required=True)

    p = sub.add_parser("to-notion", help="properties for Notion create-pages")
    p.add_argument("cards")
    p.add_argument("--week-url", required=True)
    p.add_argument("--author", default="me", help="Notion user id, or me")

    p = sub.add_parser("mark-submitted", help="record cards created in Notion")
    p.add_argument("cards")
    p.add_argument("--submitted", required=True)
    p.add_argument("--results", required=True, help='JSON list of {"card_id", "notion_url"}')

    p = sub.add_parser("options", help="multi_select choices to add in Notion before submitting")
    p.add_argument("cards")
    p.add_argument("--schema", required=True, help="file with Notion fetch output of the cards data source")

    p = sub.add_parser("workdir", help="create work directories outside the repository and print their paths")
    p.add_argument("--kind", required=True, choices=("cards", "synthesis", "tips"))
    p.add_argument("--week", help="2026-W43 (required for cards and synthesis)")
    p.add_argument("--root", default=str(DEFAULT_ROOT))

    p = sub.add_parser("cleanup", help="delete a run directory created by workdir")
    p.add_argument("run")
    p.add_argument("--root", default=str(DEFAULT_ROOT))

    args = parser.parse_args(argv)
    try:
        if args.cmd == "week":
            today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
            _print_json(week_info(args.week or previous_week(today)))
        elif args.cmd == "plan":
            catalog = load_questions(Path(args.questions))
            ids = [i.strip() for i in args.ids.split(",") if i.strip()]
            _print_json(plan(catalog, week_info(args.week)["week"], ids))
        elif args.cmd == "validate":
            catalog = load_questions(Path(args.questions))
            cards = read_cards(Path(args.cards))
            try:
                topics = load_topics(default_files() + [Path(t) for t in args.topics or []], require=True)
            except ValueError as exc:
                raise InputError(str(exc)) from None
            errors, warnings = validate(cards, catalog, topics, args.allow_term)
            for w in warnings:
                print(f"warning: {w}")
            for e in errors:
                print(f"error: {e}")
            live = sum(1 for c in cards if c.get("status") != "dropped")
            print(f"{len(errors)} error(s), {len(warnings)} warning(s), {live} card(s)")
            return 1 if errors else 0
        elif args.cmd == "render":
            catalog = load_questions(Path(args.questions))
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(read_cards(Path(args.cards)), catalog), encoding="utf-8")
            print(f"wrote {out}")
        elif args.cmd == "parse":
            try:
                text = Path(args.markdown).read_text(encoding="utf-8")
            except OSError as exc:
                raise InputError(f"cannot read markdown: {exc}") from None
            cards = parse(text, read_cards(Path(args.base)))
            write_cards(Path(args.out), cards)
            live = sum(1 for c in cards if c.get("status") != "dropped")
            print(f"wrote {args.out}: {live} card(s), {len(cards) - live} dropped")
        elif args.cmd == "dedupe":
            cards, marked = dedupe(read_cards(Path(args.cards)), read_submitted(Path(args.submitted)))
            write_cards(Path(args.cards), cards)
            print(f"{marked} card(s) were already submitted")
        elif args.cmd == "to-notion":
            _print_json(to_notion(read_cards(Path(args.cards)), args.week_url, args.author))
        elif args.cmd == "options":
            try:
                text = Path(args.schema).read_text(encoding="utf-8")
            except OSError as exc:
                raise InputError(f"cannot read schema: {exc}") from None
            _print_json(missing_options(read_cards(Path(args.cards)), load_schema_state(text)))
        elif args.cmd == "workdir":
            _print_json(workdir(args.kind, args.week, Path(args.root), Path.cwd()))
        elif args.cmd == "cleanup":
            print(f"deleted {cleanup(Path(args.run), Path(args.root))}")
        elif args.cmd == "mark-submitted":
            try:
                results = json.loads(Path(args.results).read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise InputError(f"cannot read results: {exc}") from None
            if not isinstance(results, list):
                raise InputError("results must be a JSON list")
            now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            cards, rows = mark_submitted(read_cards(Path(args.cards)), results, now)
            write_cards(Path(args.cards), cards)
            Path(args.submitted).parent.mkdir(parents=True, exist_ok=True)
            with Path(args.submitted).open("a", encoding="utf-8") as fh:
                for row in rows:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"recorded {len(rows)} submitted card(s)")
    except (InputError, KeyError) as exc:
        message = f"missing field {exc}" if isinstance(exc, KeyError) else str(exc)
        print(f"error: {message}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

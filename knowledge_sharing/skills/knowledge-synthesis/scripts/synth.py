#!/usr/bin/env python3
"""Check, render and export a weekly synthesis of knowledge cards.

Usage:
  synth.py validate THEMES.json --cards CARDS.json
  synth.py render THEMES.json --cards CARDS.json --out SUMMARY.md [--theme-urls URLS.json]
  synth.py check SUMMARY.md --cards CARDS.json [--theme-urls URLS.json] [--allow-term WORD ...] [--vocab sessions.json]
  synth.py to-notion THEMES.json --cards CARDS.json --week-url URL [--allow-term WORD ...]

CARDS.json comes from load_cards.py. THEMES.json is written by Claude:

  {"week": "2026-W43",
   "themes": [{"title": "結論の一文", "cards": ["<card url>", ...],
               "conflict": "正と反の要約（無ければ空）",
               "kinds": ["条件分け", "仕組み化"], "proposal": "合", "limits": "反証・限界",
               "decision": "共有会で決めることの一文（省略時は proposal）"}],
   "next_questions": [{"id": "Q4", "reason": "..."}, {"text": "新しい問いの案", "reason": "..."}]}

The strength of each theme (people, projects, cards) and its question are computed
here from the cards, never taken from THEMES.json.

Exit code: 0 on success, 1 when validate/check find problems, 2 on input errors.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

CARDS_SCRIPTS = Path(__file__).resolve().parents[2] / "knowledge-cards" / "scripts"
sys.path.insert(0, str(CARDS_SCRIPTS))
try:
    from cards import InputError, load_questions  # noqa: E402
    from scan_sensitive import load_vocab, scan_text  # noqa: E402
    from topics import blocked, default_files, load_topics  # noqa: E402
except ImportError as exc:  # pragma: no cover - depends on the installed plugin
    print(f"error: knowledge-cards scripts not found at {CARDS_SCRIPTS}: {exc}", file=sys.stderr)
    sys.exit(2)

DEFAULT_QUESTIONS = Path(__file__).resolve().parents[3] / "questions.json"
KINDS = ("両立案", "条件分け", "仕組み化")
TITLE_MIN, TITLE_MAX = 10, 80
VAGUE_ENDINGS = ("について", "に関して")
PERSON_LABEL_RE = re.compile(r"(?<![A-Za-z0-9])p\d+(?![A-Za-z0-9])")
MENTION_RE = re.compile(r'<mention-page url="([^"]*)"\s*/>')
# Notion turns CLAUDE.md, SKILL.md and the like into links to a domain; keep them as code.
FILENAME_RE = re.compile(r"(?<![`\w./-])([\w.-]+\.(?:md|json|jsonl|py|ts|tsx|js|yml|yaml|sh|toml))(?![`\w])")


# ---- input -----------------------------------------------------------------


def read_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InputError(f"cannot read {path}: {exc}") from None
    if not isinstance(data, dict):
        raise InputError(f"{path}: expected a JSON object")
    return data


def card_index(cards: dict) -> dict[str, dict]:
    return {c["url"]: c for c in cards.get("opinions", [])}


# ---- strength and question per theme ----------------------------------------


def enrich(theme: dict, index: dict[str, dict], catalog: dict) -> dict:
    """Add what the cards say about a theme: question, polarities and the strength of evidence."""
    members = [index[u] for u in theme.get("cards", []) if u in index]
    order = [q["id"] for q in catalog["questions"]]
    counts = Counter(c["question_id"] for c in members)
    question = min(counts, key=lambda q: (-counts[q], order.index(q))) if counts else ""
    return {
        **theme,
        "question": question,
        "polarities": sorted({c["polarity"] for c in members}),
        "people": len({c["person"] for c in members}),
        "projects": len({p for c in members for p in c["projects"]}),
        "count": len(members),
        "observed": sum(1 for c in members if c["confidence"] == "observed"),
    }


def strength(t: dict) -> str:
    return f"{t['people']} 人・{t['projects']} プロジェクト・{t['count']} 枚（observed {t['observed']}）"


# ---- validate ---------------------------------------------------------------


def _texts(theme: dict) -> list[str]:
    return [str(theme.get(k, "")) for k in ("title", "conflict", "proposal", "limits", "decision")]


def validate(themes: dict, cards: dict, catalog: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    index = card_index(cards)
    facts = {c["url"] for c in cards.get("facts", [])}
    known_ids = {q["id"] for q in catalog["questions"]}
    if themes.get("week") != cards.get("week"):
        errors.append(f"week {themes.get('week')} does not match the cards ({cards.get('week')})")
    used: Counter = Counter()
    for n, theme in enumerate(themes.get("themes", []), 1):
        label = f"theme {n} ({theme.get('title', '')[:20]})"
        title = str(theme.get("title", "")).strip()
        if not (TITLE_MIN <= len(title) <= TITLE_MAX):
            errors.append(f"{label}: title is {len(title)} chars ({TITLE_MIN}-{TITLE_MAX}); write the conclusion")
        if title.rstrip("。.").endswith(VAGUE_ENDINGS):
            errors.append(f"{label}: title ends with について/に関して; write the conclusion")
        urls = theme.get("cards") or []
        if not urls:
            errors.append(f"{label}: no cards")
        for url in urls:
            used[url] += 1
            if url in facts:
                errors.append(f"{label}: {url} is a fact card; facts go to the project table, not to themes")
            elif url not in index:
                errors.append(f"{label}: {url} is not among this week's opinion cards")
        kinds = theme.get("kinds") or []
        if not kinds or any(k not in KINDS for k in kinds):
            errors.append(f"{label}: kinds must be one or more of {', '.join(KINDS)}")
        for key in ("proposal", "limits"):
            if not str(theme.get(key, "")).strip():
                errors.append(f"{label}: {key} is empty (the synthesis needs a proposal and its limits)")
        polarities = {index[u]["polarity"] for u in urls if u in index}
        if {"worked", "failed"} <= polarities and not str(theme.get("conflict", "")).strip():
            errors.append(f"{label}: has worked and failed cards; write the conflict")
        if str(theme.get("conflict", "")).strip() and len(urls) < 2:
            warnings.append(f"{label}: a conflict with a single card; is it a common answer instead?")
        for text in _texts(theme):
            if PERSON_LABEL_RE.search(text):
                errors.append(f"{label}: mentions an author label ({PERSON_LABEL_RE.search(text).group(0)}); never name people")
                break
            if "さん" in text:
                warnings.append(f"{label}: contains さん; make sure no person is named or judged")
                break
    for url in index:
        if url not in used:
            errors.append(f"opinion card {url} is in no theme; a single card is still its own theme")
    for url, n in used.items():
        if n > 1:
            warnings.append(f"card {url} is in {n} themes")
    for n, q in enumerate(themes.get("next_questions", []), 1):
        if q.get("id") and q["id"] not in known_ids:
            errors.append(f"next question {n}: unknown id {q['id']}")
        if not q.get("id") and not str(q.get("text", "")).strip():
            errors.append(f"next question {n}: needs an id or the text of a new question")
        if not str(q.get("reason", "")).strip():
            errors.append(f"next question {n}: reason is empty")
    return errors, warnings


# ---- render -----------------------------------------------------------------


def code_filenames(text: str) -> str:
    return FILENAME_RE.sub(lambda m: f"`{m.group(1)}`", str(text))


def _mention(url: str) -> str:
    return f'<mention-page url="{url}"/>'


def _cell(text: str) -> str:
    return code_filenames(text).replace("\n", " ")


def render(themes: dict, cards: dict, catalog: dict, theme_urls: dict[str, str] | None = None) -> str:
    index = card_index(cards)
    rich = [enrich(t, index, catalog) for t in themes.get("themes", [])]
    m = cards["metrics"]
    conflicts = sum(1 for t in rich if str(t.get("conflict", "")).strip())
    by_q = "、".join(f"{q} {n}" for q, n in m["by_question"].items())
    caution = "参加者が少ないため、合は仮説として扱う。" if m["people"] <= 2 else ""
    lines = [
        '<callout icon="🧭" color="gray_bg">',
        f"\t{cards['title']}のナレッジカードの合成。参加者 {m['people']} 人・カード {m['cards']} 枚から、"
        f"テーマ {len(rich)}・対立 {conflicts}・提案 {len(rich)} を出した。{caution}採否は共有会で決める。",
        "</callout>",
        "## 指標",
        '<table header-row="true">',
        "\t<tr>",
        *[f"\t\t<td>{h}</td>" for h in ("参加者", "カード", "テーマ", "対立", "提案", "確度 observed")],
        "\t</tr>",
        "\t<tr>",
        *[
            f"\t\t<td>{v}</td>"
            for v in (f"{m['people']} 人", f"{m['cards']} 枚（{by_q}）", len(rich), conflicts, len(rich), f"{m['observed']} / {m['cards']}")
        ],
        "\t</tr>",
        "</table>",
        "## 共有会で決めること",
    ]
    for t in rich:
        ref = _mention(theme_urls[t["title"]]) if theme_urls and t["title"] in theme_urls else t["title"]
        lines.append(f"- [ ] {code_filenames(t.get('decision') or t['proposal'])}（テーマ: {ref}）")
    lines.append("## テーマと合")
    for t in rich:
        refs = "、".join(
            f"{_mention(u)}（{index[u]['question_id']}・{index[u]['polarity']}・{', '.join(index[u]['projects'])}）"
            for u in t["cards"] if u in index
        )
        lines += [f"### {code_filenames(t['title'])}", f"- **カード**: {refs}"]
        if str(t.get("conflict", "")).strip():
            lines.append(f"- **対立**: {code_filenames(t['conflict'])}")
        else:
            lines.append("- **共通解**（対立なし）")
        lines += [
            f"- **合**（{'＋'.join(t['kinds'])}）: {code_filenames(t['proposal'])}",
            f"- **根拠の強さ**: {strength(t)}",
            f"- **反証・限界**: {code_filenames(t['limits'])}",
        ]
    lines += ["## 今週動いていたプロジェクト", '<table header-row="true">', "\t<tr>"]
    lines += [f"\t\t<td>{h}</td>" for h in ("プロジェクト", "内容", "カード")]
    lines.append("\t</tr>")
    for c in cards.get("facts", []):
        project = ", ".join(c["projects"])
        content = c["claim"].split(": ", 1)[1] if ": " in c["claim"] else c["claim"]
        lines += ["\t<tr>", f"\t\t<td>{_cell(project)}</td>", f"\t\t<td>{_cell(content)}</td>",
                  f"\t\t<td>{_mention(c['url'])}</td>", "\t</tr>"]
    lines += ["</table>", "## 次の問い"]
    by_id = {q["id"]: q for q in catalog["questions"]}
    for q in themes.get("next_questions", []):
        head = f"{q['id']}（{by_id[q['id']]['text']}）" if q.get("id") in by_id else f"新しい問いの案「{q.get('text', '')}」"
        lines.append(f"- {code_filenames(head)}: {code_filenames(q['reason'])}")
    return "\n".join(lines) + "\n"


# ---- check ------------------------------------------------------------------


def check(summary: str, cards: dict, topics, vocab=(), allowed_terms=(), page_urls=()) -> list[str]:
    """Problems in the text the synthesis wrote: secrets, and confidential topics.

    Only mentions of this week's cards and of the theme pages just created are removed
    before scanning; any other mention stays and is scanned with its URL. Review words
    pass only when the user confirmed them (allowed_terms), never because a card used
    them. Each line and the whole text with line breaks removed are checked, so a word
    split across lines (or by invisible characters, see topics.normalize) is still found.
    """
    known = {c["url"] for c in cards.get("opinions", []) + cards.get("facts", [])} | set(page_urls)
    text = MENTION_RE.sub(lambda m: "[card]" if m.group(1) in known else m.group(0), summary)
    problems = [f"line {f['line']}: {f['kind']}: {f['match']}" for f in scan_text(text, vocab=vocab)]
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        hit = blocked(line, topics, allowed_terms=allowed_terms)
        if hit:
            problems.append(f"line {n}: confidential topic ({hit[1]}): {hit[2]}")
    if not problems:
        hit = blocked("".join(lines), topics, allowed_terms=allowed_terms)
        if hit:
            problems.append(f"across lines: confidential topic ({hit[1]}): {hit[2]}")
    return problems


# ---- Notion -----------------------------------------------------------------


def to_notion(themes: dict, cards: dict, catalog: dict, week_url: str, topics=None, allowed_terms=()) -> list[dict]:
    """Properties for the 合成テーマ data source. Refuses theme text that fails the same check as the summary."""
    if topics is None:
        topics = load_topics(default_files(), require=True)
    errors, _ = validate(themes, cards, catalog)
    if errors:
        raise InputError("themes do not validate: " + "; ".join(errors))
    index = card_index(cards)
    pages = []
    for t in (enrich(t, index, catalog) for t in themes.get("themes", [])):
        synthesis = f"{'＋'.join(t['kinds'])}: {t['proposal']} 根拠: {strength(t)}。限界: {t['limits']}"
        pages.append({
            "title": t["title"],
            "properties": {
                "テーマ": t["title"],
                "週": [week_url],
                "問い": t["question"],
                "カード": list(t["cards"]),
                "対立": t.get("conflict", "") or "",
                "合": synthesis,
                "採否": "検討中",
            },
            "content": f"{cards['week']} の合成で作ったテーマ。詳細は週の行の配下の「まとめ」ページを参照。",
        })
    # Check exactly what will be written: every text property and the page body. The card
    # relation holds only URLs of this week's cards, which validate() has already enforced.
    for page in pages:
        values = [v for v in page["properties"].values() if isinstance(v, str)] + [page["content"]]
        problems = check("\n".join(values), cards, topics, allowed_terms=allowed_terms)
        if problems:
            raise InputError(f"theme '{page['title']}' cannot be written: {'; '.join(problems)}")
    return pages


# ---- CLI --------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weekly synthesis helper.")
    parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS))
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "render", "to-notion"):
        p = sub.add_parser(name)
        p.add_argument("themes")
        p.add_argument("--cards", required=True)
        if name == "render":
            p.add_argument("--out", required=True)
            p.add_argument("--theme-urls", help='JSON list of {"title", "url"} after the themes were created')
        if name == "to-notion":
            p.add_argument("--week-url", required=True)
            p.add_argument("--allow-term", action="append", default=[],
                           help="review word the user confirmed is not about personnel or management")
    p = sub.add_parser("check")
    p.add_argument("summary")
    p.add_argument("--cards", required=True)
    p.add_argument("--vocab", help="sessions.json from knowledge-cards (optional)")
    p.add_argument("--theme-urls", help='JSON list of {"title", "url"} of the theme pages (their mentions are not scanned)')
    p.add_argument("--allow-term", action="append", default=[],
                   help="review word the user confirmed is not about personnel or management (never strong words)")
    p.add_argument("--topics", action="append", default=None, help="extra confidential_topics.json")

    args = parser.parse_args(argv)
    try:
        catalog = load_questions(Path(args.questions))
        cards = read_json(Path(args.cards))
        if args.cmd == "check":
            topics = load_topics(default_files() + [Path(t) for t in args.topics or []], require=True)
            vocab = load_vocab(Path(args.vocab), "internal") if args.vocab else []
            try:
                summary = Path(args.summary).read_text(encoding="utf-8")
            except OSError as exc:
                raise InputError(f"cannot read summary: {exc}") from None
            page_urls = [r["url"] for r in json.loads(Path(args.theme_urls).read_text(encoding="utf-8"))] if args.theme_urls else []
            problems = check(summary, cards, topics, vocab, args.allow_term, page_urls)
            for p in problems:
                print(f"error: {p}")
            print(f"{len(problems)} problem(s)" if problems else "clean")
            return 1 if problems else 0
        themes = read_json(Path(args.themes))
        if args.cmd == "validate":
            errors, warnings = validate(themes, cards, catalog)
            for w in warnings:
                print(f"warning: {w}")
            for e in errors:
                print(f"error: {e}")
            print(f"{len(errors)} error(s), {len(warnings)} warning(s), {len(themes.get('themes', []))} theme(s)")
            return 1 if errors else 0
        if args.cmd == "render":
            urls = None
            if args.theme_urls:
                rows = json.loads(Path(args.theme_urls).read_text(encoding="utf-8"))
                urls = {r["title"]: r["url"] for r in rows}
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(themes, cards, catalog, urls), encoding="utf-8")
            print(f"wrote {out}")
        elif args.cmd == "to-notion":
            topics = load_topics(default_files(), require=True)
            pages = to_notion(themes, cards, catalog, args.week_url, topics, args.allow_term)
            print(json.dumps(pages, ensure_ascii=False, indent=1))
    except (InputError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

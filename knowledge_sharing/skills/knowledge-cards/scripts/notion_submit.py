#!/usr/bin/env python3
"""Submit knowledge cards with the Notion REST API when Notion MCP is not available.

Usage:
  notion_submit.py ensure-week --week 2026-W43 [--questions P1,Q1,Q2,Q3] [--dry-run]
  notion_submit.py resolve-user --email someone@example.com
  notion_submit.py submit PAGES.json --results results.json [--dry-run]
  notion_submit.py add-author --week-page WEEK_URL_OR_ID --user USER_ID [--dry-run]

PAGES.json is the output of `cards.py to-notion`. The integration token comes from
the NOTION_TOKEN environment variable and is never printed. Database ids come from
notion.json at the plugin root. Exit code: 0 on success, 1 on API errors, 2 on input errors.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cards import InputError, week_info  # noqa: E402

API = "https://api.notion.com/v1"
NOTION_VERSION = "2025-09-03"
DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "notion.json"
TEXT_MAX = 2000
MAX_USER_PAGES = 100
PAGE_ID_RE = re.compile(r"([0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})(?:[?#].*)?$")

SELECT = ("問い", "極性", "確度", "公開範囲")
MULTI_SELECT = ("プロジェクト", "タグ")
RICH_TEXT = ("文脈", "根拠", "根拠参照")


class ApiError(Exception):
    pass


def page_id(value: str) -> str:
    m = PAGE_ID_RE.search(value.strip())
    if not m:
        raise InputError(f"not a Notion page URL or id: {value}")
    return m.group(1).replace("-", "")


def data_source_id(value: str) -> str:
    return value.removeprefix("collection://")


def _text(value: str) -> list[dict]:
    return [{"type": "text", "text": {"content": str(value)[:TEXT_MAX]}}] if value else []


def to_rest_properties(props: dict) -> dict:
    """Convert the flat properties of `cards.py to-notion` into REST API property values."""
    out: dict = {}
    for name, value in props.items():
        if name == "カード":
            out[name] = {"title": _text(value)}
        elif name in SELECT:
            out[name] = {"select": {"name": value}}
        elif name in MULTI_SELECT:
            out[name] = {"multi_select": [{"name": v} for v in value]}
        elif name in RICH_TEXT:
            out[name] = {"rich_text": _text(value)}
        elif name == "週":
            out[name] = {"relation": [{"id": page_id(v)} for v in value]}
        elif name == "投稿者":
            out[name] = {"people": [{"object": "user", "id": v} for v in value]}
        else:
            raise InputError(f"unknown property {name}")
    return out


def to_blocks(markdown: str) -> list[dict]:
    """Turn the page body of `cards.py to-notion` (## headings, - bullets, paragraphs) into blocks."""
    blocks = []
    for line in markdown.splitlines():
        if not line.strip():
            continue
        if line.startswith("## "):
            kind, text = "heading_2", line[3:]
        elif line.startswith("- "):
            kind, text = "bulleted_list_item", line[2:]
        else:
            kind, text = "paragraph", line
        blocks.append({"object": "block", "type": kind, kind: {"rich_text": _text(text.replace("`", ""))}})
    return blocks


def page_payload(page: dict, cards_source: str) -> dict:
    return {
        "parent": {"type": "data_source_id", "data_source_id": data_source_id(cards_source)},
        "properties": to_rest_properties(page["properties"]),
        "children": to_blocks(page.get("content", "")),
    }


def week_payload(week_id: str, questions: list[str], weeks_source: str) -> dict:
    info = week_info(week_id)
    props = {
        "週": {"title": _text(info["title"])},
        "期間": {"date": {"start": info["monday"], "end": info["sunday"]}},
        "ステータス": {"select": {"name": "募集中"}},
    }
    if questions:
        props["今週の問い"] = {"multi_select": [{"name": q} for q in questions]}
    return {"parent": {"type": "data_source_id", "data_source_id": data_source_id(weeks_source)}, "properties": props}


def week_query(week_id: str) -> dict:
    return {"filter": {"property": "週", "title": {"starts_with": week_info(week_id)["week"]}}, "page_size": 10}


class Client:
    def __init__(self, token: str):
        self._token = token

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(f"{API}{path}", data=data, method=method)
        req.add_header("Authorization", f"Bearer {self._token}")
        req.add_header("Notion-Version", NOTION_VERSION)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                message = json.loads(exc.read().decode("utf-8")).get("message", "")
            except ValueError:
                message = ""
            raise ApiError(f"{method} {path}: HTTP {exc.code} {message}".strip()) from None
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ApiError(f"{method} {path}: {exc}") from None


def _week_questions(page: dict) -> list[str]:
    prop = page.get("properties", {}).get("今週の問い", {})
    return [o.get("name") for o in prop.get("multi_select", []) if o.get("name")]


def ensure_week(client: Client, config: dict, week_id: str, questions: list[str]) -> dict:
    source = data_source_id(config["weeks"]["data_source"])
    found = client.call("POST", f"/data_sources/{source}/query", week_query(week_id)).get("results", [])
    if found:
        page = found[0]
        return {"id": page["id"], "url": page.get("url"), "questions": _week_questions(page), "created": False}
    page = client.call("POST", "/pages", week_payload(week_id, questions, config["weeks"]["data_source"]))
    return {"id": page["id"], "url": page.get("url"), "questions": questions, "created": True}


def resolve_user(client: Client, email: str) -> str | None:
    cursor = None
    seen: set[str] = set()
    for _ in range(MAX_USER_PAGES):
        res = client.call("GET", "/users" + (f"?start_cursor={cursor}" if cursor else ""))
        for user in res.get("results", []):
            if user.get("type") == "person" and user.get("person", {}).get("email", "").lower() == email.lower():
                return user["id"]
        cursor = res.get("next_cursor")
        # Stop on the last page, and on a malformed or repeating cursor instead of looping forever.
        if not res.get("has_more") or not cursor or cursor in seen:
            return None
        seen.add(cursor)
    return None


def add_author(client: Client, week_page: str, user_id: str) -> bool:
    pid = page_id(week_page)
    page = client.call("GET", f"/pages/{pid}")
    people = page.get("properties", {}).get("投稿者", {}).get("people", [])
    ids = [p.get("id") for p in people]
    if user_id in ids:
        return False
    body = {"properties": {"投稿者": {"people": [{"object": "user", "id": i} for i in [*ids, user_id]]}}}
    client.call("PATCH", f"/pages/{pid}", body)
    return True


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=1))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Submit knowledge cards with the Notion REST API.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="notion.json")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("ensure-week", help="find or create the row of the week")
    p.add_argument("--week", required=True)
    p.add_argument("--questions", default="", help="comma-separated ids for 今週の問い when creating")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("resolve-user", help="Notion user id for an email address")
    p.add_argument("--email", required=True)

    p = sub.add_parser("submit", help="create card pages from `cards.py to-notion` output")
    p.add_argument("pages")
    p.add_argument("--results", required=True, help='writes [{"card_id", "notion_url"}] for mark-submitted')
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("add-author", help="add a user to 投稿者 of the week row")
    p.add_argument("--week-page", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        dry = getattr(args, "dry_run", False)
        token = os.environ.get("NOTION_TOKEN", "")
        if not token and not dry:
            raise InputError("NOTION_TOKEN is not set")
        client = Client(token)

        if args.cmd == "ensure-week":
            questions = [q.strip() for q in args.questions.split(",") if q.strip()]
            if dry:
                _print_json({"query": week_query(args.week),
                             "create_if_missing": week_payload(args.week, questions, config["weeks"]["data_source"])})
            else:
                _print_json(ensure_week(client, config, args.week, questions))
        elif args.cmd == "resolve-user":
            user = resolve_user(client, args.email)
            if user is None:
                print("error: no Notion user with that email; use me (the token's owner is not a person)",
                      file=sys.stderr)
                return 1
            print(user)
        elif args.cmd == "submit":
            pages = json.loads(Path(args.pages).read_text(encoding="utf-8"))
            if not isinstance(pages, list):
                raise InputError("pages must be a JSON list from cards.py to-notion")
            payloads = [(p.get("card_id"), page_payload(p, config["cards"]["data_source"])) for p in pages]
            if dry:
                _print_json([body for _, body in payloads])
                return 0
            results = []
            failed = 0
            for card_id, body in payloads:
                try:
                    page = client.call("POST", "/pages", body)
                    results.append({"card_id": card_id, "notion_url": page.get("url")})
                except ApiError as exc:
                    failed += 1
                    print(f"error: {card_id}: {exc}", file=sys.stderr)
            Path(args.results).write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"created {len(results)} page(s), {failed} failed; wrote {args.results}")
            return 1 if failed else 0
        elif args.cmd == "add-author":
            if dry:
                _print_json({"week_page": page_id(args.week_page), "add": args.user})
            else:
                added = add_author(client, args.week_page, args.user)
                print("added" if added else "already listed")
    except (InputError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ApiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

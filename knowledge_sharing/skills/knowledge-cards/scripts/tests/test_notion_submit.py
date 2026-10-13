import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
SUBMIT = SCRIPTS / "notion_submit.py"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("notion_submit", SUBMIT)
ns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ns)

WEEK_URL = "https://www.notion.so/2026-W43-10-19-10-25-3f2ceb782fa380c3a2fbc74cdd435f47"
PAGE = {
    "card_id": "2026-W43/Q2/y.toyota/001",
    "properties": {
        "カード": "完了条件を書かずに依頼し、テストの範囲で 2 回言い直した",
        "問い": "Q2",
        "週": [WEEK_URL],
        "投稿者": ["user-1"],
        "プロジェクト": ["ai_development_tools"],
        "極性": "failed",
        "確度": "observed",
        "公開範囲": "internal",
        "タグ": ["prompt"],
        "文脈": "文脈",
        "根拠": "抜粋",
        "根拠参照": "abc@2026-10-20T10:12",
    },
    "content": "## 文脈\n文脈\n\n## 根拠\n- prompt: 抜粋\n\n## 根拠参照\n- `abc@2026-10-20T10:12`\n",
}


def run(*args, token=None):
    env = {k: v for k, v in os.environ.items() if k != "NOTION_TOKEN"}
    if token:
        env["NOTION_TOKEN"] = token
    return subprocess.run([sys.executable, "-I", str(SUBMIT), *map(str, args)], capture_output=True, text=True, env=env)


def test_page_id_from_url_and_dashed_id():
    assert ns.page_id(WEEK_URL) == "3f2ceb782fa380c3a2fbc74cdd435f47"
    assert ns.page_id("3f2ceb78-2fa3-80c3-a2fb-c74cdd435f47") == "3f2ceb782fa380c3a2fbc74cdd435f47"
    with pytest.raises(ns.InputError):
        ns.page_id("https://www.notion.so/no-id")


def test_page_payload_maps_property_types():
    body = ns.page_payload(PAGE, "collection://1a94fd0a-157f-40ee-b7f4-5d03e51c157c")
    assert body["parent"] == {"type": "data_source_id", "data_source_id": "1a94fd0a-157f-40ee-b7f4-5d03e51c157c"}
    p = body["properties"]
    assert p["カード"]["title"][0]["text"]["content"].startswith("完了条件")
    assert p["問い"] == {"select": {"name": "Q2"}}
    assert p["タグ"] == {"multi_select": [{"name": "prompt"}]}
    assert p["週"] == {"relation": [{"id": "3f2ceb782fa380c3a2fbc74cdd435f47"}]}
    assert p["投稿者"] == {"people": [{"object": "user", "id": "user-1"}]}
    assert p["根拠参照"]["rich_text"][0]["text"]["content"] == "abc@2026-10-20T10:12"
    kinds = [b["type"] for b in body["children"]]
    assert kinds == ["heading_2", "paragraph", "heading_2", "bulleted_list_item", "heading_2", "bulleted_list_item"]


def test_week_payload_and_query():
    body = ns.week_payload("2026-W43", ["P1", "Q3"], "collection://dc4c6a28-be46-4cf5-95d7-f35c67e2f80a")
    p = body["properties"]
    assert p["週"]["title"][0]["text"]["content"] == "2026-W43（10/19〜10/25）"
    assert p["期間"] == {"date": {"start": "2026-10-19", "end": "2026-10-25"}}
    assert p["ステータス"] == {"select": {"name": "募集中"}}
    assert p["今週の問い"] == {"multi_select": [{"name": "P1"}, {"name": "Q3"}]}
    assert ns.week_query("2026-W43")["filter"]["title"] == {"starts_with": "2026-W43"}


def test_unknown_property_is_rejected():
    with pytest.raises(ns.InputError):
        ns.to_rest_properties({"謎": "x"})


def test_cli_dry_run_needs_no_token(tmp_path):
    pages = tmp_path / "pages.json"
    pages.write_text(json.dumps([PAGE], ensure_ascii=False), encoding="utf-8")
    r = run("submit", pages, "--results", tmp_path / "r.json", "--dry-run")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)[0]["properties"]["問い"] == {"select": {"name": "Q2"}}
    assert not (tmp_path / "r.json").exists()
    r = run("ensure-week", "--week", "2026-W43", "--questions", "P1,Q1", "--dry-run")
    assert r.returncode == 0 and "2026-W43（10/19〜10/25）" in r.stdout


def test_cli_without_token_fails_and_never_prints_token(tmp_path):
    pages = tmp_path / "pages.json"
    pages.write_text("[]", encoding="utf-8")
    r = run("submit", pages, "--results", tmp_path / "r.json")
    assert r.returncode == 2 and "NOTION_TOKEN" in r.stderr


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def call(self, method, path, body=None):
        self.calls.append((method, path, body))
        return self.responses.pop(0)


def test_ensure_week_reuses_existing_row():
    config = {"weeks": {"data_source": "collection://w"}}
    client = FakeClient([{"results": [{"id": "p1", "url": "u1", "properties": {
        "今週の問い": {"multi_select": [{"name": "P1"}, {"name": "Q4"}]}}}]}])
    got = ns.ensure_week(client, config, "2026-W43", ["P1"])
    assert got == {"id": "p1", "url": "u1", "questions": ["P1", "Q4"], "created": False}
    assert client.calls[0][1] == "/data_sources/w/query"


def test_ensure_week_creates_missing_row():
    client = FakeClient([{"results": []}, {"id": "p2", "url": "u2"}])
    got = ns.ensure_week(client, {"weeks": {"data_source": "collection://w"}}, "2026-W43", ["P1"])
    assert got["created"] is True and client.calls[1][0:2] == ("POST", "/pages")


def test_resolve_user_pages_through_results():
    client = FakeClient([
        {"results": [{"type": "bot", "id": "b"}], "has_more": True, "next_cursor": "c1"},
        {"results": [{"type": "person", "id": "u9", "person": {"email": "Y.Toyota@example.com"}}], "has_more": False},
    ])
    assert ns.resolve_user(client, "y.toyota@example.com") == "u9"
    assert client.calls[1][1] == "/users?start_cursor=c1"


def test_add_author_keeps_existing_people():
    pid = "3f2ceb782fa380c3a2fbc74cdd435f47"
    client = FakeClient([{"properties": {"投稿者": {"people": [{"id": "u1"}]}}}, {}])
    assert ns.add_author(client, pid, "u2") is True
    assert client.calls[1][2] == {"properties": {"投稿者": {"people": [
        {"object": "user", "id": "u1"}, {"object": "user", "id": "u2"}]}}}
    client = FakeClient([{"properties": {"投稿者": {"people": [{"id": "u2"}]}}}])
    assert ns.add_author(client, pid, "u2") is False

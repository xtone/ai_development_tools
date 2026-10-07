import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
EXTRACT = SCRIPTS / "extract_sessions.py"
NOW = "2026-10-06T12:00:00+00:00"


def ms(day):
    return int(dt.datetime.fromisoformat(day + "T09:00:00+00:00").timestamp() * 1000)


def tool(name, **inp):
    return {"type": "tool_use", "name": name, "input": inp}


def line(ts, cwd, *tools):
    return json.dumps(
        {"type": "assistant", "timestamp": ts, "cwd": cwd, "message": {"content": list(tools)}}
    )


def make_claude(root: Path) -> Path:
    c = root / "claude"
    (c / "projects" / "-w-acme-shop" / "memory").mkdir(parents=True)
    (c / "commands").mkdir()
    (c / "skills" / "myskill").mkdir(parents=True)
    (c / "agents").mkdir()
    history = [
        json.dumps({"display": "Issue #12 を進めてください", "timestamp": ms("2026-10-05"), "project": "/w/acme-shop"}),
        json.dumps({"display": "old prompt", "timestamp": ms("2026-08-01"), "project": "/w/acme-shop"}),
        json.dumps(
            {
                "display": "key HnRXa1s7-80Y6Hrv8HhTcG_sqvqRy0nGUlqhG9pqeL8 で https://stg.example-corp.co.jp/x を確認",
                "timestamp": ms("2026-10-04"),
                "project": "/w/other-app",
            }
        ),
        "not json",
    ]
    (c / "history.jsonl").write_text("\n".join(history) + "\n", encoding="utf-8")
    session = [
        line(
            "2026-10-05T01:00:00Z",
            "/w/acme-shop/.claude/worktrees/issue-12",
            tool("Bash", command="gh pr create --base main --title x"),
            tool("Bash", command="gh stack link 10 11"),
            tool("Skill", skill="natural-japanese"),
            tool("mcp__claude_ai_Notion__notion-fetch"),
            tool("Agent", subagent_type="Explore"),
        ),
        line("2026-08-01T01:00:00Z", "/w/acme-shop", tool("Bash", command="gh issue view 1")),
        line(
            "2026-10-05T02:00:00Z",
            "/w/acme-shop",
            tool(
                "Bash",
                command="curl -H 'Authorization: Bearer abcdefghijklmnopQRST1234567890' "
                "https://api.acme-internal.io/v1 && git push git@github.com:acme-org/acme-shop.git",
            ),
        ),
        "{",
    ]
    (c / "projects" / "-w-acme-shop" / "s1.jsonl").write_text("\n".join(session) + "\n", encoding="utf-8")
    (c / "projects" / "-w-acme-shop" / "memory" / "MEMORY.md").write_text("- [x](note.md)\n", encoding="utf-8")
    (c / "projects" / "-w-acme-shop" / "memory" / "note.md").write_text(
        "---\nname: closes-keyword\ndescription: \"Closes をバッククォートで囲むと閉じない\"\n---\n\n"
        "本文。\n\n**Why:** 理由。\n\n**How to apply:** 素のテキストで書く。\n",
        encoding="utf-8",
    )
    (c / "settings.json").write_text(
        json.dumps(
            {
                "env": {"SECRET_TOKEN": "supersecretvalue123"},
                "hooks": {"PreToolUse": []},
                "enabledPlugins": {"a@b": True, "c@d": False},
                "statusLine": {"type": "command"},
            }
        ),
        encoding="utf-8",
    )
    (c / "commands" / "issue-impl.md").write_text("Issue を実装する\n", encoding="utf-8")
    (c / "agents" / "reviewer.md").write_text("---\nname: reviewer\n---\n", encoding="utf-8")
    return c


def run(claude, out, *extra):
    r = subprocess.run(
        [sys.executable, "-I", str(EXTRACT), "--claude-dir", str(claude), "--out", str(out), "--now", NOW, *extra],
        capture_output=True,
        text=True,
    )
    return r


def extract(tmp_path, *extra):
    claude = make_claude(tmp_path)
    out = tmp_path / "work" / "sessions.json"
    r = run(claude, out, *extra)
    assert r.returncode == 0, r.stderr
    return json.loads(out.read_text(encoding="utf-8")), out.read_text(encoding="utf-8")


def test_filters_prompts_by_time_and_skips_bad_lines(tmp_path):
    data, _ = extract(tmp_path)
    texts = [p["text"] for p in data["prompts"]]
    assert len(texts) == 2
    assert "Issue #12 を進めてください" in texts
    assert all("old prompt" not in t for t in texts)
    assert data["counts"]["prompts"] == 2


def test_redacts_secrets_in_prompts_and_commands(tmp_path):
    _, raw = extract(tmp_path)
    assert "HnRXa1s7" not in raw
    assert "abcdefghijklmnopQRST" not in raw
    assert "<redacted>" in raw


def test_counts_tool_usage_within_period(tmp_path):
    data, _ = extract(tmp_path)
    u = {k: dict(v) for k, v in data["tool_usage"].items()}
    assert u["tools"]["Bash"] == 3
    assert u["skills"] == {"natural-japanese": 1}
    assert u["mcp_servers"] == {"claude_ai_Notion": 1}
    assert u["agents"] == {"Explore": 1}
    assert u["gh"] == {"gh pr create": 1, "gh stack link": 1}


def test_worktree_cwd_maps_to_repository_name(tmp_path):
    data, _ = extract(tmp_path)
    stack = [s for s in data["bash_samples"] if s["pattern"] == "gh stack"]
    assert stack == [{"pattern": "gh stack", "project": "acme-shop", "command": "gh stack link 10 11"}]
    assert data["memories"][0]["project"] == "acme-shop"


def test_memories_exclude_index_and_parse_fields(tmp_path):
    data, _ = extract(tmp_path)
    assert len(data["memories"]) == 1
    m = data["memories"][0]
    assert m["name"] == "closes-keyword"
    assert m["description"] == "Closes をバッククォートで囲むと閉じない"
    assert m["how_to_apply"] == "素のテキストで書く。"


def test_harness_lists_names_without_values(tmp_path):
    data, raw = extract(tmp_path)
    h = data["harness"]
    assert h["env_keys"] == ["SECRET_TOKEN"]
    assert h["hook_events"] == ["PreToolUse"]
    assert h["enabled_plugins"] == ["a@b"]
    assert h["has_status_line"] is True
    assert h["commands"] == ["issue-impl"]
    assert h["skills"] == ["myskill"]
    assert h["agents"] == ["reviewer"]
    assert "supersecretvalue123" not in raw


def test_vocabulary_collects_identifying_names(tmp_path):
    data, _ = extract(tmp_path)
    v = data["vocabulary"]
    assert {"acme-shop", "other-app"} <= set(v["projects"])
    assert {"stg.example-corp.co.jp", "example-corp.co.jp", "api.acme-internal.io", "acme-internal.io"} <= set(v["hosts"])
    assert {"acme-org", "acme-shop"} <= set(v["repos"])
    assert "github.com" not in v["hosts"]


def test_projects_filter_limits_everything(tmp_path):
    data, _ = extract(tmp_path, "--projects", "other")
    assert [p["project"] for p in data["prompts"]] == ["other-app"]
    assert data["tool_usage"]["tools"] == []
    assert data["memories"] == []


def test_missing_history_is_not_an_error(tmp_path):
    claude = make_claude(tmp_path)
    (claude / "history.jsonl").unlink()
    out = tmp_path / "s.json"
    r = run(claude, out)
    assert r.returncode == 0, r.stderr
    assert json.loads(out.read_text(encoding="utf-8"))["prompts"] == []


def test_since_accepts_date_and_rejects_garbage(tmp_path):
    data, _ = extract(tmp_path, "--since", "2026-10-05")
    assert [p["text"] for p in data["prompts"]] == ["Issue #12 を進めてください"]
    claude = tmp_path / "claude"
    r = run(claude, tmp_path / "x.json", "--since", "last-month")
    assert r.returncode == 2
    assert "--since" in r.stderr


def test_vocabulary_does_not_store_raw_emails(tmp_path):
    claude = make_claude(tmp_path)
    with (claude / "history.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"display": "連絡先 alice@example-corp.co.jp", "timestamp": ms("2026-10-05"), "project": "/w/acme-shop"}) + "\n")
    out = tmp_path / "s.json"
    assert run(claude, out).returncode == 0
    raw = out.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert "emails" not in data["vocabulary"]
    assert "example-corp.co.jp" in data["vocabulary"]["hosts"]
    assert "alice@example-corp.co.jp" not in raw


def _memory(dirpath, name):
    (dirpath / "memory").mkdir(parents=True)
    (dirpath / "memory" / f"{name}.md").write_text(
        f"---\nname: {name}\ndescription: d\n---\n\n**How to apply:** x\n", encoding="utf-8"
    )


def test_memory_dirs_without_sessions_get_readable_project_names(tmp_path):
    claude = make_claude(tmp_path)
    with (claude / "history.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"display": "p", "timestamp": ms("2026-10-05"), "project": "/Users/alice/work/beta.app"}) + "\n")
    _memory(claude / "projects" / "-Users-alice-work-beta-app", "m1")
    _memory(claude / "projects" / "-Users-alice-PycharmProjects-zeta-lang", "m2")
    out = tmp_path / "s.json"
    assert run(claude, out).returncode == 0
    projects = {m["name"]: m["project"] for m in json.loads(out.read_text(encoding="utf-8"))["memories"]}
    assert projects["m1"] == "beta.app"
    assert projects["m2"] == "PycharmProjects-zeta-lang"
    assert "-Users-alice" not in out.read_text(encoding="utf-8")

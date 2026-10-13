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


def test_subdirectory_cwd_and_docs_urls_do_not_become_vocabulary(tmp_path):
    claude = make_claude(tmp_path)
    with (claude / "projects" / "-w-acme-shop" / "s1.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(
            line(
                "2026-10-05T03:00:00Z",
                "/w/acme-shop/docs",
                tool("Bash", command="open https://docs.github.com/en/pull-requests/how-tos && gh stack link 1 2"),
            )
            + "\n"
        )
    out = tmp_path / "s.json"
    assert run(claude, out).returncode == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "docs" not in data["vocabulary"]["projects"]
    assert "pull-requests" not in data["vocabulary"]["repos"]
    assert {s["project"] for s in data["bash_samples"]} == {"acme-shop"}


def test_unexpected_but_valid_json_shapes_do_not_abort_extraction(tmp_path):
    claude = make_claude(tmp_path)
    with (claude / "projects" / "-w-acme-shop" / "s1.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"type": "tool_use", "timestamp": "2026-10-05T04:00:00Z", "message": "tool_use as text"}) + "\n")
        fh.write(json.dumps({"timestamp": 1e30, "message": {"content": [{"type": "tool_use", "name": "Read"}]}}) + "\n")
    with (claude / "history.jsonl").open("a", encoding="utf-8") as fh:
        fh.write('{"display": "nan", "timestamp": NaN, "project": "/w/acme-shop"}\n')
        fh.write(json.dumps({"display": "huge", "timestamp": 1e30, "project": "/w/acme-shop"}) + "\n")
    out = tmp_path / "s.json"
    r = run(claude, out)
    assert r.returncode == 0, r.stderr
    assert json.loads(out.read_text(encoding="utf-8"))["counts"]["prompts"] == 2


def test_host_pattern_is_linear_on_adversarial_input():
    code = (
        f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import extract_sessions as e; "
        "e.HOST_RE.findall('a.' * 100000); assert e.HOST_RE.findall('see https://api.acme-internal.io/x') == ['api.acme-internal.io']"
    )
    try:
        subprocess.run([sys.executable, "-I", "-c", code], timeout=2.0, check=True)
    except subprocess.TimeoutExpired:
        raise AssertionError("HOST_RE took longer than 2 seconds")


def _write_session(claude, name, *lines):
    path = claude / "projects" / "-w-acme-shop" / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _bash_line(ts, command, session="s2"):
    return json.dumps(
        {
            "type": "assistant",
            "timestamp": ts,
            "cwd": "/w/acme-shop",
            "sessionId": session,
            "message": {"content": [tool("Bash", command=command)]},
        }
    )


def test_prompts_carry_session_id(tmp_path):
    claude = make_claude(tmp_path)
    with (claude / "history.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps(
                {"display": "commit して", "timestamp": ms("2026-10-05"), "project": "/w/acme-shop", "sessionId": "abc-1"}
            )
            + "\n"
        )
    out = tmp_path / "work" / "sessions.json"
    assert run(claude, out).returncode == 0
    prompts = json.loads(out.read_text(encoding="utf-8"))["prompts"]
    by_text = {p["text"]: p for p in prompts}
    assert by_text["commit して"]["session_id"] == "abc-1"
    assert by_text["Issue #12 を進めてください"]["session_id"] is None


def test_collects_commit_and_pr_titles(tmp_path):
    claude = make_claude(tmp_path)
    heredoc = "git add -A && git commit -q -m \"$(cat <<'EOF'\nfeat(cards): カードを検証する\n\n本文\nEOF\n)\""
    _write_session(
        claude,
        "s2.jsonl",
        _bash_line("2026-10-05T03:00:00Z", 'git commit -m "fix: 週の計算を直す" -m "body"'),
        _bash_line("2026-10-05T03:10:00Z", "git commit -am 'docs: README を更新'"),
        _bash_line("2026-10-05T03:20:00Z", heredoc),
        _bash_line("2026-10-05T03:30:00Z", "git commit --amend --no-edit"),
        _bash_line("2026-10-05T03:40:00Z", 'gh pr create --base main --title "feat: knowledge-cards を追加" --body x'),
        _bash_line("2026-10-05T03:50:00Z", "git log --grep 'git commit -m \"x\"'"),
        _bash_line(
            "2026-10-05T03:55:00Z",
            "cat >> t.py <<'EOF'\nx = \"git add && git commit -m \\\"$(cat <<'X'\nfake\nX\n)\\\"\"\nEOF",
        ),
        _bash_line("2026-08-01T03:00:00Z", 'git commit -m "old"'),
    )
    out = tmp_path / "work" / "sessions.json"
    assert run(claude, out).returncode == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    titles = [c["title"] for c in data["commits"]]
    assert titles == ["fix: 週の計算を直す", "docs: README を更新", "feat(cards): カードを検証する"]
    assert data["commits"][0] == {
        "time": "2026-10-05T03:00+00:00",
        "project": "acme-shop",
        "session_id": "s2",
        "title": "fix: 週の計算を直す",
    }
    prs = [p["title"] for p in data["prs"]]
    assert "feat: knowledge-cards を追加" in prs
    assert data["counts"]["commits"] == 3
    assert data["counts"]["prs"] == len(prs)


def test_commit_titles_are_redacted(tmp_path):
    claude = make_claude(tmp_path)
    _write_session(
        claude,
        "s3.jsonl",
        _bash_line("2026-10-05T04:00:00Z", 'git commit -m "token HnRXa1s7-80Y6Hrv8HhTcG_sqvqRy0nGUlqhG9pqeL8 を消す"'),
    )
    out = tmp_path / "work" / "sessions.json"
    assert run(claude, out).returncode == 0
    raw = out.read_text(encoding="utf-8")
    assert "HnRXa1s7" not in raw
    assert json.loads(raw)["commits"][0]["title"] == "token <redacted> を消す"


def test_until_limits_prompts_commits_and_tool_usage_by_local_day(tmp_path):
    claude = make_claude(tmp_path)
    with (claude / "history.jsonl").open("a", encoding="utf-8") as fh:
        for ts, text in (("2026-10-09T14:59:00+00:00", "金曜の夜（JST 23:59）"), ("2026-10-09T15:00:00+00:00", "土曜（JST 0:00）")):
            ms_ = int(dt.datetime.fromisoformat(ts).timestamp() * 1000)
            fh.write(json.dumps({"display": text, "timestamp": ms_, "project": "/w/acme-shop", "sessionId": "s9"}) + "\n")
    _write_session(
        claude,
        "s9.jsonl",
        _bash_line("2026-10-09T14:00:00Z", 'git commit -m "feat: 金曜の commit"', session="s9"),
        _bash_line("2026-10-09T16:00:00Z", 'git commit -m "feat: 土曜の commit"', session="s9"),
    )
    out = tmp_path / "work" / "sessions.json"
    r = run(claude, out, "--since", "2026-10-05", "--until", "2026-10-09", "--tz", "+09:00")
    assert r.returncode == 0, r.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    texts = [p["text"] for p in data["prompts"]]
    assert "金曜の夜（JST 23:59）" in texts and "土曜（JST 0:00）" not in texts
    assert [c["title"] for c in data["commits"]] == ["feat: 金曜の commit"]
    assert data["since"] == "2026-10-05T00:00:00+09:00"
    assert data["until"] == "2026-10-10T00:00:00+09:00"
    assert dict(data["tool_usage"]["tools"])["Bash"] == 4


def test_until_must_not_precede_since_and_must_be_a_date(tmp_path):
    claude = make_claude(tmp_path)
    r = run(claude, tmp_path / "x.json", "--since", "2026-10-05", "--until", "2026-10-04")
    assert r.returncode == 2 and "--until" in r.stderr
    r = run(claude, tmp_path / "x.json", "--until", "friday")
    assert r.returncode == 2 and "--until" in r.stderr
    r = run(claude, tmp_path / "x.json", "--tz", "JST")
    assert r.returncode == 2 and "--tz" in r.stderr


def test_without_until_output_has_null_until(tmp_path):
    data, _ = extract(tmp_path)
    assert data["until"] is None


def _history(claude, *rows):
    with (claude / "history.jsonl").open("a", encoding="utf-8") as fh:
        for ts, text, session in rows:
            ms_ = int(dt.datetime.fromisoformat(ts).timestamp() * 1000)
            fh.write(json.dumps({"display": text, "timestamp": ms_, "project": "/w/acme-shop", "sessionId": session}) + "\n")


def test_confidential_sessions_are_dropped_with_counts_only(tmp_path):
    claude = make_claude(tmp_path)
    _history(
        claude,
        ("2026-10-05T03:00:00+00:00", "部下の人事評価コメントを下書きして", "secret-1"),
        ("2026-10-05T03:05:00+00:00", "もう少し柔らかい表現にして", "secret-1"),
        ("2026-10-05T04:00:00+00:00", "週の計算を直して", "open-1"),
    )
    _write_session(
        claude,
        "secret-1.jsonl",
        _bash_line("2026-10-05T03:10:00Z", 'git commit -m "docs: 評価コメント案"', session="secret-1"),
        _bash_line("2026-10-05T03:11:00Z", "gh stack link 1 2", session="secret-1"),
    )
    _write_session(
        claude,
        "open-2.jsonl",
        _bash_line("2026-10-05T05:00:00Z", 'git commit -m "docs: 取締役会の資料を追加"', session="open-2"),
        _bash_line("2026-10-05T05:01:00Z", 'git commit -m "fix: 週の計算を直す"', session="open-3"),
    )
    with (claude / "history.jsonl").open("a", encoding="utf-8") as fh:
        ms_ = int(dt.datetime.fromisoformat("2026-10-05T05:02:00+00:00").timestamp() * 1000)
        fh.write(json.dumps({"display": "資料の誤字を直して", "timestamp": ms_, "project": "/w/acme-shop", "sessionId": "open-2"}) + "\n")
    (claude / "projects" / "-w-acme-shop" / "memory" / "board.md").write_text(
        "---\nname: board-meeting\ndescription: 経営会議の資料の置き場\n---\n\n本文\n", encoding="utf-8"
    )
    out = tmp_path / "work" / "sessions.json"
    r = run(claude, out, "--since", "2026-10-05", "--tz", "+00:00")
    assert r.returncode == 0, r.stderr
    raw = out.read_text(encoding="utf-8")
    data = json.loads(raw)
    for secret in ("人事評価", "柔らかい表現", "評価コメント案", "取締役会", "資料の誤字", "経営会議", "board-meeting"):
        assert secret not in raw, secret
    texts = [p["text"] for p in data["prompts"]]
    assert "週の計算を直して" in texts
    assert [c["title"] for c in data["commits"]] == ["fix: 週の計算を直す"]
    assert dict(data["tool_usage"]["gh"]).get("gh stack link") == 1  # only the open session's call
    assert data["excluded"] == {
        "sessions": 2,
        "prompts": 3,
        "commits": 2,
        "prs": 0,
        "memories": 1,
        "by_topic": {"evaluation": 1, "management": 1},
        "released": 0,
        "review": [],
    }


def test_extra_topics_file_extends_exclusion(tmp_path):
    claude = make_claude(tmp_path)
    _history(claude, ("2026-10-05T03:00:00+00:00", "極秘プロジェクトX の見積もり", "s-x"))
    extra = tmp_path / "extra.json"
    extra.write_text(json.dumps({"topics": [{"id": "management", "patterns": ["極秘プロジェクトX"]}]}), encoding="utf-8")
    out = tmp_path / "work" / "sessions.json"
    r = run(claude, out, "--since", "2026-10-05", "--topics", extra)
    assert r.returncode == 0, r.stderr
    assert "極秘プロジェクトX" not in out.read_text(encoding="utf-8")


def test_file_contents_do_not_mark_a_session_confidential(tmp_path):
    claude = make_claude(tmp_path)
    _history(claude, ("2026-10-05T03:00:00+00:00", "会社概要ページを更新して", "client-1"))
    line = json.dumps(
        {
            "type": "assistant",
            "timestamp": "2026-10-05T03:01:00Z",
            "cwd": "/w/acme-shop",
            "sessionId": "client-1",
            "message": {"content": [
                tool("Write", file_path="/w/acme-shop/about.html", content="代表取締役社長 山田 / 予実管理 / ADR を昇格"),
                tool("Bash", command="sed -i 's/代表取締役 A/代表取締役 B/' about.html && git commit -m 'fix: 会社概要を更新'"),
            ]},
        }
    )
    _write_session(claude, "client-1.jsonl", line)
    out = tmp_path / "work" / "sessions.json"
    r = run(claude, out, "--since", "2026-10-05", "--tz", "+00:00")
    assert r.returncode == 0, r.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["excluded"]["sessions"] == 0
    assert "会社概要ページを更新して" in [p["text"] for p in data["prompts"]]


def test_confidential_prompt_before_since_still_drops_the_session(tmp_path):
    claude = make_claude(tmp_path)
    _history(
        claude,
        ("2026-09-20T03:00:00+00:00", "部下の人事評価コメントを下書きして", "secret-old"),
        ("2026-10-05T03:00:00+00:00", "もう少し柔らかい表現にして", "secret-old"),
    )
    _write_session(
        claude, "secret-old.jsonl",
        _bash_line("2026-10-05T03:10:00Z", 'git commit -m "docs: 文面を調整"', session="secret-old"),
    )
    out = tmp_path / "work" / "sessions.json"
    r = run(claude, out, "--since", "2026-10-05", "--tz", "+00:00")
    assert r.returncode == 0, r.stderr
    raw = out.read_text(encoding="utf-8")
    assert "柔らかい表現" not in raw and "文面を調整" not in raw
    assert json.loads(raw)["excluded"]["sessions"] == 1


def test_user_messages_in_session_logs_count_without_history(tmp_path):
    claude = make_claude(tmp_path)
    user = json.dumps({
        "type": "user", "timestamp": "2026-09-01T03:00:00Z", "sessionId": "no-hist",
        "message": {"role": "user", "content": [{"type": "text", "text": "取締役会の議事録を要約して"}]},
    })
    _write_session(
        claude, "no-hist.jsonl", user,
        _bash_line("2026-10-05T03:10:00Z", 'git commit -m "docs: 要約を追加"', session="no-hist"),
    )
    out = tmp_path / "work" / "sessions.json"
    r = run(claude, out, "--since", "2026-10-05", "--tz", "+00:00")
    assert r.returncode == 0, r.stderr
    raw = out.read_text(encoding="utf-8")
    assert "要約を追加" not in raw
    assert json.loads(raw)["excluded"]["by_topic"] == {"management": 1}


def test_out_of_range_commit_title_still_drops_the_session(tmp_path):
    claude = make_claude(tmp_path)
    _write_session(
        claude, "late.jsonl",
        _bash_line("2026-09-01T03:00:00Z", 'git commit -m "docs: 賞与の配分案"', session="late"),
        _bash_line("2026-10-05T03:00:00Z", 'git commit -m "docs: 表を整形"', session="late"),
    )
    out = tmp_path / "work" / "sessions.json"
    assert run(claude, out, "--since", "2026-10-05", "--tz", "+00:00").returncode == 0
    assert "表を整形" not in out.read_text(encoding="utf-8")


def test_empty_topics_fail_closed(tmp_path):
    claude = make_claude(tmp_path)
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"topics": []}), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, "-I", "-c",
         "import sys; sys.path.insert(0, sys.argv[1]); import topics; topics.load_topics([sys.argv[2]], require=True)",
         str(SCRIPTS), str(empty)],
        capture_output=True, text=True,
    )
    assert r.returncode != 0 and "no confidential topics" in r.stderr


def test_review_words_hold_sessions_until_the_user_includes_them(tmp_path):
    claude = make_claude(tmp_path)
    _history(
        claude,
        ("2026-10-05T03:00:00+00:00", "管理画面に退職者処理の機能を追加して", "feat-1"),
        ("2026-10-05T03:05:00+00:00", "ボタンの文言を直して", "feat-1"),
        ("2026-10-05T04:00:00+00:00", "退職の件で相談したい", "people-1"),
        ("2026-10-05T05:00:00+00:00", "退職者処理の画面と取締役会の資料", "mixed-1"),
    )
    _write_session(
        claude, "feat-1.jsonl",
        _bash_line("2026-10-05T03:10:00Z", 'git commit -m "feat: 退職者処理を追加"', session="feat-1"),
    )
    out = tmp_path / "work" / "sessions.json"
    assert run(claude, out, "--since", "2026-10-05", "--tz", "+00:00").returncode == 0
    raw = out.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert "退職" not in json.dumps(data["prompts"], ensure_ascii=False)  # held back by default
    held = {r["session_id"]: r for r in data["excluded"]["review"]}
    assert set(held) == {"feat-1", "people-1"}  # mixed-1 hit a strong word: not offered for review
    assert held["feat-1"]["words"] == "退職" and held["feat-1"]["project"] == "acme-shop"
    assert "管理画面" not in json.dumps(held, ensure_ascii=False)  # ids and words only, no prompt text

    cleared = tmp_path / "include.txt"
    cleared.write_text("# 退職者処理は顧客アプリの機能\nfeat-1\nmixed-1\n", encoding="utf-8")
    assert run(claude, out, "--since", "2026-10-05", "--tz", "+00:00", "--include-sessions", cleared).returncode == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    texts = [p["text"] for p in data["prompts"]]
    assert "管理画面に退職者処理の機能を追加して" in texts and "ボタンの文言を直して" in texts
    assert "feat: 退職者処理を追加" in [c["title"] for c in data["commits"]]
    assert "退職の件で相談したい" not in texts  # not in the list
    assert "退職者処理の画面と取締役会の資料" not in texts  # strong words cannot be released
    assert data["excluded"]["released"] == 1

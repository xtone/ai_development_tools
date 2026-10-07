# session-tips-digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Claude Code のセッション記録から共有可能な Tips を抽出し、一次情報で裏付けて Markdown・Artifact・Notion に公開するスキル `session-tips-digest` を、新規プラグイン `knowledge-sharing` として追加する。

**Architecture:** 手順は SKILL.md に書き、再現性が必要な 3 処理（記録の集計、機密スキャン、Markdown→HTML 変換）だけを Python スクリプトにする。スクリプトは標準ライブラリのみで、相互依存は `extract_sessions.py` が `scan_sensitive.redact` を使う 1 点だけ。調査・執筆・公開の判断は Claude が SKILL.md と references に従って行う。

**Tech Stack:** Python 3.10+（標準ライブラリのみ）、pytest（`uv run --no-project --with pytest` で実行）、Claude Code プラグイン（skills ディレクトリ形式）

**Spec:** `docs/superpowers/specs/2026-10-06-session-tips-digest-design.md`

## Global Constraints

- プラグイン名 `knowledge-sharing`、ディレクトリ `knowledge_sharing/`、スキル名 `session-tips-digest`、プラグイン version `0.1.0`
- スクリプトは Python 3 標準ライブラリのみ。`python3 -I` で実行でき、入力はすべて引数で渡す。カレントディレクトリに依存しない
- 失敗時は非 0 で終了し、標準エラーに理由を 1 行出す（`scan_sensitive.py` は検出ありで 1、入力エラーで 2）
- `extract_sessions.py` は設定ファイルの値（env の値、ヘッダー、トークン）を出力しない。プロンプトとコマンド例の秘密情報は伏せ字にする
- 成果物の既定ディレクトリは `tips/`、作業ファイルは `tips/.work/`
- SKILL.md の description に「セッション 1 本の効率採点ではない（evaluate-session の領域）」と明記する
- 機密スキャンが 1 件でも残っていれば公開に進まない

## Review Focus

1. プロンプトや Bash コマンドに含まれるトークン（英数混在 32 文字以上、Bearer ヘッダー）は、`sessions.json` に書かれる前に伏せ字になるべき。Task 2 のテストで固定する
2. ハイフンと数字を含むファイル名や日付付きスラッグ（`claude-code-tips-2026-09-references`）はトークンとして誤検出されるべきでない。Task 1 のテストで固定する
3. 匿名化辞書のホスト名は、サブドメイン付きの表記や日本語に隣接した表記でも検出されるべき。部分一致の別語（`acme-shopping`）は検出されるべきでない。Task 1 のテストで固定する
4. 壊れた JSONL 行、`history.jsonl` が無い環境、worktree 内の `cwd` でも抽出は落ちず、worktree はリポジトリ名に寄せられるべき。Task 2 のテストで固定する
5. 二重バッククォートや太字記号を含むコードスパンは、記号が見える形で 1 段の `<code>` に変換されるべき（2026-10-06 に手作業で踏んだ不具合）。H1 が無い Markdown でも `<title>` が入るべき。Task 3 のテストで固定する

---

パスはすべてリポジトリルートからの相対パス。`S` は `knowledge_sharing/skills/session-tips-digest` を指す。

テストの実行コマンド（以降 `PYTEST` と書く）:

```bash
uv run -q --no-project --with pytest python -m pytest -q
```

### Task 1: 機密スキャン `scan_sensitive.py`

**Files:**
- Create: `S/scripts/scan_sensitive.py`
- Test: `S/scripts/tests/test_scan_sensitive.py`

**Interfaces:**
- Consumes: なし
- Produces:
  - `PATTERNS: list[tuple[str, re.Pattern[str]]]`（kind 名は `bearer` `token` `hex_token` `email` `numeric_id` `notion_url` `home_path`）
  - `redact(text: str) -> str`（`bearer` `token` `hex_token` を `<redacted>` に置換）
  - `load_vocab(path: Path) -> list[str]`（`sessions.json` の `vocabulary` から projects/repos/hosts/users を読む）
  - `scan_text(text: str, vocab: Iterable[str] = (), allow: Iterable[str] = ()) -> list[dict]`（各要素は `{"line": int, "kind": str, "match": str}`）
  - CLI: `scan_sensitive.py FILE... [--vocab JSON] [--allow a,b] [--allow-file PATH] [--json]`

- [ ] **Step 1: テストを書く**

````python path=knowledge_sharing/skills/session-tips-digest/scripts/tests/test_scan_sensitive.py
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
SCAN = SCRIPTS / "scan_sensitive.py"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scan = _load("scan_sensitive")


def kinds(text, **kw):
    return sorted({f["kind"] for f in scan.scan_text(text, **kw)})


def test_detects_each_kind():
    text = "\n".join(
        [
            "Authorization=Bearer abcdefghijklmnopQRST1234",
            "key HnRXa1s7-80Y6Hrv8HhTcG_sqvqRy0nGUlqhG9pqeL8 here",
            "sha 3f9a1c2e4b5d6f708192a3b4c5d6e7f8091a2b3c",
            "mail someone@example-corp.co.jp",
            "org 732148011048",
            "see https://app.notion.com/p/team/Page-123",
            "path /Users/alice/project",
        ]
    )
    assert kinds(text) == [
        "bearer",
        "email",
        "hex_token",
        "home_path",
        "notion_url",
        "numeric_id",
        "token",
    ]


def test_clean_technical_text_has_no_findings():
    text = "\n".join(
        [
            "詳細は claude-code-tips-2026-09-references.md を参照",
            "docs/superpowers/specs/2026-10-06-session-tips-digest-design.md",
            "arXiv 2606.05976 と v2.1.290 の変更",
            "color: #1f6f5f; font: 16px",
            "https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap",
            "UV_LOCKED=1 uv sync",
            "gh stack link 13359 13360",
            "PR 本文に `` `Closes #9` `` と書いた",
            "claude_code.lines_of_code.count",
        ]
    )
    assert scan.scan_text(text) == []


def test_vocab_matches_subdomain_and_japanese_but_not_longer_words():
    vocab = ["acme-shop", "example-corp.co.jp"]
    text = "acme-shop案件で確認\nhttps://stg.example-corp.co.jp/x\nacme-shopping は別物"
    found = [f for f in scan.scan_text(text, vocab=vocab) if f["kind"] == "vocab"]
    assert [(f["line"], f["match"]) for f in found] == [
        (1, "acme-shop"),
        (2, "example-corp.co.jp"),
    ]


def test_allow_suppresses_exact_matches_case_insensitive():
    text = "acme-shop の Issue"
    assert scan.scan_text(text, vocab=["acme-shop"], allow=["ACME-SHOP"]) == []


def test_redact_hides_tokens_and_keeps_text():
    out = scan.redact(
        "token HnRXa1s7-80Y6Hrv8HhTcG_sqvqRy0nGUlqhG9pqeL8 and Bearer abcdefghijklmnopQRST1234 end"
    )
    assert "HnRXa1s7" not in out
    assert "abcdefghijklmnop" not in out
    assert out.startswith("token <redacted>")
    assert out.endswith(" end")


def test_load_vocab_reads_sessions_json(tmp_path):
    p = tmp_path / "sessions.json"
    p.write_text(
        json.dumps(
            {
                "vocabulary": {
                    "projects": ["acme-shop", "ab"],
                    "repos": ["acme-org"],
                    "hosts": ["acme-internal.io"],
                    "emails": ["x@acme.io"],
                    "users": ["alice"],
                }
            }
        ),
        encoding="utf-8",
    )
    assert scan.load_vocab(p) == ["acme-internal.io", "acme-org", "acme-shop", "alice"]


def _run(*args):
    return subprocess.run(
        [sys.executable, "-I", str(SCAN), *map(str, args)],
        capture_output=True,
        text=True,
    )


def test_cli_exit_codes_and_allow_file(tmp_path):
    vocab = tmp_path / "sessions.json"
    vocab.write_text(json.dumps({"vocabulary": {"projects": ["acme-shop"]}}), encoding="utf-8")
    dirty = tmp_path / "dirty.md"
    dirty.write_text("# Tips\n\nacme-shop で試した\n", encoding="utf-8")
    clean = tmp_path / "clean.md"
    clean.write_text("# Tips\n\nクライアント案件で試した\n", encoding="utf-8")

    r = _run(dirty, clean, "--vocab", vocab)
    assert r.returncode == 1
    assert f"{dirty}:3: vocab: acme-shop" in r.stdout

    allow = tmp_path / "allow.txt"
    allow.write_text("# 一般語なので許可\nacme-shop\n", encoding="utf-8")
    r = _run(dirty, "--vocab", vocab, "--allow-file", allow)
    assert r.returncode == 0
    assert "clean" in r.stdout

    r = _run(tmp_path / "missing.md")
    assert r.returncode == 2


def test_cli_json_output(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("mail a@example-corp.co.jp\n", encoding="utf-8")
    r = _run(f, "--json")
    assert r.returncode == 1
    data = json.loads(r.stdout)
    assert data == [{"file": str(f), "line": 1, "kind": "email", "match": "a@example-corp.co.jp"}]
````

- [ ] **Step 2: テストが失敗することを確認する**

Run: `cd knowledge_sharing/skills/session-tips-digest/scripts && PYTEST tests/test_scan_sensitive.py`
Expected: FAIL（`scan_sensitive.py` が無いため `FileNotFoundError`）

- [ ] **Step 3: 実装する**

````python path=knowledge_sharing/skills/session-tips-digest/scripts/scan_sensitive.py
#!/usr/bin/env python3
"""Scan files for secrets and identifying names before sharing them.

Usage:
  scan_sensitive.py FILE... [--vocab sessions.json] [--allow a,b]
                            [--allow-file PATH] [--json]

Exit code: 0 when clean, 1 when anything is found, 2 on input errors.
The vocabulary comes from extract_sessions.py (project, repository, host and
user names seen in the session records).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

_T = r"A-Za-z0-9_+/=\-"

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("bearer", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=\-]{16,}")),
    (
        "token",
        re.compile(
            rf"(?<![{_T}])(?=[{_T}]*[0-9])(?=[{_T}]*[a-z])(?=[{_T}]*[A-Z])"
            rf"[{_T}]{{32,}}(?![{_T}])"
        ),
    ),
    ("hex_token", re.compile(r"(?<![0-9A-Za-z])[0-9a-f]{32,}(?![0-9A-Za-z])")),
    (
        "email",
        re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}"),
    ),
    ("numeric_id", re.compile(r"(?<![0-9.,:/\-])[0-9]{10,13}(?![0-9.,])")),
    (
        "notion_url",
        re.compile(r"https?://[^\s)\"'<>]*notion\.(?:so|com)[^\s)\"'<>]*", re.IGNORECASE),
    ),
    ("home_path", re.compile(r"/(?:Users|home)/[^/\s\"'<>)`]+")),
]

REDACT_KINDS = ("bearer", "token", "hex_token")
VOCAB_KEYS = ("projects", "repos", "hosts", "users")


def redact(text: str) -> str:
    """Replace secret-looking strings with <redacted>."""
    for kind, pattern in PATTERNS:
        if kind in REDACT_KINDS:
            text = pattern.sub("<redacted>", text)
    return text


def load_vocab(path: Path) -> list[str]:
    """Read identifying names from a sessions.json written by extract_sessions.py."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    vocab = data.get("vocabulary", data) if isinstance(data, dict) else {}
    words: set[str] = set()
    for key in VOCAB_KEYS:
        for word in vocab.get(key, []) or []:
            word = str(word).strip()
            if len(word) >= 3:
                words.add(word)
    return sorted(words, key=str.lower)


def _vocab_pattern(word: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![A-Za-z0-9_\-]){re.escape(word)}(?![A-Za-z0-9_\-])", re.IGNORECASE
    )


def scan_text(
    text: str, vocab: Iterable[str] = (), allow: Iterable[str] = ()
) -> list[dict]:
    """Return findings as {"line", "kind", "match"} dicts in line order."""
    allowed = {a.strip().lower() for a in allow if a.strip()}
    compiled = list(PATTERNS) + [("vocab", _vocab_pattern(w)) for w in vocab]
    findings: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        seen: set[tuple[str, str]] = set()
        for kind, pattern in compiled:
            for m in pattern.finditer(line):
                match = m.group(0)
                key = (kind, match.lower())
                if match.lower() in allowed or key in seen:
                    continue
                seen.add(key)
                findings.append({"line": lineno, "kind": kind, "match": match})
    return findings


def _read_allow_file(path: Path) -> list[str]:
    words = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            words.append(line)
    return words


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan files for secrets and identifying names.")
    parser.add_argument("files", nargs="+", help="files to scan")
    parser.add_argument("--vocab", help="sessions.json from extract_sessions.py")
    parser.add_argument("--allow", default="", help="comma-separated strings to ignore")
    parser.add_argument("--allow-file", help="file with one allowed string per line (# comments)")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args(argv)

    try:
        vocab = load_vocab(Path(args.vocab)) if args.vocab else []
        allow = [a for a in args.allow.split(",") if a.strip()]
        if args.allow_file:
            allow += _read_allow_file(Path(args.allow_file))
        results = []
        for name in args.files:
            text = Path(name).read_text(encoding="utf-8", errors="replace")
            for f in scan_text(text, vocab=vocab, allow=allow):
                results.append({"file": name, **f})
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=1))
    elif results:
        for f in results:
            print(f"{f['file']}:{f['line']}: {f['kind']}: {f['match']}")
        print(f"{len(results)} finding(s)")
    else:
        print(f"clean: {len(args.files)} file(s)")
    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
````

- [ ] **Step 4: テストが通ることを確認する**

Run: `cd knowledge_sharing/skills/session-tips-digest/scripts && PYTEST tests/test_scan_sensitive.py`
Expected: PASS（8 passed）

- [ ] **Step 5: コミット**

```bash
git add knowledge_sharing/skills/session-tips-digest/scripts/scan_sensitive.py knowledge_sharing/skills/session-tips-digest/scripts/tests/test_scan_sensitive.py
git commit -m "feat(knowledge-sharing): 機密情報と固有名のスキャナを追加"
```

### Task 2: 記録の集計 `extract_sessions.py`

**Files:**
- Create: `S/scripts/extract_sessions.py`
- Test: `S/scripts/tests/test_extract_sessions.py`

**Interfaces:**
- Consumes: `scan_sensitive.redact(text: str) -> str`（Task 1）
- Produces:
  - CLI: `extract_sessions.py --out PATH [--since 30d|YYYY-MM-DD] [--projects a,b] [--claude-dir DIR] [--now ISO] [--patterns p1,p2]`
  - 出力 JSON のトップレベルキー: `generated_at` `since` `projects_filter` `counts` `prompts` `tool_usage` `bash_samples` `memories` `harness` `vocabulary`
  - `tool_usage` は `tools` `skills` `agents` `mcp_servers` `gh` の各キーに `[[name, count], ...]`（多い順）
  - `vocabulary` は `projects` `repos` `hosts` `emails` `users` の各キーに文字列の配列。Task 1 の `load_vocab` がこれを読む

- [ ] **Step 1: テストを書く**

````python path=knowledge_sharing/skills/session-tips-digest/scripts/tests/test_extract_sessions.py
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
````

- [ ] **Step 2: テストが失敗することを確認する**

Run: `cd knowledge_sharing/skills/session-tips-digest/scripts && PYTEST tests/test_extract_sessions.py`
Expected: FAIL（`extract_sessions.py` が無く、終了コードが 2 になる）

- [ ] **Step 3: 実装する**

````python path=knowledge_sharing/skills/session-tips-digest/scripts/extract_sessions.py
#!/usr/bin/env python3
"""Summarize Claude Code records under ~/.claude into one JSON for tips extraction.

The output holds prompts, tool usage counts, sample commands, memory notes,
harness structure (names only, never values) and a vocabulary of identifying
names that scan_sensitive.py uses. Secrets in prompts and commands are redacted.

Usage:
  extract_sessions.py --out tips/.work/sessions.json [--since 30d|YYYY-MM-DD]
                      [--projects a,b] [--claude-dir ~/.claude] [--patterns p1,p2]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_sensitive import redact  # noqa: E402

DEFAULT_PATTERNS = [
    "gh stack",
    "git worktree",
    "gcloud",
    "aws ",
    "agy",
    "terraform",
    "docker",
    "claude -p",
    "uv ",
]
SAMPLES_PER_PATTERN = 5
PROMPT_MAX = 1000
SAMPLE_MAX = 300
MEMORY_MAX = 400

# Hosts under these suffixes are public services, not identifying names.
PUBLIC_HOST_SUFFIXES = (
    "github.com", "githubusercontent.com", "github.io", "github.blog",
    "anthropic.com", "claude.com", "claude.ai",
    "google.com", "googleapis.com", "gstatic.com", "googleusercontent.com",
    "amazon.com", "amazonaws.com", "microsoft.com", "azure.com",
    "arxiv.org", "npmjs.com", "npmjs.org", "pypi.org", "python.org", "astral.sh",
    "vercel.com", "cloudflare.com", "jsdelivr.net", "unpkg.com", "grafana.com",
    "notion.com", "notion.so", "slack.com", "figma.com", "stripe.com", "openai.com",
    "example.com", "example.org", "example.net", "localhost",
)
# Hosts under these suffixes identify a tenant, but the suffix itself is shared.
SHARED_PLATFORM_SUFFIXES = (
    "run.app", "web.app", "vercel.app", "firebaseapp.com", "appspot.com",
    "herokuapp.com", "cloudfunctions.net", "netlify.app", "pages.dev", "workers.dev",
)
PUBLIC_OWNERS = {"anthropics", "openai", "github", "microsoft", "google", "vercel", "astral-sh"}
SECOND_LEVEL = {"co", "ne", "or", "ac", "go", "gr", "ed", "lg"}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}")
HOST_RE = re.compile(
    r"(?<![A-Za-z0-9_\-])((?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)+"
    r"(?:com|net|org|io|dev|app|jp|ai|cloud|run))(?![A-Za-z0-9\-])",
    re.IGNORECASE,
)
REPO_RE = re.compile(
    r"github\.com[:/]([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+?)(?:\.git)?(?=$|[\s/'\"#)?,])"
)
REPO_FLAG_RE = re.compile(r"(?:\s-R|--repo)[\s=]+([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)")
GH_RE = re.compile(r"^\s*(gh\s+[a-z][a-z\-]*\s+[a-z][a-z\-]*)")
FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_now(value: str | None) -> dt.datetime:
    if not value:
        return dt.datetime.now(dt.timezone.utc)
    d = dt.datetime.fromisoformat(value)
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def parse_since(value: str, now: dt.datetime) -> dt.datetime:
    value = value.strip()
    m = re.fullmatch(r"(\d+)d", value)
    if m:
        return now - dt.timedelta(days=int(m.group(1)))
    try:
        day = dt.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"--since must look like 30d or YYYY-MM-DD: {value}") from None
    return dt.datetime.combine(day, dt.time.min, tzinfo=dt.timezone.utc)


def parse_ts(value) -> dt.datetime | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value / 1000, dt.timezone.utc)
    if isinstance(value, str):
        try:
            d = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    return None


def project_name(cwd: str) -> str:
    """Map a working directory to its repository name, folding worktrees in."""
    cwd = str(cwd).split("/.claude/worktrees/")[0].rstrip("/")
    return Path(cwd).name or cwd


def wanted(name: str, filters: list[str]) -> bool:
    return not filters or any(f in name.lower() for f in filters)


def read_jsonl(path: Path, must_contain: str | None = None) -> Iterator[dict]:
    try:
        fh = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return
    with fh:
        for raw in fh:
            if must_contain and must_contain not in raw:
                continue
            raw = raw.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except ValueError:
                continue
            if isinstance(data, dict):
                yield data


def dir_project(dirpath: Path, cache: dict[Path, str]) -> str:
    if dirpath not in cache:
        name = dirpath.name
        for f in sorted(dirpath.glob("*.jsonl")):
            found = next((d["cwd"] for d in read_jsonl(f, '"cwd"') if d.get("cwd")), None)
            if found:
                name = project_name(found)
                break
        cache[dirpath] = name
    return cache[dirpath]


def collect_prompts(claude_dir, cutoff, filters, texts, names) -> list[dict]:
    out = []
    for d in read_jsonl(claude_dir / "history.jsonl"):
        ts = parse_ts(d.get("timestamp"))
        if ts is None or ts < cutoff:
            continue
        proj = project_name(d.get("project", ""))
        if not wanted(proj, filters):
            continue
        text = str(d.get("display", ""))
        texts.append(text)
        names.add(proj)
        out.append(
            {"time": ts.isoformat(timespec="minutes"), "project": proj, "text": redact(text)[:PROMPT_MAX]}
        )
    return out


def _top(counter: Counter) -> list[list]:
    return [[k, v] for k, v in counter.most_common()]


def collect_usage(claude_dir, cutoff, filters, patterns, texts, names):
    tools, skills, agents, mcp, gh = Counter(), Counter(), Counter(), Counter(), Counter()
    samples: list[dict] = []
    seen: set[tuple[str, str]] = set()
    per_pattern: Counter = Counter()
    for f in sorted((claude_dir / "projects").glob("*/*.jsonl")):
        try:
            if dt.datetime.fromtimestamp(f.stat().st_mtime, dt.timezone.utc) < cutoff:
                continue
        except OSError:
            continue
        for d in read_jsonl(f, '"tool_use"'):
            ts = parse_ts(d.get("timestamp"))
            if ts is not None and ts < cutoff:
                continue
            proj = project_name(d["cwd"]) if d.get("cwd") else f.parent.name
            if not wanted(proj, filters):
                continue
            content = (d.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            names.add(proj)
            for c in content:
                if not isinstance(c, dict) or c.get("type") != "tool_use":
                    continue
                name = str(c.get("name", ""))
                inp = c.get("input") if isinstance(c.get("input"), dict) else {}
                tools[name] += 1
                if name == "Skill":
                    skills[str(inp.get("skill", ""))] += 1
                elif name in ("Agent", "Task"):
                    agents[str(inp.get("subagent_type") or "(default)")] += 1
                elif name.startswith("mcp__"):
                    parts = name.split("__")
                    mcp[parts[1] if len(parts) > 1 else name] += 1
                elif name == "Bash":
                    cmd = str(inp.get("command", ""))
                    texts.append(cmd)
                    m = GH_RE.match(cmd)
                    if m:
                        gh[" ".join(m.group(1).split())] += 1
                    one = redact(" ".join(cmd.split()))[:SAMPLE_MAX]
                    for pat in patterns:
                        if pat in cmd and per_pattern[pat] < SAMPLES_PER_PATTERN and (pat, one) not in seen:
                            seen.add((pat, one))
                            per_pattern[pat] += 1
                            samples.append({"pattern": pat.strip(), "project": proj, "command": one})
    usage = {
        "tools": _top(tools),
        "skills": _top(skills),
        "agents": _top(agents),
        "mcp_servers": _top(mcp),
        "gh": _top(gh),
    }
    return usage, samples


def parse_memory(path: Path) -> tuple[str, str, str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta: dict[str, str] = {}
    body = text
    m = FRONT_RE.match(text)
    if m:
        body = text[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t")):
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip().strip("\"'")
    how = ""
    marker = "**How to apply:**"
    i = body.find(marker)
    if i >= 0:
        how = body[i + len(marker):].split("\n\n")[0].strip()[:MEMORY_MAX]
    return meta.get("name", path.stem), meta.get("description", ""), how, body


def collect_memories(claude_dir, filters, cache, texts) -> list[dict]:
    out = []
    for f in sorted((claude_dir / "projects").glob("*/memory/*.md")):
        if f.name == "MEMORY.md":
            continue
        proj = dir_project(f.parent.parent, cache)
        if not wanted(proj, filters):
            continue
        try:
            name, desc, how, body = parse_memory(f)
            modified = dt.datetime.fromtimestamp(f.stat().st_mtime, dt.timezone.utc).date().isoformat()
        except OSError:
            continue
        texts.append(body)
        out.append(
            {
                "project": proj,
                "name": name,
                "description": redact(desc),
                "how_to_apply": redact(how),
                "modified": modified,
            }
        )
    return out


def collect_harness(claude_dir: Path) -> dict:
    try:
        settings = json.loads((claude_dir / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        settings = {}
    if not isinstance(settings, dict):
        settings = {}

    def as_dict(value):
        return value if isinstance(value, dict) else {}

    skills_dir = claude_dir / "skills"
    return {
        "hook_events": sorted(as_dict(settings.get("hooks"))),
        "enabled_plugins": sorted(k for k, v in as_dict(settings.get("enabledPlugins")).items() if v),
        "env_keys": sorted(as_dict(settings.get("env"))),
        "has_status_line": "statusLine" in settings,
        "commands": sorted(p.stem for p in (claude_dir / "commands").glob("*.md")),
        "skills": sorted(p.name for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else [],
        "agents": sorted(p.stem for p in (claude_dir / "agents").glob("*.md")),
    }


def _matches_suffix(host: str, suffixes) -> bool:
    return any(host == s or host.endswith("." + s) for s in suffixes)


def registrable(host: str) -> str:
    labels = host.split(".")
    if len(labels) >= 3 and labels[-2] in SECOND_LEVEL:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def build_vocabulary(texts: list[str], project_names: set[str], claude_dir: Path) -> dict:
    hosts: set[str] = set()
    emails: set[str] = set()
    repos: set[str] = set()
    for text in texts:
        for m in EMAIL_RE.finditer(text):
            emails.add(m.group(0).lower())
        for m in HOST_RE.finditer(text):
            host = m.group(1).lower().strip(".")
            if _matches_suffix(host, PUBLIC_HOST_SUFFIXES):
                continue
            hosts.add(host)
            if not _matches_suffix(host, SHARED_PLATFORM_SUFFIXES):
                hosts.add(registrable(host))
        for rx in (REPO_RE, REPO_FLAG_RE):
            for m in rx.finditer(text):
                owner, repo = m.group(1), m.group(2)
                if owner.lower() not in PUBLIC_OWNERS:
                    repos.update({owner, repo})
    users: set[str] = set()
    home = Path.home()
    try:
        claude_dir.resolve().relative_to(home.resolve())
        users.add(home.name)
    except ValueError:
        pass

    def keep(values):
        return sorted({v for v in values if len(v) >= 3 and v != "-"})

    return {
        "projects": keep(project_names),
        "repos": keep(repos),
        "hosts": keep(hosts),
        "emails": sorted(emails),
        "users": keep(users),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize Claude Code records for tips extraction.")
    parser.add_argument("--out", required=True, help="output JSON path")
    parser.add_argument("--since", default="30d", help="30d style or YYYY-MM-DD (default 30d)")
    parser.add_argument("--projects", default="", help="comma-separated substrings of project names")
    parser.add_argument("--claude-dir", default=str(Path.home() / ".claude"))
    parser.add_argument("--now", default=None, help="ISO datetime used as now (for tests)")
    parser.add_argument("--patterns", default=",".join(DEFAULT_PATTERNS), help="Bash sample patterns")
    args = parser.parse_args(argv)

    claude_dir = Path(args.claude_dir).expanduser()
    if not claude_dir.is_dir():
        print(f"error: not a directory: {claude_dir}", file=sys.stderr)
        return 2
    try:
        now = parse_now(args.now)
        cutoff = parse_since(args.since, now)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    filters = [f.strip().lower() for f in args.projects.split(",") if f.strip()]
    patterns = [p for p in args.patterns.split(",") if p.strip()]

    texts: list[str] = []
    names: set[str] = set()
    cache: dict[Path, str] = {}
    prompts = collect_prompts(claude_dir, cutoff, filters, texts, names)
    usage, samples = collect_usage(claude_dir, cutoff, filters, patterns, texts, names)
    memories = collect_memories(claude_dir, filters, cache, texts)
    report = {
        "generated_at": now.isoformat(timespec="seconds"),
        "since": cutoff.isoformat(timespec="seconds"),
        "projects_filter": filters,
        "counts": {"prompts": len(prompts), "bash_samples": len(samples), "memories": len(memories)},
        "prompts": prompts,
        "tool_usage": usage,
        "bash_samples": samples,
        "memories": memories,
        "harness": collect_harness(claude_dir),
        "vocabulary": build_vocabulary(texts, names, claude_dir),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    calls = sum(count for _, count in usage["tools"])
    print(f"wrote {out}: {len(prompts)} prompts, {calls} tool calls, {len(memories)} memories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

- [ ] **Step 4: テストが通ることを確認する**

Run: `cd knowledge_sharing/skills/session-tips-digest/scripts && PYTEST tests/`
Expected: PASS（Task 1 と合わせて 18 passed）

- [ ] **Step 5: コミット**

```bash
git add knowledge_sharing/skills/session-tips-digest/scripts/extract_sessions.py knowledge_sharing/skills/session-tips-digest/scripts/tests/test_extract_sessions.py
git commit -m "feat(knowledge-sharing): セッション記録の集計スクリプトを追加"
```

### Task 3: Markdown→HTML 変換 `md_to_artifact.py`

**Files:**
- Create: `S/scripts/md_to_artifact.py`
- Test: `S/scripts/tests/test_md_to_artifact.py`

**Interfaces:**
- Consumes: なし
- Produces:
  - `render(md: str, title: str | None = None, eyebrow: str = "Claude Code / Field Notes", meta: list[str] | None = None, fallback_title: str = "Claude Code Tips") -> str`
  - `inline(text: str) -> str`
  - CLI: `md_to_artifact.py INPUT.md --out OUT.html [--title T] [--eyebrow E] [--meta "対象: ..."]...`
  - 出力は Artifact の page contract に沿い、`<!doctype>` `<html>` `<head>` `<body>` を含まない。先頭が `<title>`

- [ ] **Step 1: テストを書く**

````python path=knowledge_sharing/skills/session-tips-digest/scripts/tests/test_md_to_artifact.py
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
CONVERT = SCRIPTS / "md_to_artifact.py"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


conv = _load("md_to_artifact")

SAMPLE = """# Claude Code 運用 Tips

対象読者はエンジニア。
1章は通読する。

## 1. 落とし穴

### `Closes #N` をバッククォートで囲むと閉じない

PR 本文に `` `Closes #9` `` と書いたら閉じなかった。
体裁を整えたいなら `**Closes #N**` にする。

| コマンド | 何をするか |
|---|---|
| `/fix-pr <N>` | CI を直す |

```bash
echo "<b>" && gh stack link 10 11
```

- **強調**と [リンク](https://code.claude.com/docs/en/goal)
- <script>alert(1)</script>

1. 一つ目
2. 二つ目
"""


def test_code_spans_keep_symbols_and_never_nest():
    html = conv.render(SAMPLE)
    assert "<code><code>" not in html
    assert "<code><strong>" not in html
    assert "<code>`Closes #9`</code>" in html
    assert "<code>**Closes #N**</code>" in html
    assert "<code>`Closes #N`</code>" not in html
    assert "<code>Closes #N</code>" in html


def test_page_contract_title_and_theme_tokens():
    html = conv.render(SAMPLE)
    assert html.lstrip().startswith("<title>Claude Code 運用 Tips</title>")
    assert "<!doctype" not in html.lower()
    assert "<html" not in html.lower()
    assert "<body" not in html.lower()
    root = html.index(":root{")
    assert "--bg:" in html[root : html.index("}", root)]
    assert root < html.index("@media (prefers-color-scheme: dark)")
    assert ':root[data-theme="dark"]' in html


def test_blocks_are_converted_and_escaped():
    html = conv.render(SAMPLE)
    assert "<table>" in html and "<th>コマンド</th>" in html
    assert "<td><code>/fix-pr &lt;N&gt;</code></td>" in html
    assert '<pre class="code"><code>echo "&lt;b&gt;" &amp;&amp; gh stack link 10 11</code></pre>' in html
    assert '<a href="https://code.claude.com/docs/en/goal" target="_blank" rel="noopener">リンク</a>' in html
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<ol><li>一つ目</li><li>二つ目</li></ol>" in html


def test_lead_paragraph_joins_lines_without_br():
    html = conv.render(SAMPLE)
    assert "<p>対象読者はエンジニア。1章は通読する。</p>" in html
    assert "<br>" not in html


def test_toc_lists_sections():
    html = conv.render(SAMPLE)
    toc = html[html.index('<nav class="toc"') : html.index("</nav>")]
    assert re.search(r'<li class="l2"><a href="#s1">1\. 落とし穴</a></li>', toc)
    assert '<li class="l3"><a href="#s2"><code>Closes #N</code> をバッククォートで囲むと閉じない</a></li>' in toc


def test_title_falls_back_when_no_h1():
    html = conv.render("## だけ\n\n本文\n", fallback_title="tips")
    assert html.lstrip().startswith("<title>tips</title>")
    html = conv.render("## だけ\n", title="指定タイトル")
    assert html.lstrip().startswith("<title>指定タイトル</title>")


def test_cli_writes_file(tmp_path):
    src = tmp_path / "claude-code-tips.md"
    src.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "dist" / "index.html"
    r = subprocess.run(
        [sys.executable, "-I", str(CONVERT), str(src), "--out", str(out), "--meta", "対象: エンジニア"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    html = out.read_text(encoding="utf-8")
    assert "<span>対象: エンジニア</span>" in html
    r = subprocess.run(
        [sys.executable, "-I", str(CONVERT), str(tmp_path / "missing.md"), "--out", str(out)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
````

- [ ] **Step 2: テストが失敗することを確認する**

Run: `cd knowledge_sharing/skills/session-tips-digest/scripts && PYTEST tests/test_md_to_artifact.py`
Expected: FAIL（`md_to_artifact.py` が無いため `FileNotFoundError`）

- [ ] **Step 3: 実装する**

````python path=knowledge_sharing/skills/session-tips-digest/scripts/md_to_artifact.py
#!/usr/bin/env python3
"""Convert a tips Markdown file into an Artifact page (HTML body content).

The page follows the Artifact page contract: no doctype/html/head/body tags,
a <title> first, color tokens on :root with dark-mode overrides, and a layout
that works at phone width.

Usage:
  md_to_artifact.py INPUT.md --out OUT.html [--title T] [--eyebrow E] [--meta TEXT]...
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

CSS = """<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Zen+Old+Mincho:wght@700;900&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: reading column with a sticky table of contents on the left at desktop; one column on phones. */
:root{--bg:#f6f7f4;--surface:#ffffff;--fg:#1d2420;--muted:#5b665f;--line:#d9ded8;--accent:#1f6f5f;--accent-soft:#e3efea;--code-bg:#eef1ed;--font-body:"Zen Kaku Gothic New","Hiragino Sans","Noto Sans JP",sans-serif;--font-display:"Zen Old Mincho","Hiragino Mincho ProN","Noto Serif JP",serif;--font-mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#141917;--surface:#1b211e;--fg:#e6ebe7;--muted:#9aa69f;--line:#2c352f;--accent:#6fc2ad;--accent-soft:#1f3a33;--code-bg:#222925;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#141917;--surface:#1b211e;--fg:#e6ebe7;--muted:#9aa69f;--line:#2c352f;--accent:#6fc2ad;--accent-soft:#1f3a33;--code-bg:#222925;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font-family:var(--font-body);font-size:16px;line-height:1.85;margin:0;padding-block:0 4rem;padding-inline:16px}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:3px}
a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wrap{max-width:1100px;margin:0 auto}
header.hero{padding-block:3rem 2rem;border-bottom:1px solid var(--line)}
.eyebrow{font-family:var(--font-mono);font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin:0 0 .75rem}
h1{font-family:var(--font-display);font-weight:900;font-size:clamp(1.8rem,4vw,2.6rem);line-height:1.3;margin:0 0 1rem;text-wrap:balance}
.lead p{margin:0 0 .75rem;color:var(--muted);max-width:40em}
.meta{display:flex;flex-wrap:wrap;gap:.5rem 1.25rem;font-family:var(--font-mono);font-size:.8rem;color:var(--muted);margin-top:1.25rem}
.layout{display:grid;grid-template-columns:260px minmax(0,1fr);gap:3rem;align-items:start;padding-top:2rem}
.toc{position:sticky;top:calc(env(safe-area-inset-top,0px) + 1rem);max-height:calc(100vh - 2rem);overflow:auto;font-size:.85rem;padding-right:.5rem}
.toc-label{font-family:var(--font-mono);font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 .5rem}
.toc ol{list-style:none;margin:0;padding:0;border-left:1px solid var(--line)}
.toc a{display:block;color:var(--fg);text-decoration:none;padding:.25rem .75rem;border-left:2px solid transparent;margin-left:-1px;line-height:1.5}
.toc a:hover{background:var(--accent-soft)}
.toc li.l2 a{font-weight:700;margin-top:.5rem}
.toc li.l3 a{color:var(--muted);font-size:.8rem}
.toc a.active{border-left-color:var(--accent);color:var(--accent)}
main{min-width:0;max-width:44em}
section{padding-block:1.5rem 1rem;border-bottom:1px solid var(--line)}
section:last-of-type{border-bottom:0}
h2{font-family:var(--font-display);font-weight:700;font-size:1.55rem;line-height:1.35;margin:.5rem 0 1rem;text-wrap:balance;scroll-margin-top:1rem}
h3{font-size:1.08rem;font-weight:700;line-height:1.5;margin:2.25rem 0 .6rem;padding-left:.75rem;border-left:3px solid var(--accent);text-wrap:balance;scroll-margin-top:1rem}
p{margin:0 0 .9rem}
ul,ol{margin:0 0 1rem;padding-left:1.4em}
li{margin:.25rem 0}
li::marker{color:var(--accent)}
blockquote{margin:0 0 1rem;padding:.5rem 1rem;border-left:3px solid var(--line);color:var(--muted)}
code{font-family:var(--font-mono);font-size:.86em;background:var(--code-bg);padding:.1em .4em;border-radius:4px;word-break:break-all}
pre.code{background:var(--code-bg);border:1px solid var(--line);border-radius:6px;padding:.9rem 1rem;overflow-x:auto;margin:.75rem 0 1.1rem;line-height:1.6}
pre.code code{background:none;padding:0;font-size:.82rem;word-break:normal;white-space:pre}
.tablewrap{overflow-x:auto;margin:.75rem 0 1.1rem}
table{border-collapse:collapse;width:100%;font-size:.92rem;min-width:420px}
th,td{text-align:left;vertical-align:top;padding:.55rem .7rem;border-bottom:1px solid var(--line)}
th{font-weight:700;color:var(--muted);font-size:.8rem;letter-spacing:.04em;border-bottom:2px solid var(--line)}
td code{white-space:nowrap}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);font-size:.85rem;color:var(--muted);font-family:var(--font-mono)}
@media (max-width:860px){.layout{grid-template-columns:1fr;gap:1.5rem}.toc{position:static;max-height:none;border:1px solid var(--line);border-radius:6px;padding:1rem;background:var(--surface)}.toc li.l3{display:none}}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
</style>
"""

SCRIPT = """<script>
(function(){
  var links=[].slice.call(document.querySelectorAll('.toc a'));
  var map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a});
  if(!('IntersectionObserver' in window))return;
  var obs=new IntersectionObserver(function(es){
    es.forEach(function(e){if(e.isIntersecting){links.forEach(function(l){l.classList.remove('active')});var a=map[e.target.id];if(a)a.classList.add('active');}});
  },{rootMargin:'-10% 0px -80% 0px'});
  [].slice.call(document.querySelectorAll('main section, main h3')).forEach(function(t){obs.observe(t)});
})();
</script>
"""

BLOCK_START = re.compile(r"^(#{1,3} |```|\||- |\d+\. |> )")


def inline(text: str) -> str:
    """Render inline Markdown. Code spans are taken out first so their content stays literal."""
    spans: list[str] = []

    def stash(m: re.Match) -> str:
        spans.append("<code>" + html.escape(m.group(1).strip(), quote=False) + "</code>")
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"``(.+?)``", stash, text)
    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )
    return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)


def _table(rows: list[list[str]]) -> str:
    head, body = rows[0], [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
    out = '<div class="tablewrap"><table><thead><tr>'
    out += "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
    for r in body:
        out += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
    return out + "</tbody></table></div>"


def render(
    md: str,
    title: str | None = None,
    eyebrow: str = "Claude Code / Field Notes",
    meta: list[str] | None = None,
    fallback_title: str = "Claude Code Tips",
) -> str:
    lines = md.split("\n")
    out: list[str] = []
    lead: list[str] = []
    toc: list[tuple[int, str, str]] = []
    h1: str | None = None
    in_section = False
    count = 0
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("```"):
            buf = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(f'<pre class="code"><code>{html.escape(chr(10).join(buf), quote=False)}</code></pre>')
            continue
        if line.startswith("# "):
            h1 = h1 or line[2:].strip()
            i += 1
            continue
        if line.startswith("## ") or line.startswith("### "):
            level = 2 if line.startswith("## ") else 3
            text = line[level + 1:].strip()
            count += 1
            anchor = f"s{count}"
            toc.append((level, anchor, text))
            if level == 2:
                if in_section:
                    out.append("</section>")
                out.append(f'<section id="{anchor}"><h2>{inline(text)}</h2>')
                in_section = True
            else:
                out.append(f'<h3 id="{anchor}">{inline(text)}</h3>')
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append(_table(rows))
            continue
        if re.match(r"^\d+\. ", line):
            items = []
            while i < n and re.match(r"^\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        if line.startswith("- "):
            items = []
            while i < n and lines[i].startswith("- "):
                items.append(lines[i][2:])
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        if line.startswith("> "):
            buf = []
            while i < n and lines[i].startswith("> "):
                buf.append(lines[i][2:].strip())
                i += 1
            out.append("<blockquote><p>" + "".join(inline(x) for x in buf) + "</p></blockquote>")
            continue
        if not line.strip() or line.strip() == "---":
            i += 1
            continue
        buf = []
        while i < n and lines[i].strip() and not BLOCK_START.match(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        paragraph = "<p>" + "".join(inline(x) for x in buf) + "</p>"
        (out if in_section else lead).append(paragraph)
    if in_section:
        out.append("</section>")

    page_title = title or h1 or fallback_title
    toc_html = '<nav class="toc" aria-label="目次"><p class="toc-label">目次</p><ol>'
    toc_html += "".join(f'<li class="l{lv}"><a href="#{a}">{inline(t)}</a></li>' for lv, a, t in toc)
    toc_html += "</ol></nav>"
    meta_html = "".join(f"<span>{html.escape(m, quote=False)}</span>" for m in (meta or []))
    return (
        f"<title>{html.escape(page_title, quote=False)}</title>\n"
        + CSS
        + '<div class="wrap">\n<header class="hero">\n'
        + f'<p class="eyebrow">{html.escape(eyebrow, quote=False)}</p>\n'
        + f"<h1>{inline(page_title)}</h1>\n"
        + f'<div class="lead">{"".join(lead)}</div>\n'
        + (f'<div class="meta">{meta_html}</div>\n' if meta_html else "")
        + "</header>\n"
        + f'<div class="layout">\n{toc_html}\n<main>\n{"".join(out)}\n</main>\n</div>\n'
        + "<footer>事例は案件名・固有値を伏せ、パターンとして書き直してある。</footer>\n</div>\n"
        + SCRIPT
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert tips Markdown into an Artifact page.")
    parser.add_argument("input")
    parser.add_argument("--out", required=True)
    parser.add_argument("--title")
    parser.add_argument("--eyebrow", default="Claude Code / Field Notes")
    parser.add_argument("--meta", action="append", default=[])
    args = parser.parse_args(argv)
    src = Path(args.input)
    try:
        md = src.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    page = render(md, title=args.title, eyebrow=args.eyebrow, meta=args.meta, fallback_title=src.stem)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({len(page)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
````

- [ ] **Step 4: テストが通ることを確認する**

Run: `cd knowledge_sharing/skills/session-tips-digest/scripts && PYTEST tests/`
Expected: PASS（全体で 25 passed）

- [ ] **Step 5: コミット**

```bash
git add knowledge_sharing/skills/session-tips-digest/scripts/md_to_artifact.py knowledge_sharing/skills/session-tips-digest/scripts/tests/test_md_to_artifact.py
git commit -m "feat(knowledge-sharing): Tips の Markdown を Artifact 用 HTML に変換するスクリプトを追加"
```

### Task 4: スキル本体・参照資料・プラグイン登録

**Files:**
- Create: `S/SKILL.md`
- Create: `S/references/tip-selection.md`
- Create: `S/references/research-sources.md`
- Create: `S/references/writing-style.md`
- Create: `S/templates/tips.md`
- Create: `S/templates/references.md`
- Create: `knowledge_sharing/.claude-plugin/plugin.json`
- Create: `knowledge_sharing/.claude-plugin/marketplace.json`
- Create: `knowledge_sharing/README.md`
- Modify: `.claude-plugin/marketplace.json`（`plugins` 配列の末尾にエントリを追加）
- Modify: `README.md:15`（公開中のプラグイン一覧に 1 行追加）

**Interfaces:**
- Consumes: Task 1〜3 の CLI（引数名はそれぞれの Produces を参照）
- Produces: `/knowledge-sharing:session-tips-digest` として呼べるスキル

既存プラグインに合わせ、プラグイン直下に `plugin.json`（common-development と同形式）と `marketplace.json`（development-workflows と同形式）の両方を置く。スペックの構成図にない `plugin.json` は、既存プラグインとの一貫性のために追加する。

- [ ] **Step 1: SKILL.md を書く**

````markdown path=knowledge_sharing/skills/session-tips-digest/SKILL.md
---
name: session-tips-digest
description: Claude Code の過去のセッション記録（~/.claude の履歴・セッションログ・memory）から、他のメンバーと共有できる運用 Tips を抽出し、公式ドキュメントや論文などの一次情報で裏付けを取って、Markdown・Artifact・Notion に公開する。「過去の会話から Tips をまとめて」「Claude Code の使い方をチームに共有したい」「今月の学びを Tips にして」などの依頼で使う。セッション 1 本の効率採点ではない（それは evaluate-session の領域）。
---

# Session Tips Digest

自分の Claude Code の記録から「他の人がそのまま使える運用の知見」を抜き出し、裏付けを付けて共有できる形にする。

成果物は 3 つ。

- `tips/claude-code-tips.md`: Tips 本体
- `tips/claude-code-tips-references.md`: 一次情報との対応表
- Artifact（HTML ページ）。指定があれば Notion ページも

## 引数

`$ARGUMENTS` を次のように解釈する。指定が無いものは既定値を使う。

| 引数 | 既定 | 意味 |
|---|---|---|
| `--since` | `30d` | 抽出期間。`7d` や `2026-09-01` も受ける |
| `--projects` | 全部 | 対象プロジェクト名の部分一致（カンマ区切り） |
| `--out` | `tips/` | 成果物ディレクトリ。作業ファイルは `<out>/.work/` |
| `--artifact-url` | なし | 既存 Artifact を更新する。無ければ新規公開 |
| `--notion` | なし | 指定した Notion ページの配下に本体を書き出す |
| `--no-research` | なし | Phase 3（一次情報の調査）を省略する |

以下、このスキルのディレクトリを `<skill-dir>`、`--out` を `<out>` と書く。スクリプトはすべて `python3 -I` で実行する。

## Phase 0: 準備

1. `<out>` と `<out>/.work/` を作る
2. `<out>/claude-code-tips.md` が既にあれば差分更新モードにする。本文末尾の `最終更新: YYYY-MM-DD` を読み、`--since` が指定されていなければその日付を `--since` に使う。既存の Tips は消さず、新しい Tips を該当する章に追記し、既存の Tips を新しい事例や情報で更新する
3. 作業の段取りをユーザーに 1 行で伝える（期間、対象、調査の有無）

## Phase 1: 抽出

```bash
python3 -I <skill-dir>/scripts/extract_sessions.py --since <since> [--projects <list>] --out <out>/.work/sessions.json
```

出力 JSON には、期間内のプロンプト、ツール・スキル・エージェント・MCP・`gh` の利用回数、パターンに合う Bash コマンド例、memory の要点、ハーネス構成（名前だけ）、匿名化辞書（`vocabulary`）が入る。秘密情報は伏せ字済み。

この JSON を読み、加えて次も確認する。

- `harness.commands` と `harness.skills` に出てくる自作コマンド・スキルの本文（`~/.claude/commands/*.md` など）。汎用的なものは Tips の材料になる
- 繰り返し現れるプロンプトの型（毎回付けている指示、決まった往復）
- memory のうち、プロジェクト固有でない落とし穴

候補の選び方と除外基準は `references/tip-selection.md` に従う。選んだ候補は「章」「見出し」「根拠となる記録」の 3 列でメモし、根拠が記録に無いものは採らない。

## Phase 2: 匿名化と執筆

1. `templates/tips.md` の構成で `<out>/claude-code-tips.md` を書く。各 Tips は「何をするか」「なぜ（匿名化した事例）」「コマンドや設定」の順。匿名化のルールは `references/tip-selection.md` の「匿名化」に従う
2. 文章は `references/writing-style.md` に従う。natural-japanese スキルが使えるなら Skill ツールで読み込み、その lint を実行して指摘を処理する。使えなければ同ファイルのチェックリストで代替する
3. 機密スキャンを実行する

```bash
python3 -I <skill-dir>/scripts/scan_sensitive.py <out>/claude-code-tips.md --vocab <out>/.work/sessions.json [--allow-file <out>/.work/allow.txt]
```

終了コードが 1 なら、検出箇所を書き換えて再実行する。検出語が一般語（例: プロジェクト名がたまたま `onboarding`）で、伏せる必要が無いと判断できる場合だけ、`<out>/.work/allow.txt` に理由のコメント付きで追記する。秘密情報（トークン、メール、組織 ID、ホームパス）は許可リストに入れない。

**スキャンが 0 件になるまで Phase 3 以降に進まない。**

## Phase 3: 一次情報の調査

`--no-research` のときは飛ばし、Tips 本体末尾に「一次情報による裏付けは未実施」と書く。

1. 各 Tips について、`references/research-sources.md` の優先順位で一次情報を探す。WebSearch で候補を見つけ、WebFetch で本文を確認してから引用する。ライブラリやツールの公式ドキュメントは Context7 が使えるならそれを優先する
2. `templates/references.md` の形式で `<out>/claude-code-tips-references.md` を書く。各項目を「裏付ける」「修正する」「範囲を狭める」のどれかに分類する。Tips を弱める結果も必ず載せる
3. 確度の高いもの（公式ドキュメントで確認できた仕様、Tips の記述を誤りと示すもの）は本体にも反映する。研究結果を本体に入れるときは、示唆か確定かを書き分ける
4. 本体末尾に「参考文献」の節を置く
5. 本体と参照リストの両方に Phase 2 の機密スキャンを再実行する

公式に記述が見つからない落とし穴は消さずに残し、「実測」と明記する。

## Phase 4: 公開

1. HTML を生成してスキャンする

```bash
python3 -I <skill-dir>/scripts/md_to_artifact.py <out>/claude-code-tips.md --out <out>/dist/index.html --meta "対象: <読者>" --meta "期間: <開始> 〜 <終了>" --meta "最終更新: <今日>"
python3 -I <skill-dir>/scripts/scan_sensitive.py <out>/dist/index.html --vocab <out>/.work/sessions.json [--allow-file <out>/.work/allow.txt]
```

2. Artifact ツールで `<out>/dist/index.html` を公開する
   - `--artifact-url` があれば、先に `action: "read"` で現行版を読み、その `url` を指定して更新する
   - 無ければ新規公開する。`icon` は `notebook`、`description` は Tips の要旨 1 文
   - Artifact ツールが無い環境では、HTML ファイルのパスを伝えて終える
3. `--notion` があれば Notion MCP を使う。`notion-fetch` で親ページを確認し、`notion-create-pages` で子ページとして本体の Markdown を書き出す。Notion MCP が接続されていなければ、`/mcp` で接続してから再実行するよう案内して、この手順だけ飛ばす

## 完了報告

最後のメッセージに次を入れる。

- 採用した Tips の見出し一覧（章ごと）
- 成果物のパス、Artifact の URL、Notion ページの URL
- Artifact は非公開で作られること、共有するにはページの Share メニューから設定すること
- 機密スキャンの結果（0 件）と、許可リストに入れた語とその理由
- 一次情報で確認できず「実測」のまま残した項目

作業ファイル `<out>/.work/` はユーザーのホームの記録を含むので、共有リポジトリにコミットしないよう伝える。`<out>` が git 管理下なら `.gitignore` に `.work/` を追加することを提案する。
````

- [ ] **Step 2: references と templates を書く**

````markdown path=knowledge_sharing/skills/session-tips-digest/references/tip-selection.md
# Tips の選び方と匿名化

## 採る基準

次の 3 つをすべて満たすものだけを Tips にする。

1. **他のプロジェクトでも再現できる。** 特定の案件の設計判断（「この API のトークンは SSM に置く」）ではなく、手順や型（「設定値はパラメータストア経由で環境変数に渡す」）として書けるもの
2. **記録に実例がある。** プロンプト、コマンド、memory のどれかに根拠がある。もっともらしいが記録に無いものは書かない
3. **転記ではない。** コードや公式ドキュメントを読めば分かることをそのまま書かない。「ドキュメントのこの機能を、こういう場面でこう使ったら効いた」のように、使い方の知見になっているもの

## 探す場所

| 材料 | Tips になりやすいもの |
|---|---|
| 繰り返し現れるプロンプト | 毎回付けている指示、決まった往復（「Issue #N を進めて」→「マージしました」） |
| 自作コマンド・スキル | 汎用的な手順を定型化したもの |
| ツール・MCP の利用回数 | よく使う組み合わせ、使い分け |
| Bash コマンド例 | `!` で人間が実行した操作、外部 CLI との連携、`gh` 拡張 |
| memory | 実際に踏んだ落とし穴（Why と How to apply があるもの） |
| ハーネス構成 | hooks、statusLine、テレメトリ、プラグインの組み合わせ |

## 採らないもの

- 特定案件の仕様、データ構造、インフラ構成
- 一度だけ起きた事故で、再発条件が説明できないもの
- 個人の好み（エディタの配色など）で、他人の作業を変えないもの
- セキュリティ上、手順を広めること自体が危険なもの（権限回避の方法など）

## 章の割り振り

| 章 | 入れるもの |
|---|---|
| 1. プロンプトの型 | 依頼の書き方、対話の進め方 |
| 2. ワークフロー | 作業の段取り、ツールの組み合わせ |
| 3. カスタムコマンドとプラグイン | 定型化した手順、導入したプラグイン |
| 4. 落とし穴 | 実際に踏んだ失敗と回避策 |
| 5. 環境設定 | settings、hooks、テレメトリ、memory の運用 |

## 匿名化

公開する文書には、次のものを一切残さない。

- クライアント名、案件名、プロダクト名、リポジトリ名、組織名
- ドメイン名、ホスト名、URL（公開されている公式ドキュメントを除く）
- メールアドレス、人名、アカウント名
- トークン、キー、組織 ID、アカウント ID、プロジェクト ID
- ホームディレクトリのパス、社内のファイルパス
- Notion や社内ツールのページ URL

置き換えの例:

| 元 | 置き換え |
|---|---|
| 具体的な案件名 | 「クライアント案件」「社内ツール」 |
| `PR #13166` | `PR #N` |
| 特定のステージング環境のホスト | 「ステージング環境」 |
| サービスアカウントのメール | `<SA>` |
| 自分のメールアドレス | `<自分>` |
| 特定の外部サービスへの依頼内容 | 「外部サービスの API」 |

事例は「何が起きたか」と「なぜ起きたか」だけを残し、どの案件で起きたかは書かない。
人物に触れるときは役割（「レビュアー」「並走していた別セッション」）で書き、代名詞は使わない。
````

````markdown path=knowledge_sharing/skills/session-tips-digest/references/research-sources.md
# 一次情報の探し方

## 優先順位

1. **公式ドキュメント**: code.claude.com、docs.github.com、cloud.google.com、docs.aws.amazon.com、各ツールの公式 README やドキュメントサイト
2. **ベンダー公式ブログ・チェンジログ**: anthropic.com/engineering、github.blog/changelog、aws.amazon.com/blogs など
3. **論文**: arXiv など。著者・日付・手法・数値をアブストラクトで確認する
4. **その他**: 個人ブログやまとめ記事は、一次情報への導線としてだけ使う。そこに書かれた数値は引用しない

## 手順

1. Tips ごとに「この Tips が依存している事実」を 1〜3 個書き出す（例: 「worktree は origin/main を基点に作られる」）
2. WebSearch で候補を探す。公式ドメインに絞るときは `allowed_domains` を使う
3. WebFetch で本文を開き、該当箇所を確認する。要約だけで判断しない
4. 確認できた内容を「出典」「言っていること」「Tips をどう変えるか」の 3 行で記録する

## 分類

| 分類 | 意味 | 本体への反映 |
|---|---|---|
| 裏付ける | Tips の主張を公式・研究が支持する | 参考文献に載せる |
| 修正する | 仕様が変わっている、より良い公式の方法がある | 本体を書き換える |
| 範囲を狭める | 研究結果が Tips の効果を限定する、例外がある | 本体に注意書きを足す |

Tips を弱める結果も必ず載せる。読者が過信しないことが目的。

## 書き方の注意

- 研究結果は「示唆的」「決定的」を書き分ける。単一の研究、異なる条件（コードレビューの研究を文章校正に当てはめるなど）は示唆にとどめる
- 公式に記述が無いが実際に観測した挙動は「実測」と明記して残す
- 日付を書く。プレビュー機能や実験的機能はその旨を書く
- 引用する数値は、本文を自分で確認したものだけにする
````

````markdown path=knowledge_sharing/skills/session-tips-digest/references/writing-style.md
# 文章の書き方

## 読者と構成

- 読者は「Claude Code を日常的に使っているエンジニア」を既定にする。基本操作の説明はしない
- 冒頭で「どこまで読めばよいか」を宣言する（例: 1〜2 章は通読、3 章以降は参照）
- 見出しはラベルではなく結論にする（「worktree について」ではなく「Issue ごとに worktree を切り、終わったら消す」）
- 章の重さに濃淡をつける。効果の大きい Tips は厚く、小さい落とし穴は 2〜3 行で済ませる

## 1 つの Tips の型

1. 何をするか（1〜2 文）
2. なぜ効くか、何が起きたか（匿名化した事例）
3. コマンドや設定（コードブロック）
4. 注意点や例外（あれば）

## UX ライティングと Progressive Disclosure

- 結論を先に書く。経緯は最後か、書かない
- 全員が読む情報を先に、詳細は後ろに置く
- 1 文 1 メッセージ。1 文は 60 字前後を目安にする
- 同じものは同じ言葉で呼ぶ

## natural-japanese が使えないときのチェックリスト

- [ ] 「〜することができる」「〜と言えるだろう」「重要なのは」のような空句が無い
- [ ] 「〜ではなく〜」の対比を、本当の誤解訂正以外で使っていない
- [ ] 同じ文型の書き出しが 3 回以上続いていない
- [ ] 箇条書きを、並列でない説明の代わりに使っていない
- [ ] 太字は各段落の核 1 か所までに抑えている
- [ ] 専門用語は初出で「何をするものか」を先に書いている
- [ ] 確認していない挙動を断定していない

## 別モデルでの校正（任意）

Gemini などを CLI で呼べる環境なら、本体を別モデルで校正させてもよい。プロンプトには次の変更禁止範囲を必ず入れる。

- コードブロック、インラインコード、URL、ファイルパス、識別子、数値
- 見出しの階層、箇条書きの構造、表の行数・列数
- 事実関係、固有名詞、技術用語

校正結果は diff で確認してから採用する。校正後のファイルにも機密スキャンを再実行する。
````

````markdown path=knowledge_sharing/skills/session-tips-digest/templates/tips.md
# Claude Code 運用 Tips（<期間の呼び名>の実践から）

<開始日>から<終了日>までの Claude Code のセッション記録を振り返り、他のメンバーがそのまま使えるものを集めた。
対象読者は <読者>。基本操作（プロンプト入力、`/` コマンド、`@` でのファイル指定）は知っている前提で書く。

1 章と 2 章は一度通読すると効果が大きい。3 章以降は該当する場面で引く参照部として使う。
事例はすべて案件名や固有値を伏せ、パターンとして書き直してある。

## 1. プロンプトの型

### <結論を書いた見出し>

<何をするか>

<なぜ効くか。匿名化した事例>

```
<プロンプトやコマンドの例>
```

## 2. ワークフロー

### <結論を書いた見出し>

## 3. カスタムコマンドとプラグイン

### <結論を書いた見出し>

## 4. 落とし穴（実際に踏んだもの）

### <何をすると何が起きるか>

<回避策>

## 5. 環境設定

### <結論を書いた見出し>

## 参考文献

- <出典名>: [<タイトル>](<URL>)

## 用語

- **<用語>**: <説明>

最終更新: <YYYY-MM-DD>
````

````markdown path=knowledge_sharing/skills/session-tips-digest/templates/references.md
# Tips を更新できる参考情報（<YYYY-MM> 時点）

`claude-code-tips.md` の各 Tips について、公式ドキュメント・研究・事例のうち内容を更新または補強できるものを集めた。
各項目は「出典」「言っていること」「Tips をどう変えるか」の 3 行で書く。一次情報だけを載せ、二次記事の数値は採用していない。

## 1. 公式ドキュメントで Tips を書き換えられる点

**<Tips の見出し>（<章>）**
- 出典: [<タイトル>](<URL>)
- <出典が言っていること>
- 更新（修正する）: <Tips をどう変えるか>

## 2. 研究が Tips を裏付ける、または範囲を狭める点

**<Tips の見出し>（<章>）**
- 出典: [<論文名> (arXiv <番号>)](<URL>)
- <手法と結果。数値は本文で確認したものだけ>
- 更新（範囲を狭める）: <Tips をどう変えるか。示唆か確定かを明記>

## 3. 事例とツールで補強できる点

**<Tips の見出し>（<章>）**
- 出典: [<タイトル>](<URL>)
- <事例の要点>
- 更新（裏付ける）: <Tips をどう変えるか>

## 公式に記述が見つからず実測のまま残した項目

- <Tips の見出し>: <観測した挙動>
````

- [ ] **Step 3: プラグインのマニフェストと README を書く**

````json path=knowledge_sharing/.claude-plugin/plugin.json
{
  "name": "knowledge-sharing"
}
````

````json path=knowledge_sharing/.claude-plugin/marketplace.json
{
    "name": "knowledge-sharing",
    "description": "Claude Code の利用記録から、チームで共有できる知見を抽出・検証・公開するスキル群",
    "version": "0.1.0",
    "owner": {
        "name": "TOYOTA, Yoichi",
        "email": "y.toyota@xtone.co.jp"
    },
    "skills": [
        {
            "name": "session-tips-digest",
            "source": "./skills/session-tips-digest",
            "description": "過去のセッション記録から共有できる運用 Tips を抽出し、一次情報で裏付けを取って Markdown・Artifact・Notion に公開します。「過去の会話から Tips をまとめて」などの依頼で使用します。",
            "version": "0.1.0",
            "author": {
                "name": "TOYOTA, Yoichi"
            },
            "tags": ["knowledge-sharing", "tips", "session-log", "artifact", "notion", "research"]
        }
    ]
}
````

````markdown path=knowledge_sharing/README.md
# Knowledge Sharing

Claude Code の利用記録から、チームで共有できる知見を抽出・検証・公開するスキル群です。

## インストール

```bash
/plugin marketplace add xtone/ai_development_tools
/plugin install knowledge-sharing@xtone-ai-development-tools
```

## スキル一覧

| スキル | 説明 |
|--------|------|
| **session-tips-digest** | 過去のセッション記録から共有できる運用 Tips を抽出し、一次情報で裏付けを取って Markdown・Artifact・Notion に公開する |

## session-tips-digest

### 使い方

```
/knowledge-sharing:session-tips-digest
/knowledge-sharing:session-tips-digest --since 7d --projects my-app
/knowledge-sharing:session-tips-digest --artifact-url https://claude.ai/artifact/<id>
/knowledge-sharing:session-tips-digest --notion https://www.notion.so/<page> --no-research
```

| 引数 | 既定 | 意味 |
|---|---|---|
| `--since` | `30d` | 抽出期間。`7d` や `2026-09-01` も受ける |
| `--projects` | 全部 | 対象プロジェクト名の部分一致（カンマ区切り） |
| `--out` | `tips/` | 成果物ディレクトリ |
| `--artifact-url` | なし | 既存 Artifact を更新する |
| `--notion` | なし | 指定した Notion ページの配下に書き出す |
| `--no-research` | なし | 一次情報の調査を省略する |

### 流れ

1. `~/.claude/` の履歴・セッションログ・memory を集計する（設定値やトークンは出力しない）
2. 共有できる Tips を選び、案件名や固有値を伏せて書く
3. 機密スキャンで 0 件になるまで直す
4. 公式ドキュメントや論文で各 Tips を裏付ける、修正する、範囲を狭める
5. HTML に変換して Artifact として公開する（指定があれば Notion にも書き出す）

### 成果物

| パス | 内容 |
|---|---|
| `tips/claude-code-tips.md` | Tips 本体 |
| `tips/claude-code-tips-references.md` | 一次情報との対応表 |
| `tips/dist/index.html` | Artifact の元ファイル |
| `tips/.work/` | 作業ファイル。個人の記録を含むのでコミットしない |

### 必要環境

- Python 3.10 以上（標準ライブラリのみ）
- 任意: natural-japanese プラグイン（文章の lint）、Notion MCP（Notion への書き出し）

### evaluate-session との違い

| スキル | 対象 | 目的 |
|---|---|---|
| common-development の evaluate-session | セッション 1 本 | 無駄の有無を採点する |
| session-tips-digest | 期間内の全セッション | 共有できる知見を抜き出す |

### 開発

```bash
cd knowledge_sharing/skills/session-tips-digest/scripts
uv run --no-project --with pytest python -m pytest -q
```
````

- [ ] **Step 4: ルートのマーケットプレイスと README に登録する**

`.claude-plugin/marketplace.json` の `plugins` 配列で、最後の要素（`common-development`）の後ろに次を追加する。

```json
        {
            "name": "knowledge-sharing",
            "source": "./knowledge_sharing",
            "description": "Claude Code の利用記録から、チームで共有できる知見を抽出・検証・公開するスキル群（セッション記録からの Tips 抽出など）",
            "version": "0.1.0",
            "author": {
                "name": "TOYOTA, Yoichi"
            }
        }
```

`README.md` の「公開中のプラグイン」一覧で、`common-development` の行の直後に次を追加する。

```markdown
- **[knowledge-sharing](./knowledge_sharing/README.md)** - Claude Code の利用記録から、チームで共有できる知見を抽出・検証・公開するスキル群（セッション記録からの Tips 抽出など）
```

- [ ] **Step 5: マニフェストの妥当性を確認する**

Run:

```bash
python3 -I -c "import json;[json.load(open(p)) for p in ['.claude-plugin/marketplace.json','knowledge_sharing/.claude-plugin/plugin.json','knowledge_sharing/.claude-plugin/marketplace.json']];print('json ok')"
python3 -I -c "import json;d=json.load(open('.claude-plugin/marketplace.json'));print([p['name'] for p in d['plugins']][-1])"
claude plugin validate knowledge_sharing 2>&1 | tail -5 || true
```

Expected: `json ok`、`knowledge-sharing`。`claude plugin validate` が使える環境ではエラーが無いこと

- [ ] **Step 6: コミット**

```bash
git add knowledge_sharing .claude-plugin/marketplace.json README.md
git commit -m "feat(knowledge-sharing): session-tips-digest スキルとプラグイン登録を追加"
```

### Task 5: 受け入れ確認と PR

**Files:**
- 変更なし（受け入れ確認の結果に応じて Task 1〜4 のファイルを修正する）

**Interfaces:**
- Consumes: Task 1〜4 の成果物すべて
- Produces: PR

- [ ] **Step 1: 全テストを実行する**

Run: `cd knowledge_sharing/skills/session-tips-digest/scripts && PYTEST tests/`
Expected: PASS（25 passed）

- [ ] **Step 2: 実データで Phase 1〜4 を通す**

作業ディレクトリ `/private/tmp/session-tips-digest-acceptance` で、SKILL.md の手順に従い `--since 7d` で実行する。Phase 3 は Tips 2〜3 件に絞って一次情報を確認する。

確認すること:

- `extract_sessions.py` が 0 で終わり、`sessions.json` に設定値やトークンが含まれていない（`scan_sensitive.py <out>/.work/sessions.json` で `bearer` `token` `hex_token` が 0 件）
- 本体・参照リスト・HTML の機密スキャンが 0 件で終わる
- Artifact が公開でき、URL が返る

- [ ] **Step 3: 問題があれば修正して Step 1 から繰り返す**

- [ ] **Step 4: push して PR を作る**

```bash
git push -u origin feat/knowledge-sharing-plugin
gh pr create --base main --head feat/knowledge-sharing-plugin --title "feat: knowledge-sharing プラグインと session-tips-digest スキルを追加" --body-file <PR 本文>
```

PR 本文は UX ライティングと Progressive Disclosure に従い、変更点・使い方・受け入れ確認の結果を書く。マージはしない。

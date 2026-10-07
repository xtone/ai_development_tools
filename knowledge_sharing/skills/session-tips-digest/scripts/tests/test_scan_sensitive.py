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

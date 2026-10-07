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


def test_cli_masks_secret_values_in_output(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("key HnRXa1s7-80Y6Hrv8HhTcG_sqvqRy0nGUlqhG9pqeL8\n", encoding="utf-8")
    r = _run(f)
    assert r.returncode == 1
    assert "HnRXa1s7-80Y6Hrv8HhTcG_sqvqRy0nGUlqhG9pqeL8" not in r.stdout
    assert "HnRX…(43 chars)" in r.stdout
    r = _run(f, "--json")
    assert "sqvqRy0nGUlqhG9pqeL8" not in r.stdout


def test_redact_hides_secret_assignments():
    out = scan.redact("PGPASSWORD=hunter2 MY_API_KEY='abc' DEBUG=1 psql")
    assert "hunter2" not in out
    assert "abc" not in out
    assert out == "PGPASSWORD=<redacted> MY_API_KEY=<redacted> DEBUG=1 psql"


def test_detects_and_redacts_well_known_secret_formats():
    samples = [
        "AKIAIOSFODNN7EXAMPLE",
        "ghp_" + "a1B2" * 9,
        "github_pat_11ABCDEFG0123456789_abcdefghij",
        "xoxb-1234567890-abcdefghij",
        "sk-ant-api03-abcdefghij0123456789",
        "AIza" + "SyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "https://deploy:s3cretpass@git.example-corp.co.jp/repo.git",
    ]
    for s in samples:
        assert "known_secret" in kinds(f"x {s} y"), s
        assert s not in scan.redact(f"x {s} y"), s


def test_file_paths_are_not_tokens():
    text = "app/Http/Controllers/Api/V2/UserController.php と src/components/Header/Header2026Banner.tsx"
    assert scan.scan_text(text) == []
    assert scan.redact(text) == text


def test_ids_inside_arn_and_resource_paths_are_detected():
    assert "numeric_id" in kinds("arn:aws:iam::123456789012:role/x")
    assert "numeric_id" in kinds("organizations/123456789012")


def test_redact_and_detect_common_credential_forms():
    samples = [
        "password: hunter2",
        '{"password": "hunter2"}',
        "mysql -phunter2 db",
        "psql --password hunter2",
        "curl -u admin:Passw0rd! https://x",
        "Authorization: Basic YWRtaW46aHVudGVyMg==",
        "bearer abcdefghijklmnopQRST1234",
        "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    ]
    for s in samples:
        out = scan.redact(s)
        assert "hunter2" not in out and "Passw0rd" not in out and "YWRtaW46" not in out, s
        assert "abcdefghijklmnop" not in out and "wJalrXUtnFEMI" not in out, s
        assert scan.scan_text(s), s


def test_placeholders_are_not_credentials():
    text = "\n".join(
        ["--password <PW>", "API_TOKEN=${{ secrets.API_TOKEN }}", "GITHUB_TOKEN: $GITHUB_TOKEN", "mkdir -p dir", "pytest -p no:cacheprovider"]
    )
    assert scan.scan_text(text) == []


def test_slash_containing_secrets_are_still_detected():
    for s in [
        "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "Zm9vYmFy/Qk9P4kL+Xc2vT9mNq/8RtYw3HsLp0uVaZ1bE",
    ]:
        assert "token" in kinds(f"x {s} y"), s
        assert s not in scan.redact(f"x {s} y"), s


def test_dollar_and_numeric_passwords_are_not_treated_as_placeholders():
    for s in ["password=$ecretP@ss", "password=12345678", "--password $ecretP@ss", "curl -u admin:$ecret1 x"]:
        assert "credential" in kinds(s), s
        out = scan.redact(s)
        assert "ecret" not in out and "12345678" not in out, s


def test_a_word_segment_does_not_hide_a_random_secret():
    for s in ["Zm9vYmFy/abc/Qk9P4kL+Xc2vT9mNqRtYw3HsLp0uVaZ", "src/xK9vQ2mLp7RtYw3HsLp0uVaZb4N8cE1"]:
        assert "token" in kinds(f"x {s} y"), s
        assert s not in scan.redact(f"x {s} y"), s



def _finishes_within(expr, seconds=2.0):
    code = f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import scan_sensitive as scan; {expr}"
    try:
        subprocess.run([sys.executable, "-I", "-c", code], timeout=seconds, check=True)
    except subprocess.TimeoutExpired:
        return False
    return True


def test_adversarial_inputs_finish_quickly():
    assert _finishes_within("scan._is_path_like('src/' + 'abc' * 40 + '+')")
    assert _finishes_within("scan._is_path_like('src/' + 'AB' * 40 + '+')")
    assert _finishes_within("scan.scan_text('x' * 200000 + ' PASSWORD')")
    assert _finishes_within("scan.redact('x' * 200000 + ' PASSWORD')")

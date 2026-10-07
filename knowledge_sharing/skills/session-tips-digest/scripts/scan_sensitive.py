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

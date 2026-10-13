#!/usr/bin/env python3
"""Summarize Claude Code records under ~/.claude into one JSON for tips extraction.

The output holds prompts (with session ids), tool usage counts, sample commands,
commit and pull request titles, memory notes, harness structure (names only, never values) and a vocabulary of identifying
names that scan_sensitive.py uses. Secrets in prompts and commands are redacted.

Usage:
  extract_sessions.py --out tips/.work/sessions.json [--since 30d|YYYY-MM-DD]
                      [--until YYYY-MM-DD] [--tz local|+09:00]
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
TITLE_MAX = 200
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

HOST_RE = re.compile(
    r"(?<![A-Za-z0-9_.\-])((?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.){1,8}"
    r"(?:com|net|org|io|dev|app|jp|ai|cloud|run))(?![A-Za-z0-9\-])",
    re.IGNORECASE,
)
REPO_RE = re.compile(
    r"(?<![A-Za-z0-9.\-])github\.com[:/]([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+?)(?:\.git)?(?=$|[\s/'\"#)?,])"
)
REPO_FLAG_RE = re.compile(r"(?:\s-R|--repo)[\s=]+([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)")
GH_RE = re.compile(r"^\s*(gh\s+[a-z][a-z\-]*\s+[a-z][a-z\-]*)")
FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# A command that starts a shell statement (not one quoted inside another command).
COMMIT_START_RE = re.compile(r"(?:^|&&|\|\||;|\n)\s*git\s+(?:-C\s+\S+\s+)?commit\b")
PR_START_RE = re.compile(r"(?:^|&&|\|\||;|\n)\s*gh\s+pr\s+create\b")
COMMIT_MSG_FLAG_RE = re.compile(r"(?<![\w-])(?:-[a-zA-Z]*m|--message)(?:\s+|=)")
PR_TITLE_FLAG_RE = re.compile(r"(?<![\w-])(?:-t|--title)(?:\s+|=)")
HEREDOC_RE = re.compile(r"\$\(cat\s+<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)(?:\n\s*\1\b|\Z)", re.DOTALL)


def parse_now(value: str | None) -> dt.datetime:
    if not value:
        return dt.datetime.now(dt.timezone.utc)
    d = dt.datetime.fromisoformat(value)
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def parse_tz(value: str) -> dt.tzinfo:
    """'local' for this machine's time zone, or a fixed offset such as +09:00."""
    if value == "local":
        return dt.datetime.now().astimezone().tzinfo or dt.timezone.utc
    m = re.fullmatch(r"([+-])(\d{2}):?(\d{2})", value.strip())
    if not m:
        raise ValueError(f"--tz must be local or an offset like +09:00: {value}")
    minutes = int(m.group(2)) * 60 + int(m.group(3))
    return dt.timezone(dt.timedelta(minutes=-minutes if m.group(1) == "-" else minutes))


def parse_since(value: str, now: dt.datetime, tz: dt.tzinfo = dt.timezone.utc) -> dt.datetime:
    """A date means the start of that day in tz."""
    value = value.strip()
    m = re.fullmatch(r"(\d+)d", value)
    if m:
        return now - dt.timedelta(days=int(m.group(1)))
    try:
        day = dt.date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"--since must look like 30d or YYYY-MM-DD: {value}") from None
    return dt.datetime.combine(day, dt.time.min, tzinfo=tz)


def parse_until(value: str | None, tz: dt.tzinfo = dt.timezone.utc) -> dt.datetime | None:
    """The day is included: the result is the start of the next day in tz (exclusive)."""
    if not value:
        return None
    try:
        day = dt.date.fromisoformat(value.strip())
    except ValueError:
        raise ValueError(f"--until must look like YYYY-MM-DD: {value}") from None
    return dt.datetime.combine(day + dt.timedelta(days=1), dt.time.min, tzinfo=tz)


def in_range(ts: dt.datetime, cutoff: dt.datetime, until: dt.datetime | None) -> bool:
    return ts >= cutoff and (until is None or ts < until)


def parse_ts(value) -> dt.datetime | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.fromtimestamp(value / 1000, dt.timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
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


def encode_dir(path: str) -> str:
    """Claude Code names project directories by replacing non-alphanumerics with '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def fallback_name(dirname: str, known: dict[str, str]) -> str:
    """Readable project name for an encoded directory name without a recorded cwd."""
    if dirname in known:
        return known[dirname]
    return re.sub(r"^-(?:Users|home)-[^-]+-", "", dirname) or dirname


def dir_project(dirpath: Path, cache: dict[Path, str], known: dict[str, str]) -> str:
    """Project of a ~/.claude/projects/<dir>: the directory the sessions were started in.

    Per-line cwd is not used because Claude may cd into subdirectories mid-session.
    """
    if dirpath not in cache:
        base = dirpath.name.split("--claude-worktrees-")[0]
        if base in known:
            cache[dirpath] = known[base]
            return cache[dirpath]
        name = fallback_name(base, known)
        for f in sorted(dirpath.glob("*.jsonl")):
            found = next((d["cwd"] for d in read_jsonl(f, '"cwd"') if d.get("cwd")), None)
            if found:
                name = project_name(found)
                break
        cache[dirpath] = name
    return cache[dirpath]


def _flag_value(rest: str, flag_re: re.Pattern[str]) -> str | None:
    """First line of the value given to a flag: quoted, heredoc ($(cat <<'EOF' ...)) or bare."""
    m = flag_re.search(rest)
    if not m:
        return None
    value = rest[m.end():]
    if value[:1] in ("\"", "'") and value[1:].startswith("$(cat"):
        value = value[1:]
    if value.startswith("$(cat"):
        h = HEREDOC_RE.match(value)
        text = h.group(2) if h else ""
    elif value[:1] == '"':
        q = re.match(r'"((?:[^"\\]|\\.)*)"', value)
        text = q.group(1).replace('\\"', '"') if q else value[1:]
    elif value[:1] == "'":
        q = re.match(r"'([^']*)'", value)
        text = q.group(1) if q else value[1:]
    else:
        text = value.split(None, 1)[0] if value.split() else ""
    for line in text.splitlines():
        line = line.strip()
        if line:
            # An escaped quote or a command substitution means the flag sat inside
            # another program's text (a test fixture, a heredoc), not a real commit.
            return None if line.startswith(("\\", "$(")) else line
    return None


def titles_in(command: str, start_re: re.Pattern[str], flag_re: re.Pattern[str]) -> list[str]:
    """Titles of every commit (or PR) started in a shell command."""
    out = []
    for m in start_re.finditer(command):
        title = _flag_value(command[m.end():], flag_re)
        if title:
            out.append(redact(title)[:TITLE_MAX])
    return out


def collect_prompts(claude_dir, cutoff, filters, texts, names, known, until=None) -> list[dict]:
    out = []
    for d in read_jsonl(claude_dir / "history.jsonl"):
        if isinstance(d.get("project"), str) and d["project"]:
            known.setdefault(encode_dir(d["project"]), project_name(d["project"]))
        ts = parse_ts(d.get("timestamp"))
        if ts is None or not in_range(ts, cutoff, until):
            continue
        proj = project_name(d.get("project", ""))
        if not wanted(proj, filters):
            continue
        text = str(d.get("display", ""))
        texts.append(text)
        names.add(proj)
        session = d.get("sessionId")
        out.append(
            {
                "time": ts.isoformat(timespec="minutes"),
                "project": proj,
                "session_id": session if isinstance(session, str) and session else None,
                "text": redact(text)[:PROMPT_MAX],
            }
        )
    return out


def _top(counter: Counter) -> list[list]:
    return [[k, v] for k, v in counter.most_common()]


def collect_usage(claude_dir, cutoff, filters, patterns, texts, names, known, cache, until=None):
    tools, skills, agents, mcp, gh = Counter(), Counter(), Counter(), Counter(), Counter()
    samples: list[dict] = []
    outcomes: dict[str, list[dict]] = {"commits": [], "prs": []}
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
            if ts is not None and not in_range(ts, cutoff, until):
                continue
            proj = dir_project(f.parent, cache, known)
            if not wanted(proj, filters):
                continue
            message = d.get("message")
            content = message.get("content") if isinstance(message, dict) else None
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
                    session = d.get("sessionId") if isinstance(d.get("sessionId"), str) else None
                    for key, start_re, flag_re in (
                        ("commits", COMMIT_START_RE, COMMIT_MSG_FLAG_RE),
                        ("prs", PR_START_RE, PR_TITLE_FLAG_RE),
                    ):
                        for title in titles_in(cmd, start_re, flag_re):
                            outcomes[key].append(
                                {
                                    "time": ts.isoformat(timespec="minutes") if ts else None,
                                    "project": proj,
                                    "session_id": session,
                                    "title": title,
                                }
                            )
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
    for items in outcomes.values():
        items.sort(key=lambda o: o["time"] or "")
    return usage, samples, outcomes


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


def collect_memories(claude_dir, filters, cache, texts, known) -> list[dict]:
    out = []
    for f in sorted((claude_dir / "projects").glob("*/memory/*.md")):
        if f.name == "MEMORY.md":
            continue
        proj = dir_project(f.parent.parent, cache, known)
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
    repos: set[str] = set()
    for text in texts:
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
        "users": keep(users),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize Claude Code records for tips extraction.")
    parser.add_argument("--out", required=True, help="output JSON path")
    parser.add_argument("--since", default="30d", help="30d style or YYYY-MM-DD (default 30d)")
    parser.add_argument("--until", default=None, help="last day to include, YYYY-MM-DD (default: no end)")
    parser.add_argument("--tz", default="local", help="time zone for dates: local or an offset like +09:00")
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
        tz = parse_tz(args.tz)
        cutoff = parse_since(args.since, now, tz)
        until = parse_until(args.until, tz)
        if until is not None and until <= cutoff:
            raise ValueError(f"--until must not be before --since: {args.until}")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    filters = [f.strip().lower() for f in args.projects.split(",") if f.strip()]
    patterns = [p for p in args.patterns.split(",") if p.strip()]

    texts: list[str] = []
    names: set[str] = set()
    cache: dict[Path, str] = {}
    known: dict[str, str] = {}
    prompts = collect_prompts(claude_dir, cutoff, filters, texts, names, known, until)
    usage, samples, outcomes = collect_usage(claude_dir, cutoff, filters, patterns, texts, names, known, cache, until)
    memories = collect_memories(claude_dir, filters, cache, texts, known)
    report = {
        "generated_at": now.isoformat(timespec="seconds"),
        "since": cutoff.isoformat(timespec="seconds"),
        "until": until.isoformat(timespec="seconds") if until else None,
        "projects_filter": filters,
        "counts": {
            "prompts": len(prompts),
            "bash_samples": len(samples),
            "commits": len(outcomes["commits"]),
            "prs": len(outcomes["prs"]),
            "memories": len(memories),
        },
        "prompts": prompts,
        "tool_usage": usage,
        "bash_samples": samples,
        "commits": outcomes["commits"],
        "prs": outcomes["prs"],
        "memories": memories,
        "harness": collect_harness(claude_dir),
        "vocabulary": build_vocabulary(texts, names, claude_dir),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    calls = sum(count for _, count in usage["tools"])
    print(
        f"wrote {out}: {len(prompts)} prompts, {calls} tool calls, "
        f"{len(outcomes['commits'])} commits, {len(outcomes['prs'])} PRs, {len(memories)} memories"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Notion MCP 接続の一覧・名前チェック・参照箇所の検索・接続先の記録を行う補助スクリプト。

Claude Code の設定（~/.claude.json とプロジェクトの .mcp.json）を読むだけで、書き換えはしない。
登録・削除は `claude mcp add/remove` で行う（設定の書式を Claude Code 側に任せるため）。
認証情報（headers など）は表示しない。名前・スコープ・URL だけを扱う。

必要環境: Python 3.7 以上（add_subparsers(required=True) と、dict の挿入順の保持を前提にしている）

使い方:
  notion_mcp.py list        [--project DIR]
  notion_mcp.py check-name  NAME [--project DIR]
  notion_mcp.py find-refs   NAME
  notion_mcp.py record      NAME WORKSPACE_NAME WORKSPACE_ID
  notion_mcp.py forget      NAME

環境変数:
  CLAUDE_CONFIG_PATH    ~/.claude.json の代わりに読むファイル（テスト用）
  NOTION_REGISTRY_PATH  接続先の記録ファイル（既定: ~/.claude/notion-connections.json）
"""
import argparse
import datetime
import json
import os
import re
import sys
import tempfile

NOTION_HOST = "mcp.notion.com"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
# ツール名 mcp__<登録名>__<ツール名> が 64 文字に収まる登録名の長さ。
# Notion MCP で最長のツール名 notion-show-advanced-analysis-next-steps（40 文字）を基準にする。
LONGEST_TOOL = "notion-show-advanced-analysis-next-steps"
RECOMMENDED_MAX_LEN = 64 - len("mcp__") - len("__") - len(LONGEST_TOOL)


def config_path():
    return os.environ.get("CLAUDE_CONFIG_PATH") or os.path.expanduser("~/.claude.json")


def registry_path():
    return os.environ.get("NOTION_REGISTRY_PATH") or os.path.expanduser("~/.claude/notion-connections.json")


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        # 壊れたファイルを既定値扱いにすると、record で上書きして記録を失うので止める
        sys.exit(f"エラー: {path} を JSON として読めません（{e}）。"
                 "Claude Code が書き込み中なら少し待って再実行し、直らなければファイルを確認してください。")


def save_json(path, data):
    """一時ファイルに書いてから置き換える（途中で止まっても元のファイルが壊れないように）。"""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".notion-connections-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def is_notion(server):
    return NOTION_HOST in str(server.get("url", ""))


def project_configs(cfg, project):
    """~/.claude.json の projects を、指定プロジェクトのもの（same）とそれ以外（others）に分ける。

    キーはシンボリックリンク経由のパスで保存されていることがあるので、realpath で比べる。
    """
    same, others = [], []
    for p, pc in cfg.get("projects", {}).items():
        (same if os.path.realpath(p) == project else others).append((p, pc))
    return same, others


def collect(project):
    """全スコープの MCP 登録を (name, scope, url, is_notion, disabled_here) で返す。"""
    cfg = load_json(config_path(), {})
    project = os.path.realpath(project)
    same, _ = project_configs(cfg, project)
    disabled = {n for _, pc in same for n in pc.get("disabledMcpServers", [])}
    rows = []
    for name, s in cfg.get("mcpServers", {}).items():
        rows.append((name, "user", s.get("url", ""), is_notion(s), name in disabled))
    for _, pc in same:
        for name, s in pc.get("mcpServers", {}).items():
            rows.append((name, "local", s.get("url", ""), is_notion(s), name in disabled))
    mcp_json = load_json(os.path.join(project, ".mcp.json"), {})
    for name, s in mcp_json.get("mcpServers", {}).items():
        rows.append((name, "project", s.get("url", ""), is_notion(s), name in disabled))
    return rows, cfg, project


def other_project_notion(cfg, project):
    """他プロジェクトの local に登録された Notion 接続を (プロジェクト, 名前, 無効化) で返す。"""
    _, others = project_configs(cfg, project)
    result = []
    for p, pc in others:
        for name, s in pc.get("mcpServers", {}).items():
            if is_notion(s):
                result.append((p, name, name in pc.get("disabledMcpServers", [])))
    return result


def cmd_list(args):
    rows, cfg, project = collect(args.project)
    registry = load_json(registry_path(), {})
    notion_rows = [r for r in rows if r[3]]
    print(f"プロジェクト: {project}")
    if not notion_rows:
        print("このプロジェクトから見える Notion MCP 接続はありません。")
    else:
        print("名前\tスコープ\t無効化\t記録済みワークスペース")
        for name, scope, url, _, disabled in notion_rows:
            rec = registry.get(name)
            ws = f"{rec['workspace_name']}（{rec['verified_at'][:10]} 確認）" if rec else "未確認"
            print(f"{name}\t{scope}\t{'はい' if disabled else '-'}\t{ws}")
    # 他プロジェクトの local 登録も知らせる（移行や重複、削除時の認証への影響の判断材料になる）
    others = [f"  {p}: {name}{'（無効化）' if disabled else ''}"
              for p, name, disabled in other_project_notion(cfg, project)]
    if others:
        print("\n他プロジェクトの local 登録:")
        print("\n".join(others))


def cmd_check_name(args):
    name = args.name
    problems = []
    if not NAME_RE.match(name):
        problems.append("英小文字・数字・ハイフンのみ、先頭は英数字、63文字以内にしてください")
    rows, cfg, project = collect(args.project)
    for n, scope, url, notion, _ in rows:
        if n == name:
            kind = "Notion 接続" if notion else f"別の MCP（{url or 'stdio'}）"
            problems.append(f"{scope} スコープに同名の {kind} が既にあります")
    # 認証は「登録名＋URL」ごとに共有されるので、他プロジェクトの同名登録の認証を引き継いでしまう
    for p, n, _ in other_project_notion(cfg, project):
        if n == name:
            problems.append(f"他プロジェクト（{p}）の local に同名の Notion 接続があります。"
                            "認証が共有され、そちらのワークスペースに繋がってしまいます")
    if problems:
        print("NG")
        for p in problems:
            print(f"- {p}")
        sys.exit(1)
    print("OK")
    if len(name) > RECOMMENDED_MAX_LEN:
        print(f"注意: {RECOMMENDED_MAX_LEN} 文字を超えると、ツール名（mcp__{name}__{LONGEST_TOOL} など）が"
              "64 文字を超え、一部のツールが使えない可能性があります。短い名前を勧めます")


def cmd_find_refs(args):
    """許可ルールなど、ツール名 mcp__<name> / mcp__<name>__… を参照している設定を探す。

    行全体を表示すると同じ行にある秘密情報（1 行に詰めた JSON の env など）まで出るので、
    一致した参照だけを表示する。
    """
    # mcp__<name> の直後が __<ツール名> か、名前に使えない文字・行末のときだけ一致させる
    # （mcp__notion で mcp__notion-acme を拾わないように）
    pattern = re.compile(rf"mcp__{re.escape(args.name)}(?:__[^\s\"',\]\)]*)?(?![A-Za-z0-9_-])")
    cfg = load_json(config_path(), {})
    candidates = [os.path.expanduser(p) for p in (
        "~/.claude/settings.json", "~/.claude/settings.local.json")]
    for p in cfg.get("projects", {}):
        for rel in (".claude/settings.json", ".claude/settings.local.json"):
            candidates.append(os.path.join(p, rel))
    hits = []
    for path in sorted(set(candidates)):
        try:
            with open(path) as f:
                for i, line in enumerate(f, 1):
                    refs = list(dict.fromkeys(pattern.findall(line)))
                    if refs:
                        hits.append(f"{path}:{i}: {', '.join(refs)}")
        except (FileNotFoundError, IsADirectoryError, PermissionError, UnicodeDecodeError):
            continue
    for p, pc in cfg.get("projects", {}).items():
        if args.name in pc.get("disabledMcpServers", []):
            hits.append(f"~/.claude.json: {p} の disabledMcpServers に {args.name}")
    print("\n".join(hits) if hits else "参照は見つかりませんでした。")


def cmd_record(args):
    reg = load_json(registry_path(), {})
    reg[args.name] = {
        "workspace_name": args.workspace_name,
        "workspace_id": args.workspace_id,
        "verified_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    save_json(registry_path(), reg)
    print(f"記録しました: {args.name} → {args.workspace_name}")


def cmd_forget(args):
    reg = load_json(registry_path(), {})
    if reg.pop(args.name, None) is None:
        print(f"{args.name} の記録はありません。")
        return
    save_json(registry_path(), reg)
    print(f"記録を削除しました: {args.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--project", default=os.getcwd()); p.set_defaults(fn=cmd_list)
    p = sub.add_parser("check-name"); p.add_argument("name"); p.add_argument("--project", default=os.getcwd()); p.set_defaults(fn=cmd_check_name)
    p = sub.add_parser("find-refs"); p.add_argument("name"); p.set_defaults(fn=cmd_find_refs)
    p = sub.add_parser("record"); p.add_argument("name"); p.add_argument("workspace_name"); p.add_argument("workspace_id"); p.set_defaults(fn=cmd_record)
    p = sub.add_parser("forget"); p.add_argument("name"); p.set_defaults(fn=cmd_forget)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()

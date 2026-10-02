#!/usr/bin/env python3
"""notion_mcp.py のテスト。

実行: python3 -m unittest discover -s common_development/skills/notion-connections/scripts

HOME・CLAUDE_CONFIG_PATH・NOTION_REGISTRY_PATH を一時ディレクトリに向けるので、
実際の ~/.claude.json や記録ファイルには触れない。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notion_mcp.py")
NOTION_URL = "https://mcp.notion.com/mcp"


class NotionMcpTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # macOS の /var → /private/var のように、スクリプト側の realpath と揃える
        self.root = os.path.realpath(self._tmp.name)
        self.home = os.path.join(self.root, "home")
        self.project = os.path.join(self.root, "proj")
        self.other = os.path.join(self.root, "other")
        for d in (self.home, self.project, self.other):
            os.makedirs(d)
        self.config = os.path.join(self.root, "claude.json")
        self.registry = os.path.join(self.root, "registry.json")
        self.write_config({})

    def tearDown(self):
        self._tmp.cleanup()

    def write_config(self, cfg):
        with open(self.config, "w") as f:
            json.dump(cfg, f)

    def write_json(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    def run_script(self, *args):
        env = dict(os.environ, HOME=self.home,
                   CLAUDE_CONFIG_PATH=self.config, NOTION_REGISTRY_PATH=self.registry)
        return subprocess.run([sys.executable, SCRIPT, *args],
                              capture_output=True, text=True, env=env)

    # --- list ---

    def test_list_shows_notion_servers_in_all_scopes(self):
        self.write_config({
            "mcpServers": {
                "notion-acme": {"type": "http", "url": NOTION_URL},
                "github": {"type": "http", "url": "https://api.githubcopilot.com/mcp/"},
            },
            "projects": {
                self.project: {
                    "mcpServers": {"notion-local": {"type": "http", "url": NOTION_URL}},
                    "disabledMcpServers": ["notion-local"],
                },
                self.other: {"mcpServers": {"notion": {"type": "http", "url": NOTION_URL}}},
            },
        })
        self.write_json(os.path.join(self.project, ".mcp.json"),
                        {"mcpServers": {"notion-shared": {"type": "http", "url": NOTION_URL}}})

        r = self.run_script("list", "--project", self.project)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("notion-acme\tuser\t-\t未確認", r.stdout)
        self.assertIn("notion-local\tlocal\tはい\t未確認", r.stdout)
        self.assertIn("notion-shared\tproject\t-\t未確認", r.stdout)
        self.assertNotIn("github", r.stdout)
        # 他プロジェクトの local 登録も知らせる
        self.assertIn(f"{self.other}: notion", r.stdout)

    def test_list_matches_project_key_saved_via_symlink(self):
        link = os.path.join(self.root, "proj-link")
        os.symlink(self.project, link)
        self.write_config({"projects": {
            link: {"mcpServers": {"notion-local": {"type": "http", "url": NOTION_URL}}}}})

        r = self.run_script("list", "--project", self.project)

        self.assertIn("notion-local\tlocal", r.stdout)
        self.assertNotIn("他プロジェクトの local 登録", r.stdout)

    def test_list_without_notion_servers(self):
        r = self.run_script("list", "--project", self.project)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Notion MCP 接続はありません", r.stdout)

    def test_list_does_not_print_headers(self):
        self.write_config({"mcpServers": {"notion-acme": {
            "type": "http", "url": NOTION_URL, "headers": {"Authorization": "Bearer SECRET"}}}})

        r = self.run_script("list", "--project", self.project)

        self.assertNotIn("SECRET", r.stdout)

    # --- record / forget ---

    def test_record_is_shown_in_list_and_forget_removes_it(self):
        self.write_config({"mcpServers": {"notion-acme": {"type": "http", "url": NOTION_URL}}})

        r = self.run_script("record", "notion-acme", "Acme Corp", "ws-123")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(self.registry) as f:
            saved = json.load(f)["notion-acme"]
        self.assertEqual(saved["workspace_name"], "Acme Corp")
        self.assertEqual(saved["workspace_id"], "ws-123")
        self.assertIn("Acme Corp（", self.run_script("list", "--project", self.project).stdout)

        r = self.run_script("forget", "notion-acme")
        self.assertIn("記録を削除しました", r.stdout)
        with open(self.registry) as f:
            self.assertEqual(json.load(f), {})

    def test_broken_registry_stops_without_overwriting(self):
        with open(self.registry, "w") as f:
            f.write("")

        r = self.run_script("record", "notion-acme", "Acme Corp", "ws-123")

        self.assertNotEqual(r.returncode, 0)
        self.assertIn("JSON として読めません", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        with open(self.registry) as f:
            self.assertEqual(f.read(), "")

    def test_broken_config_stops_with_message(self):
        with open(self.config, "w") as f:
            f.write("{")

        r = self.run_script("list", "--project", self.project)

        self.assertNotEqual(r.returncode, 0)
        self.assertIn("JSON として読めません", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_record_leaves_no_temp_files(self):
        self.run_script("record", "notion-acme", "Acme Corp", "ws-123")

        leftovers = [n for n in os.listdir(self.root) if n.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_forget_unknown_name(self):
        r = self.run_script("forget", "notion-unknown")

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("記録はありません", r.stdout)

    # --- check-name ---

    def test_check_name_ok(self):
        r = self.run_script("check-name", "notion-acme", "--project", self.project)

        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "OK")

    def test_check_name_rejects_invalid_format(self):
        for name in ("Notion_Acme", "_notion", "notion acme", "a" * 64):
            with self.subTest(name=name):
                r = self.run_script("check-name", name, "--project", self.project)
                self.assertEqual(r.returncode, 1)
                self.assertIn("英小文字・数字・ハイフンのみ", r.stdout)

    def test_check_name_rejects_duplicate(self):
        self.write_config({
            "mcpServers": {"github": {"type": "http", "url": "https://api.githubcopilot.com/mcp/"}},
            "projects": {self.project: {"mcpServers": {"notion-acme": {"type": "http", "url": NOTION_URL}}}},
        })

        r = self.run_script("check-name", "notion-acme", "--project", self.project)
        self.assertEqual(r.returncode, 1)
        self.assertIn("local スコープに同名の Notion 接続", r.stdout)

        r = self.run_script("check-name", "github", "--project", self.project)
        self.assertEqual(r.returncode, 1)
        self.assertIn("user スコープに同名の 別の MCP", r.stdout)

    def test_check_name_rejects_same_name_in_other_project(self):
        # 認証は「登録名＋URL」で共有されるので、他プロジェクトの同名 Notion 登録も NG にする
        self.write_config({"projects": {
            self.other: {"mcpServers": {"notion-acme": {"type": "http", "url": NOTION_URL}}}}})

        r = self.run_script("check-name", "notion-acme", "--project", self.project)

        self.assertEqual(r.returncode, 1)
        self.assertIn(f"他プロジェクト（{self.other}）の local に同名の Notion 接続", r.stdout)

    def test_check_name_ignores_other_project_non_notion_server(self):
        self.write_config({"projects": {
            self.other: {"mcpServers": {"notion-acme": {"type": "stdio", "command": "x"}}}}})

        r = self.run_script("check-name", "notion-acme", "--project", self.project)

        self.assertEqual(r.returncode, 0)

    def test_check_name_warns_long_name(self):
        r = self.run_script("check-name", "notion-example-corp", "--project", self.project)  # 19 文字

        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.startswith("OK"))
        self.assertIn("注意: 17 文字を超えると", r.stdout)

        r = self.run_script("check-name", "notion-example-co", "--project", self.project)  # 17 文字
        self.assertNotIn("注意", r.stdout)

    # --- find-refs ---

    def test_find_refs_finds_permission_rules_and_disabled(self):
        self.write_config({"projects": {
            self.project: {"disabledMcpServers": ["notion-acme"]},
            self.other: {},
        }})
        self.write_json(os.path.join(self.home, ".claude", "settings.json"),
                        {"permissions": {"allow": ["mcp__notion-acme__notion-fetch"]}})
        self.write_json(os.path.join(self.other, ".claude", "settings.local.json"),
                        {"permissions": {"allow": ["mcp__notion-acme__notion-search"]}})

        r = self.run_script("find-refs", "notion-acme")

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("mcp__notion-acme__notion-fetch", r.stdout)
        self.assertIn("mcp__notion-acme__notion-search", r.stdout)
        self.assertIn(f"{self.project} の disabledMcpServers に notion-acme", r.stdout)

    def test_find_refs_finds_server_level_rule(self):
        self.write_json(os.path.join(self.home, ".claude", "settings.json"),
                        {"permissions": {"allow": ["mcp__notion-acme", "mcp__notion-acme__*"]}})

        r = self.run_script("find-refs", "notion-acme")

        self.assertIn("mcp__notion-acme, mcp__notion-acme__*", r.stdout)

    def test_find_refs_shows_only_matched_refs(self):
        # 1 行に詰めた JSON でも、同じ行の秘密情報は表示しない
        path = os.path.join(self.home, ".claude", "settings.json")
        os.makedirs(os.path.dirname(path))
        with open(path, "w") as f:
            f.write('{"env":{"API_KEY":"sk-SECRET"},"permissions":{"allow":["mcp__notion-acme__notion-fetch"]}}')

        r = self.run_script("find-refs", "notion-acme")

        self.assertIn("mcp__notion-acme__notion-fetch", r.stdout)
        self.assertNotIn("SECRET", r.stdout)

    def test_find_refs_does_not_match_other_names(self):
        self.write_json(os.path.join(self.home, ".claude", "settings.json"),
                        {"permissions": {"allow": ["mcp__notion-acme-old__notion-fetch"]}})

        r = self.run_script("find-refs", "notion-acme")

        self.assertIn("参照は見つかりませんでした", r.stdout)


if __name__ == "__main__":
    unittest.main()

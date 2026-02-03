# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-03

### Changed

- **Breaking Change**: データ保存形式をJSONからJSONL（JSON Lines）に移行
  - 保存先を `~/.claude/hooks/state/` から `~/.claude/hooks/logs/` に変更
  - ファイル形式を1行1イベントのJSONL形式に変更
  - 追記操作が効率的になり、パフォーマンスが向上

### Added

- `bin/migrate-to-jsonl.js` マイグレーションスクリプトを追加
  - 既存のJSONデータをJSONL形式に変換
  - `--dry-run` オプションで事前確認が可能

### File Changes

| ファイル | 変更内容 |
|---------|---------|
| `hooks/skill_usage_counter.js` | JSONL形式で `logs/skill_usage.jsonl` に追記 |
| `hooks/slash_command_counter.js` | JSONL形式で `logs/slash_command.jsonl` に追記 |
| `hooks/user_prompt_command_counter.js` | JSONL形式で `logs/slash_command.jsonl` に追記 |
| `hooks/skill_usage_sender.js` | JSONL形式から読み込み対応 |
| `bin/skill-stats.js` | JSONL形式から読み込み対応 |
| `bin/migrate-to-jsonl.js` | 新規作成 |

### Migration

既存のデータを移行するには以下のコマンドを実行:

```bash
# ドライラン（確認のみ）
node ~/.claude/plugins/skill-usage-tracker/bin/migrate-to-jsonl.js --dry-run

# 実際の移行
node ~/.claude/plugins/skill-usage-tracker/bin/migrate-to-jsonl.js
```

## [0.1.1] - 2026-01-26

### Changed

- 全てのhooksに`async: true`を追加し、バックグラウンド実行を有効化
  - Claude Codeの実行をブロックしないように改善
  - ロギングや統計収集のパフォーマンスが向上

### Technical Details

- 対象hooks:
  - `user_prompt_command_counter.js` (UserPromptSubmit)
  - `skill_usage_counter.js` (PostToolUse - Skill)
  - `slash_command_counter.js` (PostToolUse - SlashCommand)
  - `skill_usage_sender.js` (Stop)

## [0.1.0] - 2025-12-03

### Added

- 初回リリース
- Skillツール使用時の自動カウント機能
- SlashCommandツール使用時の自動カウント機能
- ユーザープロンプトからのスラッシュコマンド検出機能
- セッション終了時の統計表示機能
- `/skill-stats`コマンドによるオンデマンド統計表示

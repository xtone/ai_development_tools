# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

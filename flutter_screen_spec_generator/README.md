# Flutter Screen Spec Generator

Flutterプロジェクトの画面定義書を作成・管理するプラグインです。

## 概要

このプラグインは、Flutterプロジェクトにおける画面定義書の作成環境をセットアップし、個別の画面定義書を生成する機能を提供します。

## 含まれるスキル

### screen-spec-generator

画面定義書を作成・管理するスキルです。

**主な機能:**
- プロジェクト構造の自動解析（CLAUDE.md対応）
- セクション選択による柔軟なテンプレート作成
- カスタムコマンド（/screen-spec）の自動生成
- 個別画面の定義書自動生成

**使い方:**

初期セットアップ:
```
画面定義書を作成したい
```

画面定義書の生成:
```
/screen-spec lib/ui/mypage/widgets/mypage_page.dart
```

**詳細:** [skills/screen-spec-generator/SKILL.md](./skills/screen-spec-generator/SKILL.md)

## インストール方法

### Claude Code Marketplaceから（推奨）

1. マーケットプレイスにリポジトリを追加:
```
/plugin marketplace add xtone/ai_development_tools
```

2. プラグインをインストール:
```
/plugin install flutter-screen-spec-generator@xtone-ai-development-tools
```

## 必要な環境

- Claude Code 0.1.0 以上

## ライセンス

MIT License

## 作成者

**katsume**

## バージョン履歴

### v0.1.0 (2025-12-15)
- 初期リリース
- `screen-spec-generator` スキルの実装
- プロジェクト構造の自動解析
- 会話形式でのテンプレートカスタマイズ

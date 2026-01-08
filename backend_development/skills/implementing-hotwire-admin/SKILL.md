---
name: implementing-hotwire-admin
description: Hotwire（Turbo + Stimulus）を使用してRuby on Railsの管理画面を実装し、PlaywrightによるE2Eテストを含めた完全な実装を行うスキル
---

## 概要

このスキルは、Hotwire（Turbo + Stimulus）を使用して、Ruby on Railsで完全にカスタマイズ可能な管理画面を実装します。E2Eテスト設計・実装も含め、本番運用可能な管理画面を構築します。

## このスキルを使用するタイミング

Claudeは以下の状況でこのスキルを使用します：

- ユーザーがHotwireを使用した管理画面の実装を依頼した場合
- 既存のRailsアプリケーションに管理画面を追加する場合
- 管理画面のE2Eテストを実装する場合
- ActiveAdminやAdministrateを使わずに自作の管理画面を構築する場合

## 技術スタック

| 項目 | 技術 |
|------|------|
| フレームワーク | Ruby on Rails 8.x |
| フロントエンド | Hotwire (Turbo + Stimulus) |
| スタイリング | Tailwind CSS |
| E2Eテスト | Playwright + Capybara |
| 認証 | Devise / 自作認証 |

## ステップ

各ステップの詳細は `steps/` ディレクトリ内のファイルを参照してください。

### 1. セットアップとルーティング
詳細: @steps/01_setup_and_routing.md

Claudeは、管理画面用の名前空間、ルーティング、ベースコントローラを設定します。

### 2. レイアウトとナビゲーション
詳細: @steps/02_layout_and_navigation.md

Claudeは、管理画面専用のレイアウトファイルとサイドバーナビゲーションを作成します。

### 3. CRUD画面の実装
詳細: @steps/03_crud_views.md

Claudeは、一覧・詳細・新規作成・編集画面を実装します。各種データ型に対応したフォームヘルパーも含みます。

### 4. Turbo対応アクション
詳細: @steps/04_turbo_actions.md

Claudeは、削除・公開・非公開などのアクションをTurbo対応で実装します。`button_to`と`data-turbo-confirm`を使用した安全なアクション実装を行います。

### 5. Stimulusコントローラ
詳細: @steps/05_stimulus_controllers.md

Claudeは、確認ダイアログ、フラッシュメッセージ、動的フォームなどのStimulusコントローラを実装します。

### 6. E2Eテスト設計
詳細: @steps/06_e2e_test_design.md

Claudeは、管理画面のテストケースを体系的に洗い出し、テスト計画を作成します。

### 7. E2Eテスト実装
詳細: @steps/07_e2e_test_implementation.md

Claudeは、Playwright + Capybaraを使用してE2Eテストを実装します。TDDアプローチでテストと実装を進めます。

### 8. トラブルシューティング
詳細: @steps/08_troubleshooting.md

Claudeは、よくある問題と解決策を参照し、実装中の問題を解決します。

## ファイル構成

```
implementing-hotwire-admin/
├── SKILL.md                           # このファイル
├── references/
│   └── turbo_patterns.md              # Turboパターンのリファレンス
└── steps/
    ├── 01_setup_and_routing.md        # セットアップとルーティング
    ├── 02_layout_and_navigation.md    # レイアウトとナビゲーション
    ├── 03_crud_views.md               # CRUD画面
    ├── 04_turbo_actions.md            # Turbo対応アクション
    ├── 05_stimulus_controllers.md     # Stimulusコントローラ
    ├── 06_e2e_test_design.md          # E2Eテスト設計
    ├── 07_e2e_test_implementation.md  # E2Eテスト実装
    └── 08_troubleshooting.md          # トラブルシューティング
```

## 重要な注意点

### Turbo対応の削除リンク

Rails 8のTurbo環境では、`link_to`の`method:`オプションが機能しません。必ず`button_to`を使用してください：

```erb
<%# NG: Turbo環境では機能しない %>
<%= link_to '削除', path, method: :delete, data: { confirm: '削除しますか？' } %>

<%# OK: Turbo対応 %>
<%= button_to '削除', path, method: :delete, data: { turbo_confirm: '削除しますか？' } %>
```

### E2Eテストでの注意点

- Turbo確認ダイアログのテストでは、`click_link`ではなく`click_button`を使用
- レスポンシブテストは`page.driver.with_playwright_page`でビューポートサイズを変更
- CI環境ではPlaywrightのヘッドレスモードを使用

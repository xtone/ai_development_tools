# references: hotwire（バックエンド雛形レシピ・Rails+Hotwire）

> ⬜ **未実装スタブ**。本実装は `/aid-references-new project-backend-init hotwire` で起こす（DP-AID-04）。契約は `../SKILL.md` を参照。

## 対象

SSR / 管理画面中心で、別フロント SPA を持たず Rails 内で Hotwire（Turbo / Stimulus）描画する案件。

## 起こすべき内容（実装時に埋める）

- `rails new`（フル構成）＋ Hotwire（turbo-rails / stimulus-rails）セットアップ
- DB 接続核（ローカル基盤と疎通）
- ルート共有設定の継承（rubocop / CI 核）
- 最小レイアウト・最小ビュー核（ドメイン画面は含めない）
- バージョンは tech-version-check で解決

## templates

`../templates/hotwire/`（未作成）。

# references: rails-js-hybrid（モノレポ方式レシピ）

> ⬜ **未実装スタブ**。本実装は `/aid-references-new project-monorepo-scaffold rails-js-hybrid` で起こす。契約は `../SKILL.md` を参照。

## 対象

Rails 重心の案件。Rails をルートに置き、`frontend/`（Next.js 等）を同居させるハイブリッド構成。

## 起こすべき内容（実装時に埋める）

- ルート Rails アプリ ＋ `frontend/` ワークスペース
- 共有設定（最小核・DP-PINIT-10）: `.editorconfig` / `.gitignore` / lint（rubocop + eslint）/ CI ワークフロー核 / env スキーマ
- Rails と frontend のビルド/起動の取り回し（Procfile / foreman 等）
- バージョンは `tech-version-check` で解決

## templates

`../templates/rails-js-hybrid/`（未作成）。

# references: docker-compose（ローカル基盤レシピ）

> ⬜ **未実装スタブ**。本実装は `/aid-references-new project-local-infra docker-compose` で起こす（DP-AID-04）。契約は `../SKILL.md` を参照。

## 起こすべき内容（実装時に埋める）

- `docker-compose.yml`（DB（PostgreSQL 等）＋必要な補助サービス。バージョンは tech-version-check で解決）
- `.env.sample`（DB 名 / ユーザ / ポート等のサンプル・実値なし・MCP-08）
- DB 初期化スクリプト（必要なら）
- `project-backend-init` の database.yml と整合する接続情報

## templates

`../templates/docker-compose/`（未作成）。

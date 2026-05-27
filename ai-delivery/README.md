# AIデリバリシステム（プラグイン群）

Xtone のドメインごとの開発をガイドする **Claude Code プラグイン集合体**。各プラグインが要件定義 → 設計 → 実装の一貫したフローと、ドメイン固有の判断ポイント・スキル・設計パターンを提供する。

中核価値: **人間の判断を要するポイントをスルーさせない**。AI が勝手に決めず、案件ごとの判断は人間に上がる仕組みを各プラグインに組み込んでいる（warn_and_document）。

## ドキュメント案内

| ファイル | 内容 | 主な読者 |
|---|---|---|
| **[docs/plugin-user-guide.md](./docs/plugin-user-guide.md)** | **プラグインユーザーガイド** — 案件で**プラグインを使う**ときの基本フロー・判断ポイント・フィードバックの送り方（backlog 形式）・トラブルシューティング | 案件チーム（PM・BE・FE 等） |
| **[docs/plugin-developer-guide.md](./docs/plugin-developer-guide.md)** | **プラグイン開発者ガイド** — **新しいプラグインを作る** / 既存プラグインを拡張するための型と設計パターン（横断スキル化・契約と references の分離・既知の制約明文化・実機 E2E） | プラグイン開発者 |
| [docs/environment-setup.md](./docs/environment-setup.md) | 実行環境のセットアップとバージョン方針（固定せず公式の最新安定版を使う） | 全員 |
| [docs/mcp-setup-guide.md](./docs/mcp-setup-guide.md) | MCP サーバー設定・トークン管理・トラブルシューティング | 全員 |

> AIデリバリプロセスの進行管理（プロジェクト全体のタスク・規約・判断記録）は [`TODO.md`](./TODO.md) を参照。プラグインの開発・利用には不要。

## ディレクトリ構造

```
ai-delivery/
├── README.md                       # このファイル
├── docs/                           # プラグイン開発・利用向けドキュメント
│   ├── plugin-user-guide.md
│   ├── plugin-developer-guide.md
│   ├── environment-setup.md
│   └── mcp-setup-guide.md
├── scripts/                        # プラグイン生成・検証ツール（TPL-26/27, B-07）
│   ├── generate-plugin.sh
│   ├── validate-plugin.sh
│   └── lib/validate_schema.py
├── xtone-plugin-template/          # 新規プラグインのマスターテンプレ
├── xtone-shared-plugin/            # 各プラグインが共有するスキーマ・横断スキル（SSoT, CONV-14）
│   ├── schemas/v1/
│   │   ├── requirements.schema.json
│   │   ├── design.schema.json
│   │   ├── implementation-plan.schema.json
│   │   ├── modules.schema.json
│   │   ├── risks.schema.json
│   │   ├── decision-point.schema.json
│   │   ├── module.schema.json
│   │   └── quality-gate-rules.yaml
│   └── skills/implementation/
│       └── tech-version-check/     # 横断スキル（B-17）。各プラグインから symlink で参照
└── plugins/
    └── xtone-auth-plugin/          # 認証プラグイン（リファレンス実装）
        ├── .claude-plugin/plugin.json
        ├── README.md
        ├── agents/                 # Subagent
        ├── commands/               # Slash Command
        ├── hooks/                  # hooks.json + Hook（warn_and_document）
        ├── skills/                 # auth-plugin-guide + 各フェーズのスキル
        ├── schemas/ -> ../../xtone-shared-plugin/schemas/v1/   # symlink
        ├── docs/                   # usage-guide / decision-points / pending-decisions
        ├── sample-inputs/          # 架空案件の入力例（成果物 sample-outputs は B-13 後に再生成）
        └── .github/
```

## プラグインの設計原則

各プラグインは以下の原則に従う。詳細・新規プラグイン作成手順は [`plugin-developer-guide.md`](./docs/plugin-developer-guide.md)。

### warn_and_document（警告のみ・ブロックなし）

CI / Hook / Subagent はすべて警告のみで、フェーズ移行をブロックしない。未決の判断ポイントが残ったまま次フェーズに進めるが、ドキュメント（`pending-decisions.md` など）に必ず残る。人間が判断する時間を確保するための仕組み。

### Single Source of Truth（共通スキーマ）

スキーマは `xtone-shared-plugin/schemas/v1/` のみに置き、各プラグインは symlink で参照する。Breaking change 時は `v1/` と `v2/` を並行保持。

### 言語非依存契約 + 言語別レシピ

各スキルは「契約・手順・既知の制約・判断ポイント」を言語/FW 非依存で `SKILL.md` に定義し、具体コードは `references/<stack>.md`（言語別レシピ）に分離する。新言語追加はレシピを足すだけ（契約は不変）。

## プラグイン一覧

- [xtone-auth-plugin](./plugins/xtone-auth-plugin/) — 認証モジュール（メール+PW / パスワードレス / OIDC / MFA / Firebase Auth）。リファレンス実装
- *他のプラグインは順次追加*

最初に触るなら、認証プラグインの使い方ガイド [`plugins/xtone-auth-plugin/docs/usage-guide.md`](./plugins/xtone-auth-plugin/docs/usage-guide.md) の「プロンプト例」節が、各フェーズの実プロンプトを示しているのでわかりやすい。

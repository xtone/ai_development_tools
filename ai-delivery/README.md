# AIデリバリシステム（型化プロジェクト）

Xtone の開発プロセスを **Claude Code プラグイン**で型化するプロジェクト。「人間の判断を要するポイントをスルーさせない」を中核価値とし、24ユースケース × 1プラグイン構成で展開する。

## ドキュメント案内

| ファイル | 内容 | 主な読者 |
|---|---|---|
| [CLAUDE.md](./CLAUDE.md) | Claude Code での作業ルール（鉄則・進め方・ID 体系） | 全員 |
| **[docs/plugin-developer-guide.md](./docs/plugin-developer-guide.md)** | **プラグイン開発者ガイド** — 24 ユースケースの**新しいプラグインを作る**ための型と設計パターン（横断スキル化・契約と references の分離・既知の制約明文化・実機 E2E） | プラグイン開発者 |
| **[docs/plugin-user-guide.md](./docs/plugin-user-guide.md)** | **プラグインユーザーガイド** — 案件で**プラグインを使う**ときの基本フロー・判断ポイント・フィードバックの送り方（backlog 形式）・トラブルシューティング | 案件チーム（PM・BE・FE 等） |
| [docs/notion-db-catalog.md](./docs/notion-db-catalog.md) | 全 Notion DB の一覧と data_source_id、俯瞰ページ | 全員 |
| [docs/mcp-setup-guide.md](./docs/mcp-setup-guide.md) | MCP サーバー設定・トークン管理・WSL2・エラーハンドリング・トラブルシューティング | 全員 |
| [docs/environment-setup.md](./docs/environment-setup.md) | 実行環境のセットアップとバージョン方針（固定せず公式の最新安定版を使う） | 全員 |
| [docs/pending-decisions.md](./docs/pending-decisions.md) | 未決の判断ポイント（warn_and_document の出力先） | 全員 |

## 真実の源（Source of Truth）は Notion にある

実装の根拠となる仕様・規約・判断記録はすべて Notion DB に蓄積されている。詳細は [docs/notion-db-catalog.md](./docs/notion-db-catalog.md)。重要な俯瞰ページ:

- [全体俯瞰サマリ](https://www.notion.so/368ceb782fa38155a578c151d5b2a115) — プロジェクト全体の現在地
- [MTGメモ集約](https://www.notion.so/368ceb782fa381278666f8f41dd59755) — 重要な本決定ログ
- [依存グラフ](https://www.notion.so/365ceb782fa38108a733d180386bf950) — 50 タスクの依存関係
- [持ち越し事項管理（ADR 含む）](https://www.notion.so/365ceb782fa38126b809cef55b5872a2) — 本決定ログとアーキテクチャ判断記録

## ディレクトリ構造

現状（2026-05、コードベース作業の開始直前）は `CLAUDE.md` / `README.md` / `docs/` のみ。以下は型化タスクの進行に伴って構築していく **予定構造** で、`⏳` は未作成を表す。

```
ai-delivery/
├── CLAUDE.md                      # ✅ Claude Code 作業ルール
├── README.md                      # ✅ このファイル
├── docs/                          # ✅ ドキュメント群
│   ├── notion-db-catalog.md
│   ├── mcp-setup-guide.md
│   └── pending-decisions.md       #    判断ポイントの未決ログ
├── xtone-plugin-template/         # ⏳ T-019 マスターテンプレ（TPL-01〜30）
│   ├── plugin.json.template
│   ├── .mcp.json.sample           #    MCP-15
│   ├── .env.example
│   ├── skills/plugin-guide/SKILL.md.template   # 運用ガイド（旧 CLAUDE.md, DP-27/CONV-06）
│   ├── skills/SKILL.md.template   #    SKL-19
│   ├── commands/                  #    TPL-13〜20（8コマンド）
│   ├── agents/                    #    TPL-07〜12（6 Subagent）
│   ├── hooks/                     #    TPL-21〜24（4 Hook）
│   ├── schemas/ -> ../xtone-shared-plugin/schemas/v1/   # symlink
│   ├── docs/template-usage-guide.md   # TPL-28
│   └── scripts/
│       ├── generate-plugin.sh     #    TPL-26
│       └── validate-plugin.sh     #    TPL-27
├── xtone-shared-plugin/           # ⏳ CONV-14 Single Source of Truth
│   └── schemas/v1/
│       ├── requirements.schema.json
│       ├── design.schema.json
│       ├── implementation-plan.schema.json
│       ├── modules.schema.json
│       ├── risks.schema.json
│       ├── decision-point.schema.json
│       ├── module.schema.json
│       └── quality-gate-rules.yaml
└── plugins/
    └── xtone-auth-plugin/         # ✅ T-021 MVP（最初のプラグイン）
        ├── .claude-plugin/plugin.json
        ├── README.md              #    ルート CLAUDE.md は置かない（DP-27: 運用 context は skill へ）
        ├── agents/                #    基盤6 + authentication-architect（7）
        ├── commands/              #    基盤8 + auth-design（9）
        ├── hooks/                 #    hooks.json + 4 Hook
        ├── skills/                #    auth-plugin-guide（ガイド）+ requirements / design / implementation（実動）+ test（スタブ）
        ├── schemas/ -> ../../xtone-shared-plugin/schemas/v1/   # symlink
        ├── docs/                  #    decision-points / usage-guide / pending-decisions / adr
        ├── sample-inputs/, sample-outputs/   # 架空案件の作り込み例
        └── .github/               #    PRテンプレ・CI
```

最初のプラグイン **xtone-auth-plugin** の使い方は [plugins/xtone-auth-plugin/README.md](./plugins/xtone-auth-plugin/README.md) / [docs/usage-guide.md](./plugins/xtone-auth-plugin/docs/usage-guide.md) を参照。

## 中核設計原則

### 「人間判断をスルーさせない」二段構え戦略

- **1段目（受動的可視化）**: pending-watcher Subagent + pre-phase-transition Hook
- **2段目（能動的アラート）**: 4 チャネル同期表示（docs/pending-decisions.md / Slack / コンソール / PR description）+ 週次レポート + 案件レトロ

### 全件 warn_and_document（T-002 本決定）

CI / Hook / Subagent はすべて警告のみ・ブロックなし。未決はドキュメントに明示し、人間が判断する時間を確保する。

### Single Source of Truth（CONV-14）

スキーマは `xtone-shared-plugin/schemas/v1/` の1箇所にのみ置き、各プラグインは symlink で参照する。Breaking change 時は `schemas/v1/` と `schemas/v2/` を並行保持する。

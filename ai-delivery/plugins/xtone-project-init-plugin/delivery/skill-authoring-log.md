# Skill 起稿ログ — xtone-project-init-plugin（T-051）

`/aid-skill-new`（aid-skill-authoring スキル）による Skill 起稿記録。SKL-12（description 3要素）/ SKL-20（frontmatter）/ B-19（横断は独立 Skill）/ 言語非依存契約＋references 分離を遵守。

## 2026-06-01 起稿（setup 系・DP-PINIT-08/09/10/11 反映）

| Skill | フェーズ | responsibility_split | references（state） |
|---|---|---|---|
| `project-stack-select` | design | shared | なし（オーケストレーション。レジストリは setup 系の references で表現） |
| `project-monorepo-scaffold` | implementation | shared（feature-spanning） | turborepo-pnpm / rails-js-hybrid / nx（⬜ 未実装スタブ） |
| `project-frontend-init` | implementation | client | nextjs（⬜ スタブ） |
| `project-backend-init` | implementation | backend | rails / hotwire（⬜ スタブ） |
| `project-local-infra` | implementation | iaas | docker-compose（⬜ スタブ） |

### 設計反映
- スタック選択制（DP-PINIT-09 / ADR-PINIT-003）: `project-stack-select` が候補提示→人間確定、選択を project-scope.json に保持。サポート済み＝references の有無。
- モノレポ方式（DP-PINIT-08）: 単一固定せず案件ごと選択。`project-monorepo-scaffold` は確定方式の references に従う。
- 境界（DP-PINIT-10/11）: 土台のみ生成・ドメイン機能は各モジュール。最小核設定は project-init 所有。
- バージョン方針: 全 setup 系で tech-version-check（B-17）により最新安定版を解決（固定は人間判断）。

### 2026-06-01 追記: スタック提案時の最新版併記（tech-version-check 連携）
- `project-stack-select` が候補提示時に `tech-version-check`（B-17）を呼び、各 FW/言語の最新安定版・要求ランタイム・非互換を取得して併記。`project-scope.json.stack.<layer>` に version/runtime_required/version_source を保持。setup 系は version-matrix.md を再利用（fresh skip・B-13）。project-scope.schema.json に version 系フィールド追加。

### 2026-06-01 追記: オーケストレーション系 Skill ＋ Subagent ＋ /project-* コマンド
| 種別 | 名前 | フェーズ/起動 |
|---|---|---|
| Skill | `project-scope-extraction` | requirements（/project-init） |
| Skill | `project-module-recommendation` | design（/project-modules・module-advisor から） |
| Skill | `project-scaffold` | implementation（/project-scaffold・統合オーケストレーション） |
| Skill | `project-load-guide` | implementation（/project-load-guide・should） |
| Skill | `project-status-aggregation` | test（/project-status・should） |
| Subagent | `module-advisor` | /project-modules |
| Command | `/project-init` `/project-modules` `/project-scaffold` `/project-load-guide` `/project-status` | — |

これで MVP コマンド面（/project-* 5本）＋ Skill 10本（setup 5 ＋ orchestration 5）＋ Subagent 1 が起稿済み。

### 次アクション
1. `/aid-references-new <skill> <stack>` で各 references/<stack>.md ＋ templates/<stack>/ の本実装を起こす（DP-AID-04: 案件で必要になった stack から）。
   - 初期ロールアウト対象: nextjs / rails / hotwire / docker-compose / turborepo-pnpm / rails-js-hybrid / nx
2. コミット/PR 化（feat/T-051-project-init）。

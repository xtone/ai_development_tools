# xtone-project-init-plugin

Xtone AIデリバリシステムの **案件初期化（プロジェクトブートストラップ）** メタプラグイン（T-051）。`xtone-aid-skill-creator-plugin`（プラグインを「作る」側メタ）と対称の「案件を「立ち上げる」側メタ」。マスターテンプレ `xtone-plugin-template`（T-019）から生成。

> 運用 context は `skills/project-init-plugin-guide/SKILL.md` を参照（DP-27 / CONV-06: ルート CLAUDE.md は置かない）。
> プロジェクト全体のルールは `ai-delivery/CLAUDE.md` を参照。

## 構成

- `agents/` — Subagent（基盤6 ＋ `module-advisor`）
- `commands/` — Slash Command（基盤8 ＋ `/project-init` `/project-modules` `/project-scaffold` `/project-load-guide` `/project-status`）
- `hooks/` — hooks.json + 4 Hook（warn_and_document）
- `skills/project-init-plugin-guide/` — 本プラグインの作業ガイド
- `skills/<phase>/<skill>/` — フェーズ別 Skill（setup 系 ＋ orchestration 系）
- `schemas/` — `xtone-shared-plugin/schemas/v1` への symlink（編集不可・CONV-14）
- `docs/` — decision-points / pending-decisions / adr 等

## はじめかた

```bash
cp .env.example .env   # トークンを設定
ai-delivery/scripts/validate-plugin.sh .   # 品質ゲート
claude                  # Claude Code を起動し、/project-init で開始
```

フロー: `/project-init`（ヒアリング）→ `/project-modules`（モジュール推奨）→ `/project-scaffold`（スタック選択＋土台セットアップ）→ `/project-load-guide` → `/project-status`。

## セットアップ対象の言語・フレームワークを追加する手順

本プラグインは案件の土台（モノレポ／フロント／バック／ローカル基盤）を実生成する。**対応スタックは setup 系 Skill の `references/<stack>.md` で表現**し、新しい言語・FW の追加は **references を1枚足すだけ**で済む（契約は変えない＝言語非依存契約＋references 分離。DP-PINIT-09 / ADR-PINIT-003）。

> 方針（DP-AID-04）: スタックは**先回りで全部用意しない**。案件で必要になった時点で追加する。初期サポートは Rails / Next.js / Hotwire / docker-compose / モノレポ方式（turborepo-pnpm・rails-js-hybrid・nx）。

### 手順

1. **レイヤーと reference 名を決める**

   追加先の setup Skill は土台のレイヤーで決まる。reference 名は kebab-case。

   | レイヤー | setup Skill | reference 名の例 |
   |---|---|---|
   | frontend | `skills/implementation/project-frontend-init` | `vuejs` / `nuxt` |
   | backend | `skills/implementation/project-backend-init` | `express` / `hono` / `aws-managed` |
   | local_infra | `skills/implementation/project-local-infra` | （クラウド直結など） |
   | monorepo（方式） | `skills/implementation/project-monorepo-scaffold` | 追加の方式 |
   | native / multiplatform | （新規 setup Skill が必要なら `/aid-skill-new` で起稿） | `swift` / `kotlin` / `flutter` |

2. **references（＋必要なら templates）を起こす**

   `xtone-aid-skill-creator-plugin` のコマンドで雛形を起稿する（契約は変えず、既知の制約を明文化する）。

   ```
   /aid-references-new <skill> <stack>
   # 例: /aid-references-new project-frontend-init vuejs
   ```

   - `references/<stack>.md` … そのスタックの初期化レシピ（具体コマンド・生成ファイル・共有設定の継承）
   - 必要なら `templates/<stack>/` … コピペ起点の雛形

3. **SKILL.md の「言語・FW 別レシピ表」に行を追加**（state を ⬜ → ✅ に）

   例: `project-frontend-init/SKILL.md` のレシピ表に `vuejs` 行を追加する。**SKILL.md の実装契約（言語非依存）と `schemas/v1/project-scope.schema.json` は変更しない**。

4. **レジストリ表を更新**（可視化・任意だが推奨）

   - `skills/design/project-stack-select/SKILL.md` の「サポート済みスタックレジストリ」表に追加
   - `delivery/adr/ADR-PINIT-003.md` ／ `delivery/plugin-architecture.json` の `stack_registry` で当該スタックを `future_extensions` → `initial_rollout`（サポート済み）へ移す

5. **バージョンは固定しない**

   追加スタックのバージョンは `tech-version-check`（B-17）が公式最新安定版を解決し、`/project-scaffold`（`project-stack-select`）が候補提示時に併記する（固定が必要な場合のみ人間判断）。スタック特有の**要求ランタイム・既知の非互換**は `references/<stack>.md` に明記する。

6. **検証・記録**

   ```bash
   ai-delivery/scripts/validate-plugin.sh ai-delivery/plugins/xtone-project-init-plugin
   ```

   起稿内容を `delivery/skill-authoring-log.md` に記録する。

### 原則（守ること）

- **契約は不変**: `SKILL.md` の実装契約と `project-scope.schema.json` は言語非依存。新スタック追加で契約を変えない（CONV）。
- **レジストリ＝references の有無**: references を足せば `project-stack-select` が自動的に候補として提示する（選択も固定も人間が確定・DP-PINIT-09）。
- **境界（DP-PINIT-11）**: setup 系が生成するのは**土台のみ**。ドメイン機能（認証・決済等）は各モジュールプラグインが土台の上に載せる。新スタックでもこの境界を越えない。
- **需要ドリブン（DP-AID-04）**: 案件で必要になってから追加する。

> 関連 ADR: [`delivery/adr/ADR-PINIT-003.md`](./delivery/adr/ADR-PINIT-003.md)（技術スタック選択制と拡張可能なスタックレジストリ）

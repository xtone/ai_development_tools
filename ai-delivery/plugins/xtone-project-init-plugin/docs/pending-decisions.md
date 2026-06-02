# 未決の判断ポイント（xtone-project-init-plugin / T-051）

warn_and_document（T-002 本決定）の出力先。pending-watcher Subagent と pre-phase-transition Hook が参照・更新する想定（骨格生成 `/aid-scaffold` 後に有効化）。

運用ルール:

1. 実装中に判断ポイントへ気づいたら、その場でこのリストに追記する（後回しにしない）。
2. 判断が下りたら `/decide <DP-ID> <選択肢> <rationale>` で記録し、ADR を生成して本リストから除く。
3. ブロックはしない。未決のままでも進められるが、必ずここに残す。

## 未決リスト

| 起票日 | DP-ID | 概要 | 関連タスク | 状態 |
|---|---|---|---|---|
| 2026-06-02 | DP-TEST-FW | バックエンド土台の**テストツール**。**既定 = RSpec**（`rspec-rails` + `factory_bot_rails`、2026-06-02 ユーザー確定）。作成時に確認する選択制は維持（minitest 等へ変更可）。実機検証済み（docker compose で rspec 動作）。 | project-backend-init | 既定 RSpec で確定・選択制維持 |
| 2026-06-02 | DP-CSS-FW | バックエンド土台（Hotwire）の**デザイン/アセット構成**。**既定 = Tailwind CSS**（`--css=tailwind` = `tailwindcss-rails`、**Node 不要**・importmap 維持、2026-06-02 ユーザー確定）。作成時に確認する選択制は維持。実機検証済み（`tailwindcss:build` 成功・/up=200）。 | project-backend-init | 既定 Tailwind で確定・選択制維持 |
| 2026-06-02 | DP-RUBY-VER | 言語ランタイム Ruby のバージョン候補が複数（**4.0.5（4系・最新）/ 3.4.9（3系・実績豊富）**）。Rails 8.1 は両対応。4系の新機能・将来性 vs 3系の gem 互換実績のトレードオフで案件が選ぶ。**既定サジェストは 4系**（tech-version-check が公式最新から複数候補を検出・B-25）。`delivery/version-matrix.md` §6 と相互参照。 | project-backend-init / tech-version-check | 未決（既定=4系サジェスト・人間確定待ち） |
| 2026-06-02 | DP-PINIT-12（仮） | **バックエンド環境のセットアップ手段＝docker compose に全面化**（ホストに Ruby/rbenv を入れず `rails new`・実行・lint をすべて compose で完結）。`project-backend-init` で実装・実機検証済み。**波及範囲は人間確定で「今回は backend のみ」**。`project-local-infra` / `project-frontend-init` / `project-stack-select` への反映は**別タスク**として残す。 | B-25系 / project-backend-init | backend は実装済み・他 setup スキルへの反映は別タスク |

## 判断済み（2026-06-01・decision_record / ADR / Notion DP DB に記録）

| DP-ID | 決定 | 記録先 | Notion 起票 |
|---|---|---|---|
| DP-PINIT-01〜04 | 独立メタ / AI推奨＋人間確定 / 名前空間薄層 / 案件ルート集約 | ADR-PINIT-001・design.decision_record | 既存（DP ID 34〜37） |
| DP-PINIT-05 | 着手タイミング = **先行着手** | design.decision_record | ✅ 起票済 |
| DP-PINIT-06 | project-scope スキーマ = **shared で SSoT 化**（project-scope.schema.json 新設・実装済） | design.decision_record | ✅ 起票済 |
| DP-PINIT-07 | 横断索引形式 = **両方（JSON 正本＋Markdown 派生）** | design.decision_record | ✅ 起票済 |
| DP-PINIT-08 | モノレポ方式 = **案件ごと選択**（候補提示・人間確定） | ADR-PINIT-003・design.decision_record | ✅ 起票済 |
| DP-PINIT-09 | 技術スタック = **スタック選択制＋拡張可能レジストリ**（初期 Rails/Next.js・将来拡張） | ADR-PINIT-003・design.decision_record | ✅ 起票済 |
| DP-PINIT-10 | 境界粒度 = **最小核は project-init 所有**（固有はモジュールがマージ） | design.decision_record | ✅ 起票済 |
| DP-PINIT-11 | 土台=project-init / 機能=モジュール（土台セットアップ内製化） | ADR-PINIT-002・design.decision_record | ✅ 起票済 |
| DP-PINIT-13（仮） | **compose 所有分担 = 単一 `compose.yaml` 統合**（`db`=local-infra / `web`=backend をコメントで境界明示）。`include:` 物理分割は不採用（2026-06-02 人間確定） | references/templates（rails/hotwire）・references-authoring-log | 未（Notion DP DB 起票は別途） |

> 残アクション: ~~(1) DP-PINIT-06 の実装~~ ✅ 完了。~~(2) Notion DP DB 同期~~ ✅ 完了（2026-06-01 `/aid-dp-register` で DP-PINIT-05〜11 を起票。URL は `delivery/dp-registration-log.md` / `docs/decision-points.md`）。
> 次: `/aid-skill-new` で setup 系 Skill を起稿。

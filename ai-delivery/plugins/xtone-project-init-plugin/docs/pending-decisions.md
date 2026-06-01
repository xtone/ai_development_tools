# 未決の判断ポイント（xtone-project-init-plugin / T-051）

warn_and_document（T-002 本決定）の出力先。pending-watcher Subagent と pre-phase-transition Hook が参照・更新する想定（骨格生成 `/aid-scaffold` 後に有効化）。

運用ルール:

1. 実装中に判断ポイントへ気づいたら、その場でこのリストに追記する（後回しにしない）。
2. 判断が下りたら `/decide <DP-ID> <選択肢> <rationale>` で記録し、ADR を生成して本リストから除く。
3. ブロックはしない。未決のままでも進められるが、必ずここに残す。

## 未決リスト

| 起票日 | DP-ID | 概要 | 関連タスク | 状態 |
|---|---|---|---|---|
| _(現在、未決はありません — 下記「判断済み」を参照)_ | | | | |

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

> 残アクション: ~~(1) DP-PINIT-06 の実装~~ ✅ 完了。~~(2) Notion DP DB 同期~~ ✅ 完了（2026-06-01 `/aid-dp-register` で DP-PINIT-05〜11 を起票。URL は `delivery/dp-registration-log.md` / `docs/decision-points.md`）。
> 次: `/aid-skill-new` で setup 系 Skill を起稿。

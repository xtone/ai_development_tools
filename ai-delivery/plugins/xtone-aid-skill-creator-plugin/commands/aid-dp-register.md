---
description: 新規プラグインで検出された判断ポイント候補を Notion 判断ポイントカタログDB（data_source_id 64248f5c-b2f5-4c90-8ccb-7f53692b59b2）に安全に起票する。aid-decision-point-registration スキルを起動し、プレビュー → ユーザ確認 → 起票の 3 段階で書き込み、対象プラグインの docs/decision-points.md も同期更新する。
argument-hint: [target_plugin_path]
---

`aid-decision-point-registration` スキル（`skills/implementation/aid-decision-point-registration/SKILL.md`）に従って、検出された DP 候補を Notion に起票してください。

引数: $ARGUMENTS （省略時は直前の `/aid-skill-creator-design` 対象プラグイン）

**前提**: Notion MCP 接続が必須（書き込み権限）。CI 環境や他人のローカルから起票しないこと（誤起票防止のため、人間が起動するローカルからのみ運用）。

1. **候補抽出**:
   - `<target>/delivery/plugin-architecture.json` の `dp_candidates[?reuse == false]`（新規候補）
   - `dp_candidates[?reuse == true]`（既存再利用候補）は別フロー
2. **Step A: プレビュー**:
   - 各候補を表形式で提示（仮 ID / タイトル / 選択肢 / 判断軸 / 誤判断リスク / 適用条件 / MVP 推奨 / フェーズ）
   - 既存 DP との重複チェック結果（DP-AID-02 80% ルール）も同時提示
3. **Step B: ユーザ確認**（**1 件ずつ**・一括承認禁止）:
   - 起票する / しない / 既存再利用に切替
   - 正規 ID 命名（`DP-<USECASE>-NNN` 形式を推奨）
   - MVP 推奨の有無（「既定推奨を置かない」も valid な選択）
   - 適用条件（全案件 / 特定の案件種別のみ / 本プラグインでは不採用）
4. **命名衝突チェック**（起票直前に Notion 検索で再確認）:
   - `DP-<USECASE>-NNN` 同 ID 既存 → 連番 +1 で再提案
   - `DP-NNN` 形式と衝突 → プレフィックス付き形式に変更
   - タイトル 90% 一致の既存 → 「再利用しますか？」と提示
5. **Step C: 起票**（1 件ずつ）:
   - 起票前に `notion-fetch` で DB スキーマを再確認（プロパティ変更追従）
   - Notion ページ作成 → URL を `delivery/dp-registration-log.md` に記録
   - 失敗時は指数バックオフ（1s, 2s, 4s）3 回 → 失敗で人間エスカレ
   - 起票成功後: `docs/decision-points.md` 同期追記 + `<usecase>-architect.md` の DP-ID 置換（仮 → 正規）+ `pending-decisions.md` から該当行削除
6. **既存 DP 再利用候補の検証**（`reuse: true` 項目）:
   - 既存 DP の最新内容を Notion から取得
   - 当該ユースケースでの解釈の妥当性をユーザに確認
   - 妥当なら `docs/decision-points.md` に「**`DP-NNN` を本プラグインでも採用（理由: ...）**」と追記（新規起票しない）
   - 妥当でないなら `reuse: false` に切り替えてユーザに新規起票を提案
7. **後処理**: `/aid-validation-runner` を呼び、`DP-DRAFT` 残存ゼロを確認。

> 本コマンドは **Notion DP DB への唯一の起票チャネル**。他コマンド・スキルから起票しないこと（誤起票・重複起票・命名衝突防止）。
> ブロックしない（warn_and_document, T-002）。

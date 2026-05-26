# 未決の判断ポイント（pending-decisions）— xtone-auth-plugin

warn_and_document（T-002 本決定）の出力先。認証設計・実装中に気づいた「人間判断が必要なポイント」のうち、**まだ判断が下りていないもの**をここに集約する。pending-watcher Subagent（SCH-5）と pre-phase-transition Hook が参照する。

運用ルール:

1. 判断ポイントへ気づいたら、まずこのリストに追記する（その場で・後回しにしない）。
2. 判断が下りたら、判断ポイントカタログDB（DP-XXX）に decision_record として記録し、本リストから除く。
3. ブロックはしない。未決のまま実装を進める場合も、必ずここに残す。

## 未決リスト

| 起票日 | DP ID | 概要 | フェーズ | 起票者 | 状態 |
|---|---|---|---|---|---|
| 2026-05-25 | DP候補（B-08） | **退会済みアカウントの再登録ポリシー**。同一 UID で退会後に再ログインを許すか（復活/新規作成/拒否）。T-022 パイロットの実装中に発生。本実装は暫定で **403 拒否**。判断ポイントカタログDB への正式起票が必要 | 設計/実装 | Claude（T-022パイロット） | 未決 |
| 2026-05-25 | DP候補（RN-1） | **フロントエンドのセッション戦略**（BFF=HttpOnly クッキー / クライアント直接 Bearer=メモリ保持）。`firebase-auth-frontend` のスキル内判断どまりで、案件横断の DP-XXX になっていない。要配慮個人情報案件では重要判断（再パイロットでは BFF を採用＝ADR-002）。判断ポイントカタログDB への正式起票が必要 | 設計 | Claude（T-021 再パイロット） | 未決 |
| 2026-05-26 | **DP-MVP-COMPAT** | **MVP 期のスキーマ互換性方針**（CONV-14 の例外運用）。本プラグインは MVP ステータスのため、`xtone-shared-plugin/schemas/v1/` の breaking change（required フィールド追加など）に対して **v1/v2 並行保持を厳格適用しない**。最新スキーマで型化を強制し、既存サンプル成果物が新スキーマに合わなければ削除・再生成する（B-14 の方針）。GA 移行時に CONV-14 並行保持戦略を正式策定する。本方針自体を判断ポイントカタログ DB に DP-XXX として正式起票するかは未決（豊田判断）| 規約 / Architecture | 豊田（PR #154 レビュー指示）| 未決 |

## 決定済み（トレース）

| 起票日 | DP ID | 概要 | 決定 | 決定者 |
|---|---|---|---|---|
| 2026-05-25 | [DP-27](https://www.notion.so/36bceb782fa3814c8367dc527991467a) | プラグインルートの `CLAUDE.md`（CONV-06 想定）が Claude Code `--strict` で警告（「ルート CLAUDE.md は context 非ロード。skill を使え」）。CONV-06 と Claude Code 標準の衝突 | **(B) 運用 context を `skills/auth-plugin-guide/SKILL.md` 化し、ルート CLAUDE.md を撤去 → --strict クリーン通過**。波及: CONV-06 改訂・テンプレの CLAUDE.md.template → plugin-guide skill 化（TPL-26 実装時） | 豊田 |

> 架空案件の作り込み例（要件 → 設計 → 実装計画の通し成果物）は、B-13 一連の型化修正が完了した後に `../sample-outputs/` として再生成予定。詳細は [`backlog.md`](./backlog.md) の B-14。

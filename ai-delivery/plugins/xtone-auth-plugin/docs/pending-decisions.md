# 未決の判断ポイント（pending-decisions）— xtone-auth-plugin

warn_and_document（T-002 本決定）の出力先。認証設計・実装中に気づいた「人間判断が必要なポイント」のうち、**まだ判断が下りていないもの**をここに集約する。pending-watcher Subagent（SCH-5）と pre-phase-transition Hook が参照する。

運用ルール:

1. 判断ポイントへ気づいたら、まずこのリストに追記する（その場で・後回しにしない）。
2. 判断が下りたら、判断ポイントカタログDB（DP-XXX）に decision_record として記録し、本リストから除く。
3. ブロックはしない。未決のまま実装を進める場合も、必ずここに残す。

## 未決リスト

| 起票日 | DP ID | 概要 | フェーズ | 起票者 | 状態 |
|---|---|---|---|---|---|
| _(未決なし)_ | | | | | |

## 決定済み（トレース）

| 起票日 | DP ID | 概要 | 決定 | 決定者 |
|---|---|---|---|---|
| 2026-05-25 | [DP-27](https://www.notion.so/36bceb782fa3814c8367dc527991467a) | プラグインルートの `CLAUDE.md`（CONV-06 想定）が Claude Code `--strict` で警告（「ルート CLAUDE.md は context 非ロード。skill を使え」）。CONV-06 と Claude Code 標準の衝突 | **(B) 運用 context を `skills/auth-plugin-guide/SKILL.md` 化し、ルート CLAUDE.md を撤去 → --strict クリーン通過**。波及: CONV-06 改訂・テンプレの CLAUDE.md.template → plugin-guide skill 化（TPL-26 実装時） | 豊田 |

> 架空案件の作り込み例で未決→決定の流れを示したものは [`../sample-outputs/`](../sample-outputs/) を参照（検証用）。

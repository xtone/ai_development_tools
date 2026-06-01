# DP 起票ログ — xtone-project-init-plugin（T-051）

`/aid-dp-register`（aid-decision-point-registration スキル）による Notion 判断ポイントカタログDB（data_source_id `64248f5c-b2f5-4c90-8ccb-7f53692b59b2`）への起票記録。

- 起票日時: 2026-06-01
- 起票者: 豊田（人間承認のうえローカルから起票）
- 命名衝突チェック: 起票直前に Notion 検索で DP-PINIT-05〜11 の不在を確認（DP-PINIT-01〜04 のみ既存・再起票せず）

## 起票エントリ（仮ID → 正規ID → Notion URL）

| 正規 DP-ID | 判断ポイント名 | 確定 | Notion URL |
|---|---|---|---|
| DP-PINIT-05 | 着手タイミング／フェーズ位置づけ | 先行着手 | https://www.notion.so/372ceb782fa381e29d60d0a6cafa5201 |
| DP-PINIT-06 | project-scope のスキーマ配置 | shared SSoT 化（実装済） | https://www.notion.so/372ceb782fa381fea7d6c8ea4647e035 |
| DP-PINIT-07 | 横断索引の形式 | 両方（JSON 正本＋MD 派生） | https://www.notion.so/372ceb782fa3816ca4c1ddadf9438c98 |
| DP-PINIT-08 | モノレポ方式／ツール選定 | 案件ごと選択 | https://www.notion.so/372ceb782fa38173aefbcca640924a11 |
| DP-PINIT-09 | 技術スタック方針（スタック選択制） | 選択制＋拡張可能レジストリ | https://www.notion.so/372ceb782fa3812a875ae26bab37523b |
| DP-PINIT-10 | 土台/機能の境界粒度 | 最小核は project-init 所有 | https://www.notion.so/372ceb782fa3812885ccf61f40c8d9c4 |
| DP-PINIT-11 | 土台/機能の境界・土台セットアップ内製化（旧 DP-PINIT-BOUNDARY） | 土台内製化＋境界明確化 | https://www.notion.so/372ceb782fa3816bab1be530f3d44719 |

> 仮ID `DP-PINIT-BOUNDARY` は正規 ID `DP-PINIT-11` に確定。ローカル成果物（design.json / plugin-architecture.json / ADR-PINIT-002）の参照も DP-PINIT-11 に統一。
> DP-PINIT-01〜04 は既存（DP ID 34〜37, accepted）のため本ログ対象外。
> `DP ID`（Notion auto-increment）は各ページで自動採番（読み取り専用）。

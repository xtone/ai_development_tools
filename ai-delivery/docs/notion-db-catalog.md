# Notion DB カタログ

実装の根拠となる仕様・規約・判断記録はすべて Notion DB（Notion MCP 経由で参照可能）に蓄積されている。**実装前に必ず該当エントリを参照すること。** コード内コメントには理由を書かず、該当エントリの ID（例: CONV-14、TPL-07、SKL-15）を参照する。

## DB 一覧（16 DB）

| DB 名 | プレフィックス | 役割 | data_source_id |
|---|---|---|---|
| 型化タスクDB | T- | 全 50 タスクの進捗管理 | `1356bc46-749e-43dd-b809-7deaf7af8383` |
| プロセス棚卸しDB | — | 開発プロセス 7 フェーズ | `d9d372e6-c937-402b-a2c3-b5863b062555` |
| 判断ポイントカタログDB | DP- | 人間判断必須ポイント 24 件 | `64248f5c-b2f5-4c90-8ccb-7f53692b59b2` |
| ドメインタクソノミーDB | — | 10 ドメイン分類 | `cddc07df-d76e-4ff9-a0c4-5b32d8027097` |
| 型化資産インベントリDB | — | 既存リポジトリ・Skill 棚卸し | `1c6db4f7-2835-4fde-aa27-57b0f4bae886` |
| 品質ゲート・テンプレDB | — | フェーズ移行ゲート 22 件 | `58264a00-83c6-4fec-a557-dc5975a627a1` |
| I/O契約スキーマDB | FLD- | 5 フェーズスキーマ 30 フィールド | `0f997761-9259-4f76-9056-3f209e3a3afc` |
| 判断ポイントスキーマDB | DPS- | decision-point.schema.json | `fd4eec27-907d-4abc-9395-a3031ff9e10c` |
| モジュールカタログスキーマDB | MCS- | module.schema.json | `a983ee9b-9f4c-4e76-810e-3ed7b1bb1462` |
| 品質ゲートルールDB | RULE- | 18 ルール（94% 自動検証可） | `daba3eea-af6d-4c02-8288-d1043009a28e` |
| プラグイン共通規約DB | CONV- | 20 規約 | `28849207-2a7e-46ed-a35d-d153a8329447` |
| サンプルプラグイン骨格DB | — | xtone-auth-plugin の 20 ファイル | `6baff5cf-5eeb-4a36-800f-dcc25baa64f9` |
| Subagent/Command/Hook 設計DB | SCH- | 22 要素 | `c43ad36c-81d3-4d68-bbf1-02b721f93ac0` |
| MCP統合設計DB | MCP- | 4 MCP サーバー・20 件 | `0a8581a2-8d71-4a34-b42e-69eb9ec42745` |
| Skill MD骨格DB | SKL- | SKILL.md 標準骨格 22 件 | `fd777bda-ee8e-4557-a637-1611c2ef52a7` |
| 共通テンプレ実装DB（正） | TPL- | T-019 テンプレ要素 30 件 | `e610ba21-8bff-4629-98d9-8592a64b8da2` |

## 重要な俯瞰ページ

- [全体俯瞰サマリ](https://www.notion.so/368ceb782fa38155a578c151d5b2a115) — プロジェクト全体の現在地
- [MTGメモ集約](https://www.notion.so/368ceb782fa381278666f8f41dd59755) — 重要な本決定ログ
- [依存グラフ](https://www.notion.so/365ceb782fa38108a733d180386bf950) — 50 タスクの依存関係
- [持ち越し事項管理（ADR 含む）](https://www.notion.so/365ceb782fa38126b809cef55b5872a2) — 本決定ログとアーキテクチャ判断記録

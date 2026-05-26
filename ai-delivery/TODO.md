# TODO — AIデリバリプロセス進行用

このドキュメントは、**AIデリバリシステムの型化プロジェクトを進行する側**（プロジェクトリーダー / 型化リーダーチーム）向け。**プラグインを開発・利用する側**は本ファイルを読む必要はない（[`README.md`](./README.md) からの導線を参照）。

## このリポジトリの位置づけ（プロジェクト視点）

`ai-delivery/` は、Xtone の開発プロセスを **Claude Code プラグイン**で型化するプロジェクト。「人間の判断を要するポイントをスルーさせない」を中核価値とし、24 ユースケース × 1 プラグイン構成で展開する。

- **進行管理は Notion DB が真実の源**（コードに「なぜ」を書かず、Notion の ID で参照）
- **進捗の数値は全体俯瞰サマリを正とする**

## 主要 Notion ページ

- [全体俯瞰サマリ](https://www.notion.so/368ceb782fa38155a578c151d5b2a115) — プロジェクト全体の現在地・進捗
- [MTGメモ集約](https://www.notion.so/368ceb782fa381278666f8f41dd59755) — 重要な本決定ログ
- [依存グラフ](https://www.notion.so/365ceb782fa38108a733d180386bf950) — 50 タスクの依存関係
- [持ち越し事項管理（ADR 含む）](https://www.notion.so/365ceb782fa38126b809cef55b5872a2) — 本決定ログとアーキテクチャ判断記録
- [型化タスクDB](https://www.notion.so/4abc1b5c712b40349e1aec3974907ba9) — T-NNN 全 50 タスク

## プロセス進行用ドキュメント

| ファイル | 内容 |
|---|---|
| [CLAUDE.md](./CLAUDE.md) | Claude Code 作業ルール（鉄則・進め方・ID 体系: CONV / DP / SKL / SCH / TPL / MOD / FLD / RULE / MCS / DPS / ADR / MCP） |
| [docs/notion-db-catalog.md](./docs/notion-db-catalog.md) | 全 16 Notion DB の一覧と data_source_id、俯瞰ページ |
| [docs/pending-decisions.md](./docs/pending-decisions.md) | プロジェクト全体の未決判断ポイント（warn_and_document の出力先） |

## 現在地（2026-05-26 時点）

- **Phase**: 6.MVP 完了 → **7.Rollout = Go 判定済み**（[ADR-002 / 2026-05-26 / 豊田](https://www.notion.so/365ceb782fa38126b809cef55b5872a2)）
- **MVP（T-021 認証プラグイン）**: 完成・Rollout Go
- **T-022 内部パイロット**: 完了（[pilot-report](./plugins/xtone-auth-plugin/docs/pilot-report.md) / [re-pilot-report](./plugins/xtone-auth-plugin/docs/re-pilot-report.md)）
- **次のステップ**: T-023〜の Rollout（24 ユースケース展開）

## 残課題（Rollout 並行で消化）

- **B-07**（[#132](https://github.com/xtone/ai_development_tools/issues/132)・検証スクリプト整備・Med）
- **B-08**（[#133](https://github.com/xtone/ai_development_tools/issues/133)・退会再登録 DP の正式起票・Low）
- **B-09**（[#134](https://github.com/xtone/ai_development_tools/issues/134)・言語別実装テンプレ・Low）

詳細: [認証プラグインの backlog.md](./plugins/xtone-auth-plugin/docs/backlog.md)

## 四半期レビュー（T-049）

- 未解決の DP / 持ち越し事項を一括チェック（スタック禁止）
- 各プラグインの backlog 残存数を集計
- 型の改善優先度を決め、次四半期に持ち越す

## プラグイン開発・利用の読者へ

プラグインを **開発する側** は [`docs/plugin-developer-guide.md`](./docs/plugin-developer-guide.md)、**使う側** は [`docs/plugin-user-guide.md`](./docs/plugin-user-guide.md) を読む。本ファイル（TODO.md）は読まなくてよい。

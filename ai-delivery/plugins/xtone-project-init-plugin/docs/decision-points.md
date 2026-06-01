# xtone-project-init-plugin の判断ポイント一覧（T-051）

このファイルは案件初期化メタプラグイン（T-051）が扱う **人間判断必須ポイント**の一覧。正は判断ポイントカタログDB（DP-, data_source_id: `64248f5c-b2f5-4c90-8ccb-7f53692b59b2`）。本ファイルは Notion DP DB と同期更新する（`/aid-dp-register` で同期）。

> 採番は ADR-AID-002 の `DP-<USECASE>-NN`（USECASE=PINIT）に従う。DP-PINIT-01〜04 は B-AID / Rollout 俯瞰レビューで起票済み。DP-PINIT-05〜11 は 2026-06-01 に `/aid-dp-register` で起票（決定済み）。

## DP-PINIT-01 案件初期化機能の提供形態（独立メタプラグイン vs 基盤拡張 vs ドキュメント+スクリプト）

- **フェーズ**: 設計 / **ステータス**: accepted（2026-06-01）
- **確定**: 独立メタプラグイン。Notion: https://www.notion.so/372ceb782fa38191ba37ca7fd6245954

## DP-PINIT-02 モジュール選定の主体（AI推奨+人間確定 vs 完全手動）

- **フェーズ**: 設計 / **ステータス**: accepted
- **確定**: AI推奨＋人間確定（warn_and_document）。Notion: https://www.notion.so/372ceb782fa381b6bfa8f36db3e6ab74

## DP-PINIT-03 複数プラグイン共存と横断操作の束ね方

- **フェーズ**: 設計 / **ステータス**: accepted
- **確定**: 名前空間前提＋/project-* 薄い層。Notion: https://www.notion.so/372ceb782fa381ccae58f38f7b183967

## DP-PINIT-04 案件横断 delivery の構造

- **フェーズ**: 設計 / **ステータス**: accepted
- **確定**: 案件ルート集約 delivery/<module>/＋横断索引。Notion: https://www.notion.so/372ceb782fa381f39a9edf7ab974c235

## DP-PINIT-05 着手タイミング／フェーズ位置づけ

- **フェーズ**: 設計 / **ステータス**: accepted（2026-06-01）
- **選択肢**: (A) 先行着手 / (B) Rollout 進捗後 / (C) 段階的
- **判断軸**: 重要度 / スケジュール
- **確定**: **(A) 先行着手**。MVP は他モジュール完成度に非依存で阻害要因が小さい。
- **Notion**: https://www.notion.so/372ceb782fa381e29d60d0a6cafa5201 / 関連: ADR-PINIT-001

## DP-PINIT-06 project-scope のスキーマ配置

- **フェーズ**: 設計 / **ステータス**: accepted（2026-06-01・実装済）
- **選択肢**: (A) shared SSoT 化 / (B) プラグインローカル保持
- **判断軸**: 保守性 / ドキュメント品質
- **確定**: **(A) shared SSoT 化**。`project-scope.schema.json` 新設・validate-plugin.sh 連携済（CONV-14）。
- **Notion**: https://www.notion.so/372ceb782fa381fea7d6c8ea4647e035

## DP-PINIT-07 横断索引（cross-cutting index）の形式

- **フェーズ**: 設計 / **ステータス**: accepted（2026-06-01）
- **選択肢**: (A) Markdown / (B) JSON / (C) 両方
- **判断軸**: 保守性 / ドキュメント品質 / UXコスト
- **確定**: **(C) 両方**（JSON 正本→Markdown 自動派生）。
- **Notion**: https://www.notion.so/372ceb782fa3816ca4c1ddadf9438c98

## DP-PINIT-08 モノレポ方式／ツール選定

- **フェーズ**: 設計 / **ステータス**: accepted（2026-06-01）
- **選択肢**: (A) pnpm+Turborepo / (B) Rails+JS ハイブリッド / (C) Nx / (D) 案件ごと選択
- **判断軸**: 保守性 / チームスキル / スケジュール
- **確定**: **(D) 案件ごと選択**（AI候補提示・人間確定）。既定提示 JS 重心→A / Rails 重心→B。references で拡張可能。
- **Notion**: https://www.notion.so/372ceb782fa38173aefbcca640924a11 / 関連: ADR-PINIT-003

## DP-PINIT-09 案件横断の技術スタック方針（スタック選択制）

- **フェーズ**: 設計 / **ステータス**: accepted（2026-06-01）
- **選択肢**: (A) スタック選択制＋拡張可能レジストリ / (B) 案件で統一固定 / (C) モジュールごと最適
- **判断軸**: 保守性 / チームスキル / クライアント要望
- **確定**: **(A) スタック選択制**。サポート済みを提示しユーザー選択。初期 Rails/Next.js、将来 AWS managed / express・hono / Vue / Swift・Kotlin / Flutter 等へ references 追加で拡張（契約不変）。
- **Notion**: https://www.notion.so/372ceb782fa3812a875ae26bab37523b / 関連: ADR-PINIT-003

## DP-PINIT-10 土台/機能の境界粒度（共有 base 設定の所有）

- **フェーズ**: 設計 / **ステータス**: accepted（2026-06-01）
- **選択肢**: (A) 最小核は project-init 所有・固有はモジュールがマージ / (B) 共有もモジュール持ち込み / (C) 案件ごと
- **判断軸**: 保守性 / 技術負債
- **確定**: **(A) 最小核は project-init 所有**。
- **Notion**: https://www.notion.so/372ceb782fa3812885ccf61f40c8d9c4 / 関連: ADR-PINIT-002

## DP-PINIT-11 土台/機能の境界・土台セットアップ内製化（旧 DP-PINIT-BOUNDARY）

- **フェーズ**: 設計 / **ステータス**: accepted（2026-06-01 スコープ拡張）
- **選択肢**: (A) 土台を project-init 内製・機能はモジュール / (B) サジェストのみで実セットアップは各モジュール
- **判断軸**: 保守性 / 重要度 / 機能追加の必要性
- **確定**: **(A) 土台内製化＋境界明確化**（土台=project-init / 機能=モジュール）。MVP must。
- **Notion**: https://www.notion.so/372ceb782fa3816bab1be530f3d44719 / 関連: ADR-PINIT-002・003

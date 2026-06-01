# ADR-PINIT-001: 独立メタプラグイン＋薄い /project-* 横断層アーキテクチャ

- Status: accepted
- Date: 2026-06-01
- Decided by: 人間（豊田 / Rollout 俯瞰レビュー）
- Task: T-051（xtone-project-init-plugin / 案件初期化・プロジェクトブートストラップ）
- 関連: requirements `delivery/requirements.json`、design `delivery/design.json`

## コンテキスト

AIデリバリシステムは 24 ユースケース × 1 プラグイン構成で展開しており、各プラグインは
機能モジュール単位（認証など）で要件定義 → 設計 → 実装をガイドする。しかし、実案件を
「これから始める」ときに最初にロードし、ドメイン/要件ヒアリング → 必要モジュール推奨 →
案件ルートの delivery 雛形初期化 → モジュールプラグイン群のロード手順生成までを担う
**案件ブートストラップ層が欠落していた**。機能モジュール単位の型化では「実案件でこれから
使う 1 枚と開発指針を明示する横断基盤」が型化されていない。

横断レイヤーであるがゆえにスコープが肥大しやすく、また価値発現が他モジュールプラグインの
完成度（Rollout 進捗）に依存するという特性がある。これらを踏まえ、構造を確定する必要がある。

## 決定

DP-PINIT-01〜04（いずれも Notion 判断ポイントカタログDB にて 2026-06-01 accepted）を統合し、
以下の架構を採用する。

1. **独立メタプラグイン**（DP-PINIT-01）
   案件ブートストラップは単体ロード可能な読み込み単位であることが必須。プラグインを
   「作る側」メタ（`xtone-aid-skill-creator-plugin`）と対称の「案件を立ち上げる側」メタ
   として `plugins/xtone-project-init-plugin/`（仮名）に独立配置する。

2. **AI 推奨＋人間確定のモジュール選定**（DP-PINIT-02, warn_and_document）
   `/project-modules` は Notion のモジュールカタログDB（MCS）／ドメインタクソノミーDB を
   参照して必要モジュール候補を提示するのみで、**確定は人間**が行う。T-002 本決定
   「人間判断をスルーさせない」に整合し、AI は候補と根拠を提示して判断を人間に上げる。

3. **名前空間前提の薄い /project-* 層**（DP-PINIT-03）
   横断操作は Claude Code 標準名前空間 `/<plugin>:<command>` を前提とし、その上に
   `/project-*` の薄い追加層を載せる。ハード衝突は標準名前空間で回避済みのため、
   独自の衝突回避機構は設けず、実装の重複と保守コストを抑える。

4. **案件ルート集約 delivery/<module>/ ＋横断索引**（DP-PINIT-04）
   `/project-scaffold` が案件ルートに `delivery/<module>/` 雛形と横断索引を初期化し、
   `/project-status` がそれを集約して複数モジュール横断の進捗・未決を一覧する。

加えて、本タスクは横断メタプラグインであり特定 MOD のアプリ tech_options に紐づかない。
該当する MCS モジュール tech_options は存在せず、プラグイン実装スタックはプラットフォーム
規定（Markdown skills + /slash commands + shell hooks + JSON Schema deliverables +
Notion MCP）であり、`generate-plugin.sh` ＋ `xtone-plugin-template` を標準採用する。
共通基盤 8 コマンドと skill-creator メタ構造（scaffold/architect/validation ラッパ）は
対称転用する（転用可否=2 一部改修）。

## 結果

- MVP は `/project-init`（scope ヒアリング → project-scope.json）→ `/project-modules`
  （候補提示・人間確定）→ `/project-scaffold`（delivery/<module>/ 雛形＋横断索引）→
  `/project-load-guide`（ロード手順・共存設定）→ `/project-status`（横断集約）の
  `/project-*` 群となる。スコープ肥大を抑制するため MVP は「モジュール選定支援＋案件
  雛形初期化」に限定し、`/project-load-guide`・`/project-status` は should、対称転用拡張は
  could に振り分ける。
- DB/API/UI のアプリ層フィールドは非該当として誠実適応する（design.json の
  `domain_specific.adaptation_note` を参照）。完全なスキル/サブエージェント分解は
  `/aid-skill-creator-design`（aid-plugin-architecture-design）で別途
  `plugin-architecture.json` として生成する想定。

## 未決（warn_and_document・ブロックなし）

- **DP-PINIT-05**: 着手タイミング／フェーズ位置づけ（先行着手 vs Rollout 進捗後）。継続未決。
- **DP-PINIT-06**: project-scope のスキーマ配置（shared `schemas/v1/` で SSoT 化 vs
  プラグインローカル保持）。推奨は SSoT 化（CONV-14 整合）だが決定は人間。
- **DP-PINIT-07**: 横断索引の形式（Markdown / JSON / 両方）。推奨は両方（JSON 正本＋
  Markdown 派生）だが決定は人間。

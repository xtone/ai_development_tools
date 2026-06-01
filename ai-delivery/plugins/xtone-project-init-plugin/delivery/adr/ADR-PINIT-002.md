# ADR-PINIT-002: 土台セットアップの内製化と土台/機能の境界

- Status: accepted
- Date: 2026-06-01
- Decided by: 人間（豊田 / スコープ拡張指示）
- Task: T-051（xtone-project-init-plugin / 案件初期化・プロジェクトブートストラップ）
- 関連: ADR-PINIT-001（独立メタ＋薄い /project-* 層）/ requirements `delivery/requirements.json`（FR-PINIT-10〜14・MUST-04〜07）/ design `delivery/design.json`（decision_record DP-PINIT-11・responsibility_split）

## コンテキスト

ADR-PINIT-001 では project-init を「要件から既存モジュール/プラグインを推奨するオーケストレーション層」として設計し、実コード生成は各モジュールプラグインに委ねる前提だった（「言語別 references 不要」もこの前提に依存）。

しかし実案件のブートストラップでは、モジュール選定支援（サジェスト）だけでは不足で、**いくつかのフレームワークの初期セットアップやモノレポ構造の構築など、project-init 内で完結させたいもの**がある、という要望が出た（ユーザ指示・2026-06-01）。これは project-init に**実体のあるセットアップ能力**を持たせるスコープ拡張であり、各モジュールプラグインとの責務境界を明確化する必要がある。

## 決定

### 1. 土台セットアップを project-init 内製で完結（MVP must）

以下4領域を `/project-scaffold` で実生成する（MUST-04〜07 / FR-PINIT-10〜13）:

1. **モノレポ骨格＋共有設定** — ルート構成・ワークスペース・共有 lint/format/CI・.gitignore・.editorconfig
2. **フロントエンド初期化** — Next.js アプリ雛形
3. **バックエンド初期化** — Rails（API もしくは Rails+Hotwire）雛形
4. **ローカル基盤** — docker-compose・.env・DB 等のローカル開発環境

### 2. 土台/機能の境界原則（FR-PINIT-14）

- **project-init = 土台**: モノレポ＋フレームワーク雛形＋共有設定＋ローカル基盤まで。
- **各モジュールプラグイン = 機能**: 認証・決済等のドメイン機能は土台の**上に載せる**。

この境界により、横断レイヤーのスコープ肥大を抑えつつ実用価値を持たせる。`responsibility_split` で土台の各層を仕分ける（モノレポ/共有設定=shared・フロント=client・バック=backend・ローカル基盤=iaas）。

### 3. バージョン方針・references

- フレームワーク/言語バージョンは固定せず、`tech-version-check`（B-17）で公式最新安定版を解決（env-setup 方針）。固定が必要な場合は人間判断（warn_and_document）。
- 土台生成の具体ロジックは言語別 references（`nextjs` / `rails` / `hotwire` / `docker-compose` / モノレポツール）に分離する。**ADR-PINIT-001 時点の「references 不要」前提は本 ADR で撤回**する。

## 未決（warn_and_document・ブロックなし）

- **DP-PINIT-08**: モノレポ方式／ツール選定（(a) pnpm workspaces+Turborepo / (b) Rails+JS ハイブリッド / (c) Nx / (d) 案件ごと選択）。単一固定せず AI が候補提示・人間が確定。MVP 既定提示は案件タイプで出し分け（JS 重心→(a) / Rails 重心→(b)）。
- **DP-PINIT-10**: 土台/機能の境界**粒度**。共有 base 設定（lint ルール・型・CI ジョブ・env スキーマ等）を project-init が所有するか、モジュールが持ち込むか。推奨は「全モジュール共通の最小核は project-init 所有、モジュール固有はモジュールが土台にマージ」。最終線引きは人間。

## 結果

- `/project-scaffold` が (a) delivery/<module>/ 索引＋横断索引（ADR-PINIT-001）に加えて (b) 土台セットアップ（モノレポ＋フレーム雛形＋ローカル基盤）を担う。各層の生成は専用 setup Skill＋references に委譲する。
- plugin-architecture に setup 系 Skill（`project-monorepo-scaffold` / `project-frontend-init` / `project-backend-init` / `project-local-infra`）と references_stacks を追加する。
- `local_dev_stack=emulator_docker` を既定とする（実クラウド接続は本番のみ）。

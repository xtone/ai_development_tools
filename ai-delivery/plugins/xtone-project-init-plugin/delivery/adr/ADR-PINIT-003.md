# ADR-PINIT-003: 技術スタック選択制と拡張可能なスタックレジストリ

- Status: accepted
- Date: 2026-06-01
- Decided by: 人間（豊田）
- Task: T-051（xtone-project-init-plugin）
- 関連: ADR-PINIT-002（土台セットアップの内製化）/ DP-PINIT-08（モノレポ方式）/ DP-PINIT-09（案件横断スタック方針）/ requirements `FR-PINIT-15` / design `decision_record`

## コンテキスト

ADR-PINIT-002 で project-init が土台（モノレポ＋フレームワーク雛形＋ローカル基盤）を内製生成する方針を確定した。残る論点は「どの技術スタックをどう選ぶか」（DP-PINIT-08 モノレポ方式 / DP-PINIT-09 案件横断スタック共通方針）。

人間判断: **単一スタックに固定せず、プラグインがサポートする技術スタックを提示してユーザーが選択する。対応スタックは後々拡張できる構成にする。初期ロールアウトでは Ruby on Rails / Next.js をサポートする。**

将来的に対応したいスタック（拡張対象）:
- バックエンド: AWS の managed service を用いた実装、express / hono（TypeScript）
- フロントエンド: Vue.js 等
- ネイティブアプリ: Swift / Kotlin
- マルチプラットフォーム: Flutter 等

## 決定

### 1. スタック選択制（DP-PINIT-09）

`/project-scaffold`（土台セットアップ）は、**サポート済みスタックのレジストリから候補を提示し、ユーザーが選択**する（AI 推奨＋人間確定＝warn_and_document、DP-PINIT-02 と同型）。選択結果は `project-scope.json` のスタック項目に保持し、setup 系 Skill が参照する。

### 2. 拡張可能なスタックレジストリ（CONV: 言語非依存契約＋references 分離）

「サポート済みスタック」は **setup 系 Skill の `references/<stack>.md`** で表現する。契約（SKILL.md・project-scope のスタック項目）は言語非依存に保ち、**新スタック対応は references を1枚足すだけ**（契約不変）。これにより DP-PINIT-09 の「後々拡張できる構成」を満たす。

| レイヤー | 初期ロールアウト（references あり） | 将来拡張（references を追加） |
|---|---|---|
| frontend | `nextjs` | `vuejs` ほか |
| backend | `rails` / `hotwire` | `express` / `hono`（TS）、`aws-managed`（managed backend） |
| native | （なし） | `swift` / `kotlin` |
| multiplatform | （なし） | `flutter` |
| local_infra | `docker-compose` | （クラウド直結など） |
| monorepo | `turborepo-pnpm` / `rails-js-hybrid` / `nx` | 追加方式 |

> **DP-AID-04（先回りしない）と整合**: 初期は Rails / Next.js / docker-compose / モノレポ方式のみ references を用意し、将来スタックは案件で必要になった時点で references を追加する。レジストリは「契約上は拡張可能」だが、実体（references）は需要ドリブンで足す。

### 3. モノレポ方式は案件ごと選択（DP-PINIT-08）

モノレポ方式も単一固定せず、案件タイプから候補を提示し人間が確定する（JS 重心→pnpm+Turborepo / Rails 重心→Rails+JS ハイブリッド / 大規模→Nx）。これはスタック選択制（本 ADR §1）の一部として扱う。

## 結果

- 新スキル候補 **`project-stack-select`**（または `module-advisor` と同型の `stack-advisor` Subagent）が、サポート済みスタックを提示しユーザー選択を受ける。選択は `project-scope.json` に保持。
- setup 系 Skill（`project-frontend-init` / `project-backend-init` / `project-monorepo-scaffold` / `project-local-infra`）は、選択スタックの `references/<stack>.md` を用いて雛形を生成する。
- 初期 references: `nextjs` / `rails` / `hotwire` / `docker-compose` / `turborepo-pnpm` / `rails-js-hybrid` / `nx`。
- バージョンは固定せず tech-version-check（B-17）で最新安定版を解決（ADR-PINIT-002 §3）。
- 将来スタック（Vue / express / hono / aws-managed / swift / kotlin / flutter）は references 追加で対応（契約不変）。

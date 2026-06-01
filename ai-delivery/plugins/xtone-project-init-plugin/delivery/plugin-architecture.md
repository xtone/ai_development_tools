# plugin-architecture.md — xtone-project-init-plugin（T-051 案件初期化メタプラグイン）

> 生成: meta-plugin-architect（MOD-AID / project-init-architect 立場）/ 2026-06-01
> 入力: `delivery/requirements.json` / `delivery/design.json` / `delivery/adr/ADR-PINIT-001.md`（plugin-scope.json 代替）
> リファレンス型: `xtone-auth-plugin/agents/authentication-architect.md`・`auth-plugin-guide/SKILL.md`・`xtone-aid-skill-creator-plugin/delivery/dogfood/auth/plugin-architecture.json`
> **これは推奨と根拠の叩き台です。最終決定は人間。** 未決は `undecided` に残し warn_and_document（T-002）。
> Notion 参照は親エージェントが代理取得済み（本 architect は Notion 非接続・DP DB 非書込）。

## 0. 立ち位置（メタ横断ゆえの前提）

本プラグインは **「案件を立ち上げる側」メタ**（`xtone-aid-skill-creator-plugin`＝「作る側」メタと対称）。**オーケストレーション層**（モジュール選定支援・横断初期化）に加え、**2026-06-01 スコープ拡張で土台セットアップ（モノレポ＋フレームワーク雛形＋ローカル基盤）を内製化**した。
- DP-PINIT-01〜04 は accepted（ADR-PINIT-001）。**DP-PINIT-11（土台/機能の境界・土台内製化）も accepted（ADR-PINIT-002）**。本設計は確定方針の上に載る **/project-* 群＋専用 Skill/Subagent**にフォーカスする。
- 共通基盤8コマンド＋6 Subagent はテンプレ由来で scaffold 済み（重複提案しない）。
- 責務分担: オーケストレーション系 Skill は `shared`、**土台 setup 系 Skill は client/backend/iaas を持つ**（モノレポ=shared / フロント=client / バック=backend / ローカル基盤=iaas）。横断性は「複数モジュールの delivery を串刺す」cross-module ＋「モノレポは複数層にまたがる」feature-spanning の両方向に現れる。
- **境界原則**: project-init は土台まで完結、ドメイン機能は各モジュールが土台の上に載せる（ADR-PINIT-002）。

---

## 1. 必要 Skill リスト（フェーズ別・responsibility_split）

| Skill 名 | フェーズ | 責務 | 責務分担 | 主参照 Notion |
|---|---|---|---|---|
| `project-scope-extraction` | requirements | 案件のドメイン・規模・制約をヒアリングし `project-scope.json` を生成（UC-PINIT-01 / FR-PINIT-01）。既存 `/req-collect` 基盤の対話パターンを横断初期化向けに転用 | shared | SKL-12（要件抽出骨格）, FLD-（project-scope フィールド）, CONV-06 |
| `project-module-recommendation` | design | モジュールカタログDB（MCS）／ドメインタクソノミーDB を参照し必要モジュール候補を **提示のみ**。AI 推奨・確定は人間（UC-PINIT-02 / FR-PINIT-02,06 / DP-PINIT-02 warn_and_document）。`module-selection` を `status=recommended\|confirmed` で可視化 | shared | SKL-20, CONV-06, CONV-07（人間判断） |
| `project-scaffold` | implementation（orchestration） | `/project-scaffold` の統合役。(a) `delivery/<module>/` 雛形＋横断索引＋横断 `pending-decisions` の初期化（UC-PINIT-03 / FR-PINIT-03 / DP-PINIT-04）と (b) 下記 setup 系 Skill 群の呼び出し・統合。`generate-plugin.sh` とは別物 | shared / cross-module | SKL-20, MCS-, CONV-14 |
| `project-monorepo-scaffold` 🆕 | implementation | **モノレポ骨格＋共有設定**（ルート構成・ワークスペース・共有 lint/format/CI・.gitignore・.editorconfig）を生成（UC-PINIT-06 / FR-PINIT-10）。方式は DP-PINIT-08 未決（候補提示・人間確定） | shared（feature-spanning） | SKL-20, CONV-14, env-setup |
| `project-frontend-init` 🆕 | implementation | **Next.js アプリ雛形**を生成（UC-PINIT-06 / FR-PINIT-11）。バージョンは tech-version-check で最新安定版 | client | SKL-20, B-17（tech-version-check） |
| `project-backend-init` 🆕 | implementation | **Rails（API / Rails+Hotwire）雛形**を生成（UC-PINIT-06 / FR-PINIT-12）。バージョン方針同上 | backend | SKL-20, B-17 |
| `project-local-infra` 🆕 | implementation | **ローカル基盤**（docker-compose・.env・DB 等）を生成（UC-PINIT-06 / FR-PINIT-13）。local_dev_stack=emulator_docker 既定 | iaas | SKL-20, B-12 |
| `project-load-guide` | implementation（orchestration, should） | 選定モジュールプラグインのロード手順・共存設定（名前空間共存メモ）を出力（UC-PINIT-04 / FR-PINIT-04 / DP-PINIT-03） | shared / cross-module | SKL-20, MCP-（plugin ロード）, CONV-01 |
| `project-status-aggregation` | test→ops 横断（should） | 横断索引と各モジュール `delivery/<module>/` を集約し、案件全体（複数モジュール横断）の進捗・未決を一覧（UC-PINIT-05 / FR-PINIT-05 / DP-PINIT-04） | shared / cross-module | SKL-20, RULE-（品質ゲート集約）, CONV-07 |

> **横断機能の判定（B-19）**: オーケストレーション系（`project-scaffold` / `project-load-guide` / `project-status-aggregation`）は **複数モジュールの delivery を横断する** `cross-module` 性（責務 `shared`）。一方 **🆕 setup 系**は土台生成のため client/backend/iaas を持ち、`project-monorepo-scaffold` はモノレポ＝複数層共有設定ゆえ feature-spanning（責務 shared だが層横断）。境界は ADR-PINIT-002。
> **SKL-12/SKL-20 frontmatter 準拠**を前提（name / description 必須・DP-27 によりプラグインルート CLAUDE.md は読まれないため運用文脈は plugin-guide SKILL に置く）。

---

## 2. Subagent / Command の拡張提案

| 種別 | 名前 | 役割 | 起動コマンド | 必要性の根拠 |
|---|---|---|---|---|
| Subagent | `module-advisor` | モジュール選定アドバイザ。MCS／ドメインタクソノミーを参照し、案件 scope から必要モジュール群を **複数案＋根拠つきで提示**（確定は人間）。`authentication-architect` の「複数案提示＋MVP推奨＋最終決定は人間」型を流用。ただし比較対象は技術スタックではなく **モジュール群**（MOD-XXX の組合せ） | `/project-modules` | DP-PINIT-02（AI推奨＋人間確定）の中核。比較対象（モジュール群の組合せ）が 2 つ以上想定され、判断軸（案件ドメイン適合・依存・スコープ）の整理に特化 Subagent が要る（DP-AID-05「特化必須」相当） |
| Command | `/project-init` | `project-scope-extraction` 起動。ドメイン・規模・制約ヒアリング → `project-scope.json` | — | kind=orchestration。基盤 `/req-collect` は機能モジュール要件向けで、案件全体 scope ヒアリングは粒度が異なるため薄い追加層として新設（DP-PINIT-03） |
| Command | `/project-modules` | `module-advisor` 起動 | — | kind=orchestration。基盤 `/design` は単一モジュール設計向けで、横断モジュール選定とは目的が異なるため新設 |
| Command | `/project-scaffold` | `project-scaffold` 起動 | — | kind=orchestration。案件ルート集約 delivery 初期化は基盤に存在しない |
| Command | `/project-load-guide` | `project-load-guide` 起動（should） | — | kind=orchestration |
| Command | `/project-status` | `project-status-aggregation` 起動（should） | — | kind=orchestration。基盤 `/status` は単一プラグイン内向け。複数モジュール横断集約は新設が必要 |

> 補助コマンド（`/decide` `/pending-list` `/status` `/next` `/skip-review`）は基盤共通でそのまま使う（重複実装しない）。
> Hook 拡張は **不要**と判断（アプリ層がなく、基盤 pending-watcher / pre-phase-transition で足りる）。`hooks_extension: []`。

---

## 3. 判断ポイント候補（既存再利用 + 新規）

### 3a. 既存 DP の再利用候補

| 既存 DP | 当該ユースケースでの解釈 | 流用根拠 |
|---|---|---|
| （該当薄） | — | 本プラグインは横断メタで、特定ドメインの技術スタック選択 DP（DP-007 認証スタック等）に **該当しない**。DP-AID-02 の 80% 重複ルールを満たす既存 DP は存在せず、再利用候補なし。判断は本プラグイン固有の `DP-PINIT-*` 系が中心 |

### 3b. 既に accepted の DP（再掲のみ・再起票しない）

| DP | タイトル | 状態 |
|---|---|---|
| DP-PINIT-01 | 提供形態＝独立メタプラグイン | accepted |
| DP-PINIT-02 | モジュール選定＝AI推奨＋人間確定（warn_and_document） | accepted |
| DP-PINIT-03 | 横断操作＝標準名前空間前提＋/project-* 薄い層 | accepted |
| DP-PINIT-04 | 横断 delivery＝案件ルート集約＋横断索引 | accepted |
| **DP-PINIT-11** 🆕 | **土台/機能の境界・土台セットアップの内製化**（土台=project-init / 機能=モジュール。MVP must） | **accepted**（2026-06-01・ADR-PINIT-002） |

### 3c. 設計レベル DP（2026-06-01 すべて決定済み・Notion DP DB 起票済み）

> 2026-06-01 に DP-PINIT-05〜11 を `/aid-dp-register` で Notion 判断ポイントカタログDB に起票。詳細は `docs/decision-points.md` / `delivery/dp-registration-log.md`。

| DP | タイトル | 確定 | 状態 |
|---|---|---|---|
| DP-PINIT-05 | 着手タイミング／フェーズ位置づけ | 先行着手 | ✅ accepted |
| DP-PINIT-06 | project-scope スキーマ配置 | shared SSoT 化（実装済） | ✅ accepted |
| DP-PINIT-07 | 横断索引の形式 | 両方（JSON 正本＋MD 派生） | ✅ accepted |
| DP-PINIT-08 | モノレポ方式／ツール選定 | 案件ごと選択（候補提示・人間確定） | ✅ accepted |
| DP-PINIT-09 | 技術スタック方針（スタック選択制） | 選択制＋拡張可能レジストリ（初期 Rails/Next.js） | ✅ accepted |
| DP-PINIT-10 | 土台/機能の境界粒度 | 最小核は project-init 所有 | ✅ accepted |
| DP-PINIT-11 | 土台/機能の境界・土台内製化 | 土台=project-init / 機能=モジュール | ✅ accepted |

> DP-PINIT-09 は旧 09-DRAFT（案件横断起票支援）から、ユーザー回答により本プラグインの実設計決定（スタック選択制・ADR-PINIT-003）へ昇格。

---

## 4. 言語別 references の見立て

| Skill | 必要スタック（初期） | 注意点 |
|---|---|---|
| `project-scope-extraction` / `project-module-recommendation` / `project-load-guide` / `project-status-aggregation` | なし | オーケストレーション／ドキュメント生成主体。`needs_references: false` |
| `project-scaffold` | なし（統合役・テンプレ文字列のみ） | 下記 setup 系を呼ぶオーケストレータ。自体は references なし |
| `project-monorepo-scaffold` 🆕 | `turborepo-pnpm` / `rails-js-hybrid` / `nx` | モノレポ方式（DP-PINIT-08）に応じたレシピ。`needs_references: true` |
| `project-frontend-init` 🆕 | `nextjs` | Next.js 雛形生成。`needs_references: true` |
| `project-backend-init` 🆕 | `rails` / `hotwire` | Rails 雛形生成。`needs_references: true` |
| `project-local-infra` 🆕 | `docker-compose` | ローカル基盤生成。`needs_references: true` |

> **結論（2026-06-01 更新）**: スコープ拡張で土台セットアップを内製化したため **旧『references 不要』前提は撤回**。オーケストレーション系は references 不要だが、**setup 系 4 Skill は references を持つ**（nextjs / rails / hotwire / docker-compose / モノレポツール）。バージョンは tech-version-check（B-17）で最新安定版を解決し、DP-AID-04 に従い案件で必要になった stack から起こす（全部を先回りで作らない）。

---

## 5. sample-cases 該当度（B-21）

> 本プラグインは **全ドメイン共通の横断初期化**なので原則すべて該当。複数モジュールを要する案件ほど価値が高い（モジュール選定支援の意義が大きい）ため、複合案件を上位に。

| 案件 | 該当度 | 採用理由 |
|---|---|---|
| `business-saas` | ⭐⭐⭐ | 多機能 SaaS で必要モジュールが多数。モジュール選定支援＋横断索引の価値が最大 |
| `maas-carshare` | ⭐⭐⭐ | 認証＋地図＋決済等の複合。複数モジュールの組合せ提示・ロード手順生成の代表 |
| `ec-d2c-app` | ⭐⭐⭐ | 認証＋決済の複合。EC 立ち上げの典型でモジュール束ね初期化が映える |
| `education-voucher` | ⭐⭐ | 認証＋バウチャー等の複合だが構成がやや限定的 |
| `media-content` | ⭐⭐ | CMS／配信中心。モジュール数は中程度 |
| `event-campaign-lp` | ⭐ | LP 主体で単機能寄り。横断初期化の価値は相対的に小さい |
| `corporate-site` | ⭐ | 静的サイト寄りで複数モジュール束ねの必要性が低い |

> カタログ 7 案件すべてに該当があるため、新案件 PR（DP-AID-03）は不要。

---

## 6. 外部 MCP

| MCP | 要否 | 用途 |
|---|---|---|
| Notion | **必須** | `/project-modules`（`module-advisor`）が モジュールカタログDB（MCS, `a983ee9b-9f4c-4e76-810e-3ed7b1bb1462`）と ドメインタクソノミーDB（`cddc07df-d76e-4ff9-a0c4-5b32d8027097`）を参照して候補提示 |
| GitHub | 任意 | `/project-load-guide` が各モジュールプラグインを参照する程度 |

> **差し替え可能設計（T-004 適応）**: アプリ IaaS 差し替えとは異なるが、`module-advisor` は **モジュールカタログの参照源（Notion）を adapter 越しに読む**設計余地を残し、参照源（Notion / ローカルキャッシュ / 将来別 SoT）を差し替え可能に保つ。直接 Notion SDK を全 Skill から叩く実装は MVP 推奨にしない。

---

## 7. 未決（undecided・warn_and_document）

- **未決なし**。DP-PINIT-01〜11 はすべて accepted（2026-06-01）。DP-PINIT-05〜11 は `/aid-dp-register` で Notion 判断ポイントカタログDB へ起票済み（`delivery/dp-registration-log.md` に URL）。
- 残実装アクション: 各 setup 系 Skill の起稿（`/aid-skill-new`）と、project-scope.schema.json（DP-06）は新設済み。

---

## 8. メタゆえの留意点（本プラグイン固有）

- **DP 命名**: `DP-PINIT-*`（USECASE=PINIT, ADR-AID-002 採番）。他プラグイン DP（DP-001〜/DP-AID-*）と衝突させない。新規は 08 以降。
- **循環参照注意**: 本プラグインは「作る側」メタ（skill-creator）の出力フォーマットを利用する関係にある。本 architect 修正時は skill-creator 側の再生成が通ることを確認（ADR-AID-001 予定）。
- **Notion 書込限定**: 本 architect は DP DB に書き込まない。書込は `aid-decision-point-registration` Skill（プレビュー→確認→起票の3段）のみ。

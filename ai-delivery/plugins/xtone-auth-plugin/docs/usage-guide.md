# xtone-auth-plugin 使い方ガイド

認証モジュール（MOD-001）を「要件定義 → 設計 → 実装」の垂直スライスで型化するプラグインの使い方。MVP は Firebase Auth、IaaS 差し替え可能設計が前提（T-004 本決定）。

> **実行環境**: 言語・FW（Ruby/Rails 等）は固定せず**公式の最新安定版**を使う。セットアップとバージョン方針は [`ai-delivery/docs/environment-setup.md`](../../../docs/environment-setup.md) を参照。特定バージョンが必要な場合は判断ポイントとして人間に確認する。

## 1. インストール / ロード

開発中はセッション限定でロードして試せる:

```bash
# ai-delivery/ で
claude --plugin-dir plugins/xtone-auth-plugin
```

検証のみ:

```bash
claude plugin validate --strict plugins/xtone-auth-plugin
```

## 2. 基本フロー

```
/req-collect   # 要件定義（認証要件の抽出は auth-requirements-extraction スキル）
   ↓
/auth-design   # 認証設計（authentication-architect が DP-007/008/015 を比較・推奨、
               #   firebase-auth-design が design.yaml + ADR を生成）
   ↓
/implement     # 実装（backend: firebase-auth-setup / client: firebase-auth-frontend /
               #   横断 MFA: firebase-auth-mfa / ローカル E2E: firebase-auth-emulator）
```

補助コマンド: `/decide`（判断記録）/ `/status`（進捗）/ `/next`（次アクション）/ `/pending-list`（未決一覧）/ `/skip-review`（AIレビュー）。

> 汎用設計でよい場合は `/design`、認証ドメイン特化は `/auth-design`。

## 3. 成果物（スキーマ）

| フェーズ | コマンド | 出力スキーマ |
|---|---|---|
| 要件定義 | `/req-collect` | `schemas/requirements.schema.json` |
| 設計 | `/auth-design` | `schemas/design.schema.json`（+ `docs/adr/ADR-NNN.md`、`responsibility_split` で BE/FE 仕分け） |
| 実装 | `/implement` | `schemas/implementation-plan.schema.json` + 実装コード |

`schemas/` は xtone-shared-plugin への symlink（編集不可, CONV-14）。

### 認証スキル一覧

フェーズと責務で使い分ける。横断機能（MFA / emulator）は backend・client 双方にまたがるため独立スキルに集約している（B-04 / T-021 由来）。

| 種別 | スキル | 責務 / レシピ |
|---|---|---|
| 要件定義 | [`auth-requirements-extraction`](../skills/requirements/auth-requirements-extraction/SKILL.md) | 認証要件の抽出（ログイン方式 / MFA / 規制 / 退会 / ページ単位の認証要否 A/B/C） |
| 設計 | [`firebase-auth-design`](../skills/design/firebase-auth-design/SKILL.md) | `design.yaml` + ADR + `responsibility_split` + `page_access_control` を生成 |
| 実装（backend） | [`firebase-auth-setup`](../skills/implementation/firebase-auth-setup/SKILL.md) | ID トークン検証・JWT 認可・退会時 Admin 削除・**2 段階の失効**（hard / soft）（レシピ: Rails） |
| 実装（client） | [`firebase-auth-frontend`](../skills/implementation/firebase-auth-frontend/SKILL.md) | サインイン / 退会 / トークン保持 / API への Bearer 付与 / **3 パターンの認証ガード**（protected-only / public-aware / guest-only）と /login と /signup の分離（レシピ: Hotwire / Next.js） |
| 実装（横断 MFA） | [`firebase-auth-mfa`](../skills/implementation/firebase-auth-mfa/SKILL.md) | MFA enrollment（client）/ クレーム検証・管理者強制・MFA 変更時の soft 失効（backend）。`mfa_requirement` の実装マッピング、`auth_time` 非更新の落とし穴を明文化（レシピ: rails / hotwire / nextjs） |
| 実装（ローカル E2E） | [`firebase-auth-emulator`](../skills/implementation/firebase-auth-emulator/SKILL.md) | Docker で Auth Emulator を起動。署名検証スキップ・Admin REST 切替・`connectAuthEmulator`・SMS MFA で E2E（TOTP は非対応 → 実 Identity Platform）（レシピ: docker-compose / rails / nextjs） |

> どのスキルがいつ起動するかの**実プロンプト例**は下の「[7. プロンプト例](#7-プロンプト例t-021-再パイロットの実例から)」を参照。

## 4. 判断ポイント（人間判断をスルーさせない）

| DP | 内容 |
|---|---|
| DP-007 | 認証スタック選択（Firebase Auth 推奨 + 代替比較・差し替え可能設計） |
| DP-008 | MFA 要件の振り分け |
| DP-015 | dAccount / docomo 規約の適用範囲 |
| DP-28 | 退会済みアカウントの再登録ポリシー（MVP 既定推奨 = 403 拒否、案件要件次第でクールダウン等へ） |

詳細は [`decision-points.md`](./decision-points.md)。AI は決めず推奨だけ提示。未決は各スキーマの `undecided` と [`pending-decisions.md`](./pending-decisions.md) に残る（warn_and_document, T-002）。フェーズ移行時に未決があると pre-phase-transition Hook が警告する（ブロックはしない）。

## 5. 通し検証（架空案件の作り込み例）

`sample-inputs/` に架空案件「みんなの読書会」の入力テキストがある。

> **成果物例 (`sample-outputs/`) は現在ありません。** B-13（実装スキル呼び出しプラン生成）一連の型化修正が完了した後に、最新スキーマ・スキル群で**1 から再生成**する予定（[`backlog.md`](./backlog.md) の B-14）。それまでは新規案件の雛形は `schemas/v1/*.schema.json` と各スキルの「入出力」節を直接参照する。

## 6. 差し替え可能設計（他 IaaS 追加）

Firebase 固有処理は `AuthAdapter` 実装に閉じ込める。別 IaaS（Cognito / Auth0 / Devise 等）追加時はアダプタ実装の差し替えで対応する（Rollout フェーズで実証）。

## 7. プロンプト例（T-021 再パイロットの実例から）

T-021 再パイロット（架空案件「オンライン診療・問診」/ 医療 × MFA required × Next.js + Rails）で**実際に使われた指示文**をフェーズごとに整理する。プロンプトは **「案件前提・判断ポイントの決定・任せる範囲」を明示**することで、AI が `undecided` を残さず `decision_record` に書く / 適切なスキルとレシピを呼ぶ動きをする。

### 7.1 要件定義（`/req-collect` ＋ `auth-requirements-extraction`）

案件の前提と要望を 1 メッセージで揃え、要件抽出スキルを呼ぶ。

```
医療「オンライン診療・問診」案件で要件定義を進めてください。
- ロール: 医療従事者 / 患者の2ロール
- 認証方式: メール+パスワード、パスワードレス（OIDC は could）
- MFA: 全ユーザー必須（要配慮個人情報のため）
- 規制: 個人情報保護法（要配慮個人情報）、3省2ガイドライン
- 退会: 認証アカウント削除と診療データ保存の分離（法定保存期間）
- 構成: Next.js(App Router) フロント + Rails API バックエンド
DP-007 / DP-008 は要件段階では undecided にして設計に引き継いでください。
ページ単位の認証要否（A/B/C）も洗い出してください。
```

→ `delivery/requirements.json`（`scope` / `representative_use_cases` / `functional_requirements` / `undecided=[DP-007,DP-008]`）。

### 7.2 設計（`/auth-design` ＋ `authentication-architect` / `firebase-auth-design`）

判断ポイントの決定 + 責務仕分け + ページアクセス制御を一度に揃える。

```
requirements.json をもとに認証設計（design.yaml）を作ってください。
- DP-007: Firebase Auth を採用候補とし、Devise+OmniAuth と Auth0 と比較した
  ADR-001 を残す（差し替え可能設計を AuthAdapter で維持）
- DP-008: MFA = required（全員必須・TOTP 主体、emulator 検証では SMS で代替）
- responsibility_split を Next.js=client / Rails=backend / iaas / shared で明示
- セッション戦略: BFF（HttpOnly クッキー）を採用 → ADR-002 に記録
- ページ単位アクセス制御: firebase-auth-frontend のデフォルト 3 パターン
  （A: protected-only / B: public-aware / C: guest-only）を採用
- 医療規制（3省2GL）を domain_specific_checks に
```

→ `delivery/design.yaml` + `ADR-001` `ADR-002`、`responsibility_split` + `page_access_control` + `decision_record`、`undecided=[]`。

### 7.3 スキーマ検証（B-01 解消の確認）

```
delivery/requirements.json と delivery/design.yaml を xtone-shared-plugin/schemas/v1/
の本実装スキーマで検証してください。必須フィールド欠落のネガティブ検証
（検証が実際に効くこと）も含めて確認してください。
```

→ `jsonschema` で PASS、ネガティブで NG を検出。

### 7.4 実装：backend（`firebase-auth-setup` + `firebase-auth-mfa` の Rails レシピ）

```
Rails API backend を実装してください。
- firebase-auth-setup の rails レシピ: AuthAdapter 抽象 / FirebaseAdapter /
  TestAdapter / Authenticatable concern / 運用契約（退会 Admin 削除・証明書
  キャッシュ・2 段階失効）
- firebase-auth-mfa の rails レシピ: verify_token に second_factor 取り込み /
  MfaEnforceable concern（required を強制）/ MfaController#changed（soft 失効）
- 退会は hard_revoke_tokens! を呼び、診療データは法定保存期間まで保持（ADR-002）
- TestAdapter で結合テスト（実 Firebase 不要、9件想定）
- bin/rails test と bin/rails zeitwerk:check が通ることを確認
```

→ minitest で MFA required / ロール認可 / 退会データ分離 / トークン失効 を検証。

### 7.5 実装：frontend（`firebase-auth-frontend` + `firebase-auth-mfa` の Next.js レシピ + 3 パターン）

```
Next.js (App Router) frontend を実装してください。
- firebase-auth-frontend の nextjs レシピ: lib/firebase.ts / lib/auth-client.ts /
  メモリ保持 + 自動リフレッシュ
- firebase-auth-mfa の nextjs レシピ: SMS MFA enrollment/challenge
- 3 パターンの AuthGate コンポーネント（type="protected" | "public-aware" | "guest"）
- /login と /signup は別ページ・相互リンク・callback 引き継ぎ（open redirect 防止）
- /mfa/enroll, /settings, /consultations は protected-only
- / は public-aware（認証状態でコンテンツ切替）
- tsc --noEmit と next build が通ることを確認
```

→ `<AuthGate>` でルートガード、`safeCallback` で URL 検証。

### 7.6 ローカル E2E（`firebase-auth-emulator` の Docker レシピ）

```
ローカルで E2E 検証するため、Docker で Firebase Auth Emulator 環境を構築してください。
- firebase-auth-emulator の docker-compose / rails / nextjs レシピに沿う
- backend は EMULATOR_HOST 設定時のみ署名検証スキップ + Admin REST 切替（Bearer owner）
- frontend は connectAuthEmulator
- 本番混入ガード（production && emulator? → abort）を入れる
- docker compose up で起動、E2E スクリプトで:
  signUp → emailVerified=true 設定 → signIn → /auth/session →
  /consultations が 403 mfa_required → SMS MFA enroll → /consultations 200 →
  ロール認可（医師=全件・患者=自分のみ）→ 退会 → 再ログイン拒否
```

→ docker-compose（auth-emulator / backend / frontend）が healthy、E2E 全 PASS。

> **MFA は SMS で検証**（Auth Emulator は TOTP 非対応＝[firebase-tools #6224](https://github.com/firebase/firebase-tools/issues/6224)）。TOTP の E2E は実 Identity Platform で。

### 7.7 ブラウザ動作確認（最小 UI）

```
http://localhost:3001 でフルフローをブラウザから操作できる最小 UI を実装してください。
- /login（サインイン・/signup へのリンク・callback 引き継ぎ・guest-only）
- /signup（サインアップ・/login へのリンク・callback 引き継ぎ・guest-only。
  emulator では emailVerified=true 自動設定）
- /mfa/enroll（SMS 登録、emulator からコード自動取得・protected-only）
- /consultations（保護リソース・protected-only）
- /settings（退会・protected-only）
- /（認証状態に応じてコンテンツ切替・public-aware）
- AuthGate で 3 パターン宣言的にラップ。tsc/next build 通過。
```

### 7.8 不具合報告 → 実機再現 → スキル根本対応

実機で不具合を踏んだら「再現・原因特定・スキル修正」までセットで指示する。型を直すことで再発を防ぐ。

```
http://localhost:3001/consultations にログイン／MFA 設定後にアクセスすると
401 が返ってきます。実際にブラウザで操作して確認してください。
不具合を修正したら、スキルのどの部分が原因で発生した不具合かを調査し、
スキル側でこの不具合が起きないように修正してください。
```

→ Playwright で再現 → 根本原因（**`auth_time` は MFA enrollment で更新されない** vs スキル既定の即時失効の衝突）特定 → **2 段階失効**にスキル更新（hard / soft 分離）。サンプル+スキル両方を修正し、再発を防ぐ。

### 7.9 プロンプト設計のコツ

- **案件前提と判断ポイントの決定を最初に揃える**: 「DP-XXX をこう決めた」と明示すると AI が `undecided` に残さず `decision_record` に書く
- **判断は人間、実装は AI**: スタック比較・MFA 方針・セッション戦略・ページ A/B/C 振り分けはユーザーが決め、コードはスキルが書く（warn_and_document に沿う）
- **不具合報告は「実機再現 + 原因特定 + スキル修正」までセットで**: 型を直すことで他案件にも効く（本プラグインの中核価値）
- **横断機能は新スキル化を依頼する**: MFA / emulator / フロント 3 パターンのように backend/client 双方にまたがる機能は、既存スキルに無理に詰めず**横断スキル新設**を指示すると整合性が保たれる（前例: `firebase-auth-mfa`、`firebase-auth-emulator`）
- **要件で別指定があれば要件優先**: スキル既定（例: ページ 3 パターンのデフォルト一覧）に反する案件特性はプロンプトで明示し、`decision_record` に逸脱根拠を残す

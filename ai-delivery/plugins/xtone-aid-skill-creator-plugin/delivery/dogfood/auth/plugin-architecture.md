# auth プラグイン メタアーキテクチャ（ドッグフード再現）

> **ドッグフード成果物**: 本プラグイン（`xtone-aid-skill-creator-plugin`）の `aid-plugin-architecture-design` スキルの出力フォーマット（4 チャネル）が、既存 `xtone-auth-plugin` の実態を表現できるかを後追いで実証する成果物。実物との照合は `findings.md` を参照。

- **対象**: `xtone-auth-plugin`（MOD-001 認証）
- **scope 入力**: [`./plugin-scope.json`](./plugin-scope.json)
- **構造化抜粋**: [`./plugin-architecture.json`](./plugin-architecture.json)
- **作成日**: 2026-05-28

---

## Channel 1: 必要 Skill リスト（フェーズ別・responsibility_split つき）

| Skill 名 | フェーズ | 責務 | 責務分担 | 主参照 Notion / リファレンス |
|---|---|---|---|---|
| `auth-requirements-extraction` | requirements | 認証要件の抽出（ログイン方式 / MFA / 規制 / 退会 / ページ A/B/C / 招待・監査・通知） | shared | SKL-DB（要件抽出系）/ FLD-DB |
| `firebase-auth-design` | design | design.yaml + ADR + responsibility_split + page_access_control 生成 | shared | SKL-DB（設計系）/ CONV-06 |
| `firebase-auth-setup` | implementation | ID トークン検証 / JWT 認可 / 退会 Admin 削除 / 公開鍵キャッシュ / 2 段階失効 | backend | SKL-DB（実装系）/ MCS-001 |
| `firebase-auth-frontend` | implementation | サインイン / 退会 / トークン保持 / 3 パターン認証ガード / /login と /signup 分離 | client | SKL-DB（実装系）|
| `firebase-auth-mfa` ⭐ | implementation | MFA enrollment（client）/ クレーム検証・管理者強制・soft 失効（backend）/ TOTP・SMS SDK（iaas） | client + backend + iaas（**横断**） | SKL-DB / B-19（横断 Skill 化の前例）|
| `firebase-auth-emulator` ⭐ | implementation | Docker で Auth Emulator 起動 / 署名検証スキップ / connectAuthEmulator / SMS MFA E2E（TOTP 非対応） | client + backend + infrastructure（**横断**） | SKL-DB / B-19 |
| `auth-e2e-verify` | test | 代表 UC の Playwright 実機 E2E / delivery/e2e-verification-report.md に通過証跡 | shared | SKL-DB（test 系）/ RULE-DB |

⭐ = B-19 横断機能（独立 Skill 化済み）。`firebase-auth-mfa` は **feature-spanning**（機能が複数層にまたがる）、`firebase-auth-emulator` は **environment-spanning**（実行環境が複数層にまたがる）。

> **ギャップ**: 本プラグイン仕様の `skills[].responsibility_split` 配列だけでは「横断の種類」（feature / environment）を区別できない。kind フィールドの追加候補（FINDING-01）。

## Channel 2: Subagent / Command の拡張提案

| 種別 | 名前 | 役割 | 起動コマンド | 必要性の根拠 |
|---|---|---|---|---|
| Subagent | `authentication-architect` | 認証ドメイン特化設計・DP 比較・差し替え可能設計の担保 | `/auth-design` | 比較スタック 6 つ（Firebase Auth / Devise+OmniAuth / Cognito / dAccount / NextAuth.js / Laravel Sanctum）= DP-AID-05 で「特化必須」推奨 |
| Command | `/auth-design` | 上記 architect 起動 | — | 同上 |
| Hook 追加 | （なし） | — | — | 基盤 4 Hook で十分 |

## Channel 3: 判断ポイント候補

### 既存 DP の再利用候補

（auth プラグインは AIデリバリ初の本格実装のため、再利用元 DP は存在しない。Rollout プラグインからの再利用方向のみ。）

| 既存 DP | 当該ユースケースでの解釈 | 流用根拠 |
|---|---|---|
| — | — | — |

### 新規 DP 起票候補（`/aid-dp-register` で起票）

| 仮 ID | タイトル | 選択肢 | 判断軸 | 誤判断リスク | MVP 推奨 |
|---|---|---|---|---|---|
| DP-007 | 認証スタック選択 | Firebase Auth / Devise+OmniAuth / Cognito / dAccount / NextAuth.js / Laravel Sanctum | セキュリティ / クライアント規制 / ユーザ規模 / コスト | 後段でスタック交代 | **Firebase Auth**（AuthAdapter で IaaS 差し替え可能設計を維持） |
| DP-008 | MFA 要件の振り分け | 全員必須 / 管理者のみ / オプトイン / 不要 | セキュリティ / UX / 規制 | MFA スキップでインシデント / 過度適用で UX 劣化 | **既定推奨を置かない**（案件次第） |
| DP-015 | dAccount / docomo 規約遵守タイミング | 全面遵守 / コア部分のみ / 事前協議 / 独自規約 | クライアント規制 / セキュリティ / スケジュール | 規約見落としで検収不合格 | 適用条件: docomo 系案件のみ |
| DP-28 | 退会済みアカウントの再登録ポリシー | (A) 拒否（403）/ (B) 復活 / (C) 新規作成 / (D) クールダウン | セキュリティ / 規制 / UX / 保守性 | 旧データ引き継ぎなりすまし（GDPR 17 条 / 個情法 30 条） | **(A) 拒否** |
| DP-INVITATION-POLICY-001 | 招待制サインアップの運用ポリシー | 有効期限 / 使い切り / 送信手段 / 失効通知の組合せ | セキュリティ / UX / 運用負荷 | 期限長すぎで漏洩 / 短すぎで再依頼負荷 | 72h・1 回限り・メール・通知あり（招待者） |
| DP-AUDIT-VIEW-001 | 監査ログ | 対象操作 / 保存期間 / 閲覧権限 / 閲覧 UI | 規制 / セキュリティ / コスト | 絞りすぎで後追い不能 / 閲覧 UI 無で形骸化 | 4 種・1 年・admin・管理画面 + CSV |
| DP-NOTIFY-001 | 通知方針 | 手段 / イベント / オプトアウト / 開発環境 | セキュリティ / UX / 規制 / 開発運用 | セキュリティ系通知欠如で乗っ取り検知遅れ | メール・4 イベント・開発環境 Mailcatcher |

> **命名形式**: DP-007 / DP-008 / DP-015 / DP-28 は番号形式（CONV-19 既存）、DP-INVITATION-POLICY-001 等はプレフィックス付き形式。本プラグインの **DP-AID-02** の議論（80% 重複ルール）と **CONV-19 拡張**（ADR-AID-002 予定）に直結する例。

## Channel 4: 言語別 references 見立て + sample-cases 該当度

### references 初期スタック

| Skill | 必要スタック | 追加予定 | 注意 |
|---|---|---|---|
| `firebase-auth-setup` | rails | node-express / laravel | Ruby は公式 Admin SDK 無し → REST API 代替（既知の制約として明文化済） |
| `firebase-auth-frontend` | nextjs / hotwire | flutter | XSS 配慮で `inMemoryPersistence` 既定 |
| `firebase-auth-mfa` | rails / nextjs / hotwire | — | `auth_time` 非更新の落とし穴（2 段階失効で対応） |
| `firebase-auth-emulator` | docker-compose / rails / nextjs / hotwire | — | TOTP は非対応 → 実 Identity Platform へ |

### sample-cases 紐付け案

| 案件 | 該当度 | 採用理由 |
|---|---|---|
| — | — | **auth プラグインは B-21 以前に独自 `bookclub-app` を作成した経緯**。新規 Rollout プラグインからは `sample-cases/` カタログ運用（DP-AID-03）|

> **ギャップ**: 本プラグイン仕様の `sample_case_bindings` 配列だけでは「カタログ運用 vs 独自案件並存」を表現できない。`sample_case_legacy` フィールドの追加候補（FINDING-02）。

## 採用したドメイン拡張スキーマ

- `xtone-shared-plugin/schemas/v1/design.auth.schema.json`（B-20 / #173）
- `.claude-plugin/plugin.json` に `delivery.design_extensions: ["design.auth.schema.json"]` を宣言済み

## 外部 MCP

- `github`（PR・コミット・リリース）
- `notion`（DP-DB / SKL-DB / CONV-DB / FLD-DB / DPS-DB / 型化タスクDB 参照）
- （`figma` は auth プラグインでは未使用）

## 後続スキルへの引き渡し

| 後続 Command/Skill | 入力（本ファイルの何を渡すか） |
|---|---|
| `/aid-scaffold auth` | `usecase` / `plugin_name` / `applicable_domains` / `module_candidates` / `commands` 拡張 |
| `/aid-architect-author auth` | `subagents[0]`（authentication-architect）+ `dp_candidates[0..2]`（DP-007/008/015）|
| `/aid-skill-new <phase> <skill>` | `skills[*]` の各行 |
| `/aid-references-new <skill> <stack>` | `skills[*].references_stacks` |
| `/aid-dp-register` | `dp_candidates[?reuse == false]` 7 件 |
| `/aid-sample-case-binding` | **N/A**（独自 bookclub-app を並存運用）|

## 未決（undecided）

| field | reason |
|---|---|
| `skills[].kind` | 本プラグイン仕様に kind（feature-spanning / environment-spanning）フィールドが未定義（FINDING-01） |
| `sample_case_legacy` | 本プラグイン仕様に独自 sample-input を表現するフィールドが未定義（FINDING-02） |

---

> ドッグフードで判明したギャップ・本プラグイン側の修正候補・ADR 候補は [`./findings.md`](./findings.md) にまとめる。

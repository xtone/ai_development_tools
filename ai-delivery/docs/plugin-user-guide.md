# プラグインユーザーガイド（案件で型化プラグインを使う）

このドキュメントは、AIデリバリシステムの **型化プラグインを使って実案件を進める開発者**向け。要件→設計→実装の各フェーズで、プラグインがどう支援するか、**自分が何を判断するか**、不具合や改善要望をどう開発者に届けるかを示す。

> **対をなすガイド**: プラグインを*作る*側は [`plugin-developer-guide.md`](./plugin-developer-guide.md)。

## このガイドの読者

- 実案件で型化プラグインを使う**プロジェクトメンバー**（PM / バックエンド / フロント / アプリ / インフラ）
- プラグインのフィードバック（うまく動かない / 改善要望）をプラグイン開発者に伝えたい開発者

## 0. まず読んでほしい中核価値

> **AI に決めさせない判断は、必ず人間に上がってくる仕組みです。**

CI / Hook / Subagent はすべて **warn_and_document**（警告のみ・ブロックなし）。フェーズ移行時に未決ポイントが残っていると警告が出るが、進めることはできる。**警告を放置せず、最終的に必ず人間判断で確定する**ことが型化の中核価値です。

## 1. 基本の流れ

### 1.1 ドメインに合うプラグインをロード

```bash
# 例: 認証案件
cd ai-delivery
claude --plugin-dir plugins/xtone-auth-plugin
```

利用可能なプラグイン一覧は `ai-delivery/plugins/` 配下を参照（Rollout フェーズで段階的に増える）。

### 1.2 フェーズを順に進める

```
/req-collect → /design → /implement
```

各プラグインに**フェーズ固有のコマンド**が追加されている（例: 認証は `/auth-design`、認証ドメイン特化の設計）。

### 1.3 補助コマンド

- `/decide` — 判断記録
- `/status` — 進捗
- `/next` — 次アクション
- `/pending-list` — 未決一覧
- `/skip-review` — AI レビュー

## 2. あなたが決めること / AI が書くこと

### あなた（人間）が決めること = 判断ポイント

| カテゴリ | 例 |
|---|---|
| スタック選定 | DP-007 認証スタック / DP-004 アーキテクチャ |
| セキュリティ・規制 | DP-008 MFA 方針 / DP-015 dAccount / DP-016 PCI-DSS |
| 非機能要件 | ユーザー規模 / SLA / 退会データ保存期間 |
| ドメイン特化 | 業界規制・コンプライアンス（医療なら 3省2GL、金融なら FISC など） |
| 既定パターンからの逸脱 | フロント 3 パターン（protected/public-aware/guest）と違う配置にする 等 |

これらは **AI が決めず推奨だけ提示**する設計。あなたが決めたものを `decision_record` に記録、決まらないものは `undecided` に残す。

### AI が書くこと

- スキーマに沿った構造化成果物（requirements.json / design.yaml / implementation-plan.json）
- 言語非依存の契約に従ったコード（プラグインの references レシピ準拠）
- スキル既定パターン（例: 認証なら「2 段階の失効」「3 パターンの認証ガード」「/login と /signup の別ページ化」）

## 3. 「警告」と「未決」の扱い方

### 警告が出たら

フェーズ移行時に **pre-phase-transition Hook** が `undecided` を検出して警告を出す（ブロックはしない）。

- **未決を残したまま進める** — 後で必ず人間判断で確定する前提なら OK。`docs/pending-decisions.md` に残る
- **その場で決める** — 判断材料が揃っているなら、`/decide` で `decision_record` に記録して `undecided` から外す

### 未決を放置しない

- 案件横断で再発する未決は **DP-NNN として正式起票**（Notion 判断ポイントカタログDB）
- T-049（四半期レビュー）で未決一括チェックがあるので、それまでには消化する

## 4. delivery 成果物の確認

各フェーズで `delivery/` 配下に成果物が出る:

| フェーズ | 成果物 |
|---|---|
| 要件定義 | `requirements.json` |
| 設計 | `design.yaml` + `docs/adr/ADR-NNN.md` |
| 実装 | `implementation-plan.json` + 実装コード |

**スキーマ検証**は必ず通す（B-01 で本実装済み）。検証が落ちる場合は、案件特有の要件で逸脱しているのか、スキーマ側の穴かを切り分けてフィードバックする。

## 5. フィードバックの送り方（重要）

プラグインを使って気づいた問題（穴・改善余地・不具合・改善要望）は、**訂正バックログ形式**でプラグイン開発者に送ります。

### 5.1 フォーマット

参考: [認証プラグインの backlog.md](../plugins/xtone-auth-plugin/docs/backlog.md)

| 項目 | 内容 |
|---|---|
| **症状** | 実機で再現できる具体的な手順 |
| **想定挙動 vs 実挙動** | スキルや usage-guide に書かれている内容との差 |
| **重要度** | High（型の穴・実装が止まる）/ Med（並行対応可）/ Low（任意改善） |
| **影響範囲** | 自分の案件のみ / 同種案件にも影響 / 横断的 |
| **回避策**（あれば） | 案件で踏んだ対処 |
| **再現コード**（あれば） | プロンプトや E2E スクリプトの抜粋 |

### 5.2 起票先

- **プラグイン特定の問題** → そのプラグインの `docs/backlog.md` に **B-NNN** で追記 + GitHub Issue
- **横断的な問題**（複数プラグインに関わる、CONV/スキーマレベル）→ `ai-delivery/` 全体の GitHub Issue
- **新規 DP 候補** → プラグインの `docs/pending-decisions.md` に起票

### 5.3 良いフィードバックの例

T-021 再パイロットで踏んだ `auth_time` 不具合（[PR #147](https://github.com/xtone/ai_development_tools/pull/147)）は：

1. **症状**: `/consultations` でログイン→ MFA 設定後に **401 `token revoked`**
2. **想定 vs 実挙動**: 想定は 200（MFA 充足）。実挙動は 401（backend が `auth_time < tokens_valid_after` で拒否）
3. **重要度**: High（実装が止まる）
4. **影響範囲**: MFA を使う全案件
5. **回避策**: なし
6. **再現コード**: Playwright で `/signup → /mfa/enroll → /consultations` の操作

→ 開発者が原因を特定（Firebase の `auth_time` は MFA enrollment で更新されない仕様）し、**スキルの型を直す**まで進めた（2 段階失効化、再発防止）。

このように、**実機再現 + 原因仮説**まで添えるとスキルの根本改善につながりやすい。

## 6. トラブルシューティング（よくある罠）

各プラグインの「既知の制約」は SKILL.md に書いてあるので、まずそこを読む。代表的なもの:

### 認証プラグイン

- **Firebase Auth Emulator は TOTP MFA 非対応** — ローカル検証は SMS で代替、TOTP は実 Identity Platform で（[firebase-tools #6224](https://github.com/firebase/firebase-tools/issues/6224)）
- **emulator の MFA enrollment は `emailVerified=true` 前提** — signUp 後に `accounts:update` で立てる
- **`auth_time` は MFA enrollment で更新されない** — MFA 変更時は **soft 失効**（IaaS refresh のみ、サーバ側 `tokens_valid_after` は触らない）
- 詳細: [`firebase-auth-mfa` SKILL.md の既知の制約](../plugins/xtone-auth-plugin/skills/implementation/firebase-auth-mfa/SKILL.md)

### 環境前提

- バージョンは固定しない方針（[`environment-setup.md`](./environment-setup.md)）— 公式の最新安定版を使う。古いシステム Ruby/Node を踏みやすいので、rbenv / mise / nvm 等で最新を入れる

## 7. 参考プラグインの使い方

最初に読むべきは、対応プラグインの **`docs/usage-guide.md`** の「プロンプト例」節。実プロンプトが各フェーズで載っているので、自分の案件に置き換えて使える。

代表例: [認証プラグイン usage-guide §7「プロンプト例」](../plugins/xtone-auth-plugin/docs/usage-guide.md#7-プロンプト例t-021-再パイロットの実例から)

- 7.1 要件定義
- 7.2 設計（判断ポイント決定）
- 7.3 スキーマ検証
- 7.4 backend 実装
- 7.5 frontend 実装
- 7.6 ローカル E2E（Docker emulator）
- 7.7 ブラウザ動作確認
- 7.8 不具合報告 → 実機再現 → スキル根本対応
- 7.9 プロンプト設計のコツ

## 8. レビュー・サポート

- **使い方の質問・困りごと**: 開発チーム（Slack の関連チャンネル）or 豊田に直接
- **機能要望・不具合**: 上記 §5 のフォーマットで GitHub Issue
- **案件横断の判断ポイント**: Notion 持ち越し事項管理（ADR）

---

> **プラグインユーザーは「型化の改善ループ」の重要な担い手**です。実案件で踏んだ穴ほど、型化の品質を上げる材料になります。気軽に GitHub Issue を立ててください。

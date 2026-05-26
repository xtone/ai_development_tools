# プラグイン開発者ガイド（Rollout 24 ユースケース）

このドキュメントは、AIデリバリシステムの **24 ユースケースのうち、新しいプラグインを実装する開発者**向け。MVP（T-021 認証プラグイン）と内部パイロット（T-022 ＋ T-021 再パイロット）で確立した型を使い、自分のドメインのプラグインを作るために必要な情報をここに集約する。

> **既存資産との関係**: 本ガイドは「型の使い方」の発展形（プラグイン*ユーザー*向け）である [`plugin-user-guide.md`](./plugin-user-guide.md) と対をなす。プラグインを使う案件チームではなく、**プラグインを作る**側の視点。

## このガイドの読者

- 24 ユースケースのいずれか（管理画面 / コンテンツ配信 / 決済 / 通知 / コミュニティ 等）を担当する**型化プラグイン開発者**
- 既存プラグインに新スキルを追加する開発者

## 0. 中核価値（必読）

リポジトリの [`ai-delivery/CLAUDE.md`](../CLAUDE.md) の鉄則をそのまま守る:

1. **実装の根拠は Notion / コメントに ID 参照**（CONV- / SKL- / DP- / SCH- 等）
2. **判断ポイントは「気づいたその場で」記録**（後でまとめない）
3. **CI / Hook / Subagent は warn_and_document**（警告のみ・ブロックなし）
4. **スキーマは Single Source of Truth**（CONV-14、`xtone-shared-plugin/schemas/v1/` のみに置く）

これに反する設計をしないこと。型化プロジェクトの中核価値「**人間の判断を要するポイントをスルーさせない**」を全層で守る。

## 1. プラグインの作り方（手順）

### Step 1: マスターテンプレからコピー

```bash
# 将来 generate-plugin.sh が整備されたら（B-07 / TPL-26）:
cd ai-delivery
./xtone-plugin-template/scripts/generate-plugin.sh my-plugin

# 現状は手動コピー
cp -r xtone-plugin-template plugins/xtone-<your-domain>-plugin
```

### Step 2: プラグイン構造に従う

```
plugins/xtone-<domain>-plugin/
├── .claude-plugin/plugin.json     # Claude Code 標準フィールドのみ
├── README.md                      # 人間向け概要
├── agents/                        # Subagent（基盤 6 + ドメイン特化）
├── commands/                      # Slash Command（基盤 8 + ドメイン特化）
├── hooks/                         # hooks.json + 4 Hook（warn_and_document）
├── skills/
│   ├── <domain>-plugin-guide/SKILL.md   # 運用ガイド（旧ルート CLAUDE.md / DP-27）
│   ├── requirements/<domain>-requirements-extraction/
│   ├── design/<domain>-design/ (+ templates/)
│   ├── implementation/<domain>-setup/ (+ references/)
│   └── implementation/<domain>-frontend/ など
├── schemas/                       # xtone-shared-plugin への symlink（編集不可・CONV-14）
├── docs/                          # decision-points / usage-guide / pending-decisions / adr
├── sample-inputs/, sample-outputs/  # 架空案件の作り込み例
└── .github/                       # PRテンプレ・CI
```

### Step 3: スキル設計の原則（言語非依存契約 + references）

認証プラグインで確立した型:

- **SKILL.md は言語/FW 非依存の「契約」と「手順」**を定義
- 具体コードは `references/<stack>.md`（言語別レシピ）に分離
- レシピを追加するときは契約を変えない（差し替え可能設計を維持）
- **「既知の制約」を徹底的に明文化**（後続の開発者が同じ穴を踏まないため）
- **「要件で別指定があれば要件優先」**を全層で明記

### Step 4: 判断ポイント（DP-XXX）の追跡

- 案件で出てくる判断は、既存 DP-XXX を再利用するか新規起票
- 新規 DP は `docs/pending-decisions.md` に起票 → Notion 判断ポイントカタログDB に登録 → スキル側に「**未決のまま実装に来た場合は確定せず残す**」と明記
- フェーズ移行時に `undecided` が残ると pre-phase-transition Hook が**警告**（ブロックはしない）

### Step 5: パイロット → 訂正バックログ → 再パイロット

認証プラグインで型化した検証サイクル:

1. **架空案件**で要件→設計→実装を 1 本通す
2. 発見事項を `pilot-report.md` に列挙（成功事例 + 失敗・摩擦）
3. 訂正タスクを `backlog.md` ＋ GitHub Issue 化（High / Med / Low）
4. High を解消した後で**再パイロット**（前回と異なる条件で）
5. 再判定で Rollout Go/No-go を決める

## 2. 認証プラグインから学べる設計パターン（必読）

参考実装である [`xtone-auth-plugin`](../plugins/xtone-auth-plugin/) は MVP として完成し、Rollout Go 判定済み（ADR-002）。設計判断の根拠は再パイロット報告と一連の PR に残っているので、自分のドメインでも踏襲する。

### 2.1 横断機能は独立スキルにする

backend / client / iaas のどれか 2 つ以上にまたがる機能は、既存スキルに無理に詰めず**独立スキル**にする。

- `firebase-auth-mfa`（[PR #143](https://github.com/xtone/ai_development_tools/pull/143)）— enrollment(client) / 検証・強制(backend) / iaas にまたがる
- `firebase-auth-emulator`（[PR #145](https://github.com/xtone/ai_development_tools/pull/145)）— Docker / 署名検証スキップ / connectAuthEmulator にまたがる

スキル内部で `responsibility_split` を表で示し、何が client / backend / iaas / shared かを明示する。

### 2.2 言語非依存契約 + references レシピ

すべてのスキルは「契約」と「実装手段」を分離する:

| 層 | 役割 |
|---|---|
| `SKILL.md` | 言語非依存の契約・手順・既知の制約・判断ポイント |
| `references/<stack>.md` | 言語/FW 別の具体コード（例: rails.md / nextjs.md / hotwire.md） |

別言語が増えても契約は不変。新言語のレシピを追加するだけ。

### 2.3 既知の制約は徹底的に明文化

後続の開発者が同じ穴を踏まないように、スキル側にすべて書く:

- 例: `firebase-auth-mfa/SKILL.md`「**`auth_time` は MFA enrollment で更新されない**」 / 「**emulator は `emailVerified=true` が前提**」
- これらは再パイロットで実機の不具合として顕在化し、根本対応（[PR #147](https://github.com/xtone/ai_development_tools/pull/147)・2 段階失効）でスキルに反映された

### 2.4 「要件で別指定があれば要件優先」を全層で明記

スキル既定パターン（例: フロント 3 パターンの protected/public-aware/guest、デフォルトページ一覧）を作るときも、**案件で別指定があれば要件優先**を必ず書く:

- `design.responsibility_split` または `page_access_control` で逸脱を明示
- `decision_record` に逸脱根拠を残す
- warn_and_document に沿わせる

### 2.5 実機 E2E まで通す

test スタブのみだと**型の穴を見逃す**。Docker + emulator + Playwright で実機まで通すと、再パイロットでの発見（auth_time 仕様の不具合）が拾える:

- backend は TestAdapter で結合テスト（実 IaaS 不要）
- frontend は tsc/build を通す
- ローカル E2E は Docker emulator（auth-emulator / backend / frontend 3 サービス）
- ブラウザ動作確認は最小 UI で実プロンプト経由

### 2.6 不具合は「再現 + 原因特定 + スキル根本対応」までセットで

実機で不具合を踏んだら、スキルの型を直すまでが 1 タスク。再パイロットの auth_time 不具合は **Playwright で再現 → 原因（Firebase 仕様）特定 → スキルの 2 段階失効化**まで進めた（PR #147）。これにより他案件での再発を防ぐ。

## 3. 参考実装と便利リンク

- **xtone-auth-plugin（MVP / Rollout Go 判定済み）**
  - 全体ガイド: [`auth-plugin-guide`](../plugins/xtone-auth-plugin/skills/auth-plugin-guide/SKILL.md)
  - 使い方とプロンプト例: [`docs/usage-guide.md`](../plugins/xtone-auth-plugin/docs/usage-guide.md)（§7 が実プロンプト例）
  - パイロット報告: [`pilot-report.md`](../plugins/xtone-auth-plugin/docs/pilot-report.md) / [`re-pilot-report.md`](../plugins/xtone-auth-plugin/docs/re-pilot-report.md)
  - 訂正バックログ: [`backlog.md`](../plugins/xtone-auth-plugin/docs/backlog.md)
  - 関連 PR: [#143](https://github.com/xtone/ai_development_tools/pull/143)〜[#150](https://github.com/xtone/ai_development_tools/pull/150)
- **共通スキーマ**: `ai-delivery/xtone-shared-plugin/schemas/v1/`（編集不可・CONV-14）
- **環境前提**: [`environment-setup.md`](./environment-setup.md)（バージョンは固定せず公式の最新安定版）
- **Notion DB カタログ**: [`notion-db-catalog.md`](./notion-db-catalog.md)（16 DB 一覧）
- **MCP 設定**: [`mcp-setup-guide.md`](./mcp-setup-guide.md)
- **持ち越し事項管理（ADR 含む）**: Notion / ADR-001 作業ベース、ADR-002 Rollout Go

## 4. レビュー・フィードバックの流れ

### あなたから外への流れ

- **PR レビュー**: 豊田（T-005 1 名体制）。Vertex AI 自動レビューが先に triage → review で指摘を出すので、Major までは対応してから人間レビュー依頼が効率的
- **新規 DP / 規約改訂**: Notion 持ち越し事項管理に **ADR-NNN**（プロジェクト ADR）として起票
- **新規 SKL / SCH / CONV**: Notion の各 DB に登録

### プラグインユーザーからのフィードバックを受ける

[`plugin-user-guide.md`](./plugin-user-guide.md) が案件チームに案内する**フィードバックフォーマット**は次の通り:

- 案件で使って気づいた問題は、プラグインの `docs/backlog.md` 形式（**B-NNN**）で GitHub Issue 起票
- 「症状 / 想定挙動 vs 実挙動 / 影響範囲 / 回避策」を含める
- 開発者は **High（型の穴）/ Med / Low** でトリアージし、Rollout 並行で消化

T-021 再パイロットの auth_time 不具合（PR #147）はこのフォーマットで「実機再現 → 原因特定 → スキル根本対応」まで到達した好例。プラグインユーザーからの報告も同じ流れで型を改善できる。

## 5. Rollout 期間中の進め方

- **新しいプラグインのキックオフ**: 該当ユースケース（24 のうち未着手のもの）の Notion タスク（T-NNN）を確認し、対応する DP / MOD を読み、本ガイドの Step 1〜5 で実装
- **複数並行**: 24 を 1 人で全部はやらない。**ユースケース担当者**を Notion 型化タスクDB の「担当ロール」で明示する
- **共通基盤の改善**: 複数プラグインで似たパターンが出たら、**xtone-shared-plugin / xtone-plugin-template に昇格**させて他プラグインで使えるようにする（CONV-XX への昇格は持ち越し事項管理に ADR 化）

## 6. T-049（四半期レビュー）との連携

- 四半期で**未解決の DP / 持ち越し事項**を一括チェック（スタック禁止）
- 各プラグインの **backlog 残存数**を集計し、型の改善優先度を決める
- パイロット報告で見つかった発見事項のうち、Rollout 並行で消化できなかったものを次四半期に持ち越し

---

> **質問・提案**: GitHub Issue（`xtone/ai_development_tools` リポジトリ）or 豊田に直接。「やりたいことが既存スキルに無い」場合は遠慮なく**新スキル新設**を提案。横断機能なら独立スキル、特定の言語/FW 向けの実装は references レシピに、という分離を意識する。

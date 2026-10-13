# Claude Code ログからの弁証法的ナレッジ創出 — 計画 v0.1

作成日: 2026-10-13（v0.1: 決定事項を反映。同日中に Notion 構築と実装計画 doc を完了）
前提: `xtone/ai_development_tools/knowledge_sharing`（session-tips-digest v0.1.0）と Notion「Claude Codeまとめ置き場」を読んだ上での計画。
実装の詳細（Notion の ID、questions.yaml、カードのスキーマ、Phase 1〜3 のタスク）は Claude Doc「ナレッジカード実装計画」にある。

## 0. 一言で

「問いを決める → 各自の Claude Code ログから AI が付箋（カード）を下書きする → 本人が確認して Notion に提出する → AI が週次で分類・対立整理・合成する → 人間が決める → 採用したものをスキルや CLAUDE.md に還元する」を、週 1 回・1 人 15 分で回せる仕組みにする。

## 決定事項（2026-10-13）

| 項目 | 決定 |
|---|---|
| 問い | §3 の問いカタログ v0 で進める |
| 提出先 | Notion。既存の「Claude Codeまとめ置き場 › 週次 Tips」を拡張する |
| 周期 | 週 1 回。活動週の翌週はじめに提出、その後に合成 |
| 匿名性 | プロジェクト名・著者ともに実名（社内 tier）。秘密情報・顧客 PII・クライアント内部 URL は引き続き伏せる |
| スキル構成 | 新規 `knowledge-cards`（抽出→下書き→自己確認→提出）と `knowledge-synthesis`（週次合成）。既存 session-tips-digest はカードから Tips 文書を作る下流に位置づけ直す |
| パイロット | シニアエンジニア 5〜6 名、2 週間〜1 か月、途中参加あり |

## 1. 現行スキル（session-tips-digest）の評価

### できていること
- `~/.claude/` から prompts（history.jsonl）、tool_use 回数、Bash サンプル、memory、ハーネス構成を 1 つの JSON に集計する
- 匿名化辞書と `scan_sensitive.py` による機密ゲート（0 件まで公開しない）
- Tips の採用基準（再現性・記録に根拠・転記でない）と文体ガイド
- 一次情報による裏付けと Artifact / Notion 公開。W41 の個人ページはこの出力

### 弁証法フォーマットに向けて足りないこと
| 不足 | 影響 |
|---|---|
| 出力が個人の Tips 文書（散文）で、構造化された中間データが無い | 複数人分を機械的に集計・分類できない |
| 抽出が user prompt とツール名の回数のみ。assistant 応答・tool_result・ターン構造を見ていない | 「言い直し」「中断」「同じエラーの反復」「手戻り」など課題側のシグナルが拾えない |
| 問いが固定で「うまくいったこと」に偏る | 正と反が出ないので合成が弱い |
| 匿名化が社外公開前提の 1 段階のみ | プロジェクト名が消え、目的 3・4（プロジェクトの進め方・全社把握）に使えない |
| 1 回の実行が重い（月次・調査フェーズ込み） | 週次では回らない |

## 2. 全体像

```
[問いカタログ]  knowledge_sharing/questions.yaml（正本・版管理）+ Notion「問いカタログ v0」(閲覧用)
      │
      ▼  各エンジニアのローカル（週 1 回、15 分）  /knowledge-sharing:knowledge-cards
[抽出]   ~/.claude → セッション索引 + 問いごとの根拠パック（Python、決定的）
[下書き] 根拠パック → カード（JSONL）を問いごとに下書き
[自己確認] 本人がカードを修正・削除・追加（「人間が付箋を書く」工程）
[機密ゲート] 秘密情報スキャン 0 件
[提出]   Notion MCP で「ナレッジカード」DB に行を作成、「週次 Tips」の行に投稿者を追加
      │
      ▼  週 1 回、集約側（スケジュールタスク or 手動）  /knowledge-sharing:knowledge-synthesis
[合成]   当週のカード全件 → 重複排除 → 親和図 → 対立（正・反）→ 合（提案）→ 次の問い候補
      ├─ 週のまとめページ（週次 Tips の行の配下）
      ├─ 「合成テーマ」DB にクラスタを記録、カードと関連付け
      └─ 月 1 回: プロジェクトマップ（P1/P2 の集計表）と月次ロールアップ
      │
      ▼
[共有会] 隔週 30 分。合の採否を決める（FigJam 出力は任意）
      │
[還元]   採用 → ai_development_tools（スキル / CLAUDE.md テンプレ / プラグイン）へ PR。カードの「採用先」に記録
```

原則: 決定的に取れるものは Python、意味の判断だけ Claude。下書き（大量・並列）は低コストモデル／サブエージェント、合成（大量入力・少量出力・発散）は高思考モデル。

## 3. 問いカタログ v0（確定）

### 事実カード（目的 4: 全社でどんなプロジェクトが動いているか）

| ID | 周期 | 問い | ログ上の根拠 |
|---|---|---|---|
| P1 | 週次 | この週、どのプロジェクトで何を進めたか（機能領域・フェーズ・状態） | プロジェクト dir、gitBranch、`git commit -m`、`gh pr create --title`、Edit/Write の対象ファイル |
| P2 | 月次 | そのプロジェクトで使っている技術・外部サービス・AI ツール構成 | 触ったファイルの拡張子・マニフェスト、MCP サーバー名、CLI、Skill 名、CLAUDE.md |

### 意見カード（弁証法の対象）

| ID | 周期 | 目的 | 問い | 極性 | ログ上の根拠 |
|---|---|---|---|---|---|
| Q1 | 週次 | 1 使い方 | 一発で意図が通った依頼の書き方は何か | 正 worked | 少ないターンで commit/PR に到達したセッションの最初の prompt、再利用されている文型 |
| Q2 | 週次 | 1 使い方 | 言い直し・中断が起きた場面で、最初の依頼に何が足りなかったか | 反 failed | `[Request interrupted by user]`、短時間の連続 user ターン、訂正語、同一ファイルへの連続 Edit |
| Q3 | ラウンド | 1 使い方 | 定型化して他人に渡せる手順（コマンド・スキル・hook）は何か | 提案 | `~/.claude/commands|skills|agents`、Skill 利用、毎回付ける前置き |
| Q4 | ラウンド | 2 プロセス | 手戻りが最も大きかった作業はどこで、順序を変えればどう防げたか | 反→提案 | is_error の反復、テスト失敗→成功の回数、EnterPlanMode の遅い登場、compaction |
| Q5 | ラウンド | 2 プロセス | 人間が判断・介入した場面はどこか。必要な介入だったか、仕組みで減らせるか | 問い | ツール呼び出しの却下、`!` の手動コマンド、権限拒否、plan 却下 |
| Q6 | 月次 | 3 チーム | 要件→設計→実装→レビューをどう回したか。AI をどこで使い／使わなかったか | 事実+意見 | フェーズ別スキル利用（/aid 系）、gh コマンドの流れ、PR 単位のセッション構造 |
| Q7 | ラウンド | 3 チーム | レビューや後工程で判明した問題のうち、前倒しで防げたものは何か | 反→提案 | `gh pr view --comments`、レビュー後の修正セッション |
| Q8 | 月次 | 3 チーム | プロジェクト固有に書いたルール（CLAUDE.md / rules / memory）のうち全社共通にできるものは何か | 提案 | CLAUDE.md・`.claude/` への Edit、memory の Why/How to apply |
| Q9 | ラウンド | 4 全社 | 今プロジェクトで詰まっている・リスクと感じていることは何か | 問い | 未解決で終わったセッション、繰り返し調べている話題、memory の落とし穴 |

回し方:
- **毎週**: P1, Q1, Q2 + ラウンドの問い 1 つ（Q3/Q4/Q5/Q7/Q9 から週替わり。合成で出た「次の問い」を優先）
- **月 1 回**（4 週分をまとめて）: P2, Q6, Q8。週次カードを材料に、月末の実行で追加する
- 1 人あたり週 5〜10 枚、15 分以内を上限にする。「該当なし」も 1 枚として提出できる

## 4. Notion の構成（2026-10-13 構築済み）

ページ「Claude Codeまとめ置き場」（Xtoneポータル / 全社エリア / エンジニアリングチーム）配下。

### 4.1 既存「週次 Tips」DB（週 = ラウンド）に足したプロパティ
| プロパティ | 型 | 用途 |
|---|---|---|
| ステータス | select: 募集中 / 合成済み / 共有済み | 週の進行 |
| 今週の問い | multi_select: P1, P2, Q1〜Q9 | その週に答える問い |
| カード | relation → ナレッジカード（双方向） | 件数の rollup 用 |
| 合成テーマ | relation → 合成テーマ（双方向） | |
| カード数 | rollup(count) | 参加状況の把握 |
| まとめ | 週ページ配下の子ページ（合成スキルが生成） | 弁証法レポート |

既存の「投稿者」「期間」「備考」はそのまま使う。個人ページは任意（カード提出で投稿したことになる）。

### 4.2 新規「ナレッジカード」DB
| プロパティ | 型 | 内容 |
|---|---|---|
| カード | title | 付箋の一文（60 字前後） |
| 問い | select: P1, P2, Q1〜Q9 | 問い ID |
| 週 | relation → 週次 Tips | 活動週 |
| 投稿者 | person | 実名 |
| プロジェクト | multi_select（実名） | 提出時に選択肢が増える |
| 極性 | select: worked / failed / proposal / question / fact | 正・反・合の材料 |
| 確度 | select: observed / inferred | ログに直接あるか、推定か |
| タグ | multi_select | prompt, plan-mode, worktree, review, hooks, skill, mcp, testing, git, ci |
| 文脈 | text | どんな状況で（2〜3 文） |
| 根拠 | text | 伏せ字済みの抜粋（300 字以内） |
| 根拠参照 | text | `<session_id>#<uuid>`。本人の手元で辿る用 |
| 合成テーマ | relation → 合成テーマ | 合成スキルが付与 |
| 採用先 | url | 還元された先（スキル名、PR） |
| 公開範囲 | select: internal / public | 社外発信に転用できるか |

### 4.3 新規「合成テーマ」DB（クラスタ）
| プロパティ | 型 | 内容 |
|---|---|---|
| テーマ | title | クラスタ名 |
| 週 | relation → 週次 Tips | |
| 問い | select | |
| カード | relation → ナレッジカード | |
| 件数 / 人数 | rollup | 根拠の強さ |
| 対立 | text | 正と反の要約 |
| 合 | text | 提案 |
| 採否 | select: 検討中 / 採用 / 見送り / 次の問いへ | 共有会で決める |
| 採用先 | url | |

### 4.4 問いカタログ
正本はリポジトリの `knowledge_sharing/questions.yaml`（スキルが読む）。Notion の「問いカタログ v0」ページは閲覧用で、`問い` select の選択肢と ID を揃える。

### 4.5 接続方法
- パイロット: 各自の Claude Code に Notion MCP を接続（OAuth、投稿者 = 本人になる）。`common_development/notion-connections` の既存ノウハウを再利用する
- 代替: 社内インテグレーショントークンで Python（標準ライブラリ）から Notion API を直接叩く。MCP が不安定なときの逃げ道として Phase 1 で用意する
- 週の行が無ければスキルが作る（`2026-W43（10/19〜10/25）` 形式、期間 = 月〜日）

## 5. カードの JSON（スキルの中間データ）

```yaml
card_id: "2026-W43/Q2/toyota/003"
question_id: Q2
week: "2026-W43"
author: "toyota"            # git user.email → Notion user に解決
project: "<実名>"
claim: "付箋に書く一文"
context: "どんな状況で起きたか"
polarity: worked | failed | proposal | question | fact
confidence: observed | inferred
evidence:
  - type: prompt | command | tool_error | memory | session
    ref: "<session_id>#<uuid>"
    excerpt: "伏せ字済みの抜粋"
tags: []
sensitivity: internal | public
```

## 6. ログ収集ロジックの改善（extract v2）

### 6.1 取るシグナル
| シグナル | 取り方 | 使う問い |
|---|---|---|
| セッション索引 | 1 行 1 セッション: id, project, gitBranch, 開始・終了, user ターン数, tool 呼び出し数, compaction 有無, 最終 assistant 要約 | 全部 |
| 中断・却下 | user メッセージの `[Request interrupted by user]` / `... for tool use` と直前の assistant tool_use | Q2, Q5 |
| 言い直し | 連続 user ターンの間隔と訂正語（違う／そうではなく／やっぱり／戻して／もう一度）、同一 file_path への連続 Edit | Q2 |
| エラー反復 | tool_result の is_error、同一エラー文字列の反復、失敗→成功の回数 | Q4 |
| 計画 | EnterPlanMode / ExitPlanMode の位置、plan 却下 | Q4, Q5 |
| 成果 | `git commit -m`、`gh pr create --title`、PR 番号 | P1, Q1, Q6 |
| 技術スタック | Edit/Write の拡張子分布、マニフェスト、MCP サーバー、CLI | P2 |
| ルール変更 | CLAUDE.md / `.claude/` / rules への Edit | Q8 |
| サブエージェント | `<session>/subagents/*.jsonl`、isSidechain | Q3, Q6 |
| 既存 | history.jsonl prompts、memory、harness | Q1, Q3, Q8, Q9 |

### 6.2 出力の形
- `sessions.jsonl`（索引）+ `evidence/<Qid>.json`（問いごとの根拠パック）。Claude は問いごとに根拠パックだけ読む
- カードは evidence の ref を持ち、本人が元セッションを辿れる
- 週次なので `--since` 既定を週の月曜にし、セッションファイルごとに処理済み位置を記録して差分処理する

### 6.3 機密区分
`scan_sensitive.py` の vocabulary を `secrets`（常に消す: トークン・鍵、メール、顧客 PII、クライアント内部ホスト・URL、組織 ID、ホームパス）と `identifiers`（プロジェクト名・リポジトリ名。internal では残す）に分け、`--tier internal|public` で切り替える。既定は internal。

### 6.4 任意: SessionEnd hook
セッション終了時に索引 1 行を `~/.claude/hooks/logs/session_index.jsonl` へ追記しておくと、週次の全文走査が軽くなる。skill_usage_tracker と同じ流儀。

## 7. 合成（knowledge-synthesis）

入力: 週（既定は前週）。手順:
1. 「ナレッジカード」DB から当週のカードを全件取得、重複排除
2. 問いごとに親和図（200 枚以下なら Claude が一括）。クラスタごとにラベル・件数・人数・代表カード
3. 同じクラスタ内の worked と failed、明示的に矛盾する claim を「対立」として抽出
4. 対立ごとに合（両立案・条件分け・仕組み化）と根拠の強さ・反証
5. 次の問い候補
6. 出力: 週ページ配下に「まとめ」子ページ、「合成テーマ」DB に行を作りカードを関連付け、週のステータスを「合成済み」に
7. 月末: P1/P2 からプロジェクトマップ（プロジェクト × 週 × 領域 × 技術）、Q6/Q8 の月次合成

運用: パイロット中は手動実行。安定したらスケジュールタスク（例: 火曜 10:00）で自動化。共有会（隔週 30 分）で採否を決め、採用は ai_development_tools に PR。

## 8. 参加の設計
- 提出前に本人がカードを編集・削除できる
- 実名運用なので、カードは「自分の作業」について書く。他人の作業や判断を評価する内容は書かない。failed はプロセスの話として書く
- 合成レポートはパターンを並べる。個人別の件数ランキングは出さない
- evaluate-session（採点）とは別物であることを README・SKILL.md・Notion の使い方に明記する

## 9. パイロット計画

| 週 | 内容 | 完了条件 |
|---|---|---|
| W42（10/12〜10/18） | 準備。Notion DB 構築（完了）。`knowledge-cards` v0（既存 extract を流用 + 問いカタログ + カード下書き + 自己確認 + Notion 提出）。参加者 5〜6 名に 15 分の説明、Notion MCP 接続確認 | 参加者全員が手元でスキルを起動できる |
| W43（10/19〜10/25） | ラウンド 1。初回は `--since 14d` で W42〜W43 を対象に、10/27（月）までに提出。合成は手動で実行し、まとめページを作る。問いごとに「カードが書けたか／対立が出たか」を評価して問いを改訂 | まとめページ 1 本、問いカタログ v0.1 |
| W44（10/26〜11/1） | ラウンド 2。extract v2（中断・言い直し・エラー反復・成果）を投入。`knowledge-synthesis` v0 で合成を半自動化 | カードの根拠が evidence ref 付きで出る |
| W45（11/2〜11/8） | ラウンド 3。評価と全員展開の判断。参加率、1 人あたりの所要時間、問いごとのカード数、対立の検出数、採用された合の数、参加者の所感 | 展開可否と v1 の改修リスト |
| W46〜（任意） | ラウンド 4。途中参加者を含めて回す。スケジュールタスク化、月次ロールアップ（P2/Q6/Q8）を 1 回試す | |

### 成功指標
- 参加率と 1 人あたり所要時間（15 分以内）
- 1 問あたりのカード数、対立が検出された問いの割合
- 合の採用数と還元先の数
- 採用後の変化（Q2 の言い直しエピソード数の推移、P2 での採用スキル利用率）

## 10. 進捗と次のアクション（2026-10-13 更新）

| 項目 | 状態 |
|---|---|
| Notion: 「ナレッジカード」「合成テーマ」DB 作成、「週次 Tips」にステータス・今週の問い・カード数を追加、使い方 callout 更新、「問いカタログ v0」ページ | 完了（§4 の構成どおり。ID は実装計画 doc に記載） |
| 実装計画（Claude Code 用のコンテキストと Phase 1〜3 のタスク） | 完了。Claude Doc「ナレッジカード実装計画」 |
| `questions.yaml` と `knowledge-cards` v0 の実装（ai_development_tools に PR） | 未着手。実装計画の Phase 1 に従う |
| 参加者の決定と説明会の日程 | 未着手 |

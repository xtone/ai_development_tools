# knowledge-cards 設計スペック

作成日: 2026-10-13
対象: プラグイン `knowledge-sharing` の新スキル `knowledge-cards`（v0.2.0）
上位文書: `docs/superpowers/specs/2026-10-13-knowledge-dialectic-plan.md`（計画 v0.1）、Claude Doc「ナレッジカード実装計画」の Phase 1

## 目的

Claude Code のセッション記録から、問いカタログの問いに答える「カード」を下書きし、本人の確認と機密スキャンを経て Notion の「ナレッジカード」DB に提出する。弁証法的な合成（`knowledge-synthesis`）の入力を、週 1 回・1 人 15 分で集められるようにする。

## 利用者と成功条件

- 利用者: パイロットに参加するシニアエンジニア 5〜6 名。週 1 回、前週分を提出する
- 成功条件: `/knowledge-sharing:knowledge-cards` を 1 回実行すると、15 分以内に、機密スキャン 0 件のカードが Notion に入り、週の行に投稿者として載る

## スコープ外

- extract v2（中断・言い直し・エラー反復などのシグナル、`sessions.jsonl` と `evidence/<Qid>.json`）。Phase 2 で扱う
- `knowledge-synthesis`（合成）。Phase 3 で扱う。ラウンド 1 は手動で合成する
- 自動提出。カードは必ず本人が見てから提出する
- 個人の採点や評価（`evaluate-session` の領域）

## 決定事項

| 項目 | 決定 |
|---|---|
| 問いカタログの正本 | `knowledge_sharing/questions.json`。標準ライブラリだけで読むため YAML にしない |
| スクリプトの共有 | スキルごとにコピーして自己完結にする。`session-tips-digest` の `extract_sessions.py` と `scan_sensitive.py` を `knowledge-cards/scripts/` にコピーし、そこで拡張する |
| 設定の置き場 | `questions.json` と `notion.json` はプラグイン直下。SKILL.md からは `<skill-dir>/../../` で参照する |
| 週の定義 | ISO 週（月曜始まり）。タイトルは `2026-W43（10/19〜10/25）` |
| P1 の材料 | 抽出スクリプトに `commits[]` と `prs[]` を足す（Phase 2 の `commits` / `prs` シグナルの前倒し） |
| 根拠参照 | プロンプトに `session_id` を付け、`ref` を `<session_id>@<時刻>` にする |
| ラウンド 1 の rotation | Q3（既存の harness 情報だけで答えられる） |

## プラグイン構成

```
knowledge_sharing/
├── .claude-plugin/plugin.json        # 0.2.0
├── README.md                         # 2 スキルの使い分け、実名運用の約束
├── questions.json                    # 問いカタログ（正本）
├── notion.json                       # DB / data source ID
└── skills/
    ├── session-tips-digest/          # description に「カードから Tips 文書を作る下流」を追記
    └── knowledge-cards/
        ├── SKILL.md
        ├── scripts/
        │   ├── extract_sessions.py   # コピー + commits / prs / prompts[].session_id
        │   ├── scan_sensitive.py     # コピー + --tier internal|public
        │   ├── cards.py
        │   ├── notion_submit.py
        │   └── tests/
        ├── references/
        │   ├── card-writing.md
        │   └── notion-submit.md
        └── templates/cards.md
```

ルートの `.claude-plugin/marketplace.json` の `knowledge-sharing` を 0.2.0 にし、description に「週次のナレッジカード提出」を足す。

## 起動と引数

```
/knowledge-sharing:knowledge-cards
/knowledge-sharing:knowledge-cards --since 14d --dry-run
/knowledge-sharing:knowledge-cards --week 2026-W43 --questions P1,Q1,Q2,Q3
```

| 引数 | 既定 | 意味 |
|---|---|---|
| `--week` | 前の ISO 週 | 対象週。`2026-W43` 形式 |
| `--since` | 対象週の月曜 | 抽出の開始日。初回参加者には `14d` を案内する |
| `--questions` | Notion の週の行の `今週の問い`。無ければ `weekly` + `rotation` の 1 つ | 答える問い |
| `--projects` | 全部 | 対象プロジェクト名の部分一致 |
| `--out` | `cards/` | 成果物ディレクトリ。作業ファイルは `<out>/.work/` |
| `--tier` | `internal` | 機密スキャンの区分 |
| `--dry-run` | なし | Notion に書かない。送る内容を表示する |
| `--no-notion` | なし | `cards.jsonl` と Markdown を作って終える |

## 処理の流れ

1. **準備**: `cards.py week` で対象週の ID・月曜・日曜・タイトルを得る。`cards.py plan` で問いを決める。Notion の週の行に `今週の問い` があればそれを優先する。段取りを 1 行で伝える
2. **抽出**: `extract_sessions.py --since <since> --out <out>/.work/sessions.json`
3. **下書き**: Claude が問いごとに `sessions.json` の該当部分（`card-writing.md` の対応表）を読み、`draft_hint` に従って `<out>/.work/cards.jsonl` を書く。`cards.py validate` で検査し、エラーが 0 になるまで直す。`cards.py render` で `<out>/cards-<week>.md` を出す
4. **自己確認**: 問いごとの枚数と claim を表示し、AskUserQuestion で「提出する / ファイルを直したので読み直す / 中止」を聞く。読み直しは `cards.py parse` で Markdown から JSONL に戻し、再び validate と render を通す
5. **機密ゲート**: `scan_sensitive.py <out>/cards-<week>.md --vocab <out>/.work/sessions.json --tier internal [--allow-file <out>/.work/allow.txt]`。0 件になるまで先に進まない
6. **提出**: `cards.py dedupe` で提出済みを除き、`cards.py to-notion` で create-pages 用のプロパティを出す。`references/notion-submit.md` の手順で、週の行の確保 → 投稿者の解決 → create-pages → 週の行の投稿者追加を行う。投稿者は Notion MCP の接続ユーザー（get-self）にする。git のメールアドレスで検索すると、Notion アカウントのメールアドレスが違う場合に別アカウントが返ることを実環境で確認した（2026-10-13）。成功したカードは `cards.py mark-submitted` で `submitted.jsonl` に記録する。`--dry-run` では Notion にも `submitted.jsonl` にも書かない
7. **完了報告**: 問いごとの枚数、週の行の URL、スキャン結果、開始と終了の時刻、`.work/` をコミットしないことの注意

Notion MCP が無い環境では、`notion_submit.py`（`NOTION_TOKEN` で REST API を叩く）を案内する。

## questions.json

Claude Doc の YAML と同じ内容を JSON にする。トップレベルは `version`、`cadence`（`weekly` / `rotation` / `monthly`）、`limits`、`questions`。各問いは `id`、`kind`（fact / opinion）、`goal`、`text`、`polarity`（既定値）、`allowed_polarities`（既定値以外に許す値。計画で「反→提案」とした Q4 と Q7 は `["proposal"]`、他は空）、`signals`、`draft_hint`。

`cards.py plan --week <id>` は `weekly` に rotation の 1 つを足して返す。rotation の起点を `cadence.rotation_epoch: "2026-W43"` で持ち、`rotation[(起点からの週数) % len(rotation)]` で選ぶ。2026-W43 は Q3 になる。起点より前の週も同じ式（負の剰余は Python の `%` のまま）で選ぶ。

## notion.json

```json
{
  "page_id": "3f2ceb782fa380c3a2fbc74cdd435f47",
  "weeks": {"database_id": "031c04a116d14f6c95e5edbedf3bafcd", "data_source": "collection://dc4c6a28-be46-4cf5-95d7-f35c67e2f80a"},
  "cards": {"database_id": "a764d458369c44f6959560a62a8d37f9", "data_source": "collection://1a94fd0a-157f-40ee-b7f4-5d03e51c157c"},
  "themes": {"database_id": "e643072d2f3641e9892a7a7009bd6736", "data_source": "collection://d0925f00-0e5a-4a7d-affa-3825a042f4b1"}
}
```

## カードの JSON（`cards.jsonl` の 1 行）

```json
{
  "card_id": "2026-W43/Q2/y.toyota/003",
  "question_id": "Q2",
  "week": "2026-W43",
  "week_range": ["2026-10-19", "2026-10-25"],
  "author_email": "<git config user.email>",
  "project": "ai_development_tools",
  "claim": "付箋の一文（20〜80 字）",
  "context": "どんな状況で起きたか（2〜3 文）",
  "polarity": "failed",
  "confidence": "observed",
  "evidence": [
    {"type": "prompt", "ref": "<session_id>@2026-10-20T10:12", "excerpt": "伏せ字済みの抜粋"}
  ],
  "tags": ["prompt"],
  "sensitivity": "internal",
  "status": "draft",
  "notion_url": null
}
```

- `card_id` の作者部分はメールの `@` より前。連番は問いごとに 3 桁
- `status`: `draft` / `approved` / `dropped` / `submitted`
- `evidence[].type`: `prompt` / `command` / `commit` / `pr` / `memory` / `harness` / `session`

### 根拠参照（Phase 1）

| type | ref | 出どころ |
|---|---|---|
| prompt | `<session_id>@<時刻>`（session_id が無ければ `prompt@<時刻>`） | `prompts[]` |
| command | `<session_id>@<時刻>` | `bash_samples[]` |
| commit / pr | `<session_id>@<時刻>` | `commits[]` / `prs[]` |
| memory | `memory:<project>/<name>` | `memories[]` |
| harness | `harness:<種類>/<名前>` | `harness` |
| session | `<session_id>#<uuid>` | Phase 2 で使う |

## validate の規則

エラー（終了コード 1）:

- 必須キー（`question_id`、`week`、`project`、`claim`、`context`、`polarity`、`confidence`、`evidence`、`sensitivity`、`status`）が無い
- `question_id` が questions.json に無い
- `claim` が 20〜80 文字の範囲外、または「について」「に関して」で終わる。ただし「該当なし: 」で始まるカードは長さの下限を問わない
- `evidence` が空。`type` が上の表に無い。`excerpt` が 300 文字を超える。`type: session` で `ref` が `<session_id>#<uuid>` 形式でない
- `polarity` が問いの既定値でも `allowed_polarities` でもない
- `confidence` が observed / inferred 以外、`sensitivity` が internal / public 以外
- `card_id` の重複

警告（終了コードは変えない）:

- 1 問あたり 1 人 4 枚以上、1 週 10 枚超（questions.json の `limits`）
- `tags` に Notion の選択肢に無い値がある（提出すると選択肢が増える）

他人の名前を評価の文脈で書かないことは機械では検査しない。`card-writing.md` の禁止事項と自己確認の案内で扱う。

## cards-<week>.md の形（`templates/cards.md`）

```markdown
# ナレッジカード 2026-W43（10/19〜10/25）

<!-- 消したいカードは節ごと削除するか、状態を dropped にする。author_email はここに出さない -->

## Q2 言い直し・中断が起きた場面で、最初の依頼に何が足りなかったか

### 完了条件を書かずに依頼し、テストの範囲で 2 回言い直した

- id: 2026-W43/Q2/y.toyota/001
- 状態: draft
- 極性: failed / 確度: observed / 公開範囲: internal
- プロジェクト: ai_development_tools
- タグ: prompt, testing

文脈（複数行可）

**根拠**

- prompt `<session_id>@2026-10-20T10:12`: 抜粋
```

`parse` は `### ` を claim、メタ行をキーと値、`**根拠**` までを文脈、その後の箇条を evidence として読む。`id` で JSONL の元カードと突き合わせ、Markdown に無いキー（`author_email`、`week_range`、`notion_url`）は元カードから引き継ぐ。`id` の無い新しい節は新規カードとして採番する。元 JSONL にあって Markdown に無いカードは `dropped` にする。JSONL → MD → JSONL で値が変わらないことをテストで固定する。

## to-notion の出力

`cards.py to-notion <cards.jsonl> --week-url <URL> --author <user://id|me>` が、`status` が `approved` か `draft` のカードについて次の配列を出す。`dropped` と `submitted` は出さない。

```json
[{"card_id": "...", "properties": {
  "カード": "claim",
  "問い": "Q2",
  "週": ["<週の行の URL>"],
  "投稿者": ["<user id>"],
  "プロジェクト": ["ai_development_tools"],
  "極性": "failed", "確度": "observed", "公開範囲": "internal",
  "タグ": ["prompt"],
  "文脈": "...",
  "根拠": "excerpt を改行で連結し 300 字で切る",
  "根拠参照": "ref を ', ' で連結"
 }, "content": "## 文脈\n...\n## 根拠\n...\n## 根拠参照\n..."}]
```

`--author me` のときは `投稿者` を出さない（MCP では接続ユーザーとして作られ、後から週の行で本人を足す）。

## 重複排除

キーは `(question_id, project, normalize(claim))`。`normalize` は NFKC、空白と句読点の除去、小文字化。`<out>/.work/submitted.jsonl` に `{"key", "card_id", "notion_url", "submitted_at"}` を追記する。`dedupe` は既に記録のあるキーのカードを `submitted` にして返す。

## scan_sensitive.py の tier

- `VOCAB_KEYS` を `SECRET_VOCAB = ("hosts",)` と `IDENTIFIER_VOCAB = ("projects", "repos", "users")` に分ける。`users` は OS のユーザー名で、カード id の著者部分（`y.toyota` など）と重なる。internal では著者を実名で残すため、public のときだけ検査する。ホームパスは固定パターン `home_path` で常に止まる
- セッション ID（UUID）の中の 10 桁以上の数字列は `numeric_id` として扱わない（根拠参照に UUID が入るため）
- `--tier internal`（既定）: `SECRET_VOCAB` だけを語彙として検査する
- `--tier public`: 両方を検査する
- 固定パターン（トークン、メール、ID、ホームパス、Notion URL）は tier に関係なく常に検査する。`redact()` は変えない
- `load_vocab(path, tier="public")` の既定値は public にし、`session-tips-digest` 側の挙動と揃える

## extract_sessions.py の追加

- `prompts[]` に `session_id`（`history.jsonl` の `sessionId`）を足す
- `commits[]`: Bash の `git commit` から `-m "..."` / `-m '...'` / heredoc の 1 行目をタイトルとして取る。`{"time", "project", "session_id", "title"}`。タイトルは `redact()` して 200 文字まで
- `prs[]`: `gh pr create` の `--title` を取る。同じ形
- `counts` に `commits` と `prs` を足す
- 既存のキーと挙動は変えない

## notion_submit.py（代替経路）

- `NOTION_TOKEN` と `notion.json` を使い、`urllib` で REST API を叩く
- サブコマンド: `ensure-week`（`週` の前方一致で検索、無ければ作成して URL を返す）、`submit`（`to-notion` の出力を受けて `POST /v1/pages`）、`add-author`（週の行の `投稿者` に追加）
- 投稿者はメールから `GET /v1/users` で解決する
- `--dry-run` でリクエストの本文だけを表示する
- 失敗は終了コード 1 と stderr に 1 行。トークンは出力しない

## エラー処理

- スクリプトは標準ライブラリのみ、`python3 -I` で実行する。入力エラーは終了コード 2、検査で問題ありは 1
- 壊れた JSONL 行は読み飛ばし、件数を stderr に出す
- Notion MCP の呼び出しが失敗したら、そのカードを `submitted.jsonl` に入れずに残し、再実行で送れるようにする

## テスト

`uv run --no-project --with pytest python -m pytest -q -p no:cacheprovider` で走らせる。

- `week`: 2026-10-13 の前の週が 2026-W41、`2026-W43` のタイトル、`2026-W53` の翌週が `2027-W01`、`2027-W01` の月曜が 2027-01-04
- `plan`: weekly + rotation、2026-W43 で Q3
- `validate`: 各エラー条件 1 件ずつと、正常なカード
- `render` → `parse`: 往復で同値（複数 evidence、日本語、`該当なし`）。節の削除で `dropped`、新しい節で新規採番
- `to-notion`: プロパティの形、根拠の 300 字切り、`dropped` の除外、`--author me`
- `dedupe`: 正規化で同一とみなすこと
- `scan_sensitive --tier internal`: プロジェクト名・ユーザー名を通し、トークン・メール・ホスト名を止める。`--tier public` はプロジェクト名を止める。UUID の中の数字列は `numeric_id` にしない
- `extract_sessions`: `commits[]` / `prs[]` / `prompts[].session_id`
- `notion_submit`: `--dry-run` のペイロード（ネットワークに出ない）

## 受け入れ確認

1. この環境で `--since 14d --dry-run` を最後まで通す。問いごとにカードが出て、スキャンが 0 件
2. `--dry-run` なしで 1 回提出し、Notion の「ナレッジカード」に行ができ、週の行に投稿者が載ることを確認する（実行前にユーザーの了承を取る）

## 実名運用の約束

README・SKILL.md に同じ文を置く。

- カードは自分の作業について書く。他人の作業や判断を評価する内容は書かない。failed はプロセスの話として書く
- 提出前に本人がカードを編集・削除できる。削ったことは記録しない。自動提出はしない
- 合成レポートはパターンを並べる。個人別の件数ランキングは出さない
- この仕組みは課題の抽出とアイデア創出のためのもので、人事評価には使わない
- Notion のページは全社エリアにある。エンジニア以外も読む前提で書く

## 改訂（2026-10-13、v0.2.1）

初回の実提出（W41）で見つかった 2 点を直した。

- **Notion の選択肢**: Notion MCP の create-pages は、multi_select に選択肢に無い値を渡すと全件を拒否し、選択肢は自動で増えない。提出前に `cards.py options` で足りない選択肢と `ALTER COLUMN ... SET MULTI_SELECT(...)` 文を出し、update-data-source で足す。この文は既存の選択肢を色ごとすべて並べる（並べ忘れると消えるため、手で書かない）。REST API（`notion_submit.py`）は選択肢を自動で足すので不要
- **抽出の期間**: `extract_sessions.py` に `--until`（その日を含む）と `--tz`（既定はローカル）を足した。日付は `--tz` のその日の 0 時として解釈する。prompt、ツールの利用回数、Bash の例、commit、PR を期間で絞る。memory は絞らない。SKILL.md の既定は、`--since` が対象週の月曜、`--until` が日曜

## 改訂（2026-10-13、v0.2.2）: カードにしない話題

人事評価・処遇と、Xtone・PKSHA の経営に関する話題は、カードにしない。経営層のメンバーが使ったときに、社内秘の情報が全社エリアに出ないようにするため。3 段で防ぐ。

1. **抽出**: `extract_sessions.py` は、prompt または commit・PR のタイトルが `confidential_topics.json` の語に当たるセッションを、まるごと外す（prompt、commit、PR、ツールの利用回数、Bash の例）。memory は本文まで見て、当たるものを外す。出力の `excluded` には件数と話題ごとのセッション数だけを入れる。ファイルの中身などツールの入力は判定に使わない。実データで試すと、コードや顧客の文書にある「昇格」「代表取締役」「予実管理」で、普段の開発セッションまで外れたため
2. **下書き**: card-writing.md と SKILL.md に禁止事項として書く
3. **検査**: `cards.py validate` は、提出するカードの claim・文脈・プロジェクト名・根拠の抜粋のどれかが当たればエラーにする

語は、一般語（評価、予算、昇格、退職、IR、社名だけ）を避けて複合語で書く。個人で足したい語は `~/.claude/knowledge-cards/confidential_topics.json` に置き、同じ id の話題に合流させる。

fail-open を避けるため、次の 2 点を決めた（コミット後のセキュリティレビューの指摘による）。

- セッションの判定は、期間の外も含めて行う。`history.jsonl` 全体の prompt と、期間に関わるセッションログの全行（ユーザー発言、commit・PR のタイトル）を見る。期間の前に評価の話をしたセッションの続きや、`sessionId` の無い古い履歴しかないセッションも外す。スキル本文などシステムが差し込む文章（`isMeta`、`<` で始まる差し込み）は数えない。knowledge-cards の SKILL.md 自身がこの話題の語を含むため
- 語が 1 つも読めなければ、抽出と検査はエラーで止まる

直近 30 日の実データで除外されたのは 4 セッションで、どれもこの機能自体を作ったセッションだった。普段の開発セッションと memory の誤除外は 0 件。顧客アプリの「退職者処理」、コードの「評価結果」、base64 の文字列は当たらないことを確認した。

### 強い語と要確認の語（2 段）

誤除外を減らすために語を複合語へ絞ったところ、セキュリティレビューで「統制の後退」と指摘された。「退職の件で」「昇格の相談」のような書き方がすり抜けるため。誤除外と取りこぼしの両方を避けるため、語を 2 段にした。

| 段 | 例 | 抽出 | validate |
|---|---|---|---|
| 強い語（`patterns`） | 人事評価、評価面談、取締役、経営、決算、M&A | 必ず外す。戻せない | エラー。通せない |
| 要確認の語（`review_patterns`） | 昇格、降格、ボーナス、自己評価、評価結果、退職、IR | 既定で外す。`excluded.review` にセッション id・プロジェクト・時刻・当たった語だけを出す。本人が確認したセッションだけ `--include-sessions` で戻す | エラー。本人が確認した語だけ `--allow-term` で通す |

確認の手間を抑えるため、SKILL.md は要確認の一覧を「プロジェクト × 語」でまとめて 1 回の質問で聞く。直近 30 日の実データでは要確認が 33 セッションあり、ほぼ ai-delivery と ourpick-mt-proto の「昇格」「降格」（業務用語）で、数グループにまとまった。W41 の 1 週間では 0 件だった。戻したセッションでも、強い語を含む prompt は外したままにする。

戻す経路にも抜け道があったので塞いだ（2 回目のセキュリティレビューと advisor の指摘による）。

- セッションごとに、当たった要確認の語を全部記録して本人に示す（`excluded.review[].words` はリスト）。以前は最初の 1 語だけを示していたので、「昇格」を見て戻したセッションの「退職の相談」まで通っていた
- 戻したセッションの prompt も、本人に示した語だけを許可して判定し直す
- `blocked()` は、許可した語を 1 語ずつ消して判定し直す。1 語の許可で、同じ文の別の要確認の語や強い語が隠れないようにするため
- 要確認の語で外した memory は、名前と語を `excluded.review_memories` に出し、`memory:<project>/<name>` で戻せるようにした

### 脅威モデル（2026-10-13 追記）

この判定が防ぐのは、うっかりの漏洩（経営層の prompt、Claude の下書き、Notion 上で書き換えられたカード）である。最後の歯止めは、Notion に書く前に必ずある本人の確認。記号・空白・記法・見えない文字で語を分けて意図的にすり抜ける書き方は、元の情報と書き込み権限を持つ本人にしかできないので、想定の外に置く。

コミット後のセキュリティレビューでは、この種類の指摘（見えない文字、Markdown の記法、区切り記号による分割）が 3 回続いた。判定は、書いたままの文字列・Notion で表示される文字列・日本語の文字の間の区切りを詰めた文字列の 3 つに当てるところまで広げた。それより先の同じ種類の指摘は、既知の限界として扱う。型の取り違えや、検査を通らない書き込み先のような別の種類の穴は直す。

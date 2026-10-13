# Knowledge Sharing

Claude Code の利用記録から、チームで共有できる知見を抽出・検証・公開するスキル群です。

## インストール

```bash
/plugin marketplace add xtone/ai_development_tools
/plugin install knowledge-sharing@xtone-ai-development-tools
```

## スキル一覧

| スキル | 説明 |
|--------|------|
| **knowledge-cards** | 週ごとの問いに答える「ナレッジカード」をセッション記録から下書きし、本人の確認と機密スキャンを経て Notion に提出する |
| **knowledge-synthesis** | 週ごとに集まったカードを束ね、対立から合（提案）と次の問いを出して、Notion の合成テーマとまとめページに書き込む |
| **session-tips-digest** | 過去のセッション記録から共有できる運用 Tips を抽出し、一次情報で裏付けを取って Markdown・Artifact・Notion に公開する。カードや記録から Tips 文書を作る下流工程 |

### 使い分け

| やりたいこと | スキル |
|---|---|
| 毎週、問いへの答えをカードで提出し、チームの合成（正・反・合）に回す | knowledge-cards |
| 集まったカードを週ごとに合成し、対立から提案と次の問いを出す | knowledge-synthesis |
| 自分の記録から、社外にも出せる Tips 文書を書いて公開する | session-tips-digest |
| セッション 1 本に無駄が無かったか採点する | common-development の evaluate-session |

## knowledge-cards

### 使い方

```
/knowledge-sharing:knowledge-cards
/knowledge-sharing:knowledge-cards --since 14d --dry-run
/knowledge-sharing:knowledge-cards --week 2026-W43 --questions P1,Q1,Q2,Q3
```

| 引数 | 既定 | 意味 |
|---|---|---|
| `--week` | 前の ISO 週 | 対象週。`2026-W43` 形式 |
| `--since` | 対象週の月曜 | 抽出の開始日。初めて参加するときは `14d` |
| `--until` | 対象週の日曜 | 抽出の最終日（その日を含む）。「月〜金」なら金曜を指定する |
| `--tz` | `local` | 日付を解釈するタイムゾーン（`+09:00` など） |
| `--questions` | Notion の週の行の「今週の問い」、無ければ cadence | 答える問い |
| `--projects` | 全部 | 対象プロジェクト名の部分一致（カンマ区切り） |
| `--out` | `cards/` | 成果物ディレクトリ |
| `--tier` | `internal` | 機密スキャンの区分。社外に転用するときは `public` |
| `--dry-run` | なし | Notion に書かず、送る内容を表示する |
| `--no-notion` | なし | カードの確認と機密スキャンまでで終える |

### 流れ

1. 対象週と問いを決める（問いカタログはプラグイン直下の `questions.json`）
2. `~/.claude/` から prompt、commit・PR のタイトル、ツールの利用回数、memory を抽出する（秘密情報は伏せ字）
3. 問いごとにカードを下書きし、形式と品質を検査する
4. `cards/cards-<週>.md` を本人が確認し、直す・消す・足す
5. 機密スキャン（internal: プロジェクト名は残し、トークン・メール・ホスト名などを止める）が 0 件になるまで直す
6. カードのプロジェクト名とタグのうち Notion の選択肢に無いものを足してから、「ナレッジカード」DB に提出し、「週次 Tips」の週の行に投稿者として載る

### 実名運用の約束

- カードは自分の作業について書く。他人の作業や判断を評価する内容は書かない。failed はプロセスの話として書く
- 提出前に本人がカードを編集・削除できる。削ったことは記録しない。自動提出はしない
- 合成レポートはパターンを並べる。個人別の件数ランキングは出さない
- この仕組みは課題の抽出とアイデア創出のためのもので、人事評価には使わない
- Notion のページは全社エリアにある。エンジニア以外も読む前提で書く

### カードにしない話題

人事評価・処遇（評価、査定、給与、賞与、昇格要件、1on1 など）と、Xtone・PKSHA の経営（経営会議、役員、決算、業績、事業計画、M&A、組織変更など）に関する話題は、カードにしません。経営層のメンバーが使ったときに、社内秘の情報が全社エリアの Notion に出ないようにするためです。

- 抽出の段階で、prompt または commit・PR のタイトルがこの話題に当たるセッションを、まるごと外します。期間の外の発言も含めて判定し、残るのは外した件数だけです
- 語は 2 段です。強い語（人事評価、取締役会など）に当たると必ず外れます。要確認の語（昇格、退職、IR など業務用語でも使う語）に当たると既定で外れ、本人が人事・経営の話ではないと確認したセッションだけ戻せます（スキルがプロジェクトと語でまとめて聞きます）
- 判定に使う語が読めないときは、抽出も検査もエラーで止まります
- それでもカードに書かれた場合は、検査（validate）がエラーにして提出させません
- 判定に使う語はプラグイン直下の `confidential_topics.json` にあります。自分だけ足したい語は `~/.claude/knowledge-cards/confidential_topics.json` に同じ形式で置いてください

### 成果物

| パス | 内容 |
|---|---|
| `cards/cards-<週>.md` | 確認・修正用のカード一覧 |
| `cards/.work/cards.jsonl` | カードの正本 |
| `cards/.work/submitted.jsonl` | 提出済みのカード（再実行で二重に送らない） |
| `cards/.work/` | 作業ファイル。個人の記録を含むのでコミットしない |

### 必要環境

- Python 3.10 以上（標準ライブラリのみ）
- Notion MCP（提出）。使えない環境では社内インテグレーショントークンを `NOTION_TOKEN` に入れて `notion_submit.py` で提出する

### 設定ファイル

| ファイル | 内容 |
|---|---|
| `questions.json` | 問いカタログの正本（問い、既定の極性、下書きの指示、週ごとの回し方） |
| `notion.json` | 提出先の Notion DB と data source の ID |
| `confidential_topics.json` | カードにしない話題（人事評価・処遇、経営）を判定する語 |

## session-tips-digest

### 使い方

```
/knowledge-sharing:session-tips-digest
/knowledge-sharing:session-tips-digest --since 7d --projects my-app
/knowledge-sharing:session-tips-digest --artifact-url https://claude.ai/artifact/<id>
/knowledge-sharing:session-tips-digest --notion <Notion ページの URL> --no-research
```

| 引数 | 既定 | 意味 |
|---|---|---|
| `--since` | `30d` | 抽出期間。`7d` や `2026-09-01` も受ける |
| `--projects` | 全部 | 対象プロジェクト名の部分一致（カンマ区切り） |
| `--out` | `tips/` | 成果物ディレクトリ |
| `--artifact-url` | なし | 既存 Artifact を更新する |
| `--notion` | なし | 指定した Notion ページの配下に書き出す |
| `--no-research` | なし | 一次情報の調査を省略する |

### 流れ

1. `~/.claude/` の履歴・セッションログ・memory を集計する（設定値やトークンは出力しない）
2. 共有できる Tips を選び、案件名や固有値を伏せて書く
3. 機密スキャンで 0 件になるまで直す
4. 公式ドキュメントや論文で各 Tips を裏付ける、修正する、範囲を狭める
5. HTML に変換して Artifact として公開する（指定があれば Notion にも書き出す）

### 成果物

| パス | 内容 |
|---|---|
| `tips/claude-code-tips.md` | Tips 本体 |
| `tips/claude-code-tips-references.md` | 一次情報との対応表 |
| `tips/dist/index.html` | Artifact の元ファイル |
| `tips/.work/` | 作業ファイル。個人の記録を含むのでコミットしない |

### 必要環境

- Python 3.10 以上（標準ライブラリのみ）
- 任意: natural-japanese プラグイン（文章の lint）、Notion MCP（Notion への書き出し）

### evaluate-session との違い

| スキル | 対象 | 目的 |
|---|---|---|
| common-development の evaluate-session | セッション 1 本 | 無駄の有無を採点する |
| session-tips-digest | 期間内の全セッション | 共有できる知見を抜き出す |

## knowledge-synthesis

週ごとに集まったカードを束ね、正（worked）と反（failed）の対立から合（提案）を出し、次の問いを決めて、Notion の「合成テーマ」DB と週の行の配下の「まとめ」ページに書き込みます。v0 は週次だけで、月次（P2・Q6・Q8 とプロジェクトマップ）は対象外です。

### 使い方

```
/knowledge-sharing:knowledge-synthesis
/knowledge-sharing:knowledge-synthesis --week 2026-W43 --dry-run
```

| 引数 | 既定 | 意味 |
|---|---|---|
| `--week` | 前の ISO 週 | 合成する週 |
| `--out` | `synthesis/` | 成果物ディレクトリ。作業ファイルは `<out>/.work/` |
| `--dry-run` | なし | Notion に書かず、書き込む内容を表示する |

### 流れ

1. Notion から週のカードを読み出し、`load_cards.py` で正規化する（投稿者は匿名のラベルにし、重複を束ね、強い語に当たるカードは外す）
2. Claude が意見カードを問いをまたいで束ね、対立・合・次の問いを書く。根拠の強さはスクリプトが数える
3. `synth.py` で検査し、まとめを作り、機密スキャンと話題判定をかける
4. 下書きを確認してから、合成テーマ・まとめページを作り、週の行を「合成済み」にする。同じ週の合成テーマが既にあれば止まる

機密スキャナと話題判定は、同じプラグインの knowledge-cards のスクリプトを使います。

| パス | 内容 |
|---|---|
| `skills/knowledge-synthesis/references/synthesis-method.md` | 合成の手順と判断基準 |
| `skills/knowledge-synthesis/templates/summary.md` | 「まとめ」ページの形 |

要点は 3 つです。

- 意見カードは問いをまたいで束ねる。問いごとに極性が固定されているため、正と反が別の問いに分かれて届くからです
- 合には、根拠の強さ（人数・プロジェクト数・枚数）と反証を必ず添える
- 個人別の件数や「誰が何を失敗した」は書かない

## 開発

```bash
cd knowledge_sharing/skills/session-tips-digest/scripts
uv run --no-project --with pytest python -m pytest -q -p no:cacheprovider
cd ../../knowledge-cards/scripts
uv run --no-project --with pytest python -m pytest -q -p no:cacheprovider
cd ../../knowledge-synthesis/scripts
uv run --no-project --with pytest python -m pytest -q -p no:cacheprovider
```

`knowledge-cards` の `extract_sessions.py` と `scan_sensitive.py` は `session-tips-digest` からコピーして拡張したもの（スキルごとに自己完結させるため）。共通の修正は両方に入れる。

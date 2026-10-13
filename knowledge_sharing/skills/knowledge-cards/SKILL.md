---
name: knowledge-cards
description: Claude Code のセッション記録（~/.claude の履歴・セッションログ・memory）から、週ごとの問い（questions.json）に答える「ナレッジカード」を下書きし、本人が確認・修正したうえで機密スキャンを通し、Notion の「ナレッジカード」DB に提出する。「今週のカードを出して」「ナレッジカードを提出したい」「週次の振り返りカードを作って」などの依頼で使う。週次のカード提出であり、個人の採点や評価ではない（セッション 1 本の採点は evaluate-session の領域）。
---

# Knowledge Cards

自分の Claude Code の記録から、その週の問いへの答えを付箋（カード）として下書きし、本人が確かめてから Notion に提出する。集まったカードは週次の合成（正・反・合の整理）の材料になる。1 回 15 分以内で終えることを目標にする。

成果物は 3 つ。

- `<out>/cards-<week>.md`: 本人が確認・修正するカード一覧
- `<out>/.work/cards.jsonl`: カードの正本（1 行 1 カード）
- Notion「ナレッジカード」DB の行と、「週次 Tips」DB の週の行への投稿者の追加

## 実名運用の約束

カードはプロジェクト名と著者名を実名のまま全社エリアの Notion に置く。始める前にユーザーに 1 度だけ伝える。

- カードは自分の作業について書く。他人の作業や判断を評価する内容は書かない。failed はプロセスの話として書く
- 提出前に本人がカードを編集・削除できる。削ったことは記録しない。自動提出はしない
- 合成レポートはパターンを並べる。個人別の件数ランキングは出さない
- この仕組みは課題の抽出とアイデア創出のためのもので、人事評価には使わない
- Notion のページは全社エリアにある。エンジニア以外も読む前提で書く

## 引数

`$ARGUMENTS` を次のように解釈する。指定が無いものは既定値を使う。

| 引数 | 既定 | 意味 |
|---|---|---|
| `--week` | 前の ISO 週 | 対象週。`2026-W43` 形式 |
| `--since` | 対象週の月曜 | 抽出の開始日。`14d` や `2026-10-12` も受ける。初めて参加する人には `14d` を勧める |
| `--questions` | 週の行の `今週の問い`。無ければ cadence | 答える問い（カンマ区切り） |
| `--projects` | 全部 | 対象プロジェクト名の部分一致（カンマ区切り） |
| `--out` | `cards/` | 成果物ディレクトリ。作業ファイルは `<out>/.work/` |
| `--tier` | `internal` | 機密スキャンの区分。社外に転用するときだけ `public` |
| `--dry-run` | なし | Notion に書かない。送る内容を表示して終える |
| `--no-notion` | なし | カードの確認と機密スキャンまでで終える |

以下、このスキルのディレクトリを `<skill-dir>`、プラグインのディレクトリ（`<skill-dir>/../..`）を `<plugin-dir>`、`--out` を `<out>` と書く。スクリプトはすべて `python3 -I` で実行する。

## Phase 0: 準備

1. 開始時刻を控える（完了報告で所要時間を出す）
2. `<out>/.work/` を作る。`<out>` が git 管理下で `.gitignore` に `.work/` が無ければ、追加を提案する
3. 対象週を決める

```bash
python3 -I <skill-dir>/scripts/cards.py week [--week <week>]
```

出力の `week`、`monday`、`sunday`、`title` を以降で使う。`--since` の指定が無ければ `monday` を使う。

4. 問いを決める。`--questions` があればそれを使う。無ければ、Notion MCP が使えて `--no-notion` でないとき、`references/notion-submit.md` の「2. 週の行を確保する」の query だけを実行して `今週の問い` を読む（行が無くてもここでは作らない）。それも無ければ cadence に従う

```bash
python3 -I <skill-dir>/scripts/cards.py plan --week <week> [--ids <問いのID>]
```

5. ユーザーに段取りを 1 行で伝える（対象週、期間、問い、提出の有無）

## Phase 1: 抽出

```bash
python3 -I <skill-dir>/scripts/extract_sessions.py --since <since> [--projects <list>] --out <out>/.work/sessions.json
```

出力には、期間内の prompt（`session_id` 付き）、ツール・スキル・MCP の利用回数、Bash の例、commit と PR のタイトル、memory、ハーネス構成（名前だけ）、匿名化辞書（`vocabulary`）が入る。秘密情報は伏せ字済み。

## Phase 2: 下書き

1. `references/card-writing.md` を読む
2. 問いごとに、`plan` の `text` と `draft_hint`、`card-writing.md` の「問いごとに見る場所」に従って `sessions.json` の該当部分を読み、カードを書く。1 問 1〜3 枚、材料が無ければ「該当なし」を 1 枚
3. カードを `<out>/.work/cards.jsonl` に 1 行 1 枚で書く。形式は次のとおり

```json
{"card_id": "<week>/<問い>/<メールの@より前>/001", "question_id": "Q2", "week": "<week>", "week_range": ["<monday>", "<sunday>"], "author_email": "<git config user.email>", "project": "<プロジェクト名>", "claim": "20〜80 字の結論", "context": "2〜3 文", "polarity": "failed", "confidence": "observed", "evidence": [{"type": "prompt", "ref": "<session_id>@<time>", "excerpt": "伏せ字済みの抜粋"}], "tags": ["prompt"], "sensitivity": "internal", "status": "draft", "notion_url": null}
```

`author_email` は `git config user.email` から取る。`project` は `sessions.json` のプロジェクト名をそのまま使う。

4. 検査する。エラーが 0 になるまで直す

```bash
python3 -I <skill-dir>/scripts/cards.py validate <out>/.work/cards.jsonl
```

5. 確認用の Markdown を出す

```bash
python3 -I <skill-dir>/scripts/cards.py render <out>/.work/cards.jsonl --out <out>/cards-<week>.md
```

## Phase 3: 自己確認

1. 問いごとの枚数と、各カードの claim を一覧で表示する。`<out>/cards-<week>.md` を開けば直せることも伝える
2. AskUserQuestion で聞く: 「このまま進める」「ファイルを直したので読み直す」「中止する」
3. 「読み直す」なら、Markdown を正本に戻してから検査し、再び 1 に戻る

```bash
python3 -I <skill-dir>/scripts/cards.py parse <out>/cards-<week>.md --base <out>/.work/cards.jsonl --out <out>/.work/cards.jsonl
python3 -I <skill-dir>/scripts/cards.py validate <out>/.work/cards.jsonl
python3 -I <skill-dir>/scripts/cards.py render <out>/.work/cards.jsonl --out <out>/cards-<week>.md
```

4. 「中止する」なら、作ったファイルの場所を伝えて終える

消したカードと `状態: dropped` のカードは提出しない。ユーザーが文面を直したカードは、そのまま尊重する（Claude が書き戻さない）。

## Phase 4: 機密ゲート

```bash
python3 -I <skill-dir>/scripts/scan_sensitive.py <out>/cards-<week>.md --vocab <out>/.work/sessions.json --tier <tier> [--allow-file <out>/.work/allow.txt]
```

終了コードが 1 なら、検出箇所を `<out>/cards-<week>.md` で書き換え、Phase 3 の 3（parse → validate → render）を通してから再実行する。検出語が一般語で伏せる必要が無いと判断できるときだけ、`<out>/.work/allow.txt` に理由のコメント付きで追記する。社内で公知のホスト名（社内ツールのドメインなど）も同じ扱い。秘密情報（トークン、メール、組織 ID、ホームパス）は許可リストに入れない。

**スキャンが 0 件になるまで Phase 5 に進まない。**

## Phase 5: 提出

`--no-notion` なら飛ばす。`--dry-run` なら、週の行の検索結果と `cards.py to-notion` の出力を表示し、Notion にも `submitted.jsonl` にも書かずに完了報告へ進む（週の行が無ければ `--week-url` には仮の値を入れて表示だけ行う）。

それ以外は `references/notion-submit.md` の手順に従う。

1. スキーマを確認する
2. 週の行を確保する（無ければ作る）
3. 投稿者を解決する（Notion MCP の接続ユーザー。決まらなければ `me`）
4. `cards.py dedupe` → `cards.py to-notion` → create-pages → `cards.py mark-submitted`
5. 週の行に投稿者を足す

Notion MCP が使えない、または接続されていないときは、同じ文書の「MCP が使えないとき」の手順（`notion_submit.py` と `NOTION_TOKEN`）を案内する。トークンをチャットに貼らせない。

## 完了報告

最後のメッセージに次を入れる。

- 対象週と問い、問いごとのカード枚数（提出した数、除外した数）
- Notion の週の行の URL（`--dry-run` / `--no-notion` のときはその旨）
- 機密スキャンの結果（0 件）と、許可リストに入れた語とその理由
- 開始から終了までの所要時間（参加者が週の行の「備考」に書けるように）
- 投稿者を自動で足せなかった場合は、その旨と手順

作業ファイル `<out>/.work/` は個人の記録を含むので、共有リポジトリにコミットしないよう伝える。

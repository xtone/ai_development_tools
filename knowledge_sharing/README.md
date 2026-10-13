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
| **session-tips-digest** | 過去のセッション記録から共有できる運用 Tips を抽出し、一次情報で裏付けを取って Markdown・Artifact・Notion に公開する。カードや記録から Tips 文書を作る下流工程 |

### 使い分け

| やりたいこと | スキル |
|---|---|
| 毎週、問いへの答えをカードで提出し、チームの合成（正・反・合）に回す | knowledge-cards |
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

## 開発

```bash
cd knowledge_sharing/skills/session-tips-digest/scripts
uv run --no-project --with pytest python -m pytest -q -p no:cacheprovider
cd ../../knowledge-cards/scripts
uv run --no-project --with pytest python -m pytest -q -p no:cacheprovider
```

`knowledge-cards` の `extract_sessions.py` と `scan_sensitive.py` は `session-tips-digest` からコピーして拡張したもの（スキルごとに自己完結させるため）。共通の修正は両方に入れる。

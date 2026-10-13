# Notion への提出手順

提出先は Notion「Claude Codeまとめ置き場」の「週次 Tips」DB（週の行）と「ナレッジカード」DB。ID はプラグイン直下の `notion.json` にある。

Notion MCP のツール名は接続名によって変わる（`mcp__claude_ai_Notion__notion-fetch`、`mcp__notion__notion-fetch` など）。以下では fetch / search / query-data-sources / create-pages / update-page と書く。使えるツールが無ければ、末尾の「MCP が使えないとき」に進む。

以下、`<cards-ds>` は `notion.json` の `cards.data_source`、`<weeks-ds>` は `weeks.data_source`。

## 1. スキーマを確認する

create-pages の前に、fetch で `<cards-ds>` と `<weeks-ds>` を 1 回ずつ読み、プロパティ名がこの文書と合っているか確かめる。違っていたら提出を止めてユーザーに知らせる。

## 2. 週の行を確保する

query-data-sources（SQL モード）で週の行を探す。

```json
{
  "data_source_urls": ["<weeks-ds>"],
  "query": "SELECT url, \"週\", \"今週の問い\", \"投稿者\" FROM \"<weeks-ds>\" WHERE \"週\" LIKE ?",
  "params": ["2026-W43%"]
}
```

- 見つかったら、その `url` を週の行の URL とする。`今週の問い` が空でなければ、それを今週の問いとして使う（準備段階で使った問いと違えば、ユーザーに知らせて下書きをやり直すか聞く）
- 無ければ create-pages で作る。`parent` は `{"type": "data_source_id", "data_source_id": "<weeks-ds の collection:// を除いた ID>"}`

```json
{
  "週": "2026-W43（10/19〜10/25）",
  "date:期間:start": "2026-10-19",
  "date:期間:end": "2026-10-25",
  "date:期間:is_datetime": 0,
  "ステータス": "募集中",
  "今週の問い": ["P1", "Q1", "Q2", "Q3"]
}
```

タイトルと日付は `cards.py week --week <週>` の `title`、`monday`、`sunday` を使う。

## 3. 投稿者を解決する

投稿者は、Notion MCP に接続している本人とする。git のメールアドレスでは引かない。Notion アカウントのメールアドレスが git と違うことがあり、メールで検索すると同じ名前の別アカウントが返ることがあるため（2026-10-13 に実環境で確認）。

1. `<out>/.work/notion-user.json` があれば、その `user_id` を使う
2. 無ければ get-self（または get-users を `user_id: "self"` で）呼び、返った `user.id` を使う。`type` が `person` でなければ（bot 接続など）、ユーザーに自分の Notion アカウントのメールアドレスを聞き、search（`query_type: "user"`）で引く
3. どれでも決まらなければ `me` にする。提出は止めない
4. 決めた結果をユーザーに名前で示して確認し、`<out>/.work/notion-user.json` に `{"name": "...", "user_id": "<id または me>"}` で保存する

## 4. 選択肢を足す

Notion MCP の create-pages は、multi_select（`プロジェクト`、`タグ`）に選択肢に無い値を渡すと、全件を validation_error で拒否する。自動では増えない（2026-10-13 に実環境で確認）。提出前に足りない選択肢を足す。

1. 手順 1 の fetch で得た `<cards-ds>` の出力（`<data-source-state>` を含む部分）を `<out>/.work/cards-schema.txt` に保存する
2. 足りない選択肢と DDL を出す

```bash
python3 -I <skill-dir>/scripts/cards.py options <out>/.work/cards.jsonl --schema <out>/.work/cards-schema.txt
```

3. `statements` が空でなければ、各文を update-data-source（`data_source_id` は `<cards-ds>`、`statements` にその文）で実行する。`ALTER COLUMN ... SET` は選択肢の一覧を丸ごと置き換えるので、既存の選択肢を並べた `cards.py options` の出力をそのまま使い、手で書き換えない
4. 足したプロジェクト名とタグをユーザーに伝える

## 5. カードを作る

```bash
python3 -I <skill-dir>/scripts/cards.py dedupe <out>/.work/cards.jsonl --submitted <out>/.work/submitted.jsonl
python3 -I <skill-dir>/scripts/cards.py to-notion <out>/.work/cards.jsonl --week-url <週の行の URL> --author <user_id または me> > <out>/.work/pages.json
```

`pages.json` の各要素の `properties` と `content` を、そのまま create-pages の `pages[]` に入れる。`parent` は `{"type": "data_source_id", "data_source_id": "<cards-ds の ID>"}`。1 回の呼び出しで 100 件まで。`allow_async` は `false` にして、作られたページの URL を受け取る。

- `プロジェクト` と `タグ` の値は、手順 4 で選択肢に足してあること
- 失敗したカードがあれば、そのカードは記録せずに残す（次の実行で送れる）

成功したカードの `card_id` と URL を `<out>/.work/results.json` に書き、記録する。

```json
[{"card_id": "2026-W43/Q2/y.toyota/001", "notion_url": "https://www.notion.so/..."}]
```

```bash
python3 -I <skill-dir>/scripts/cards.py mark-submitted <out>/.work/cards.jsonl --submitted <out>/.work/submitted.jsonl --results <out>/.work/results.json
```

## 6. 週の行に投稿者を足す

fetch で週の行を読み、`投稿者` の現在の値を得る。自分が入っていなければ、既存の値に自分を足した配列で update-page（`command: "update_properties"`）を呼ぶ。

```json
{"投稿者": ["<既存の user id>", "<自分の user id>"]}
```

投稿者が `me` のままなら、fetch で返る自分の ID が分からないので、この手順は飛ばして完了報告で「週の行の投稿者には手で自分を足す」と伝える。`カード` relation はカード側の `週` から自動で入るので触らない。

## MCP が使えないとき

社内インテグレーショントークンを `NOTION_TOKEN` に入れ、`notion_submit.py` を使う。インテグレーションに「Claude Codeまとめ置き場」への接続を許可しておく必要がある。トークンの持ち主はボットなので、投稿者は本人の Notion アカウントのメールアドレス（git のメールアドレスと違うことがある）で引く。トークンはチャットに貼らず、ユーザー自身のシェルで設定してもらう。

```bash
python3 -I <skill-dir>/scripts/notion_submit.py ensure-week --week 2026-W43 --questions P1,Q1,Q2,Q3
python3 -I <skill-dir>/scripts/notion_submit.py resolve-user --email <本人の Notion アカウントのメールアドレス>
python3 -I <skill-dir>/scripts/cards.py to-notion <out>/.work/cards.jsonl --week-url <ensure-week の url> --author <user id> > <out>/.work/pages.json
python3 -I <skill-dir>/scripts/notion_submit.py submit <out>/.work/pages.json --results <out>/.work/results.json
python3 -I <skill-dir>/scripts/cards.py mark-submitted <out>/.work/cards.jsonl --submitted <out>/.work/submitted.jsonl --results <out>/.work/results.json
python3 -I <skill-dir>/scripts/notion_submit.py add-author --week-page <ensure-week の url> --user <user id>
```

各コマンドに `--dry-run` を付けると、送る内容だけを表示する（トークン不要）。REST API は multi_select に無い値を渡すと選択肢を自動で足すので、手順 4 は要らない。

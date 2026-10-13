---
name: knowledge-synthesis
description: 週ごとに Notion「ナレッジカード」DB に集まったカードを読み、問いをまたいで親和図にまとめ、正（worked）と反（failed）の対立から合（提案）を出し、次の問いを決めて、「合成テーマ」DB と週の行の配下の「まとめ」ページに書き込む。「今週のカードを合成して」「W43 のまとめを作って」「ナレッジカードの合成」などの依頼で使う。カードの提出は knowledge-cards、個人の採点は evaluate-session の領域。個人別の件数ランキングや「誰が何を失敗した」は出さない。
---

# Knowledge Synthesis

週ごとに集まったナレッジカードを束ね、対立から提案を出し、次の問いを決める。手順の根拠と判断基準は `references/synthesis-method.md` にある。このスキルはその手順を実行する。v0 は週次の合成だけを扱う（月次の P2・Q6・Q8 とプロジェクトマップは対象外）。

成果物は 3 つ。

- Notion「合成テーマ」DB の行（1 テーマ 1 行、採否 = 検討中）
- 週の行の配下の「まとめ（<週>）」ページ
- 週の行のステータス = 合成済み

## 守ること

- 個人別の件数ランキングや、「誰が何を失敗した」は書かない。代表カードの引用は claim とプロジェクトまでにする。投稿者は匿名のラベル（p1、p2 …）で渡すが、ラベルも本文に書かない
- カードに無い事実を足さない。推定は推定と書く
- 人事評価・処遇と経営に関する話題（knowledge-cards の `confidential_topics.json`）は書かない。強い語に当たるカードは、読み込みの段階で合成から外れる
- Notion への書き込みは、まとめの下書きをユーザーが確認してから行う

## 引数

`$ARGUMENTS` を次のように解釈する。

| 引数 | 既定 | 意味 |
|---|---|---|
| `--week` | 前の ISO 週 | 合成する週。`2026-W43` 形式 |
| `--out` | `synthesis/` | 成果物ディレクトリ。作業ファイルは `<out>/.work/` |
| `--dry-run` | なし | Notion に書かない。書き込む内容を表示して終える |

以下、このスキルのディレクトリを `<skill-dir>`、knowledge-cards のスクリプトを `<cards-scripts>`（`<skill-dir>/../knowledge-cards/scripts`）、プラグインのディレクトリを `<plugin-dir>`（`<skill-dir>/../..`）と書く。スクリプトはすべて `python3 -I` で実行する。このスキルは knowledge-cards の機密スキャナと話題判定をそのまま使うので、同じプラグインの knowledge-cards が必要。

## Phase 0: 準備

1. `<out>/.work/` を作る
2. 対象週を決める: `python3 -I <cards-scripts>/cards.py week [--week <week>]`。`week` と `title` を以降で使う
3. `<plugin-dir>/notion.json` から、週次 Tips・ナレッジカード・合成テーマの data source を読む
4. Notion MCP の query-data-sources で週の行を探す（`"週" LIKE '<week>%'`）。`url`、`ステータス` を控える
   - 週の行が無ければ、合成するカードも無いので、その旨を伝えて終える
   - `ステータス` が `合成済み` か `共有済み` なら、既に合成されている。そのまま進めると合成テーマが重複するので、AskUserQuestion で「中止する（推奨）/ dry-run で内容だけ見る」を聞く。既存の行を消したり書き換えたりはしない
5. 段取りを 1 行で伝える（対象週、dry-run かどうか）

## Phase 1: カードの読み出し

`references/synthesis-method.md` の手順 1 の SQL で、週の行のページ ID（URL の末尾 32 桁）を `LIKE` で含むカードを全件読む。結果は、MCP が返した JSON をそのまま `<out>/.work/query-1.json` に保存する（100 件を超えたら `query-2.json` 以降に分ける）。

```bash
python3 -I <skill-dir>/scripts/load_cards.py <out>/.work/query-*.json --week <week> --out <out>/.work/cards-<week>.json
```

出力には、指標（参加者数、問い・極性ごとの枚数、observed の数）、事実カード、意見カードが入る。投稿者は匿名のラベルに置き換わっている。重複は代表カードの `duplicates` に束ねられる。強い語に当たるカードは外れ、`excluded.confidential` に件数だけが入る。指標と除外の件数をユーザーに伝える。意見カードが 0 枚なら、事実カードの表だけのまとめになると伝えてから進む。

## Phase 2: 合成（Claude が判断する）

`references/synthesis-method.md` の手順 4〜7 に従い、`<out>/.work/cards-<week>.json` の意見カードを読んで、`<out>/.work/themes-<week>.json` を書く。

```json
{"week": "<week>",
 "themes": [{"title": "結論の一文（10〜80 字）", "cards": ["<カードの url>"],
             "conflict": "正と反の要約と分かれ目（推定は推定と書く）。対立が無ければ空",
             "kinds": ["条件分け", "仕組み化"], "proposal": "合", "limits": "反証・限界",
             "decision": "共有会で決めることの一文"}],
 "next_questions": [{"id": "Q4", "reason": "なぜ次に聞くか"}, {"text": "新しい問いの案", "reason": "..."}]}
```

- 意見カードは問いをまたいで束ねる。すべての意見カードを、どれか 1 つのテーマに入れる（1 枚だけのテーマも残す）
- `kinds` は「両立案」「条件分け」「仕組み化」から選ぶ。仕組み化なら還元先（スキル、hook、CLAUDE.md、プラグイン設定など）を名指しする
- テーマの問い・根拠の強さ（人数・プロジェクト数・枚数）はスクリプトが数えるので書かない
- 対立の分かれ目や合は、カードの文脈と根拠から言えることに限る

検査して、エラーが 0 になるまで直す。

```bash
python3 -I <skill-dir>/scripts/synth.py validate <out>/.work/themes-<week>.json --cards <out>/.work/cards-<week>.json
```

worked と failed が同じテーマにあるのに対立が空、テーマに入っていない意見カード、事実カードの混入、合や限界の空欄、投稿者ラベルの記載はエラーになる。

## Phase 3: まとめの下書きと機密の再確認

```bash
python3 -I <skill-dir>/scripts/synth.py render <out>/.work/themes-<week>.json --cards <out>/.work/cards-<week>.json --out <out>/summary-<week>.md
python3 -I <skill-dir>/scripts/synth.py check <out>/summary-<week>.md --cards <out>/.work/cards-<week>.json
```

`check` は、カードへのメンションを除いた本文に、機密スキャナとカードにしない話題の判定をかける。要確認の語は、提出されたカードに既に含まれていたもの（投稿者が提出時に確認済み）だけ通す。問題が 1 件でもあれば `themes-<week>.json` を直して、render からやり直す。**0 件になるまで Phase 4 に進まない。**

## Phase 4: 確認

1. テーマの一覧（テーマ名、対立の有無、合の一文、根拠の強さ）と次の問いを表示する。`<out>/summary-<week>.md` を開けば全文を読めると伝える
2. AskUserQuestion で聞く: 「Notion に書き込む」「themes を直したので読み直す」「書き込まずに終える」
3. 「読み直す」なら Phase 2 の validate からやり直す

`--dry-run` のときは、次の `synth.py to-notion` の出力と、まとめの本文を表示して完了報告に進む。

## Phase 5: 書き込み

1. 合成テーマ DB に、同じ週の行が既に無いかを query-data-sources で確かめる（`"週" LIKE '%<週の行のページ ID>%'`）。あれば書き込まずに止め、ユーザーに伝える
2. 合成テーマを作る

```bash
python3 -I <skill-dir>/scripts/synth.py to-notion <out>/.work/themes-<week>.json --cards <out>/.work/cards-<week>.json --week-url <週の行の URL> > <out>/.work/theme-pages.json
```

各要素の `properties` と `content` を create-pages の `pages[]` に入れる（parent は合成テーマの data source、`allow_async: false`）。返ってきた URL を `title` と組にして `<out>/.work/theme-urls.json`（`[{"title": "...", "url": "..."}]`）に書く。

3. テーマへのメンション付きで、まとめを作り直して再確認する

```bash
python3 -I <skill-dir>/scripts/synth.py render <out>/.work/themes-<week>.json --cards <out>/.work/cards-<week>.json --theme-urls <out>/.work/theme-urls.json --out <out>/summary-<week>.md
python3 -I <skill-dir>/scripts/synth.py check <out>/summary-<week>.md --cards <out>/.work/cards-<week>.json
```

4. 週の行の配下に「まとめ」ページを create-pages で作る（parent は `{"type": "page_id", "page_id": "<週の行のページ ID>"}`、properties は `{"title": "まとめ（<week>）"}`、icon は 🧭、content は `<out>/summary-<week>.md` の中身）
5. fetch でまとめページを読み返し、崩れ（ファイル名の自動リンクなど）が無いか確かめる。あれば update-page の `update_content` で直す
6. 週の行の `ステータス` を update-page（`update_properties`）で `合成済み` にする

## 完了報告

- 対象週、参加者数、カード枚数（問い別）、除外した件数（重複・カードにしない話題）
- テーマ数・対立数・提案数と、テーマ名の一覧
- 次の問い
- まとめページと合成テーマの URL（`--dry-run` のときはその旨）
- 共有会で採否を決めること（合成テーマの `採否` を共有会で更新する）

作業ファイル `<out>/.work/` はカードの全文を含むので、共有リポジトリにコミットしないよう伝える。

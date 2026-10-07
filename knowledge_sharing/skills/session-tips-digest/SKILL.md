---
name: session-tips-digest
description: Claude Code の過去のセッション記録（~/.claude の履歴・セッションログ・memory）から、他のメンバーと共有できる運用 Tips を抽出し、公式ドキュメントや論文などの一次情報で裏付けを取って、Markdown・Artifact・Notion に公開する。「過去の会話から Tips をまとめて」「Claude Code の使い方をチームに共有したい」「今月の学びを Tips にして」などの依頼で使う。セッション 1 本の効率採点ではない（それは evaluate-session の領域）。
---

# Session Tips Digest

自分の Claude Code の記録から「他の人がそのまま使える運用の知見」を抜き出し、裏付けを付けて共有できる形にする。

成果物は 3 つ。

- `tips/claude-code-tips.md`: Tips 本体
- `tips/claude-code-tips-references.md`: 一次情報との対応表
- Artifact（HTML ページ）。指定があれば Notion ページも

## 引数

`$ARGUMENTS` を次のように解釈する。指定が無いものは既定値を使う。

| 引数 | 既定 | 意味 |
|---|---|---|
| `--since` | `30d` | 抽出期間。`7d` や `2026-09-01` も受ける |
| `--projects` | 全部 | 対象プロジェクト名の部分一致（カンマ区切り） |
| `--out` | `tips/` | 成果物ディレクトリ。作業ファイルは `<out>/.work/` |
| `--artifact-url` | なし | 既存 Artifact を更新する。無ければ新規公開 |
| `--notion` | なし | 指定した Notion ページの配下に本体を書き出す |
| `--no-research` | なし | Phase 3（一次情報の調査）を省略する |

以下、このスキルのディレクトリを `<skill-dir>`、`--out` を `<out>` と書く。スクリプトはすべて `python3 -I` で実行する。

## Phase 0: 準備

1. `<out>` と `<out>/.work/` を作る
2. `<out>/claude-code-tips.md` が既にあれば差分更新モードにする。本文末尾の `最終更新: YYYY-MM-DD` を読み、`--since` が指定されていなければその日付を `--since` に使う。既存の Tips は消さず、新しい Tips を該当する章に追記し、既存の Tips を新しい事例や情報で更新する
3. 作業の段取りをユーザーに 1 行で伝える（期間、対象、調査の有無）

## Phase 1: 抽出

```bash
python3 -I <skill-dir>/scripts/extract_sessions.py --since <since> [--projects <list>] --out <out>/.work/sessions.json
```

出力 JSON には、期間内のプロンプト、ツール・スキル・エージェント・MCP・`gh` の利用回数、パターンに合う Bash コマンド例、memory の要点、ハーネス構成（名前だけ）、匿名化辞書（`vocabulary`）が入る。秘密情報は伏せ字済み。

この JSON を読み、加えて次も確認する。

- `harness.commands` と `harness.skills` に出てくる自作コマンド・スキルの本文（`~/.claude/commands/*.md` など）。汎用的なものは Tips の材料になる
- 繰り返し現れるプロンプトの型（毎回付けている指示、決まった往復）
- memory のうち、プロジェクト固有でない落とし穴

候補の選び方と除外基準は `references/tip-selection.md` に従う。選んだ候補は「章」「見出し」「根拠となる記録」の 3 列でメモし、根拠が記録に無いものは採らない。

## Phase 2: 匿名化と執筆

1. `templates/tips.md` の構成で `<out>/claude-code-tips.md` を書く。各 Tips は「何をするか」「なぜ（匿名化した事例）」「コマンドや設定」の順。匿名化のルールは `references/tip-selection.md` の「匿名化」に従う
2. 文章は `references/writing-style.md` に従う。natural-japanese スキルが使えるなら Skill ツールで読み込み、その lint を実行して指摘を処理する。使えなければ同ファイルのチェックリストで代替する
3. 機密スキャンを実行する

```bash
python3 -I <skill-dir>/scripts/scan_sensitive.py <out>/claude-code-tips.md --vocab <out>/.work/sessions.json [--allow-file <out>/.work/allow.txt]
```

終了コードが 1 なら、検出箇所を書き換えて再実行する。検出語が一般語（例: プロジェクト名がたまたま `onboarding`）で、伏せる必要が無いと判断できる場合だけ、`<out>/.work/allow.txt` に理由のコメント付きで追記する。秘密情報（トークン、メール、組織 ID、ホームパス）は許可リストに入れない。

**スキャンが 0 件になるまで Phase 3 以降に進まない。**

## Phase 3: 一次情報の調査

`--no-research` のときは飛ばし、Tips 本体末尾に「一次情報による裏付けは未実施」と書く。

1. 各 Tips について、`references/research-sources.md` の優先順位で一次情報を探す。WebSearch で候補を見つけ、WebFetch で本文を確認してから引用する。ライブラリやツールの公式ドキュメントは Context7 が使えるならそれを優先する
2. `templates/references.md` の形式で `<out>/claude-code-tips-references.md` を書く。各項目を「裏付ける」「修正する」「範囲を狭める」のどれかに分類する。Tips を弱める結果も必ず載せる
3. 確度の高いもの（公式ドキュメントで確認できた仕様、Tips の記述を誤りと示すもの）は本体にも反映する。研究結果を本体に入れるときは、示唆か確定かを書き分ける
4. 本体末尾に「参考文献」の節を置く
5. 本体と参照リストの両方に Phase 2 の機密スキャンを再実行する

公式に記述が見つからない落とし穴は消さずに残し、「実測」と明記する。

## Phase 4: 公開

1. HTML を生成してスキャンする

```bash
python3 -I <skill-dir>/scripts/md_to_artifact.py <out>/claude-code-tips.md --out <out>/dist/index.html --meta "対象: <読者>" --meta "期間: <開始> 〜 <終了>" --meta "最終更新: <今日>"
python3 -I <skill-dir>/scripts/scan_sensitive.py <out>/dist/index.html --vocab <out>/.work/sessions.json [--allow-file <out>/.work/allow.txt]
```

2. Artifact ツールで `<out>/dist/index.html` を公開する
   - `--artifact-url` があれば、先に `action: "read"` で現行版を読み、その `url` を指定して更新する
   - 無ければ新規公開する。`icon` は `notebook`、`description` は Tips の要旨 1 文
   - Artifact ツールが無い環境では、HTML ファイルのパスを伝えて終える
3. `--notion` があれば Notion MCP を使う。`notion-fetch` で親ページを確認し、`notion-create-pages` で子ページとして本体の Markdown を書き出す。Notion MCP が接続されていなければ、`/mcp` で接続してから再実行するよう案内して、この手順だけ飛ばす

## 完了報告

最後のメッセージに次を入れる。

- 採用した Tips の見出し一覧（章ごと）
- 成果物のパス、Artifact の URL、Notion ページの URL
- Artifact は非公開で作られること、共有するにはページの Share メニューから設定すること
- 機密スキャンの結果（0 件）と、許可リストに入れた語とその理由
- 一次情報で確認できず「実測」のまま残した項目

作業ファイル `<out>/.work/` はユーザーのホームの記録を含むので、共有リポジトリにコミットしないよう伝える。`<out>` が git 管理下なら `.gitignore` に `.work/` を追加することを提案する。

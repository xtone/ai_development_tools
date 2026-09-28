---
name: rules-split-manager
description: "CLAUDE.mdを分割ルールファイル(.claude/rules/)で管理するスキル。学習トライアドの書き込み先を分割ファイルにリダイレクトし、CLAUDE.mdには目次だけを生成する（本文は .claude/rules/ を Claude Code が自動で読み込む）。/rules-init, /rules-merge, /rules-add, /rules-status コマンドを提供。CLAUDE.mdが肥大化している場合や、学習トライアドの蓄積を分割管理したい場合に使用。"
---

# Rules Split Manager

CLAUDE.mdを分割ルールファイル（`.claude/rules/`）で管理するスキル。学習トライアドの書き込み先を分割ファイルにリダイレクトし、CLAUDE.md には目次だけを生成する。

**前提: Claude Code は `.claude/rules/*.md` を番号に関係なく全部自動で読み込む。** CLAUDE.md に本文を連結すると、同じ内容が毎セッション二重に context に入る。そのため CLAUDE.md は本文を持たず、どのファイルに何があるかの目次にする。

## 目的

CLAUDE.mdが学習トライアド（`/lessons`, `/review-learn`, `/ci-learn`）の蓄積により肥大化する問題を解決する:
- セクションごとの分割ファイルで管理しやすくする
- 手書きルール（01-89番台）と自動蓄積ルール（90番台）を明確に分離
- 外部ツール不要で、Claude Codeスキルだけで完結

## トリガー

- `/rules-init` — 既存CLAUDE.mdを分割ファイルに移行
- `/rules-merge` — 分割ファイルからCLAUDE.mdの目次を再生成
- `/rules-add [topic]` — 新規ルールファイルを作成（01-89番台）
- `/rules-status` — 分割ファイルの一覧・行数・健全性を表示
- 「CLAUDE.mdを分割して」「ルールファイルを管理して」等の自然言語

## トライアド統合メカニズム

ベーストライアド（`/lessons`, `/review-learn`, `/ci-learn`）と同時にロードされる**条件付き振る舞いモディファイア**。ベーストライアドのSystem Instructionsは変更しない。

### 動作条件

```
.claude/rules/ ディレクトリが存在する場合:
  /lessons    → .claude/rules/90-lessons-learned.md に書き込み
  /review-learn → .claude/rules/91-review-learnings.md に書き込み
  /ci-learn   → .claude/rules/92-ci-learnings.md に書き込み
  書き込み後 → CLAUDE.md の目次を再生成（本文は連結しない）

.claude/rules/ ディレクトリが存在しない場合:
  従来通り CLAUDE.md に直接書き込み（介入なし）
```

### 重複チェック

重複チェックは**対象の分割ファイルを直接読む**。CLAUDE.md は目次だけで本文を持たないので、CLAUDE.md を読んでも重複は判定できない。

### トライアド書き込みのリダイレクト手順

トライアドスキルがCLAUDE.mdに書き込もうとする場面（各スキルの「CLAUDE.mdへの書き込み」ステップ）で、以下の手順に従う:

1. プロジェクトルートに `.claude/rules/` ディレクトリが存在するか確認
2. 存在する場合、書き込み先を対応する分割ファイルに変更:
   - `## Lessons Learned` セクション → `.claude/rules/90-lessons-learned.md`
   - `## Review Learnings` セクション → `.claude/rules/91-review-learnings.md`
   - `## CI Learnings` セクション → `.claude/rules/92-ci-learnings.md`
3. 分割ファイルが存在しない場合は新規作成（セクションヘッダー付き）
4. 分割ファイルへの書き込み完了後、目次を再生成する（`/rules-merge` と同じ手順）

## ファイル番号規約

```
01-89: 手書きルール（人間管理）
90:    /lessons → lessons-learned
91:    /review-learn → review-learnings
92:    /ci-learn → ci-learnings
93-99: 将来の学習スキル用に予約
```

## System Instructions

### /rules-init — 既存CLAUDE.mdを分割ファイルに移行

#### ステップ1: CLAUDE.mdの読み込み

1. 現在のプロジェクトルート（gitルート）を特定する
2. プロジェクトルートの `CLAUDE.md` を読み込む
3. ファイルが存在しない場合はエラーメッセージを表示:
   ```
   CLAUDE.md が見つかりません。先に CLAUDE.md を作成してください。
   ```

#### ステップ2: セクション分割

1. CLAUDE.md を `## ` ヘッダーでセクション分割する
2. トライアドセクションを自動検出する:
   - `## Lessons Learned` → `90-lessons-learned.md`
   - `## Review Learnings` → `91-review-learnings.md`
   - `## CI Learnings` → `92-ci-learnings.md`
3. 残りのセクションは内容の関連性に基づいてグルーピングを提案する

#### ステップ3: 分割案の提示

ユーザーに分割案を提示し、確認を求める:

```
分割案:
  01-overview.md: プロジェクト概要 + アーキテクチャ概要
  02-commands.md: 必須コマンド
  03-coding-rules.md: 開発ガイドライン
  04-session-rules.md: Session Rules
  90-lessons-learned.md: Lessons Learned（自動蓄積）
  91-review-learnings.md: Review Learnings（自動蓄積）
  92-ci-learnings.md: CI Learnings（自動蓄積）

この分割案で進めますか？（修正があれば指示してください）
```

#### ステップ4: 分割ファイルの作成

1. `.claude/rules/` ディレクトリを作成する
2. 分割案に従い、各ファイルにセクション内容を書き込む
3. トライアドセクションが存在しない場合は、空のファイルを作らない（初回書き込み時に自動作成）

#### ステップ5: CLAUDE.md を目次に置き換える

1. 元の CLAUDE.md のすべての `## ` セクションが、いずれかの分割ファイルに入っていることを確認する（取りこぼしがゼロであること。確認は見出しの突き合わせで行う）
2. 目次アルゴリズム（`/rules-merge` を参照）に従って CLAUDE.md を再生成する
3. 生成した目次を表示する

#### 実行例

**実行前のCLAUDE.md**:
```markdown
# CLAUDE.md

## Project Overview
dmenu-newsはAndroidアプリです。

## 必須コマンド
- `./gradlew assembleDebug`

## Session Rules
- セッション終了前に `/lessons` の実行を提案すること

## Lessons Learned

### テスト
- `@JvmInline value class` はMockKでモック不可

## Review Learnings

### 命名規則
- Repository層のメソッドは `getXxx` を使う
```

**実行後のディレクトリ構造**:
```
.claude/rules/
├── 01-overview.md          # Project Overview
├── 02-commands.md          # 必須コマンド
├── 03-session-rules.md     # Session Rules
├── 90-lessons-learned.md   # Lessons Learned（自動蓄積）
└── 91-review-learnings.md  # Review Learnings（自動蓄積）
```

**再生成されたCLAUDE.md**（目次だけ。本文は `.claude/rules/` から自動で読み込まれる）:
```markdown
<!-- このファイルは .claude/rules/ から自動生成された目次です。直接編集しないでください。 -->
<!-- 本文は .claude/rules/*.md にあり、Claude Code が自動で読み込みます。ここに本文を連結すると二重に読み込まれます。 -->

# ルール目次

## 常に読み込まれる
- 01-overview.md — Project Overview
- 02-commands.md — 必須コマンド
- 03-session-rules.md — Session Rules
- 90-lessons-learned.md — Lessons Learned
- 91-review-learnings.md — Review Learnings
```

frontmatter に `paths:` を持つファイルがある場合は、次の節を足す（glob を添える）:
```markdown
## 条件付き（該当するファイルを触ったときだけ読み込まれる）
- 10-api-guidelines.md — API Guidelines（src/api/**）
```

---

### /rules-merge — 分割ファイルからCLAUDE.mdを再生成

#### ステップ1: 前提チェック

1. `.claude/rules/` ディレクトリが存在するか確認
2. 存在しない場合はエラーメッセージを表示:
   ```
   .claude/rules/ ディレクトリが見つかりません。
   先に /rules-init で分割ファイルを作成してください。
   ```

#### ステップ2: 目次アルゴリズムの実行

1. `.claude/rules/*.md` をファイル名でソートする
2. **本文は連結しない。** Claude Code は `.claude/rules/*.md` を番号に関係なく全部自動で読み込むので、CLAUDE.md に本文を入れると同じ内容が二重に context に入る（v1.2 までは 01-89 番台を連結していたが、90 番台を外した理由と同じ理屈が 01-89 番台にも当てはまる）
3. 各ファイルについて、ファイル名と最初の `## ` 見出しを 1 行にする
4. frontmatter に `paths:` を持つファイルは、該当するファイルを触ったときだけ読み込まれる。「条件付き」の見出しの下に分けて列挙し、glob も添える
5. 先頭にヘッダーコメントを付与する:
   ```markdown
   <!-- このファイルは .claude/rules/ から自動生成された目次です。直接編集しないでください。 -->
   <!-- 本文は .claude/rules/*.md にあり、Claude Code が自動で読み込みます。ここに本文を連結すると二重に読み込まれます。 -->
   ```
6. CLAUDE.md に上書きする。既存の CLAUDE.md に rules 由来でない手書きの記述がある場合は、上書きする前にユーザーに見せ、どの分割ファイルへ移すかを確認する

#### ステップ3: 結果の表示

1. 目次に載せたファイルを「常に読み込まれる」と「条件付き」に分けて件数を表示する
2. 生成されたCLAUDE.mdの行数を表示する
3. 前回の目次との差分（追加・削除・見出しが変わったファイル）を表示する

出力例:
```
目次を再生成:
  常に読み込まれる: 7個
  条件付き（paths:）: 1個
  CLAUDE.md: 14行（目次のみ）

  前回からの変化:
    05-testing.md: 追加
```

---

### /rules-add [topic] — 新規ルールファイルを作成

#### ステップ1: 前提チェック

1. `.claude/rules/` ディレクトリが存在するか確認
2. 存在しない場合はエラーメッセージを表示:
   ```
   .claude/rules/ ディレクトリが見つかりません。
   先に /rules-init で分割ファイルを作成してください。
   ```

#### ステップ2: ファイル番号の決定

1. `.claude/rules/` 内の既存ファイルをスキャンする
2. 01-89番台の中で使われていない最小の番号を採番する
3. topic引数からファイル名を生成する:
   - 例: `/rules-add testing` → `05-testing.md`（既存が01-04の場合）

#### ステップ3: ファイルの作成

1. 番号とトピック名をユーザーに確認する:
   ```
   新規ルールファイルを作成します:
     .claude/rules/05-testing.md

   よろしいですか？
   ```
2. 承認後、空のファイルを以下のテンプレートで作成する:
   ```markdown
   ## {Topic名}

   <!-- ルールをここに記述してください -->
   ```
3. 目次を再生成して CLAUDE.md を更新する

### /rules-status — 分割ファイルの一覧・行数・健全性を表示

#### ステップ1: 前提チェック

1. `.claude/rules/` ディレクトリが存在するか確認
2. 存在しない場合はエラーメッセージを表示:
   ```
   .claude/rules/ ディレクトリが見つかりません。
   先に /rules-init で分割ファイルを作成してください。
   ```

#### ステップ2: ファイルスキャン

1. `.claude/rules/*.md` をファイル名でソートして取得する
2. 各ファイルの行数をカウントする
3. CLAUDE.md の行数もカウントする

#### ステップ3: 一覧表示

以下のフォーマットでファイル一覧を表示する:

```
.claude/rules/ ステータス:
  [常に読み込まれる]
  01-overview.md           7行
  02-commands.md          32行
  03-architecture.md      27行
  04-guidelines.md        35行
  05-session-rules.md      3行
  90-lessons-learned.md   16行
  91-review-learnings.md  28行
  ─────────────────────────
  小計: 7ファイル / 148行

  [条件付き: paths: あり]
  （なし）

  CLAUDE.md: 14行（目次のみ）
```

#### ステップ4: 健全性チェック

以下の項目をチェックし、結果を表示する:

1. **番号の重複**: ファイル名の先頭2桁の番号が重複していないか
2. **番号帯の混在**: 01-89番台（手書き）と90番台（自動蓄積）の分離が維持されているか（90番台に手書きルールが混在していないか）
3. **空ファイル**: 0行のファイルがないか
4. **二重読み込み**: CLAUDE.md に分割ファイルの本文が連結されていないか（v1.2 以前の形式が残っていれば、目次への置き換えを提案する）

すべてOKの場合:
```
健全性: OK
```

問題がある場合は具体的な内容を表示する:
```
健全性: 要確認
  ⚠ 番号の重複: 03-architecture.md, 03-coding-rules.md
  ⚠ 空ファイル: 05-session-rules.md
```

---

## エッジケース

| ケース | 対応 |
|--------|------|
| CLAUDE.md がマージ後に手動編集された | 次回マージで上書き（ヘッダーコメントで警告済み） |
| 分割ファイルが全て空 | 空のCLAUDE.md + ユーザーに警告表示 |
| トライアドセクションがまだない | 空の90/91/92は作らない。初回書き込み時に自動作成 |
| `.claude/rules/` に `.md` 以外のファイルがある | 無視する（`.md` のみ対象） |
| ファイル番号が重複 | エラーを表示し、ユーザーに修正を促す |
| v1.2 以前の連結形式の CLAUDE.md が残っている | 本文が rules と一致しているかを確かめてから目次に置き換える（一致しない行があれば、先にどの分割ファイルへ移すかをユーザーに確認） |
| Claude Code 以外に CLAUDE.md の本文だけを読むツールがある | CLAUDE.md に本文を戻すと Claude Code で二重に読み込まれる。そのツール向けのファイルを別に用意するかをユーザーに確認する |

## 重要事項

- このスキルはベーストライアド（`/lessons`, `/review-learn`, `/ci-learn`）を変更しない
- `.claude/rules/` が存在するプロジェクトでのみ振る舞いを変更する条件付きモディファイア
- CLAUDE.mdは自動生成の目次になるため、直接編集しないことをヘッダーコメントで明示する
- 分割ファイルの編集は必ずユーザーの承認を得てから実行する
- 再生成した CLAUDE.md（目次）は git にコミットする（チーム全員が地図として参照するため）

## バージョン

### v1.3 - CLAUDE.md を目次にし、二重読み込みを解消
- `/rules-merge`: 本文の連結をやめ、ファイル名と見出しの目次だけを生成する。Claude Code は `.claude/rules/*.md` を番号に関係なく全部自動で読み込むため、v1.2 の 01-89 番台の連結は毎セッション二重に読み込まれていた（toryu-web で実測: 01〜07 の約 1.4 万字が二重。`paths:` を付けても CLAUDE.md 側に全文が残るので条件付き読み込みが効かなかった）
- 目次で `paths:` 付きのファイル（条件付き読み込み）を分けて示す
- 重複チェック: 分割ファイルを直接読む（CLAUDE.md は本文を持たない）
- `/rules-init`: 元の CLAUDE.md の全セクションが分割ファイルに入ったことを確認してから目次に置き換える
- `/rules-status`: 二重読み込み（本文が連結された CLAUDE.md）を健全性チェックに追加

### v1.2 - マージ対象を01-89番台に限定
- `/rules-merge`: 90番台以降をスキップし、01-89番台のみCLAUDE.mdに連結。末尾に90番台の参照注記を付与
- `/rules-status`: マージ対象（01-89番台）と自動ロード（90番台）を区別して表示
- 重複チェック: CLAUDE.mdと対象分割ファイルの両方を参照するよう変更
- トライアド自動マージ: 同じ01-89限定ロジックを適用

### v1.1 - /rules-status 追加 & /rules-merge 差分サマリー
- `/rules-status`: 分割ファイルの一覧・行数・健全性チェック（番号重複、番号帯混在、空ファイル検出）
- `/rules-merge`: ステップ3に前回CLAUDE.mdとの差分サマリー表示を追加

### v1.0 - 初回リリース
- `/rules-init`: 既存CLAUDE.mdの分割移行
- `/rules-merge`: 分割ファイルからCLAUDE.mdの再生成
- `/rules-add`: 新規ルールファイル作成（01-89番台の自動採番）
- トライアド統合: `/lessons`, `/review-learn`, `/ci-learn` の書き込み先リダイレクト
- ファイル番号規約: 01-89手書き、90-92トライアド、93-99予約

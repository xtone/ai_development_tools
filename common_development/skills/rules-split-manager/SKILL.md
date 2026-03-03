---
name: rules-split-manager
description: "CLAUDE.mdを分割ルールファイル(.claude/rules/)で管理するスキル。学習トライアドの書き込み先を分割ファイルにリダイレクトし、自動マージでCLAUDE.mdを生成。/rules-init, /rules-merge, /rules-add コマンドを提供。CLAUDE.mdが肥大化している場合や、学習トライアドの蓄積を分割管理したい場合に使用。"
---

# Rules Split Manager

CLAUDE.mdを分割ルールファイル（`.claude/rules/`）で管理するスキル。学習トライアドの書き込み先を分割ファイルにリダイレクトし、自動マージでCLAUDE.mdを生成する。

## 目的

CLAUDE.mdが学習トライアド（`/lessons`, `/review-learn`, `/ci-learn`）の蓄積により肥大化する問題を解決する:
- セクションごとの分割ファイルで管理しやすくする
- 手書きルール（01-89番台）と自動蓄積ルール（90番台）を明確に分離
- 外部ツール不要で、Claude Codeスキルだけで完結

## トリガー

- `/rules-init` — 既存CLAUDE.mdを分割ファイルに移行
- `/rules-merge` — 分割ファイルからCLAUDE.mdを再生成
- `/rules-add [topic]` — 新規ルールファイルを作成（01-89番台）
- 「CLAUDE.mdを分割して」「ルールファイルを管理して」等の自然言語

## トライアド統合メカニズム

ベーストライアド（`/lessons`, `/review-learn`, `/ci-learn`）と同時にロードされる**条件付き振る舞いモディファイア**。ベーストライアドのSystem Instructionsは変更しない。

### 動作条件

```
.claude/rules/ ディレクトリが存在する場合:
  /lessons    → .claude/rules/90-lessons-learned.md に書き込み
  /review-learn → .claude/rules/91-review-learnings.md に書き込み
  /ci-learn   → .claude/rules/92-ci-learnings.md に書き込み
  書き込み後 → 自動マージで CLAUDE.md 再生成

.claude/rules/ ディレクトリが存在しない場合:
  従来通り CLAUDE.md に直接書き込み（介入なし）
```

### 重複チェック

重複チェックは**CLAUDE.mdを読む**。マージ済みの全体ビューなので、トライアド側の重複チェックロジックは変更不要。書き込み先だけが分割ファイルに変わる。

### トライアド書き込みのリダイレクト手順

トライアドスキルがCLAUDE.mdに書き込もうとする場面（各スキルの「CLAUDE.mdへの書き込み」ステップ）で、以下の手順に従う:

1. プロジェクトルートに `.claude/rules/` ディレクトリが存在するか確認
2. 存在する場合、書き込み先を対応する分割ファイルに変更:
   - `## Lessons Learned` セクション → `.claude/rules/90-lessons-learned.md`
   - `## Review Learnings` セクション → `.claude/rules/91-review-learnings.md`
   - `## CI Learnings` セクション → `.claude/rules/92-ci-learnings.md`
3. 分割ファイルが存在しない場合は新規作成（セクションヘッダー付き）
4. 分割ファイルへの書き込み完了後、自動マージを実行してCLAUDE.mdを再生成

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

#### ステップ5: マージによるCLAUDE.md再生成

1. マージアルゴリズム（後述）に従いCLAUDE.mdを再生成する
2. 再生成されたCLAUDE.mdの内容を表示し、元の内容と差異がないことを確認する（ヘッダーコメント以外）

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

**再生成されたCLAUDE.md**:
```markdown
<!-- このファイルは .claude/rules/ から自動生成されています。直接編集しないでください。 -->
<!-- /rules-merge または学習トライアド実行で自動更新されます。 -->

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

---

### /rules-merge — 分割ファイルからCLAUDE.mdを再生成

#### ステップ1: 前提チェック

1. `.claude/rules/` ディレクトリが存在するか確認
2. 存在しない場合はエラーメッセージを表示:
   ```
   .claude/rules/ ディレクトリが見つかりません。
   先に /rules-init で分割ファイルを作成してください。
   ```

#### ステップ2: マージアルゴリズムの実行

1. `.claude/rules/*.md` をファイル名でソートする
2. 各ファイルの内容を連結する（ファイル間は空行1行で区切り）
3. 先頭にヘッダーコメントを付与する:
   ```markdown
   <!-- このファイルは .claude/rules/ から自動生成されています。直接編集しないでください。 -->
   <!-- /rules-merge または学習トライアド実行で自動更新されます。 -->
   ```
4. CLAUDE.md に上書きする

#### ステップ3: 結果の表示

1. マージに含まれたファイル一覧を表示する
2. 生成されたCLAUDE.mdの行数を表示する

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
3. マージを実行してCLAUDE.mdを更新する

## エッジケース

| ケース | 対応 |
|--------|------|
| CLAUDE.md がマージ後に手動編集された | 次回マージで上書き（ヘッダーコメントで警告済み） |
| 分割ファイルが全て空 | 空のCLAUDE.md + ユーザーに警告表示 |
| トライアドセクションがまだない | 空の90/91/92は作らない。初回書き込み時に自動作成 |
| `.claude/rules/` に `.md` 以外のファイルがある | 無視する（`.md` のみ対象） |
| ファイル番号が重複 | エラーを表示し、ユーザーに修正を促す |

## 重要事項

- このスキルはベーストライアド（`/lessons`, `/review-learn`, `/ci-learn`）を変更しない
- `.claude/rules/` が存在するプロジェクトでのみ振る舞いを変更する条件付きモディファイア
- CLAUDE.mdは自動生成ファイルになるため、直接編集しないことをヘッダーコメントで明示する
- 分割ファイルの編集は必ずユーザーの承認を得てから実行する
- マージ後のCLAUDE.mdはgitにコミットする（チーム全員が参照するため）

## バージョン

### v1.0 - 初回リリース
- `/rules-init`: 既存CLAUDE.mdの分割移行
- `/rules-merge`: 分割ファイルからCLAUDE.mdの再生成
- `/rules-add`: 新規ルールファイル作成（01-89番台の自動採番）
- トライアド統合: `/lessons`, `/review-learn`, `/ci-learn` の書き込み先リダイレクト
- ファイル番号規約: 01-89手書き、90-92トライアド、93-99予約

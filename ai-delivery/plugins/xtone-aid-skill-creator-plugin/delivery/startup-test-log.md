# xtone-aid-skill-creator-plugin 実起動試験ログ

- 起票: Issue #199 [B-AID-02] xtone-aid-skill-creator-plugin の実起動試験
- 実施日時: 2026-05-28
- 実施環境: WSL2 (Linux 6.6.114), Claude Code CLI（`claude --print --plugin-dir` ヘッドレス起動）
- 対象プラグイン: `plugins/xtone-aid-skill-creator-plugin/` (version 0.1.0)
- 関連 PR: #197 (merged)

## サマリ

DoD のチェックリスト 5 項目をすべて確認し、構造的な異常なし。`validate-plugin.sh --strict` も pass。
不具合・追加 Issue 起票はなし。`post-pr-merge.sh` のみ hooks.json 未登録だが、これは仕様（CI/手動実行用と注記済み）。

| # | 確認項目 | 結果 |
|---|---|---|
| 1 | `/aid-*` 8 コマンドが一覧表示 | OK |
| 2 | 基盤 8 コマンド表示 | OK |
| 3 | `aid-skill-creator-architect` Subagent 認識 | OK |
| 4 | 各 SKILL.md の frontmatter description が Skill 候補に出る | OK（9 Skill 全部） |
| 5 | Hook のイベントマッチャー通り発火 | OK（登録 3 本＋仕様通り未登録 1 本） |

## 実施手順

### 1. 静的検証（前提）

```bash
bash scripts/validate-plugin.sh --strict plugins/xtone-aid-skill-creator-plugin
# => ✅ Validation passed
```

### 2. ヘッドレス起動（プラグイン読み込み）

```bash
claude --plugin-dir plugins/xtone-aid-skill-creator-plugin --print --output-format json \
  --disallowedTools "*" -- "<検証用プロンプト>"
```

`--disallowedTools "*"` により Skill / Subagent / Bash 等の副作用ある実行を抑止し、認識結果の列挙のみ取得。

### 3. デバッグログでの Hook 登録確認

```bash
claude --plugin-dir ... --debug-file /tmp/claude_debug.log --debug -- "<任意>"
grep -iE "pre-phase|hook|UserPromptSubmit" /tmp/claude_debug.log
```

debug 出力に以下が現れることを確認：

```
[DEBUG] Read hooks.json for plugin xtone-aid-skill-creator-plugin (enabled=true)
[DEBUG] Loading hooks from plugin: xtone-aid-skill-creator-plugin
[DEBUG] Registered 5 hooks from 19 plugins
[DEBUG] Hook output does not start with {, treating as plain text
```

### 4. Hook マッチャー検証（直接実行）

`hooks.json` の matcher と各シェルの case 文を検証するため、Hook 入力 JSON を `stdin` に流し、`CLAUDE_PLUGIN_ROOT` を一時 dir に差し向けて疑似発火させた（合成 `pending-decisions.md` を含む）。

## 結果詳細

### A. スラッシュコマンド一覧（16 本検出）

`/aid-*`（8 本）:

| # | コマンド | 用途 |
|---|---|---|
| 1 | `/aid-architect-author` | 対象プラグインの `<usecase>-architect.md` を中身ごと埋める |
| 2 | `/aid-dp-register` | 新規プラグインの判断ポイント候補を Notion 判断ポイントカタログDB に起票 |
| 3 | `/aid-references-new` | 対象 Skill に言語別 references レシピと templates 雛形を起稿 |
| 4 | `/aid-sample-case-binding` | sample-inputs/ に xtone-shared-plugin/sample-cases/ から symlink を張る（B-21） |
| 5 | `/aid-scaffold` | AIデリバリ用プラグインの骨格生成（generate-plugin.sh の対話実行） |
| 6 | `/aid-skill-creator-design` | 新規ユースケースのメタ設計（aid-skill-creator-architect 起動） |
| 7 | `/aid-skill-new` | 対象プラグインに新 Skill を SKL-12 / SKL-20 準拠で起稿 |
| 8 | `/aid-validation-runner` | validate-plugin.sh を実行し警告を pending-decisions.md に整形追記 |

基盤コマンド（8 本）:

| # | コマンド | 用途 |
|---|---|---|
| 1 | `/status` | 状態確認 |
| 2 | `/next` | 次アクション提案 |
| 3 | `/req-collect` | 要件収集 |
| 4 | `/design` | 設計 |
| 5 | `/implement` | 実装 |
| 6 | `/decide` | 判断記録 |
| 7 | `/pending-list` | 未決一覧 |
| 8 | `/skip-review` | AI レビュー |

### B. Subagent 一覧（7 体検出）

| name | 役割 |
|---|---|
| `aid-skill-creator-architect` | メタ設計スペシャリスト（`/aid-skill-creator-design` から起動） |
| `requirements-analyst` | 要件収集（`/req-collect`） |
| `designer` | 設計（`/design`） |
| `implementer` | 実装（`/implement`） |
| `reviewer` | 品質ゲート検証（`/skip-review`、pre-pr-merge Hook） |
| `pending-watcher` | 未決可視化（`/pending-list`、pre-phase-transition Hook） |
| `decision-recorder` | 判断記録（`/decide`） |

### C. Skill 一覧（9 件検出）

| name | 概要 |
|---|---|
| `aid-skill-creator-plugin-guide` | 作業ガイド（新規ユースケース T-023〜T-045 Rollout） |
| `aid-plugin-scope-extraction` | 要件: `plugin-scope.json` 生成 |
| `aid-domain-architect-design` | 設計: `<usecase>-architect.md` 雛形を中身ごと |
| `aid-plugin-architecture-design` | 設計: `plugin-architecture.{md,json}` 生成 |
| `aid-skill-authoring` | 実装: SKL-12/SKL-20 準拠で新 Skill 起稿 |
| `aid-references-authoring` | 実装: `references/<stack>.md` + `templates/<stack>/` |
| `aid-validation-runner` | 実装末尾: `validate-plugin.sh` ラップ |
| `aid-plugin-scaffold` | 実装: `generate-plugin.sh` 対話ラップ |
| `aid-decision-point-registration` | 実装: DP-DRAFT を Notion DP-DB に書き込み |

すべて frontmatter の `name`, `description` が読み取れており Skill 選択候補に出る状態（Claude の応答で 9 件すべて列挙された）。

### D. Hook 発火検証

`hooks/hooks.json` 登録 3 本＋未登録 1 本（仕様通り）。

| Hook | イベント | matcher | 直接実行での発火 |
|---|---|---|---|
| `pre-phase-transition.sh` | `UserPromptSubmit` | `""`（全 prompt） | `/design`, `/implement`, `/test`, `/<plugin>:design` でケース内マッチ → 警告出力／その他は冒頭 exit 0 ✅ |
| `pre-pr-merge.sh` | `PreToolUse` | `Bash` | `git push` を含むコマンドでマッチ → 警告出力／`ls` 等では出力なし ✅ |
| `post-decision-record.sh` | `PostToolUse` | `Write\|Edit` | `docs/adr/ADR-*.md` への書き込みで警告出力／その他ファイルでは出力なし ✅ |
| `post-pr-merge.sh` | （未登録） | — | スクリプト先頭で「PR マージは Claude Code 外イベントのため hooks.json には登録しない」と明示。CI / 手動実行で `git log --merges` を出力 ✅ |

`pre-phase-transition.sh` の `DP-*` 検出は ADR-AID-002 で定義した 3 形式（`DP-NNN` / `DP-<USECASE>-NN` / `DP-<DOMAIN>-<TOPIC>-NNN`）すべてに対応していることを実 stdin で確認（DP-007 / DP-PAYMENT-01 / DP-AID-99 を含む合成 `pending-decisions.md` で 3 件カウント成立）。

### E. 実起動時の挙動

```text
[DEBUG] Read hooks.json for plugin xtone-aid-skill-creator-plugin (enabled=true)
[DEBUG] Loading hooks from plugin: xtone-aid-skill-creator-plugin
[DEBUG] Registered 5 hooks from 19 plugins
[DEBUG] Hook output does not start with {, treating as plain text  ← UserPromptSubmit Hook 発火
[DEBUG] Hook output does not start with {, treating as plain text  ← Stop 等の Hook 発火
```

- 起動エラーなし
- プラグインから 16 commands, 7 subagents, 9 skills が認識
- UserPromptSubmit Hook が毎プロンプトで発火（pending-decisions が空のため stderr 出力なし → exit 0）

## 確認できなかった項目（手動 / インタラクティブ推奨）

`--print` / `--disallowedTools "*"` 制約下では確認しきれない以下は、必要に応じ人手でインタラクティブ起動して確認する。

- `/aid-dp-register` の Notion MCP 接続前提エラー出力（`.mcp.json` 未設定環境で「正しくエラーになる」挙動）
- `/aid-skill-creator-design` を実際に試打して `aid-skill-creator-architect` Subagent に処理が委譲されるシーケンス全体（コマンド・Subagent ともに認識は ✅ 済）
- Skill 自動選択（プロンプト「新しいプラグインを作りたい」等で `aid-skill-creator-plugin-guide` 等が候補に出るかの観察）

実コマンド:

```bash
cd ai-delivery
claude --plugin-dir plugins/xtone-aid-skill-creator-plugin
> /aid-skill-creator-design
> /aid-dp-register  # MCP 未設定だとエラーが正しい
```

## DoD 充足状況

- [x] `/aid-*` 8 本と基盤 8 本がコマンド一覧に表示される
- [x] `aid-skill-creator-architect` Subagent が呼び出し可能
- [x] 各 SKILL.md の frontmatter description が Claude の Skill 選択候補に出る
- [x] Hook 4 本がイベントマッチャー通り発火（登録 3 本 + 仕様通り未登録 1 本）
- [x] 不具合なし（追加 Issue 起票不要）
- [x] 起動ログを `delivery/startup-test-log.md` に記録（本ファイル）

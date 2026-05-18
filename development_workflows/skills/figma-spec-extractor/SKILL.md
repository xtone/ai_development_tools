---
name: figma-spec-extractor
description: Figma のワイヤーフレーム URL から仕様書一式を docs/ 配下に Markdown で抽出するスキル。ページ構成・ユースケース・アクター・データモデル・コンポーネントを 15 ステップで段階的に生成し、整合性／データモデル／コンポーネントの 3 レビューを作成する。**既存リポジトリの機能拡張モード** では既存モデル・ルーティング・ビューを再利用優先。**レビュー反復反映ステップ** では質問ループで方針を確定しドキュメントに反映する。Figma URL が提供されたとき、Figma デザインから実装用仕様書を作りたいとき、または既存仕様書の精度向上を求められたときに使用する。
---

# Figma Spec Extractor

Figma ワイヤーフレームから仕様書一式を段階的に抽出し、`docs/` 配下に Markdown で出力する。**Figma に明示的に無い属性は推測補完しない** が、構成要素から客観的に導ける範囲（ページ役割、状態遷移、設計示唆、典型ペインポイント等）は本体に含める。

## 出力構造

```
docs/
├── existing-codebase.md             # extension モードのみ
├── pages/
│   ├── README.md                    # ページインデックス + 横断サマリー
│   └── <page-slug>.md               # 6 セクション固定: 構成要素 / テキスト要素一覧 / アクションボタン / 参照モデル / 利用コンポーネント / 関連する未解決事項
├── use-cases.md
├── actors.md
├── data-model.md
├── components.md
└── reviews/
    ├── coverage-review.md
    ├── data-model-review.md
    └── components-review.md
```

## ID 命名規則（スコープ付き）

| 対象 | ID 形式 | 例 |
|---|---|---|
| ユースケース | `UC-XX` | `UC-01` |
| アクター | `A-XX` | `A-01` |
| Entity | `E-XX` | `E-01` |
| Entity のカラム | `E-XX.C-YY` | `E-01.C-03` |
| Entity のインデックス | `E-XX.I-YY` | `E-01.I-01` |
| Relation | `R-XX` | `R-01` |
| コンポーネント | `CMP-XX` | `CMP-01` |
| コンポーネントのパラメータ | `CMP-XX.P-YY` | `CMP-01.P-02` |
| コンポーネントのイベントハンドラ | `CMP-XX.H-YY` | `CMP-01.H-01` |

数字は **発見順にゼロパディング 2 桁** で採番。後続ステップで参照する際は必ずこの ID を使い、**必ず名前を併記** する（例: `` `E-02.C-06`（Award.application_close_at） ``）。

## 補完しない原則 と 客観抽出の許容範囲

### 禁止（推測補完）

- Figma に存在しない属性（業務要件、KPI、戦略目標）を勝手に書き起こす
- 「ありそう」な追加機能（例: ユーザー登録、認証、決済）を勝手に追加する
- ペルソナの架空属性（具体的な年齢、職業、家族構成）をでっち上げる

### 許容（客観抽出。本体ドキュメントに記述してよい）

- ページ名称＋構成要素から導ける **役割記述**
- 属性の状態遷移／ライフサイクル（ENUM 値自体は Figma にある）
- CMS／運用／SEO の設計示唆（構成から自然に導出される）
- アクターの分類（プライマリ／セカンダリ／オフステージ）と典型ペインポイント
- アクションの挙動概要（構成要素名＋親要素＋アイコンから一意に決まるもの）

### Figma 未記載のままにする項目

レビューステップ（Step 6 / 9 / 12）で初めて不足を列挙し、ユーザーに提示する。本体側で「未記載」と書くのは、上記「許容」にも当てはまらない場合のみ。

## 前提条件

1. `figma-dev` MCP サーバー（`Figma:get_design_context` 等）が認証済み（未認証なら `/mcp` で認証を促す）
2. 出力先のディレクトリで作業中
3. ユーザーから以下を取得済み：
   - Figma URL（`https://www.figma.com/design/:fileKey/...`）
   - **プロジェクトのゴール**（レビュー時の評価軸として必須）
   - **転記先**（ローカル Markdown / Notion / GitHub Wiki 等）
   - **実装モード**（次項参照）

## 実装モード × 実行モード

### 実装モード（Step 0 で確認）

| モード | 用途 | Step 0.5 の実行 |
|---|---|---|
| `new` | 新規アプリ | スキップ |
| `extension` | 既存アプリの機能拡張 | **実行**（既存資産再利用が前提） |

`extension` モードでは既存モデル → カラム追加 → 新規 Entity の優先順位で設計する。詳細は [`references/extension-mode-guide.md`](references/extension-mode-guide.md) 参照。

### 実行モード（Step 0 で確認）

| モード | 確認頻度 | Step 14 |
|---|---|---|
| ハイブリッド（推奨） | Step 0 / 1 / 4 / 7 / 6 / 9 / 12 後 | ユーザー意向に応じて |
| 全自動 | レビュー提示のみ | 質問ループあり |
| 反復反映（`extension` 推奨） | ハイブリッドと同じ | **必ず実行** |

### 推奨パス

| ケース | 推奨モード組み合わせ |
|---|---|
| 新規アプリ + 軽量利用 | `new` + ハイブリッド |
| 既存リポジトリの機能拡張 | `extension` + 反復反映 |

## ステップ概要

| Step | 内容 | モデル | 並列化 | 対象 |
|---|---|---|---|---|
| 0 | 準備（URL + ゴール + 転記先 + 実装モード取得） | 親（Opus） | — | 全モード |
| 0.5 | 既存コードベース調査 | サブ（Sonnet） | — | **extension のみ** |
| 1 | ページ一覧抽出 + キャンバスサイズ自動検出 | 親 + Figma MCP | — | 全モード |
| 2 | 各ページ構造抽出 | サブ（Sonnet） | ページ単位で並列 | 全モード |
| 3 | 各ページのアクション抽出（ソース列付） | サブ（Sonnet） | ページ単位で並列 | 全モード |
| 4 | ユースケース抽出 | 親（Opus） | — | 全モード |
| 5 | アクター抽出 + UC×Actor マトリクス | 親（Opus） | — | 全モード |
| 6 | 整合性レビュー + 横断サマリー追記 | 親（Opus） | — | 全モード |
| 7 | データモデル抽出（状態遷移 + 設計メモ） | 親（Opus） | — | 全モード |
| 8 | 各ページにモデル参照を追記 | サブ（Sonnet） | ページ単位で並列 | 全モード |
| 9 | データモデルレビュー | 親（Opus） | — | 全モード |
| 10 | コンポーネント抽出（共通化方針 + マッピング検証） | 親（Opus） | — | 全モード |
| 11 | 各ページにコンポーネント参照を追記 | サブ（Sonnet） | ページ単位で並列 | 全モード |
| 12 | コンポーネントレビュー | 親（Opus） | — | 全モード |
| 13 | 各ページに「関連する未解決事項」を追記 | サブ（Sonnet） | ページ単位で並列 | 全モード |
| 14 | レビュー反復反映（質問ループ → 全関連ドキュメント反映） | 親 + サブ | レビュー単位は直列／反映は並列 | 反復反映モード推奨 |

## モデル割当の方針

| 用途 | モデル |
|---|---|
| Figma JSON → Markdown 整形（Step 2 / 3 / 8 / 11 / 0.5 / 14c） | Sonnet |
| 合成・抽象化（Step 4 / 5） | Opus |
| 設計判断（Step 7 / 10） | Opus |
| レビュー判定（Step 6 / 9 / 12） | Opus |
| 質問ループ設計（Step 14a / 14b） | Opus |

## ステップ詳細

### Step 0: 準備

1. ユーザーから確認：
   - Figma URL（無ければ依頼）
   - プロジェクトのゴール（レビューで利用するため必須）
   - 出力ディレクトリ（デフォルト `docs/`）
   - 転記先（Notion 等の場合、相対パスリンクは「{{ファイル名}}（別ページ）」表記に切替）
   - **実装モード**: 作業ディレクトリに既存リポジトリ（`Gemfile` / `package.json` / `app/` / `src/`）が存在するなら `extension` を提案。それ以外は `new`
2. URL から `fileKey` を抽出
3. `docs/pages/` と `docs/reviews/` を作成
4. 既存 `docs/` の有無を確認し、上書きの可否を確認
5. プロジェクトゴールを `docs/reviews/coverage-review.md` の先頭に保存
6. `extension` モードなら Step 0.5 を実行

### Step 0.5: 既存コードベース調査（extension モードのみ）

詳細は [`references/extension-mode-guide.md`](references/extension-mode-guide.md) 参照。

Sonnet サブエージェント 1 つで既存リポジトリの主要資産を調査し、`docs/existing-codebase.md` に出力：

- 既存モデル一覧（Figma 関連度の 4 段階評価付き）
- 既存ルーティング（Figma 関連のみ）
- 既存ビュー資産
- 既存設定（Settings 等）
- **再利用候補のサマリー**（Step 7 / 14 で参照される最重要セクション）

サブエージェント用プロンプトは [`references/sub-agent-prompts.md`](references/sub-agent-prompts.md) の Step 0.5 セクション参照。

### Step 1: ページ一覧抽出

1. `figma-use` スキルをロード
2. `Figma:get_metadata` または `use_figma` で全ページ／トップレベルフレームを列挙
3. 実装対象を判定（Slice や注釈帯は除外）
4. **キャンバスサイズ自動検出**:
   - 全実装対象ページの width を集計し、一意な値が 1 つしか無い場合 → 「単一幅設計（モバイル想定）」と判定し README の「未確認・要追加情報」に自動追記
   - 一意な値が 2 つ以上ある場合 → レスポンシブ対応済みと判定
5. **プロトタイプ Reactions の有無検出**:
   - Reactions が 1 件も無い場合 → ワイヤーフレームレベルと判定
   - 一部のみ設定 → 混在モード
6. 各ページのスラッグを決定
7. `docs/pages/README.md` の骨組みを作成（横断サマリーは Step 6 で追記）

### Step 2-3: 各ページ構造・アクション抽出（並列）

Sonnet サブエージェントをページ単位で並列起動。プロンプト詳細は [`references/sub-agent-prompts.md`](references/sub-agent-prompts.md) 参照。

- **Step 2**: 構成要素一覧表、テキスト要素、ページ役割概要（客観抽出可）
- **Step 3**: アクションボタン一覧（**ソース列付**、語彙制限あり）

### Step 4: ユースケース抽出

`docs/pages/` 全件を Read し、明示的に読み取れる UC を `docs/use-cases.md` に列挙。ハイブリッドモードではサマリ確認を挟む。

各 UC の必須フィールド: UC-XX / ユースケース名 / ユースケースカテゴリ / 目的 / シナリオ / 前提・後続 UC / データ更新の有無。

### Step 5: アクター抽出 + UC×Actor マトリクス

`docs/use-cases.md` から登場アクターを集約し、`docs/actors.md` を生成。

- 各アクターの必須フィールド: A-XX / 名前 / 分類（プライマリ・セカンダリ・オフステージ）/ 役割 / ゴール / 典型ペインポイント / 主なオペレーション / UC 一覧
- **UC×Actor マトリクス必須**（行=UC、列=全アクター、関与は「●」）
- マトリクス直後に「読み取れる事実」を散文で追記

### Step 6: 整合性レビュー + 横断サマリー追記

#### 6a: 整合性レビュー（出力のみ）

`docs/reviews/coverage-review.md` に以下を列挙：

- ゴールから見て足りない UC / Actor
- UC から見て足りない Page / Action Button

#### 6b: 横断サマリー追記（pages/README.md）

- 共通要素（Header / Footer / Menu Overlay）
- サイト全体のインタラクション分布
- **エンティティ／データ設計上の示唆**（Step 7 の入力）
- 未確認・要追加情報

### Step 7: データモデル抽出

1. `docs/pages/README.md` の「エンティティ／データ設計上の示唆」セクションを Read（Step 7 の起点）
2. `docs/pages/` 全件を Read
3. **extension モードの場合**: `docs/existing-codebase.md` の「既存モデル一覧」「再利用候補のサマリー」を Read
4. 明示的に読み取れる Entity / Relation を分類
5. `docs/data-model.md` を生成（**状態遷移セクションと設計メモ必須**）
6. ハイブリッドモードでは Entity 一覧サマリ確認

#### 過剰定義の回避

「Figma に対応ページ／表示要素が存在しない汎用 Entity」（`StaticPage`、`User`、`Session` 等）は本体に定義せず、レビュー側で提案するに留める。

#### extension モードでの設計優先順位

1. 既存モデルそのまま再利用
2. 既存モデルにカラム追加
3. 既存カラムの用途流用（**衝突有無を実コード grep で確認必須**）
4. 新規 Entity 作成

詳細は [`references/extension-mode-guide.md`](references/extension-mode-guide.md) の「Step 7 拡張」セクション参照。

### Step 8: 各ページにモデル参照を追記（並列）

Sonnet サブエージェントをページ単位で並列起動。詳細は [`references/sub-agent-prompts.md`](references/sub-agent-prompts.md) 参照。

#### 親エージェントの責務

1. **事前準備**: `data-model.md` から使用可能 Entity / カラム ID リストを抽出してサブのプロンプトに含める（リスト外の捏造を防ぐ）
2. **事後検証**: `grep "^## 参照モデル" docs/pages/*.md` で全ページに 1 行ずつヒットすることを確認

#### 集約ルール（冗長性削減）

- 同一カラムを参照する複数の表示要素は集約
- 静的文言は 1 行にまとめる
- セクションあたりの行数の目安は 8 行以内（**可読性を担保するため**）

### Step 9: データモデルレビュー（出力のみ）

`docs/reviews/data-model-review.md` に以下を列挙（**優先度ラベル「必須／推奨／オプション」必須**）：

- ページに表示要素があるのに対応する Entity / カラムが無い
- Entity / カラムの過剰定義
- FK の整合性
- インデックスの過不足

### Step 10: コンポーネント抽出

1. `docs/pages/` 全件を Read
2. `extension` モードの場合、既存 UI 資産（`docs/existing-codebase.md` の「既存ビュー資産」）を考慮
3. 表示要素を Atomic Design（Atoms / Molecules / Organisms / Templates）に分類
4. **冒頭に「共通化方針サマリー」セクションを配置**
5. **ページ→Organism マッピング検証表を必須化**（未対応セルが 1 つでも残れば追加）
6. `docs/components.md` を生成

詳細は [`references/extension-mode-guide.md`](references/extension-mode-guide.md) の「Step 10 拡張」セクション参照。

各コンポーネントの必須フィールド: CMP-XX / 名前 / 概要 / Atomic Design 種別 / パラメータ一覧 / イベントハンドラ一覧。

### Step 11: 各ページにコンポーネント参照を追記（並列）

Step 8 と同じパターン。詳細は [`references/sub-agent-prompts.md`](references/sub-agent-prompts.md) 参照。

#### 集約ルール

- 出力対象は **Organism / Template / 主要 Molecule のみ**（Atom は内包される設計のため省略）
- 同一コンポーネントの複数利用箇所は「利用箇所数」に集計

#### 親エージェントの事後検証

```bash
grep "^## 利用コンポーネント" docs/pages/*.md
```

ページで使われている CMP-XX が `components.md` に実在するかも検証する。

### Step 12: コンポーネントレビュー（出力のみ）

`docs/reviews/components-review.md` に以下を列挙（**優先度ラベル必須**）：

- ページに表示要素があるのに対応するコンポーネントが無い → 通常「必須」
- コンポーネントが定義されているが使われていない → 通常「オプション」
- 類似コンポーネントの共通化候補 → 通常「推奨」
- パラメータ・イベントハンドラの過不足 → 内容により分類

### Step 13: 各ページに「関連する未解決事項」を追記（並列）

3 つのレビューを Read し、自ページに関連する不足項目を逆引きで抽出。

抽出ルール:
- coverage-review の「足りない Page / Action」で自ページ言及あり
- data-model-review の「ページにあるがモデルに無い」で自ページ slug
- components-review の「ページにあるがコンポーネント未定義」で自ページ slug

該当なしの場合は「該当なし」と記載。

### Step 14: レビュー反復反映

詳細は [`references/step-14-review-iteration.md`](references/step-14-review-iteration.md) 参照。

#### 進行チェックリスト（コピーして使用）

```
Step 14 進行:
- [ ] データモデルレビュー: 質問ループ完了
- [ ] データモデルレビュー: data-model.md 反映完了
- [ ] データモデルレビュー: pages/ 並列反映完了
- [ ] 整合性レビュー: 質問ループ完了
- [ ] 整合性レビュー: coverage-review.md 反映完了
- [ ] 整合性レビュー: pages/actors/use-cases 並列反映完了
- [ ] コンポーネントレビュー: 質問ループ完了
- [ ] コンポーネントレビュー: components.md 反映完了
- [ ] コンポーネントレビュー: pages/ 並列反映完了
- [ ] 最終サマリーをユーザーに提示
```

#### 質問ループの要点

- **データモデル → 整合性 → コンポーネント** の順で処理
- **1 ラウンドで 4 件以内**（`AskUserQuestion` ツールの質問数上限のため）
- 関連項目は **1 質問に集約**（例: ON DELETE 挙動 6 件を 1 質問に）
- Figma 未定義／デザイン待ち項目は質問せず「デザイン待ち」ラベル付与

## 並列起動の実装パターン

ステップ単位の並列起動は **1 メッセージ内で複数の Agent ツール呼び出しを並べる** ことで実現：

```js
// Step 2 並列起動の擬似コード
const pages = ["top", "award-detail-open", ...];
const agents = pages.map(p => Agent({
  description: `${p} 構造抽出`,
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: extractStep2Prompt(p),
}));
```

Step 0.5 / 2 / 3 / 8 / 11 / 13 / 14c がページ単位またはレビュー単位で並列化されるステップ。

## ハイブリッド対話のチェックポイント

| タイミング | 確認内容 | スキップ条件 |
|---|---|---|
| Step 0 | URL / ゴール / 転記先 / 出力先 / 実装モード | すべて提示済み |
| Step 0.5 後 | 既存コードベース調査結果 | new モード時 |
| Step 1 後 | 抽出ページ一覧 + キャンバスサイズ検出結果 | 全自動モード時 |
| Step 4 後 | UC 一覧サマリ（任意） | 全自動モード時 |
| Step 7 後 | データモデル Entity 一覧サマリ（任意） | 全自動モード時 |
| Step 6 / 9 / 12 後 | 各レビュー結果（優先度ラベル付） | **スキップ不可** |
| Step 13 後 | 各ページの「関連する未解決事項」追記確認 | 全自動モード時 |
| Step 14 中 | レビュー反復反映の質問ループ | ユーザーが Step 14 を希望しない場合 |
| Step 14 後 | 反映後の最終サマリー | スキップ不可（Step 14 実行時） |

## エラー時の挙動

- Figma MCP 未認証 → `/mcp` での認証を促す
- ノードID エラー → URL の fileKey 部分を確認、ユーザーに再提示を依頼
- サブエージェント失敗 → 親が直接リトライ（Sonnet → Opus フォールバック）
- 出力ファイルが既存 → 上書き／追記／中止をユーザーに確認
- 「Figma 未記載」項目が多い → そのまま「未記載」表記で進める（レビューステップで列挙）

## 仕上げ

全 13 ステップ（および希望時は Step 14）完了後、**最終検証を必須化**：

### 最終検証チェックリスト

```bash
# 1. 全ページに 6 セクションが揃っているか
for f in docs/pages/*.md; do
  if [ "$(basename $f)" != "README.md" ]; then
    echo "=== $f ==="
    grep "^## " "$f"
  fi
done
```

期待される 6 セクション（順序固定）:
1. `## 構成要素`
2. `## テキスト要素一覧`
3. `## アクションボタン`
4. `## 参照モデル`
5. `## 利用コンポーネント`
6. `## 関連する未解決事項`

### Entity / CMP の整合性検証

```bash
grep -ho "E-[0-9]\+" docs/pages/*.md | sort -u > /tmp/used_entities.txt
grep -ho "E-[0-9]\+" docs/data-model.md | sort -u > /tmp/defined_entities.txt
diff /tmp/used_entities.txt /tmp/defined_entities.txt
```

ページで使われている ID がマスタに無ければサブエージェントが番号を捏造した可能性が高い。該当ページを再実行。

### Step 14 実行時の追加検証

```bash
# 解消マークが付いた項目数を確認
for f in docs/reviews/*.md; do
  echo "=== $f ==="
  grep -c "解消済み" "$f"
done

# 取り下げ ID の能動的参照（取り下げ説明以外）が残っていないか
grep -rn "{{取り下げた ID パターン}}" docs/pages/ docs/actors.md docs/use-cases.md | \
  grep -v "取り下げ\|統合\|解消済み\|旧\|~~"
```

### 完了報告

1. 生成ファイル一覧と各ファイルの行数（extension モード時は `docs/existing-codebase.md` も含む）
2. 3 つのレビューレポートのサマリ（不足検出数 + 優先度別件数）
3. **Step 14 実行時**: 仕様確認反復プロセスの解消件数と、残存項目の性質（Figma デザイン待ち／将来要件）
4. ユーザーが手動で対応すべき必須項目
5. 最終検証結果（セクション完備、ID 整合性 OK）

## 関連スキル・参照ファイル

### スキル

- `figma-use` — `use_figma` MCP ツールを呼ぶ前にロード必須（公式 Figma プラグインに含まれる）

### references/ ディレクトリ

- [`extension-mode-guide.md`](references/extension-mode-guide.md) — extension モードの Step 0.5 / 7 / 10 詳細ガイド
- [`step-14-review-iteration.md`](references/step-14-review-iteration.md) — レビュー反復反映の完全プロセス
- [`sub-agent-prompts.md`](references/sub-agent-prompts.md) — サブエージェント用プロンプトテンプレート
- [`output-templates.md`](references/output-templates.md) — 出力 Markdown の骨組み

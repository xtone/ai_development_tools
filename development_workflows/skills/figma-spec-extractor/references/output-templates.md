# 出力ドキュメントテンプレート

各ステップが生成する Markdown の骨組み。`{{ ... }}` はプレースホルダ、`<!-- 説明 -->` は実装メモ。

## ID 命名規則（再掲）

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

採番は **発見順にゼロパディング 2 桁**。Figma 未記載の項目は値ではなく「Figma 未記載」と表記する（ただし SKILL.md の「客観抽出の許容範囲」に該当する場合は記述する）。

---

## docs/pages/<slug>.md

Step 2 で生成、Step 3 / 8 / 11 で順次追記される。

```markdown
# {{ページ名}}

- **ノードID**: `{{nodeId}}`
- **キャンバスサイズ**: {{width}} × {{height}} px
- **ページの役割概要**: {{ページ名称＋構成要素から導ける役割を 1〜2 文で記述。完全に推測になる場合のみ「Figma 未記載」}}

## 構成要素

| # | 構成要素名 | 種類 | ノードID | 役割概要 |
|---|---|---|---|---|
| 1 | {{要素名}} | {{FRAME / TEXT / FRAME(Card) など}} | `{{nodeId}}` | {{役割。構成要素から客観的に導けるなら 1 文。完全に推測なら「Figma 未記載」}} |
| 2 | ... | ... | ... | ... |

## テキスト要素一覧

各構成要素内のテキスト要素を 1 表に集約（H3 で構成要素別に分けない）。

| ノードID | 種別 | テキスト（Figma 表記そのまま） |
|---|---|---|
| `{{nodeId}}` | TEXT | 「{{テキスト}}」 |
| `{{nodeId}}` | TEXT | 「{{プレースホルダー文字列も含む}}」 |

<!-- TEXT ノードのみ列挙。FRAME / VECTOR は構成要素表で扱う。15〜25 行程度が目安 -->

<!-- ===== Step 3 が追記 ===== -->

## アクションボタン

<!-- ケース A: 全件同一ソース（推奨） -->
**ソース**: 全件「客観推定」（このページのプロトタイプ Reactions は未設定）

| # | 構成要素名 | ノードID | アクション種別 | 挙動概要 |
|---|---|---|---|---|
| 1 | {{要素名}} | `{{nodeId}}` | {{ページ遷移 / 外部リンク / ...}} | {{挙動。客観推定で 1 文}} |

<!-- ケース B: 混在の場合（Figma 明示と客観推定が両方ある等）— ソース列を残す -->

| # | 構成要素名 | ノードID | アクション種別 | 挙動概要 | ソース |
|---|---|---|---|---|---|
| 1 | {{要素名}} | `{{nodeId}}` | ... | ... | Figma 明示 / 客観推定 / Figma 未記載 |

<!-- ソース判定基準：
  - Figma 明示: Figma の Prototype Reactions パネルで明示的に reaction が設定されている（`node.reactions.length > 0`）
  - 客観推定: それ以外で構成要素から挙動が客観的に導ける（ワイヤーフレームでは多数派）
  - Figma 未記載: 完全に推測になる場合のみ
  - ❌ アイコン向き・色・テキスト表記は「Figma 明示」ではない（UI 状態と reaction の混同に注意）
-->

<!-- ===== Step 8 が追記 ===== -->

## 参照モデル

各構成要素が参照する Entity のカラムをマッピング。詳細は [`docs/data-model.md`](../data-model.md) 参照。

### {{セクション名}} (`{{nodeId}}`)
| 表示要素 | 参照 |
|---|---|
| {{表示テキスト or 要素名}} | `E-XX.C-YY`（{{Entity名}}.{{カラム名}}）/ 静的 / 対応モデル未定義（要レビュー） |

### 利用 Entity サマリー
`E-XX`, `E-YY`, ...

<!-- 集約ルール：同一カラム参照は 1 行に集約、静的文言群も 1 行に集約、セクションあたり 8 行以内目安 -->

<!-- ===== Step 11 が追記 ===== -->

## 利用コンポーネント

各構成要素が利用するコンポーネント（Organism 中心）。詳細は [`docs/components.md`](../components.md) 参照。

| # | 構成要素名 | ノードID | コンポーネント | 利用箇所数 |
|---|---|---|---|---|
| 1 | {{要素名}} | `{{nodeId}}` | `CMP-XX`（{{コンポーネント名}}） | {{n}} |
| N | ページ全体レイアウト | `{{page_root_id}}` | `CMP-80`（StandardPageTemplate） | 1 |

<!-- 集約ルール：Organism / Template / 主要 Molecule のみ、ページあたり 15 行以内目安 -->

<!-- ===== Step 13 が追記（必須） ===== -->

## 関連する未解決事項

各レビューレポートで本ページに紐づく不足項目を逆引きしたサマリ。詳細は各レビューレポートを参照。

**フォーマット厳守**: `- #N: 概要 — **優先度**` の単一形式。

- **整合性レビュー** ([reviews/coverage-review.md](../reviews/coverage-review.md)):
  - #1: Award Card のステータス別遷移先振り分けロジック未定義 — **必須**
  - #2: Article Card の記事種別判別ロジック未定義 — **推奨**
- **データモデルレビュー** ([reviews/data-model-review.md](../reviews/data-model-review.md)):
  - 該当なし
- **コンポーネントレビュー** ([reviews/components-review.md](../reviews/components-review.md)):
  - #1: `CMP-45 AwardCard` の Union 型を整理 — **必須**
```

---

## docs/pages/README.md

Step 1 で骨組みを作成、Step 6b で **横断サマリーを追記**。

```markdown
> 上位ドキュメント: [ユースケース](../use-cases.md) ／ [アクター](../actors.md) ／ [データモデル](../data-model.md) ／ [コンポーネント](../components.md) ／ [レビュー](../reviews/)

# {{プロジェクト名}} — ページ構成ドキュメント

{{プロジェクト概要を 1〜2 文で記述。Figma ファイルから読み取れる範囲で}}

- Figma ファイル: <{{Figma URL}}>
- プロジェクトのゴール: {{Step 0 で取得したゴール}}
- 設計対象: {{モバイル / PC / レスポンシブ。Figma のキャンバスサイズから読み取り}}
- 抽出日: {{YYYY-MM-DD}}

## ページ一覧

| # | 種別 | ページ名 | ノードID | ページの役割概要 | ドキュメント |
|---|---|---|---|---|---|
| 1 | ページ | {{ページ名}} | `{{nodeId}}` | {{役割（1 文）}} | [{{slug}}.md](./{{slug}}.md) |

## 除外ノード（実装対象外）

| ノードID | 名前 | 除外理由 |
|---|---|---|
| `{{nodeId}}` | {{名前}} | {{SLICE 型／注釈帯／参考用 等}} |

<!-- ===== Step 6b で追記 ===== -->

## 共通要素（横断的な実装方針）

各ページに繰り返し登場する以下の要素は、共通コンポーネントとして抽出することを推奨します。

### 共通レイアウト
- **Header**: {{各ページ共通のヘッダー構造。バリアント有無も明記}}
- **Footer**: {{共通フッター構造。例外があれば明記}}
- **Menu Overlay**: {{グローバルナビゲーション}}

### 共通 UI パターン
- **Section Header**: {{各セクション冒頭に繰り返し現れるヘッダー（アイコン円＋見出し等）}}
- **Status Label**: {{ステータスバッジ（募集中／選考中／結果発表等）}}
- **Card**: {{画像＋コンテンツの 2 層構造で繰り返し利用されるカード形式}}
- **CTA Button**: {{プライマリ／セカンダリ／テキストの 3 バリアント}}
- ...

## サイト全体のインタラクション分布

各ページのドキュメント末尾の「アクションボタン」セクションを集計したサマリー。

| アクション種別 | 主な発生場所 |
|---|---|
| ページ遷移（内部） | {{発生する場所のリスト}} |
| ページ遷移（外部リンク） | ... |
| ページ内アンカー | ... |
| オーバーレイ表示／クローズ | ... |
| 一覧フィルター | ... |
| アコーディオン展開／折りたたみ | ... |
| テキスト入力＋検索送信 | ... |
| スライド切替 | ... |

### データ送信を伴うフォーム要素
{{ワイヤー上に明示的なフォーム送信 UI があるかどうか。「Web 投稿フォーム」「お問い合わせフォーム」等が外部リンクの場合はそれを明記}}

## エンティティ／データ設計上の示唆

- {{ページ表示から導ける Entity 設計の方針。例: 状態を持つ共通エンティティのライフサイクル、テンプレート切替条件、ブロック型コンテンツの推奨など}}

## 未確認・要追加情報

Figma 未提供のため別途仕様確認が必要なページ・フォーム・遷移先。

- **PC（デスクトップ）レイアウト**: {{モバイル版のみの場合の注釈}}
- **{{未提供ページ A}}**: {{メニュー or フッターのリンク先として存在する想定だが、ワイヤーフレーム未提供}}
- **{{未提供フォーム}}**: {{複数の動線があるが、フォーム本体は未提供}}
```

---

## docs/use-cases.md（Step 4）

```markdown
# ユースケース一覧

{{プロジェクト名}}のユースケースを、[ページ構成](./pages/README.md) と各ページのアクションから整理したものです。Figma 未記載の項目は補完しません。

## ユースケース一覧（サマリー）

| ID | カテゴリ | 名前 | データ更新 |
|---|---|---|---|
| UC-01 | {{カテゴリ}} | {{名前}} | あり / なし |

## UC-XX: {{ユースケース名}}

- **カテゴリ**: {{ユースケースカテゴリ}}
- **目的**: {{1 文}}
- **シナリオ**:
  1. {{手順 1}}
  2. {{手順 2}}
- **前提のユースケース**: `UC-YY` / なし
- **後続のユースケース**: `UC-ZZ` / なし
- **データ更新の有無**: あり（{{何を更新するか}}） / なし

<!-- UC-XX を必要な数だけ繰り返す -->

## カテゴリ別インデックス

### {{カテゴリ名}}
- [UC-01: {{名前}}](#uc-01-...)
- [UC-02: {{名前}}](#uc-02-...)
```

---

## docs/actors.md（Step 5）

```markdown
# アクター一覧

[ユースケース一覧](./use-cases.md) で参照されるアクターを、属性・目的・関連 UC・典型ペインポイント付きで整理したものです。

## アクター分類の前提

- **プライマリアクター** = 本サイトの最重要ターゲット。サイト構造はこのアクターに最適化されている
- **セカンダリアクター** = 主要ではないが利用シナリオに含まれるユーザー
- **オフステージアクター** = サイト本体には登場しないが、ユースケースに影響する関係者（編集部・外部システム等）

## アクター一覧（サマリー）

| ID | 分類 | アクター名 | 役割 |
|---|---|---|---|
| A-01 | プライマリ | {{名前}} | {{役割}} |

## A-XX: {{アクター名}}

- **分類**: プライマリ / セカンダリ / オフステージ
- **役割**: {{システム上の位置づけ}}
- **アクターが達成したいゴール**: {{Figma から読み取れる範囲で}}
- **典型ペインポイント**: {{Figma の解決対象である UI 要素から逆算できる範囲で。例：FAQ で解消される疑問、Status Filter で解決される選別、Sticky CTA で解消される入口の不明確さ等}}
- **訪問頻度**: {{Figma の構造から推察できる場合のみ。例：締切前にスパイク、結果発表時に集中 等}}
- **利用デバイス**: {{Figma のキャンバス設計から読み取れる範囲。例：モバイル中心 / PC との併用 等}}
- **主なオペレーション**:
  - {{操作 1}}
  - {{操作 2}}
- **ユースケース一覧**: `UC-01`, `UC-03`, `UC-05`
- **ペルソナ例**: {{Figma の Hero コピー、CTA 文言、対象賞ジャンルから読み取れる場合のみ。無ければ「Figma 未記載」}}

## アクター × ユースケース マトリクス

**全アクター（プライマリ／セカンダリ／オフステージ）を列に含める**。オフステージアクター（編集部・SEO クローラー等）は UI 上の UC として明示しないため通常は空欄になるが、列としては存在を明記する。

| UC | タイトル | A-01 | A-02 | A-03 | A-04 | A-05 | A-06 |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| UC-01 | {{名前}} | ● | | ● | | | ● |
| UC-02 | {{名前}} | ● | | | | | |

オフステージアクター（A-05、A-06）が UI 上の UC に関与する例：
- A-06（SEO クローラー）は **公開ページの閲覧 UC** に「●」（クローラーは全公開 UC をアクセスする）
- A-05（編集部）は通常 UI 上の UC では空欄（管理画面の UC は別途）

### マトリクスから読み取れる事実

- **{{A-01}} が関わる UC は X / Y 件**。サイトの大部分が {{A-01}} のために設計されている
- **応募導線（UC-Y〜UC-Z）は {{A-01}} 専用**
- **結果確認（UC-A〜UC-B）は {{A-02 / A-03 / A-04}} が中心**
- **全アクター共通の UC は ナビゲーション系（Menu / Footer / 戻る）**

## 実装・設計上の含意

1. **{{A-01}} 最優先のスタイル設計**: {{ファーストビュー〜CTA までのスクロール完了率を計測する KPI を持つ等}}
2. **{{A-X}} のための {{機能}} 整備**: {{該当アクターのペインポイントに応じた施策}}
3. ...
```

---

## docs/data-model.md（Step 7）

```markdown
# データモデル

Figma のページ表示要素・アクションから明示的に読み取れる Entity と Relation を定義する。状態遷移と設計上のメモも併記する。

## Entity 一覧（サマリー）

| ID | モデル名 | 概要 |
|---|---|---|
| E-01 | {{モデル名}} | {{概要}} |

## Entity 定義

### E-XX: {{モデル名}}

- **概要**: {{1〜2 文の説明}}
- **PK**: `E-XX.C-YY`
- **FK**:
  - `E-XX.C-YY` → `E-AA`
  - {{無ければ「なし」}}

#### 属性

| カラムID | カラム名 | 型 | 制約 | 概要 |
|---|---|---|---|---|
| E-XX.C-01 | id | int | PK, NOT NULL | 主キー |
| E-XX.C-02 | {{name}} | {{型}} | {{制約: NOT NULL / UNIQUE / DEFAULT ... / ENUM(a,b,c)}} | {{概要}} |

#### インデックス

| インデックスID | 対象カラム | 種類 | 目的 |
|---|---|---|---|
| E-XX.I-01 | `E-XX.C-02` | UNIQUE | {{用途}} |
| E-XX.I-02 | `E-XX.C-03`, `E-XX.C-04` | 複合 | {{用途。一覧の絞り込み等}} |

#### 状態遷移（ENUM カラムを持つ Entity のみ）

```
{{初期状態}} ──(条件)──→ {{中間状態}} ──(条件)──→ {{最終状態}}
```

| 状態 | 必須となるカラム | 主な表示テンプレート |
|---|---|---|
| {{state-a}} | {{C-XX, C-YY}} | {{pages/xxx.md}} |
| {{state-b}} | {{C-ZZ}} | {{pages/yyy.md}} |

<!-- E-XX を必要な数だけ繰り返す -->

## Relation 一覧

| ID | 親 Entity | 子 Entity | 多重度 | 外部キー | 補足 |
|---|---|---|---|---|---|
| R-01 | `E-01` ({{名}}) | `E-02` ({{名}}) | 1 — N | `E-02.C-02` → `E-01.C-01` | {{補足}} |

## ER 構造（概略）

\`\`\`
{{ASCII ER 図。Entity を E-XX 形式で記載}}
\`\`\`

## 設計上のメモ

### 状態遷移と表示テンプレートの対応

{{status を持つ Entity の遷移と、各状態で表示されるページの対応をまとめる}}

| status | 主テンプレート | 必須となるフィールド |
|---|---|---|
| {{state}} | {{pages/xxx.md}} | {{列挙}} |

### CMS / 運用上の留意

- **編集 UI の構成**: {{タブ分割推奨。基本情報 / 賞金 / 審査員 / フロー / 要項 等}}
- **一括投入手段**: {{CSV インポート、API 一括登録の必要性}}
- **デフォルト値ルール**: {{display_order の自動採番、is_active のデフォルト等}}
- **バリデーション**: {{1 カテゴリにつき 1 件のみ true となる項目（FaqItem.is_default_expanded 等）}}

### SEO / 構造化データに向けた追加検討

- **OGP / メタデータ**: {{og_image_url, meta_description を持つべき Entity の列挙}}
- **構造化データ（JSON-LD）**: {{FAQ Schema, Event Schema 等の対象 Entity}}
- **URL 設計**: {{slug カラムの命名規則と階層}}

### 本データモデルに含めない要素

- {{会員機能、認証、決済、分析データなど対象外を明示}}
```

---

## docs/components.md（Step 10）

```markdown
# コンポーネント定義（Atomic Design）

Figma の表示要素を Atomic Design の 5 レイヤーで分類したものです。**類似要素は単一コンポーネント + Props（variant 等）に統合** することで実装・運用コストを削減します。

## Atomic Design レイヤー定義

| レイヤー | 役割 | 本プロジェクトでの粒度 | CMP 番号帯 |
|---|---|---|---|
| **Atoms** | 最小の表示部品 | アイコン・タイポ・ボタン・入力・バッジ | `CMP-01` 〜 `CMP-10` |
| **Molecules** | 小機能ユニット | 検索入力、ナビ項目、メッセージバブル等 | `CMP-11` 〜 `CMP-40` |
| **Organisms** | 機能セクション | ヘッダー、賞カード、選考フロー等 | `CMP-41` 〜 `CMP-79` |
| **Templates** | ページレイアウト骨組み | StandardPageTemplate, OverlayTemplate | `CMP-80` 〜 `CMP-89` |
| **Pages** | Templates にデータを流し込んだ完成形 | 実画面 | （番号不要） |

### 番号帯のルール
- 新規コンポーネント追加時は **該当レイヤーの番号帯内で連番末尾** に追加
- 既存 CMP の番号を変えない（後方互換性）
- 番号空きがあれば順次埋める

---

## 0. 共通化方針サマリー

### Atoms の統合

| 統合前（個別コンポーネント） | 統合後 | 統合プロパティ |
|---|---|---|
| Text/PageTitle, Text/SectionHeading, ... 9 種 | `Text` | `variant` |
| Button/Primary, Button/Secondary, ... | `Button` | `variant` + `leadingIcon` / `trailingIcon` |
| Badge/Status, Badge/Category, ... 8 種 | `Badge` | `variant` + `tone` |
| Icon/Menu, Icon/ArrowLeft, ... 28 種 | `Icon` | `name` |

### Molecules の統合

| 統合前 | 統合後 | 補足 |
|---|---|---|
| SearchInput | `Input` with `leadingIcon="search"` | 専用 Molecule を廃し Input + props で表現 |
| Date, RelatedTag, DeadlineRow | `IconText` | アイコン＋ラベルの汎用横並び |
| SectionHeader/WithIcon, SectionHeader/WithViewAll | `SectionHeader` | `iconName?`, `actionLabel?`, `onAction?` |
| MessageBubble/Editor, MessageBubble/Author | `MessageBubble` | `role` プロパティ |

### Organisms の統合

| 統合前 | 統合後 | 統合プロパティ |
|---|---|---|
| AwardCard, RelatedAwardCard | `AwardCard` | `mode: "summary" \| "related"` |
| StickyFooterCTA, FixedCTABanner | `StickyFooter` | `position` |
| NewsSection, ContentPickup, JudgesSection, ... | `ContentSection` を内部で利用 | `header`, `lead?`, `children`, `footer?` の汎用スロット |

### 統合の判断基準

- **見た目とレイアウトが似ている** → variant prop で吸収
- **構造は同じだが内容のみ違う** → props で吸収
- **コンテンツが完全に異なる** → 個別 Organism を維持
- **CMS のフィールドが大きく異なる** → 個別 Organism

---

## 1. Atoms

| CMP-XX | 名前 | Props | 概要 |
|---|---|---|---|
| CMP-01 | `Text` | `variant`, `children`, `color?` | テキスト表示。`variant`: pageTitle / sectionHeading / body / caption / label / number 等 |
| CMP-02 | `Icon` | `name`, `size?`, `color?` | SVG アイコン。`name` 候補は 28 種程度（Menu / ArrowLeft / Calendar / Trophy / ...） |
| CMP-03 | `Button` | `variant`, `label?`, `leadingIcon?`, `trailingIcon?`, `onClick?`, `href?`, `disabled?`, `fullWidth?` | プライマリ／セカンダリ／テキスト／アイコンの 4 バリアント |
| CMP-04 | `Badge` | `variant`, `tone`, `label`, `leadingIcon?` | ステータスラベル、カテゴリタグ、ランクバッジ等を統合 |
| CMP-05 | `Input` | `value`, `placeholder?`, `leadingIcon?`, `onChange?`, `onSubmit?` | テキスト入力。検索ボックスも `leadingIcon="search"` で表現 |
| CMP-06 | `Image` | `src`, `alt`, `aspectRatio?`, `variant?` | 画像／プレースホルダー。`variant`: placeholder / thumbnail / hero / logo |
| CMP-07 | `Divider` | `orientation?`, `inset?` | 区切り線 |
| CMP-08 | `Avatar` | `label`, `tone?`, `size?` | 円形アバター |
| CMP-09 | `Dot` | `active` | スライドインジケータの 1 ドット |

<!-- 必要な数だけ行を追加。1 Atom = 1 H2 は廃止 -->

---

## 2. Molecules

| CMP-XX | 名前 | Props | 概要 |
|---|---|---|---|
| CMP-11 | `IconText` | `icon`, `text`, `gap?` | アイコン＋テキストの汎用横並び |
| CMP-12 | `SectionHeader` | `title`, `iconName?`, `actionLabel?`, `onAction?` | セクション冒頭の見出し（アイコン円付き／View All リンク付きを統合） |
| CMP-13 | `FilterChip` | `label`, `active`, `code` | フィルター用チップ |
| CMP-14 | `SlideIndicators` | `total`, `activeIndex`, `onSelect` | スライドドット群 |
| CMP-15 | `DeadlineCountdown` | `deadline`, `label?` | 「締切まで N日」表示 |
| CMP-16 | `QuoteBlock` | `quote`, `citation` | 引用＋出典 |
| CMP-17 | `MessageBubble` | `role`, `avatarLabel`, `message`, `align` | 対談記事の発言（編集者／作家） |
| CMP-18 | `FaqItem` | `question`, `answer`, `expanded`, `onToggle` | アコーディオン |
| CMP-19 | `MenuItem` | `icon`, `label`, `href`, `onClick` | メニュー項目 |
| ... | ... | ... | ... |

---

## 3. Organisms

### 出力ルール（重要・コンパクト化）

**ルール 1**: 全 Organism を冒頭の **「Organism 一覧表」** に列挙：

| CMP-XX | 名前 | Props 数 | 概要 |
|---|---|---|---|
| `CMP-41` | `Header` | 4 | `variant: "top" \| "detail"`, `title`, `onBack?`, `onMenuOpen` |
| `CMP-42` | `Footer` | 3 | `links`, `copyrightText`, `variant?` |
| `CMP-46` | `NewsSection` | 1 | `items[]`。`SectionHeader` + `NewsItem` の繰り返し |
| ... | ... | ... | ... |

**ルール 2**: H3 で個別記載するのは **「複雑なバリアント」「Discriminated Union 型」「親 → 子 Organism の構造説明が必要」** のみ：

- ✅ `CMP-45 AwardCard`（Discriminated Union）
- ✅ `CMP-50 FirstViewHero`（多数の props、複雑な構造）
- ✅ `CMP-67 MenuOverlay`（MenuItem + SocialIcon を内包する構造説明）
- ❌ `CMP-46 NewsSection`（単純な SectionHeader + リスト）→ 表 1 行で十分

**ルール 3**: H3 個別記載は **全 Organism の 30% 以下** を目標（残り 70% は表に集約）。

### CMP-41: `Header`

| Props | 型 | 概要 |
|---|---|---|
| `variant` | `"top" \| "detail"` | トップ用（戻る無し）／詳細用（戻る有り） |
| `title` | `string` | 表示タイトル |
| `onBack?` | `() => void` | 戻るボタン（detail のみ） |
| `onMenuOpen` | `() => void` | メニュー開く |

### CMP-32: `Footer`

| Props | 型 | 概要 |
|---|---|---|
| `links` | `Array<{label: string; href: string}>` | リンク一覧 |
| `copyrightText` | `string` | コピーライト |

### CMP-33: `HeroSlider`

| Props | 型 | 概要 |
|---|---|---|
| `slides` | `HeroSlide[]` | スライドデータ |
| `onSlideChange?` | `(index: number) => void` | スライド切替 |

<!-- 重要 Organism を H3 で個別に記載。シンプルなものは表に統合してもよい -->

### CMP-35: `AwardCard`

Award の `status` に応じて表示が変わる Discriminated Union 型。

```typescript
type AwardCardProps =
  | { status: "OPEN"; deadline: Date; ... }
  | { status: "REVIEWING"; reviewMilestone: string; ... }
  | { status: "RESULT"; resultHref: string; ... }
```

| Props | 型 | 概要 |
|---|---|---|
| `imageUrl` | `string` | カード画像 |
| `status` | `"OPEN" \| "REVIEWING" \| "RESULT"` | ステータス |
| ... | ... | ... |

---

## 4. Templates

### CMP-60: `StandardPageTemplate`

| Props | 型 | 概要 |
|---|---|---|
| `headerVariant` | `"top" \| "detail"` | ヘッダーバリアント |
| `headerTitle` | `string` | ヘッダータイトル |
| `children` | `React.ReactNode` | コンテンツスロット |
| `stickyFooter?` | `React.ReactNode` | 画面下固定 CTA スロット |

### CMP-61: `OverlayTemplate`

| Props | 型 | 概要 |
|---|---|---|
| `title` | `string` | ヘッダータイトル |
| `children` | `React.ReactNode` | コンテンツ |
| `onClose` | `() => void` | 閉じる |

---

## 5. Pages

各ページは Template に必要な Organism を流し込んだ完成形。

| ページ | 利用 Template | 主な Organism |
|---|---|---|
| top.md | CMP-80 | CMP-41, CMP-43, CMP-44, CMP-45, CMP-46, CMP-47, CMP-49, CMP-42 |
| award-detail-open.md | CMP-80 | CMP-41, CMP-50, CMP-51, ..., CMP-49, CMP-42 |
| ... | ... | ... |

---

## ページ→Organism マッピング検証

各ページの構成要素（H3 セクション）に対して、対応する Organism が定義されていることを確認する表。**未対応セルが 1 つでもあれば Step 10 を完了とせず Organism を追加する**。

### top.md
| 構成要素（ノードID） | 対応 Organism |
|---|---|
| Header (`98:64`) | `CMP-41` Header |
| Hero Section (`98:71`) | `CMP-43` HeroSlider |
| Status Filter (`98:78`) | `CMP-44` StatusFilter |
| Award List (`98:87`) | （リスト構造）AwardList 抽出 or AwardCard × N |
| News Section (`98:133`) | `CMP-46` NewsSection |
| Content Pickup (`98:150`) | `CMP-47` ContentPickup |
| Fixed CTA Banner (`98:168`) | `CMP-49` StickyFooter |
| Footer (`98:178`) | `CMP-42` Footer |

### award-detail-result.md
| 構成要素（ノードID） | 対応 Organism |
|---|---|
| Header (`98:185`) | `CMP-41` Header |
| Result Hero (`98:195`) | `CMP-XX` ResultHero |
| Overall Comment (`98:201`) | `CMP-XX` OverallCommentSection |
| Winners Section (`98:204`) | `CMP-57` WinnerCard × N + `CMP-58` ExcellenceCard × N |
| Back Number Section (`98:352`) | `CMP-59` BackNumberList |
| Footer (`98:367`) | `CMP-42` Footer |

<!-- 全ページについて 1 行ずつ。「対応 Organism: 未定義」の行があれば Organism を追加してから再生成 -->
```

---

## docs/reviews/coverage-review.md（Step 6）

```markdown
# 整合性レビュー（Goal × UC × Actor × Page × Action）

## プロジェクトのゴール

{{Step 0 で取得したゴール}}

## レビュー結果

修正は適用しません。検出した不足を **優先度ラベル付き** で提示します。

### 優先度ラベル定義
- **必須**: ゴール達成に必須で、未対応だと UC が成立しない
- **推奨**: あれば UX が向上する、または運用負荷が下がる
- **オプション**: あれば望ましいが MVP では省略可

### 1. ゴールから見て足りないユースケース候補

| # | 優先度 | ゴール上の要求 | 対応 UC 状況 | 不足の内容 |
|---|---|---|---|---|
| 1 | 必須 / 推奨 / オプション | {{要求}} | 該当 UC: なし / 部分一致 `UC-XX` | {{不足内容}} |

### 2. ゴールから見て足りないアクター候補

| # | 優先度 | ゴール上の要求 | 対応 Actor 状況 | 不足の内容 |
|---|---|---|---|---|
| 1 | 必須 / 推奨 / オプション | {{要求}} | 該当 Actor: なし | {{不足内容}} |

### 3. ユースケースから見て足りないページ候補

| # | 優先度 | UC-ID | UC 名 | 必要な遷移先 | 該当ページ状況 |
|---|---|---|---|---|---|
| 1 | 必須 / 推奨 / オプション | `UC-XX` | {{名}} | {{遷移先名}} | 未定義 |

### 4. ユースケースから見て足りないアクション候補

| # | 優先度 | UC-ID | UC 名 | 必要なアクション | 該当ページ | 該当アクション状況 |
|---|---|---|---|---|---|---|
| 1 | 必須 / 推奨 / オプション | `UC-XX` | {{名}} | {{アクション名}} | `{{slug}}.md` | 未定義 |

## 推奨アクション（必須項目を上に、推奨／オプションは下に）

1. **【必須】** {{項目}}
2. **【推奨】** {{項目}}
3. **【オプション】** {{項目}}
```

---

## docs/reviews/data-model-review.md（Step 9）

```markdown
# データモデルレビュー

修正は適用しません。検出した不整合・過不足を **優先度ラベル付き** で提示します。

### 1. ページにあるがモデルに無い表示要素

| # | 優先度 | ページ | 表示要素 | ノードID | 推測される対応 |
|---|---|---|---|---|---|
| 1 | 必須 / 推奨 / オプション | `{{slug}}.md` | {{要素}} | `{{nodeId}}` | {{追加すべき Entity / カラム}} |

### 2. モデルに定義があるが利用されていない Entity / カラム

| # | 優先度 | モデル / カラムID | 名前 | 状況 |
|---|---|---|---|---|
| 1 | 推奨 / オプション | `E-XX` | {{Entity 名}} | どのページからも参照されていない |
| 2 | 推奨 / オプション | `E-XX.C-YY` | {{カラム名}} | どのページからも参照されていない |

### 3. Relation / FK の整合性

| # | 優先度 | Relation ID | 問題 |
|---|---|---|---|
| 1 | 必須 | `R-XX` | 参照先 `E-YY` が存在しない |

### 4. インデックス追加候補

| # | 優先度 | カラム | 検出根拠 |
|---|---|---|---|
| 1 | 推奨 | `E-XX.C-YY` | {{一覧表示の絞り込み・ソートに使われているのに INDEX 未定義}} |

## 推奨アクション（必須項目を上に）

1. **【必須】** {{項目}}
2. **【推奨】** {{項目}}
3. **【オプション】** {{項目}}
```

---

## docs/reviews/components-review.md（Step 12）

```markdown
# コンポーネントレビュー

修正は適用しません。検出した不整合・過不足・共通化候補を **優先度ラベル付き** で提示します。

### 1. ページにあるがコンポーネント未定義の表示要素

| # | 優先度 | ページ | 表示要素 | ノードID | 想定 Atomic 種別 |
|---|---|---|---|---|---|
| 1 | 必須 / 推奨 | `{{slug}}.md` | {{要素}} | `{{nodeId}}` | Atom / Molecule / Organism |

### 2. 定義済みだがどのページでも利用されていないコンポーネント

| # | 優先度 | コンポーネントID | 名前 | 状況 |
|---|---|---|---|---|
| 1 | オプション | `CMP-XX` | {{名}} | 利用箇所なし |

### 3. 共通化候補

| # | 優先度 | 対象 | 共通化方針 | 統合候補 ID |
|---|---|---|---|---|
| 1 | 推奨 | {{類似コンポーネント群}} | variant prop で統合 | `CMP-XX`, `CMP-YY` → 統合 |

### 4. パラメータ・ハンドラの過不足

| # | 優先度 | コンポーネントID | 過不足の内容 |
|---|---|---|---|
| 1 | 必須 / 推奨 / オプション | `CMP-XX` | パラメータ `label` が未定義だが、ページでは異なるラベル文字列で利用されている |

## 推奨アクション（必須項目を上に）

1. **【必須】** {{項目}}
2. **【推奨】** {{項目}}
3. **【オプション】** {{項目}}
```

---

## 共通スタイル規約

- Markdown の見出しレベル: ファイル先頭は `#`、最初のセクションは `##`
- ID は **必ずバッククォート** で囲む（例: `` `UC-01` ``, `` `E-01.C-03` ``）
- ノードIDも backtick で囲む（例: `` `98:63` ``）
- ファイルパスも backtick で囲む（例: `` `docs/pages/top.md` ``）
- ID を記載するとき必ず Entity 名／カラム名／コンポーネント名を併記する（例: `` `E-02.C-06`（AwardEdition.application_close_at） ``）
- Figma 未記載は **「Figma 未記載」** で統一（「不明」「-」などは使わない）
- 静的文言は **「静的」** で統一
- 半角・全角の混在ルール: Figma 表記をそのまま転記。識別子・カラム名は半角英数

## 集約ルール（重要）

ドキュメントの冗長性を防ぐため、以下のルールを徹底：

- **同一カラム参照は 1 行に集約**（参照モデルセクション）
- **静的文言群は 1 行に集約**（フッターリンク群など）
- **Atom レベルのコンポーネントはページ単位の利用コンポーネントセクションに含めない**（Organism に内包される設計のため）
- **Atom コンポーネントは 1 つの表に統合**（1 Atom = 1 H2 は禁止）
- **Molecule もシンプルなものは表に統合**、複雑なバリアントを持つもののみ H3 で個別記載

## 客観抽出と推測補完の境界

| 客観抽出（本体に記述してよい） | 推測補完（禁止） |
|---|---|
| ページ名 + 構成要素から導ける役割記述 | ペルソナの架空属性（年齢、職業、家族構成 等） |
| 構成要素から導ける挙動概要（アクション） | 業務要件、KPI、戦略目標 |
| ENUM 値の状態遷移可視化 | 「ありそう」な追加機能 |
| Figma の解決対象から逆算した典型ペインポイント | Figma に存在しない属性 |
| CMS／SEO のベストプラクティス（Figma 構成から導出） | 具体的な実装詳細（フレームワーク選定等） |

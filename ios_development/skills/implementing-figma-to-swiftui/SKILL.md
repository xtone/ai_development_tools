---
name: implementing-figma-to-swiftui
description: Implements SwiftUI Views from Figma designs using Figma MCP tools (figma:get_design_context, figma:get_screenshot, figma:get_variable_defs, figma:get_metadata). Splits large designs into appropriately-sized components, respects existing codebase conventions, and adds previews for each component. Use when implementing SwiftUI from Figma design URLs (e.g., figma.com/design/...), converting designs to code, or building iOS UI from Figma mockups. Do NOT call Figma MCP tools directly without reading this skill first.
---

# Implementing Figma to SwiftUI

## ワークフロー

以下のチェックリストをコピーして進捗を管理する：

```
- [ ] Step 1: デザイン情報を収集（Figma MCP）
- [ ] Step 2: 既存コードベースを確認
- [ ] Step 3: コンポーネント構造を計画
- [ ] Step 4: ユーザーに方針を確認
- [ ] Step 5: プレビュー付きで実装
- [ ] Step 6: デザインと照合して検証
```

## Step 1: デザイン情報を収集

Figma MCPツールを完全修飾名で使用する：

```
1. figma:get_design_context(nodeId, clientLanguages: "swift", clientFrameworks: "swiftui")
   → コード生成用のデザインデータを取得

2. figma:get_screenshot(nodeId)
   → 実装時の視覚的リファレンス

3. figma:get_variable_defs(nodeId)
   → 色・フォント・スペーシング変数をSwiftUIにマッピング

4. figma:get_metadata(nodeId) [構造が複雑な場合]
   → 子ノード一覧を取得してコンポーネント分割を検討
```

**システムUIは除外**: ステータスバー、ホームインジケーター、セーフエリア表示。

## Step 2: 既存コードベースを確認

実装前に確認する：

- **再利用可能なView**: 既存のButton、Card、CellなどのコンポーネントおよびNavigation Bar、TabViewなどグローバルな遷移に関わる要素
- **リソース**: Color/Font extension、Image assets、spacing定数
- **命名パターン**: Viewのサフィックス、ファイル構成、プロパティ命名

## Step 3: コンポーネント構造を計画

**分割する場合：**
- 繰り返し使用されるUI要素
- 独立したセクション（ヘッダー、リストセル）
- Viewが約50行を超える
- 要素が独自の状態を持つ

**分割しない場合：**
- 1回限りの単純な要素
- 10行未満
- 親と密結合している

## Step 4: ユーザーに確認

不明な場合は実装前に確認する：

| トピック | 確認例 |
|----------|--------|
| 命名 | 「既存の`CommonHeaderView`を使用？新規で`ProductDetailHeaderView`を作成？」 |
| ファイル配置 | 「`Features/ProductDetail/`に配置？」 |
| 既存コンポーネント | 「類似の`PriceLabel`が存在—再利用？バリアント作成？」 |
| デザイン解釈 | 「このスペーシングが曖昧—16pt？20pt？」 |
| 状態管理 | 「`@State`で管理？親から渡す？」 |

**選択肢が明確な場合はAskUserQuestionツールを使用する**（例：既存コンポーネントの再利用 vs 新規作成、複数のファイル配置オプション）。

## Step 5: 実装

すべてのViewに`#Preview`を追加する：

```swift
#Preview { ComponentView(model: .preview) }

// 複数の状態がある場合
#Preview("Default") { ComponentView(model: .preview) }
#Preview("Loading") { ComponentView(model: .previewLoading) }
```

Figmaの値を正確に使用する—丸めたり近似したりしない。

`figma:get_variable_defs`の出力を既存のColor/Font extensionにマッピングする（利用可能な場合）。

実装したViewでは警告が残らないようする。

実装中でも不明点があればユーザーに確認を行う。

## Step 6: 検証

`figma:get_screenshot`の出力と実装を比較して正確性を確認する。

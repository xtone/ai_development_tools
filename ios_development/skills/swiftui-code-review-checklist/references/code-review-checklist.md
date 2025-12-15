# SwiftUI コードレビューチェックリスト

## 優先度: 必須（Must）

### 状態管理

- [ ] **SSOT遵守**: 各データは唯一の情報源から管理されているか
- [ ] **導出状態なし**: 計算で求められる状態を`@State`で持っていないか
- [ ] **プロパティラッパー適切**: `@State`（値型ローカル）、`@StateObject`（参照型所有）、`@ObservedObject`（参照型非所有）
- [ ] **@State private**: `@State`は`private`になっているか
- [ ] **iOS 17+ @Observable**: 適切に移行されているか（該当する場合）

```swift
// ❌ 導出状態を保持
@State private var items: [Item] = []
@State private var count: Int = 0  // items.countで計算可能

// ✅ 計算プロパティを使用
@State private var items: [Item] = []
private var count: Int { items.count }
```

### パフォーマンス

- [ ] **Lazyコンテナ**: 大量データに`LazyVStack`/`LazyHStack`/`LazyVGrid`使用
- [ ] **body内計算**: 重い計算をbody内で実行していないか
- [ ] **GeometryReader最小限**: 必要な箇所のみで使用しているか

### エラーハンドリング

- [ ] **エラー状態表示**: ネットワークエラー等のUI表示があるか
- [ ] **空状態表示**: データなし時のプレースホルダーがあるか
- [ ] **ローディング状態**: 非同期処理中のインジケータがあるか

## 優先度: 推奨（Should）

### コンポーネント設計

- [ ] **Root/Content分離**: ロジック（Root）とUI（Content）が分離されているか
- [ ] **適切なサイズ**: 1ビューが10-15サブビュー以下か
- [ ] **単一責任**: 各コンポーネントが単一の責任を持つか
- [ ] **ViewModifier活用**: 再利用可能なスタイルがモディファイアになっているか

```swift
// ✅ Root/Content分離
struct ArticleListView: View {  // Root: ロジック
    @StateObject private var viewModel = ArticleListViewModel()
    
    var body: some View {
        ArticleListContent(  // Content: UI
            articles: viewModel.articles,
            isLoading: viewModel.isLoading
        )
    }
}
```

### 非同期処理

- [ ] **.task使用**: `onAppear`ではなく`.task`モディファイアを使用（iOS 15+）
- [ ] **@MainActor**: UI更新メソッドに`@MainActor`が付いているか
- [ ] **キャンセル考慮**: 長時間処理のキャンセルが考慮されているか

```swift
// ✅ .taskモディファイア
.task {
    await viewModel.fetchData()
}

// ✅ idパラメータで再実行
.task(id: selectedCategory) {
    await viewModel.fetchData(category: selectedCategory)
}
```

### ナビゲーション（iOS 16+）

- [ ] **NavigationStack使用**: `NavigationView`ではなく`NavigationStack`使用
- [ ] **型安全ルート**: 文字列ではなくenumでルート定義
- [ ] **navigationDestination**: 宣言的にルート定義

### アクセシビリティ

- [ ] **画像ボタンにラベル**: `accessibilityLabel`設定
- [ ] **onTapGestureに特性**: `.accessibilityAddTraits(.isButton)`
- [ ] **見出しマーク**: タイトルに`.accessibilityAddTraits(.isHeader)`
- [ ] **グループ化**: 関連要素を`accessibilityElement(children: .combine)`

### プレビュー

- [ ] **複数状態**: 空、ローディング、エラー、データありのプレビュー
- [ ] **ダーク/ライト**: 両モードでプレビュー
- [ ] **Dynamic Type**: 異なるサイズでプレビュー

## 優先度: 提案（Nice to have）

### 最適化

- [ ] **Equatable**: 高コストビューに`Equatable`実装
- [ ] **_printChanges()**: パフォーマンス問題時のデバッグ

### コードスタイル

- [ ] **命名規則**: SwiftAPIデザインガイドライン準拠
- [ ] **モディファイア順序**: 意図を理解した順序
- [ ] **ファイル構成**: 機能別に整理

### ドキュメント

- [ ] **公開APIコメント**: 公開メソッドにドキュメントコメント
- [ ] **複雑なロジック説明**: 非自明な処理にコメント

## アンチパターンチェック

### 絶対に避けるべき

- [ ] `@State`で参照型（class）を使用していない
- [ ] body内で毎回重い計算を実行していない
- [ ] 状態の重複がない
- [ ] `NavigationView`を使用していない（iOS 16+）

### 注意が必要

- [ ] GeometryReaderの過剰使用
- [ ] 深いネスト構造
- [ ] UIKitとSwiftUIの不要な混在
- [ ] Combineの不適切な使用（async/awaitで代替可能な場合）

## レビューコメント例

### 状態管理

```
🔴 [必須] この`@State var count`は`items.count`から導出可能です。
計算プロパティに変更してください。
```

### パフォーマンス

```
🟡 [推奨] このForEach内の処理はLazyVStackでラップすると
パフォーマンスが向上します（30-40%のメモリ削減）。
```

### アクセシビリティ

```
🟡 [推奨] この画像ボタンにaccessibilityLabelを追加してください。
VoiceOverユーザーが機能を理解できません。
```

### 非同期処理

```
🟡 [推奨] onAppear内のTask{}は.taskモディファイアに変更すると
自動キャンセルが効くため、メモリリーク防止になります。
```

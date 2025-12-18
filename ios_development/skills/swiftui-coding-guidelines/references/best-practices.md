# SwiftUI Best Practices

## 1. 状態管理

### Property Wrapperの使い分け（iOS 13-16）

| ラッパー | 用途 | 所有権 |
|---------|------|--------|
| `@State` | 値型のローカル状態（Int, String, Bool, struct）。必ず`private`にする | 所有 |
| `@StateObject` | 参照型の所有者。1度だけ初期化、再描画でも維持 | 所有 |
| `@ObservedObject` | 外部から受け取る参照型。親から渡される場合 | 非所有 |
| `@EnvironmentObject` | アプリ全体で共有する状態。依存性注入として使用 | 非所有 |
| `@Binding` | 親ビューの状態への双方向参照 | 非所有 |

```swift
// ✅ 正しい使い分け
struct ParentView: View {
    @StateObject private var viewModel = MyViewModel() // 所有者
    
    var body: some View {
        ChildView(viewModel: viewModel)
    }
}

struct ChildView: View {
    @ObservedObject var viewModel: MyViewModel // 外部から受け取る
    
    var body: some View {
        GrandchildView(text: $viewModel.text) // Bindingで渡す
    }
}
```

### Single Source of Truth (SSOT)

データは1箇所でのみ管理。複数ビューで共有時は`@Binding`や`@ObservedObject`使用。

```swift
// ❌ 状態の重複
struct BadView: View {
    @State private var items: [Item] = []
    @State private var count: Int = 0 // itemsから導出可能
}

// ✅ 導出プロパティを使用
struct GoodView: View {
    @State private var items: [Item] = []
    private var count: Int { items.count }
}
```

## 2. パフォーマンス最適化

### 不要な再レンダリング防止

```swift
// デバッグ: なぜ再レンダリングされたか確認
var body: some View {
    let _ = Self._printChanges()
    // ...
}
```

**ポイント**:
- `@StateObject`は所有者で使用、`@ObservedObject`は注入時のみ
- `body`内で重い計算を避ける → `onChange`等で事前計算
- 小さなビューに分割してSwiftUIが必要な部分のみ更新

### Lazyコンテナの活用

```swift
// ✅ オンデマンドレンダリング（30-40%のメモリ削減）
ScrollView {
    LazyVStack {
        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
}

// ❌ 全アイテムを即座にレンダリング
ScrollView {
    VStack {
        ForEach(items) { ... }
    }
}
```

### EquatableViewの活用

```swift
// 15%のレンダリング時間削減（高コストなビューに効果的）
struct ExpensiveView: View, Equatable {
    let data: ExpensiveData
    
    static func == (lhs: Self, rhs: Self) -> Bool {
        lhs.data.id == rhs.data.id
    }
    
    var body: some View {
        // 複雑なレンダリング
    }
}
```

### GeometryReaderの使用を最小限に

- レイアウト変更毎に再計算、パフォーマンス影響
- 動的レイアウト計算が本当に必要な場合のみ使用
- リスト/グリッド内での使用を避ける

## 3. ビュー構成（View Composition）

### Root Views vs Content Views

```swift
// Root View: ビジネスロジック、ナビゲーション管理
struct ArticleListView: View {
    @StateObject private var viewModel = ArticleListViewModel()
    
    var body: some View {
        ArticleListContent(
            articles: viewModel.articles,
            isLoading: viewModel.isLoading,
            onRefresh: { await viewModel.refresh() }
        )
    }
}

// Content View: 純粋なUI表示、プリミティブ型のみ受け取る
struct ArticleListContent: View {
    let articles: [Article]
    let isLoading: Bool
    let onRefresh: () async -> Void
    
    var body: some View {
        // UIのみ
    }
}
```

### ViewModifierの活用

```swift
// カスタムモディファイア定義
struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding()
            .background(Color(.systemBackground))
            .cornerRadius(12)
            .shadow(radius: 4)
    }
}

extension View {
    func cardStyle() -> some View {
        modifier(CardStyle())
    }
}

// 使用
Text("Hello").cardStyle()
```

### コンポーネントライブラリ構造

```
Design/
├── Colors.swift      # カラーパレット
├── Typography.swift  # フォントスタイル
└── Spacing.swift     # 間隔定数

Components/
├── Buttons/
├── Cards/
└── TextFields/

Modifiers/
└── CardStyle.swift
```

## 4. ナビゲーション（iOS 16+）

### NavigationStackの使用

```swift
// 型安全なルート定義
enum Route: Hashable {
    case detail(Article)
    case settings
    case profile(userId: String)
}

struct ContentView: View {
    @State private var path = NavigationPath()
    
    var body: some View {
        NavigationStack(path: $path) {
            List(articles) { article in
                NavigationLink(value: Route.detail(article)) {
                    ArticleRow(article: article)
                }
            }
            .navigationDestination(for: Route.self) { route in
                switch route {
                case .detail(let article):
                    ArticleDetailView(article: article)
                case .settings:
                    SettingsView()
                case .profile(let userId):
                    ProfileView(userId: userId)
                }
            }
        }
    }
    
    // プログラマティックナビゲーション
    func navigateToSettings() {
        path.append(Route.settings)
    }
    
    func popToRoot() {
        path.removeLast(path.count)
    }
}
```

## 5. 非同期処理（Async/Await）

### .taskモディファイアの使用（iOS 15+）

```swift
struct ArticleListView: View {
    @StateObject private var viewModel = ArticleListViewModel()
    
    var body: some View {
        List(viewModel.articles) { article in
            ArticleRow(article: article)
        }
        .task {
            // async/await直接使用、ビュー消失時に自動キャンセル
            await viewModel.fetchArticles()
        }
        .task(id: viewModel.selectedCategory) {
            // idが変わると再実行
            await viewModel.fetchArticles()
        }
    }
}
```

### .task vs .onAppear

| 特徴 | .task | .onAppear |
|------|-------|-----------|
| async/await | 直接使用可能 | Task{}で囲む必要 |
| キャンセル | 自動 | 手動 |
| 優先度設定 | 可能 | 不可 |
| iOS | 15+ | 13+ |

### @MainActorの使用

```swift
@MainActor
class ArticleListViewModel: ObservableObject {
    @Published var articles: [Article] = []
    @Published var isLoading = false
    
    func fetchArticles() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            articles = try await articleService.fetch()
        } catch {
            // エラーハンドリング
        }
    }
}
```

## 6. Preview駆動開発

### 複数状態のプレビュー

```swift
#Preview("Loading") {
    ArticleListContent(articles: [], isLoading: true, onRefresh: {})
}

#Preview("Empty") {
    ArticleListContent(articles: [], isLoading: false, onRefresh: {})
}

#Preview("With Data") {
    ArticleListContent(articles: Article.samples, isLoading: false, onRefresh: {})
}

#Preview("Error") {
    ArticleListContent(articles: [], isLoading: false, error: .networkError, onRefresh: {})
}

// iOS 17+ @Previewableマクロ
#Preview {
    @Previewable @State var isOn = false
    Toggle("Switch", isOn: $isOn)
}
```

### プレビューのベストプラクティス

- 異なるデバイスサイズ、Dynamic Type設定でプレビュー
- ダークモード、ライトモード両方
- 空、ロード中、エラー、データありの各状態

## 7. プロジェクト構造

```
Sources/
├── App/                 # メインアプリファイル
├── Features/            # 機能別
│   ├── Home/
│   │   ├── HomeView.swift
│   │   └── HomeViewModel.swift
│   └── Profile/
├── Shared/              # 共通コンポーネント
│   ├── Components/
│   └── Modifiers/
├── Models/              # データモデル
├── Services/            # Network, Persistence
└── Utilities/           # Extensions, Constants

Resources/
├── Assets/              # 画像、色
├── Localization/        # ローカライズ
└── Fonts/               # カスタムフォント
```

## 8. MVVM vs MV パターン

SwiftUIではMVVMは必須ではない。Apple Developer Forumsでも議論されている。

```swift
// MVパターン（Store使用）
@MainActor
class ArticleStore: ObservableObject {
    @Published private(set) var articles: [Article] = []
    
    func fetch() async { /* ... */ }
}

// Viewで直接使用
struct ArticleListView: View {
    @StateObject private var store = ArticleStore()
    // ...
}
```

**ポイント**:
- ViewModelという名称は混乱を招く可能性
- テスタビリティのために過度な抽象化を避ける
- Storeパターンも有効な選択肢

## 9. Layoutプロトコル（iOS 16+）

GeometryReaderの代替として、カスタムレイアウトコンテナを作成可能。パフォーマンスに優れ、レイアウトサイクルのリスクが低い。

### 基本構造

```swift
struct EqualWidthHStack: Layout {
    var spacing: CGFloat = 8
    
    // 1. 必要なサイズを計算
    func sizeThatFits(
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) -> CGSize {
        let maxWidth = subviews.map { $0.sizeThatFits(.unspecified).width }.max() ?? 0
        let totalWidth = maxWidth * CGFloat(subviews.count) + spacing * CGFloat(subviews.count - 1)
        let maxHeight = subviews.map { $0.sizeThatFits(.unspecified).height }.max() ?? 0
        
        return CGSize(width: totalWidth, height: maxHeight)
    }
    
    // 2. 子Viewを配置
    func placeSubviews(
        in bounds: CGRect,
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) {
        let maxWidth = subviews.map { $0.sizeThatFits(.unspecified).width }.max() ?? 0
        var x = bounds.minX
        
        for subview in subviews {
            subview.place(
                at: CGPoint(x: x, y: bounds.minY),
                proposal: ProposedViewSize(width: maxWidth, height: bounds.height)
            )
            x += maxWidth + spacing
        }
    }
}

// 使用
EqualWidthHStack(spacing: 12) {
    Button("Short") { }
    Button("Medium Text") { }
    Button("Very Long Button") { }
}
```

### フローレイアウト（折り返し配置）

```swift
struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    
    func sizeThatFits(
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) -> CGSize {
        let result = arrange(subviews: subviews, in: proposal.width ?? 0)
        return result.size
    }
    
    func placeSubviews(
        in bounds: CGRect,
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) {
        let result = arrange(subviews: subviews, in: bounds.width)
        
        for (index, position) in result.positions.enumerated() {
            subviews[index].place(
                at: CGPoint(x: bounds.minX + position.x, y: bounds.minY + position.y),
                proposal: .unspecified
            )
        }
    }
    
    private func arrange(subviews: Subviews, in width: CGFloat) -> (size: CGSize, positions: [CGPoint]) {
        var positions: [CGPoint] = []
        var currentX: CGFloat = 0
        var currentY: CGFloat = 0
        var lineHeight: CGFloat = 0
        var maxWidth: CGFloat = 0
        
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            
            if currentX + size.width > width && currentX > 0 {
                currentX = 0
                currentY += lineHeight + spacing
                lineHeight = 0
            }
            
            positions.append(CGPoint(x: currentX, y: currentY))
            lineHeight = max(lineHeight, size.height)
            currentX += size.width + spacing
            maxWidth = max(maxWidth, currentX - spacing)
        }
        
        return (CGSize(width: maxWidth, height: currentY + lineHeight), positions)
    }
}

// 使用（タグ表示など）
FlowLayout(spacing: 8) {
    ForEach(tags, id: \.self) { tag in
        TagView(text: tag)
    }
}
```

### GeometryReaderとの比較

| 特徴 | Layout | GeometryReader |
|------|--------|----------------|
| パフォーマンス | ◎ 優秀 | △ レイアウトサイクルのリスク |
| 再利用性 | ◎ 高い | △ 低い |
| 複雑さ | やや高い | 低い |
| iOS | 16+ | 13+ |
| 用途 | カスタムコンテナ | サイズ取得・相対配置 |

### GeometryReaderを使う場合の注意

```swift
// ❌ 避ける: リスト内でGeometryReader
List(items) { item in
    GeometryReader { geo in
        ItemRow(item: item, width: geo.size.width)
    }
}

// ✅ 推奨: background/overlayで使用
Text("Hello")
    .background(
        GeometryReader { geo in
            Color.clear.onAppear {
                size = geo.size
            }
        }
    )

// ✅ 推奨: 外側で1回だけ
GeometryReader { geo in
    ScrollView {
        LazyVStack {
            ForEach(items) { item in
                ItemRow(item: item, width: geo.size.width)
            }
        }
    }
}

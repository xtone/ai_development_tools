# SwiftUI View構築・レイアウトパターン

## 4-1. AsyncImage（キャッシュ付き）

### 基本使用

```swift
AsyncImage(url: imageURL) { phase in
    switch phase {
    case .empty:
        ProgressView()
    case .success(let image):
        image
            .resizable()
            .aspectRatio(contentMode: .fill)
    case .failure:
        Image(systemName: "photo")
            .foregroundColor(.gray)
    @unknown default:
        EmptyView()
    }
}
.frame(width: 100, height: 100)
.clipShape(RoundedRectangle(cornerRadius: 8))
```

### キャッシュ付き実装

```swift
struct CachedAsyncImage: View {
    let url: URL?

    @State private var image: Image?

    var body: some View {
        Group {
            if let image = image {
                image
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            } else {
                ProgressView()
                    .task {
                        await loadImage()
                    }
            }
        }
    }

    private func loadImage() async {
        guard let url = url else { return }

        // キャッシュチェック
        if let cached = ImageCache.shared.get(for: url) {
            image = cached
            return
        }

        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let uiImage = UIImage(data: data) {
                let loadedImage = Image(uiImage: uiImage)
                ImageCache.shared.set(loadedImage, for: url)
                image = loadedImage
            }
        } catch {
            // エラーハンドリング
        }
    }
}

actor ImageCache {
    static let shared = ImageCache()
    private var cache: [URL: Image] = [:]

    func get(for url: URL) -> Image? {
        cache[url]
    }

    func set(_ image: Image, for url: URL) {
        cache[url] = image
    }
}
```

---

## 4-2. 空状態・エラー状態

```swift
struct ContentStateView<Content: View, Empty: View, Loading: View, Error: View>: View {
    let state: ContentState
    let content: () -> Content
    let empty: () -> Empty
    let loading: () -> Loading
    let error: (Swift.Error) -> Error

    var body: some View {
        switch state {
        case .idle:
            empty()
        case .loading:
            loading()
        case .loaded:
            content()
        case .error(let err):
            error(err)
        }
    }
}

enum ContentState {
    case idle
    case loading
    case loaded
    case error(Error)
}

// 使用例
struct ArticleListView: View {
    @StateObject private var viewModel = ArticleListViewModel()

    var body: some View {
        ContentStateView(state: viewModel.state) {
            List(viewModel.articles) { article in
                ArticleRow(article: article)
            }
        } empty: {
            EmptyStateView(
                icon: "doc.text",
                title: "記事がありません",
                message: "新しい記事を追加してください"
            )
        } loading: {
            ProgressView("読み込み中...")
        } error: { error in
            ErrorStateView(
                error: error,
                onRetry: {
                    Task { await viewModel.fetch() }
                }
            )
        }
    }
}

struct EmptyStateView: View {
    let icon: String
    let title: String
    let message: String

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 60))
                .foregroundColor(.gray)

            Text(title)
                .font(.title2)
                .fontWeight(.semibold)

            Text(message)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}

struct ErrorStateView: View {
    let error: Error
    let onRetry: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 60))
                .foregroundColor(.orange)

            Text("エラーが発生しました")
                .font(.title2)
                .fontWeight(.semibold)

            Text(error.localizedDescription)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            Button("再試行") {
                onRetry()
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}
```

---

## 4-3. アニメーション

```swift
struct AnimatedView: View {
    @State private var isExpanded = false

    var body: some View {
        VStack {
            Button("トグル") {
                withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                    isExpanded.toggle()
                }
            }

            RoundedRectangle(cornerRadius: 12)
                .fill(Color.blue)
                .frame(
                    width: isExpanded ? 200 : 100,
                    height: isExpanded ? 200 : 100
                )
        }
    }
}

// Reduce Motion対応
struct AccessibleAnimatedView: View {
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    @State private var isVisible = false

    var body: some View {
        Text("Hello")
            .opacity(isVisible ? 1 : 0)
            .animation(reduceMotion ? nil : .easeInOut, value: isVisible)
    }
}
```

---

## 4-4. View重なりパターン（ZStack / overlay / background）

### 使い分けガイド

| 方法 | サイズ決定 | 用途 |
|------|-----------|------|
| `ZStack` | 最大の子に合わせる | 複数の独立したViewを重ねる |
| `.overlay` | ベースViewに合わせる | 前面に装飾・バッジを追加 |
| `.background` | ベースViewに合わせる | 背景として配置 |

### ZStack: 複数の独立したViewを重ねる

```swift
// 複数の独立した要素を重ねる
ZStack(alignment: .topTrailing) {
    Image("photo")
        .resizable()
        .aspectRatio(contentMode: .fill)

    // お気に入りボタン
    Button(action: toggleFavorite) {
        Image(systemName: "heart.fill")
            .foregroundColor(.red)
    }
    .padding(8)
}
```

### overlay: ベースViewの前面に装飾

```swift
// バッジ付きアイコン
Image(systemName: "bell")
    .font(.title)
    .overlay(alignment: .topTrailing) {
        // バッジはベースアイコンのサイズに影響しない
        Text("3")
            .font(.caption2)
            .padding(4)
            .background(Color.red)
            .clipShape(Circle())
            .offset(x: 8, y: -8)
    }

// ローディングオーバーレイ
List(items) { item in
    ItemRow(item: item)
}
.overlay {
    if isLoading {
        ProgressView()
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color.black.opacity(0.3))
    }
}
```

### background: ベースViewの背景

```swift
// カード背景
Text("Hello, World!")
    .padding()
    .background {
        RoundedRectangle(cornerRadius: 12)
            .fill(Color.white)
            .shadow(radius: 4)
    }

// グラデーション背景
Text("Gradient")
    .padding()
    .background {
        LinearGradient(
            colors: [.blue, .purple],
            startPoint: .leading,
            endPoint: .trailing
        )
    }
```

### 選択の指針

```swift
// ✅ ZStack: 両方のサイズが重要、または複数要素を対等に扱う
ZStack {
    BackgroundView()
    ContentView()
    OverlayView()
}

// ✅ overlay: メインコンテンツに付加的な要素を追加
MainContent()
    .overlay(alignment: .bottomTrailing) {
        FloatingActionButton()
    }

// ✅ background: メインコンテンツに背景を追加
MainContent()
    .background {
        BackgroundEffect()
    }
```

---

## 4-5. ContentUnavailableView パターン（iOS 17+）

### 基本的な使い方

```swift
// システム提供のスタイル
ContentUnavailableView.search  // 検索結果なし
ContentUnavailableView.search(text: query)  // 検索クエリ付き

// カスタムメッセージ
ContentUnavailableView(
    "データがありません",
    systemImage: "tray",
    description: Text("新しいアイテムを追加してください")
)
```

### overlayを使った責務分離パターン

メインコンテンツと空/エラー状態を分離して可読性を向上。

```swift
// ✅ 推奨: overlayで分離
struct ItemListView: View {
    @State private var items: [Item] = []
    @State private var searchText = ""
    @State private var error: Error?

    var filteredItems: [Item] {
        if searchText.isEmpty {
            return items
        }
        return items.filter { $0.name.contains(searchText) }
    }

    var body: some View {
        NavigationStack {
            List(filteredItems) { item in
                ItemRow(item: item)
            }
            .searchable(text: $searchText)
            // 空状態・エラー状態をoverlayで分離
            .overlay {
                if let error {
                    ContentUnavailableView(
                        "読み込みエラー",
                        systemImage: "exclamationmark.triangle",
                        description: Text(error.localizedDescription)
                    )
                } else if items.isEmpty {
                    ContentUnavailableView(
                        "アイテムがありません",
                        systemImage: "tray",
                        description: Text("右上の＋ボタンから追加できます")
                    )
                } else if filteredItems.isEmpty {
                    ContentUnavailableView.search(text: searchText)
                }
            }
        }
    }
}

// ❌ 避けるべき: if-elseで分岐（可読性低下）
var body: some View {
    if let error {
        ErrorView(error: error)
    } else if items.isEmpty {
        EmptyView()
    } else if filteredItems.isEmpty {
        SearchEmptyView()
    } else {
        List(filteredItems) { ... }  // メインロジックが深くネスト
    }
}
```

### アクションボタン付き

```swift
ContentUnavailableView {
    Label("接続エラー", systemImage: "wifi.slash")
} description: {
    Text("インターネット接続を確認してください")
} actions: {
    Button("再試行") {
        Task { await retry() }
    }
    .buttonStyle(.borderedProminent)
}
```

### iOS 16以前との互換性

```swift
struct ContentUnavailableViewCompat<Label: View, Description: View, Actions: View>: View {
    let label: Label
    let description: Description
    let actions: Actions

    init(
        @ViewBuilder label: () -> Label,
        @ViewBuilder description: () -> Description = { EmptyView() },
        @ViewBuilder actions: () -> Actions = { EmptyView() }
    ) {
        self.label = label()
        self.description = description()
        self.actions = actions()
    }

    var body: some View {
        VStack(spacing: 16) {
            label
                .font(.title)
                .foregroundColor(.secondary)
            description
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            actions
        }
        .padding()
    }
}
```

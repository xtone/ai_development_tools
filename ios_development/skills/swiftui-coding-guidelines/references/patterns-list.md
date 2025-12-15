# SwiftUI リスト・データ表示パターン

## 1-1. 無限スクロール（Pagination）

### 基本実装

```swift
@MainActor
class ArticleListViewModel: ObservableObject {
    @Published var articles: [Article] = []
    @Published var isLoading = false
    @Published var hasMorePages = true

    private var currentPage = 1
    private let pageSize = 20

    func loadMoreIfNeeded(currentItem: Article?) async {
        guard !isLoading, hasMorePages else { return }

        // 最後から5番目に到達したら次を読み込み
        guard let currentItem = currentItem,
              let index = articles.firstIndex(where: { $0.id == currentItem.id }),
              index >= articles.count - 5 else {
            return
        }

        await loadMore()
    }

    func loadMore() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let newArticles = try await articleService.fetch(
                page: currentPage,
                limit: pageSize
            )
            articles.append(contentsOf: newArticles)
            currentPage += 1
            hasMorePages = newArticles.count == pageSize
        } catch {
            // エラーハンドリング
        }
    }
}

struct ArticleListView: View {
    @StateObject private var viewModel = ArticleListViewModel()

    var body: some View {
        List {
            ForEach(viewModel.articles) { article in
                ArticleRow(article: article)
                    .task {
                        await viewModel.loadMoreIfNeeded(currentItem: article)
                    }
            }

            if viewModel.isLoading {
                ProgressView()
                    .frame(maxWidth: .infinity)
            }
        }
        .task {
            await viewModel.loadMore()
        }
    }
}
```

---

## 1-2. プルトゥリフレッシュ

```swift
struct ArticleListView: View {
    @StateObject private var viewModel = ArticleListViewModel()

    var body: some View {
        List(viewModel.articles) { article in
            ArticleRow(article: article)
        }
        .refreshable {
            await viewModel.refresh()
        }
    }
}

// ViewModel
func refresh() async {
    currentPage = 1
    hasMorePages = true

    do {
        articles = try await articleService.fetch(page: 1, limit: pageSize)
        currentPage = 2
    } catch {
        // エラーハンドリング
    }
}
```

---

## 1-3. フィルタリング・ソート

```swift
struct FilterableListView: View {
    @StateObject private var viewModel = ItemListViewModel()
    @State private var selectedFilter: Filter = .all
    @State private var sortOrder: SortOrder = .dateDescending

    enum Filter: String, CaseIterable {
        case all = "すべて"
        case active = "アクティブ"
        case completed = "完了"
    }

    enum SortOrder: String, CaseIterable {
        case dateDescending = "新しい順"
        case dateAscending = "古い順"
        case nameAscending = "名前順"
    }

    var filteredItems: [Item] {
        var items = viewModel.items

        // フィルタ適用
        switch selectedFilter {
        case .active:
            items = items.filter { !$0.isCompleted }
        case .completed:
            items = items.filter { $0.isCompleted }
        case .all:
            break
        }

        // ソート適用
        switch sortOrder {
        case .dateDescending:
            items.sort { $0.date > $1.date }
        case .dateAscending:
            items.sort { $0.date < $1.date }
        case .nameAscending:
            items.sort { $0.name < $1.name }
        }

        return items
    }

    var body: some View {
        List(filteredItems) { item in
            ItemRow(item: item)
        }
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Menu {
                    Picker("フィルタ", selection: $selectedFilter) {
                        ForEach(Filter.allCases, id: \.self) { filter in
                            Text(filter.rawValue).tag(filter)
                        }
                    }

                    Picker("並び替え", selection: $sortOrder) {
                        ForEach(SortOrder.allCases, id: \.self) { order in
                            Text(order.rawValue).tag(order)
                        }
                    }
                } label: {
                    Image(systemName: "line.3.horizontal.decrease.circle")
                }
            }
        }
    }
}
```

---

## 1-4. スワイプアクション

```swift
List {
    ForEach(items) { item in
        ItemRow(item: item)
            .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                Button(role: .destructive) {
                    deleteItem(item)
                } label: {
                    Label("削除", systemImage: "trash")
                }

                Button {
                    archiveItem(item)
                } label: {
                    Label("アーカイブ", systemImage: "archivebox")
                }
                .tint(.orange)
            }
            .swipeActions(edge: .leading) {
                Button {
                    toggleFavorite(item)
                } label: {
                    Label(
                        item.isFavorite ? "お気に入り解除" : "お気に入り",
                        systemImage: item.isFavorite ? "star.slash" : "star"
                    )
                }
                .tint(.yellow)
            }
    }
}
```

---

## 1-5. コンテキストメニュー

```swift
ArticleRow(article: article)
    .contextMenu {
        Button {
            shareArticle(article)
        } label: {
            Label("共有", systemImage: "square.and.arrow.up")
        }

        Button {
            toggleFavorite(article)
        } label: {
            Label(
                article.isFavorite ? "お気に入り解除" : "お気に入り",
                systemImage: article.isFavorite ? "star.slash" : "star"
            )
        }

        Divider()

        Button(role: .destructive) {
            deleteArticle(article)
        } label: {
            Label("削除", systemImage: "trash")
        }
    }
```

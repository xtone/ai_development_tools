# SwiftUI ナビゲーション・画面遷移パターン

## 2-1. タブビュー

```swift
struct MainTabView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem {
                    Label("ホーム", systemImage: "house")
                }
                .tag(0)

            SearchView()
                .tabItem {
                    Label("検索", systemImage: "magnifyingglass")
                }
                .tag(1)

            ProfileView()
                .tabItem {
                    Label("プロフィール", systemImage: "person")
                }
                .tag(2)
        }
    }

    // プログラマティックにタブ切り替え
    func switchToSearch() {
        selectedTab = 1
    }
}
```

---

## 2-2. ナビゲーション（NavigationStack）

```swift
enum Route: Hashable {
    case articleDetail(Article)
    case userProfile(userId: String)
    case settings
}

struct ContentView: View {
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            ArticleListView(onSelectArticle: { article in
                path.append(Route.articleDetail(article))
            })
            .navigationDestination(for: Route.self) { route in
                switch route {
                case .articleDetail(let article):
                    ArticleDetailView(article: article)
                case .userProfile(let userId):
                    UserProfileView(userId: userId)
                case .settings:
                    SettingsView()
                }
            }
        }
    }

    // ディープリンク対応
    func handleDeepLink(url: URL) {
        guard let route = parseDeepLink(url) else { return }
        path.append(route)
    }

    func popToRoot() {
        path.removeLast(path.count)
    }
}
```

---

## 2-3. モーダル表示

### Sheet

```swift
struct ContentView: View {
    @State private var showSheet = false
    @State private var selectedItem: Item?

    var body: some View {
        List(items) { item in
            Button(item.name) {
                selectedItem = item
            }
        }
        .sheet(item: $selectedItem) { item in
            ItemDetailView(item: item)
        }

        // または isPresented
        Button("新規作成") {
            showSheet = true
        }
        .sheet(isPresented: $showSheet) {
            CreateItemView()
        }
    }
}
```

### FullScreenCover

```swift
.fullScreenCover(isPresented: $showFullScreen) {
    FullScreenView()
}
```

### 閉じる処理

```swift
struct SheetView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Content()
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("キャンセル") {
                            dismiss()
                        }
                    }
                }
        }
    }
}
```

---

## 2-4. アラート・ダイアログ

```swift
struct ContentView: View {
    @State private var showAlert = false
    @State private var showConfirmation = false

    var body: some View {
        VStack {
            Button("アラート表示") {
                showAlert = true
            }
            .alert("タイトル", isPresented: $showAlert) {
                Button("OK") { }
            } message: {
                Text("メッセージ内容")
            }

            Button("確認ダイアログ") {
                showConfirmation = true
            }
            .confirmationDialog("選択してください", isPresented: $showConfirmation) {
                Button("編集") { }
                Button("削除", role: .destructive) { }
                Button("キャンセル", role: .cancel) { }
            }
        }
    }
}
```

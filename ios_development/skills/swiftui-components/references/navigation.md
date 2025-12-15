# ナビゲーションコンポーネント

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | 備考 |
|--------------|-----|--------|-------|------|
| NavigationStack | 16+ | 16+ | 13+ | NavigationViewの後継 |
| NavigationSplitView | 16+ | 16+ | 13+ | 2列/3列レイアウト |
| NavigationPath | 16+ | 16+ | 13+ | 複数型のナビゲーションパス |
| navigationDestination | 16+ | 16+ | 13+ | 宣言的な遷移先定義 |
| TabView (iOS 26刷新) | 26+ | 26+ | - | 新デザイン・アニメーション |

---

## NavigationStack

iOS 16で導入された`NavigationView`の後継。プログラマティックなナビゲーション制御が可能。

### 基本的な使用法

```swift
// iOS 15以前: NavigationView（非推奨）
NavigationView {
    List(items) { item in
        NavigationLink(destination: DetailView(item: item)) {
            Text(item.name)
        }
    }
}

// iOS 16+: NavigationStack
NavigationStack {
    List(items) { item in
        NavigationLink(value: item) {
            Text(item.name)
        }
    }
    .navigationDestination(for: Item.self) { item in
        DetailView(item: item)
    }
}
```

### プログラマティックナビゲーション

```swift
struct ContentView: View {
    @State private var path: [Item] = []

    var body: some View {
        NavigationStack(path: $path) {
            List(items) { item in
                NavigationLink(value: item) {
                    Text(item.name)
                }
            }
            .navigationDestination(for: Item.self) { item in
                DetailView(item: item)
            }
        }
    }

    // プログラムでナビゲーション
    func navigateTo(_ item: Item) {
        path.append(item)
    }

    // ルートに戻る
    func popToRoot() {
        path.removeAll()
    }
}
```

### NavigationPath（複数の型をサポート）

```swift
struct ContentView: View {
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            VStack {
                Button("Show User") {
                    path.append(User(name: "John"))
                }
                Button("Show Article") {
                    path.append(Article(title: "News"))
                }
            }
            .navigationDestination(for: User.self) { user in
                UserDetailView(user: user)
            }
            .navigationDestination(for: Article.self) { article in
                ArticleDetailView(article: article)
            }
        }
    }
}
```

---

## NavigationSplitView

2列または3列のレイアウトを提供。iPadやMacでのマスター・ディテール表示に最適。

### 2列レイアウト

```swift
NavigationSplitView {
    // サイドバー
    List(categories, selection: $selectedCategory) { category in
        Text(category.name)
    }
} detail: {
    // 詳細ビュー
    if let category = selectedCategory {
        CategoryDetailView(category: category)
    } else {
        Text("カテゴリを選択してください")
    }
}
```

### 3列レイアウト

```swift
NavigationSplitView {
    // サイドバー
    CategoryList(selection: $selectedCategory)
} content: {
    // コンテンツ列
    if let category = selectedCategory {
        ItemList(category: category, selection: $selectedItem)
    }
} detail: {
    // 詳細列
    if let item = selectedItem {
        ItemDetailView(item: item)
    }
}
```

### カラム幅のカスタマイズ

```swift
NavigationSplitView(columnVisibility: $columnVisibility) {
    Sidebar()
} content: {
    Content()
} detail: {
    Detail()
}
.navigationSplitViewColumnWidth(min: 180, ideal: 200, max: 250)
```

---

## 後方互換性

iOS 15以前をサポートする場合：

```swift
var body: some View {
    if #available(iOS 16.0, *) {
        NavigationStack {
            content
        }
    } else {
        NavigationView {
            content
        }
        .navigationViewStyle(.stack)
    }
}
```

---

## TabView刷新 (iOS 26+)

iOS 26ではiPhoneのTabViewのUI/UXが刷新。

### 特徴

- 新しいビジュアルデザイン（Liquid Glassとの統合）
- スムーズなアニメーション
- よりモダンなタブ切り替え体験

### 基本的な使用法

```swift
TabView {
    HomeView()
        .tabItem {
            Label("ホーム", systemImage: "house")
        }

    SearchView()
        .tabItem {
            Label("検索", systemImage: "magnifyingglass")
        }

    ProfileView()
        .tabItem {
            Label("プロフィール", systemImage: "person")
        }
}
```

> **注意**: iOS 26では標準のTabViewが自動的に新デザインに更新されます。特別な対応は不要ですが、カスタマイズしている場合は確認が必要です。

---

## 移行チェックリスト

### NavigationViewからの移行

1. [ ] `NavigationView`を`NavigationStack`または`NavigationSplitView`に置換
2. [ ] `NavigationLink(destination:)`を`NavigationLink(value:)`に変更
3. [ ] `.navigationDestination(for:)`を追加
4. [ ] プログラマティックナビゲーションには`@State`でパスを管理
5. [ ] `.navigationViewStyle(.stack)`を削除（NavigationStackはデフォルトでスタック）

---

## 関連ドキュメント

- [NavigationStack - Apple Developer](https://developer.apple.com/documentation/swiftui/navigationstack)
- [NavigationSplitView - Apple Developer](https://developer.apple.com/documentation/swiftui/navigationsplitview)
- [NavigationPath - Apple Developer](https://developer.apple.com/documentation/swiftui/navigationpath)

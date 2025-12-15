# iOS 17+ @Observable マクロガイド

## 概要

iOS 17で導入された`@Observable`マクロは、SwiftUIの状態管理を大幅に簡素化し、パフォーマンスを向上させる。

## 移行パターン

### 基本的な変更

| iOS 13-16 | iOS 17+ |
|-----------|---------|
| `ObservableObject` + `@Published` | `@Observable`（`@Published`不要） |
| `@StateObject` | `@State` |
| `@ObservedObject` | ラッパー不要（直接渡す） |
| `@EnvironmentObject` | `@Environment(MyType.self)` |

### Before: ObservableObject（iOS 13-16）

```swift
class ArticleViewModel: ObservableObject {
    @Published var articles: [Article] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    func fetch() async {
        isLoading = true
        defer { isLoading = false }
        // ...
    }
}

struct ArticleListView: View {
    @StateObject private var viewModel = ArticleViewModel()
    
    var body: some View {
        ChildView(viewModel: viewModel)
    }
}

struct ChildView: View {
    @ObservedObject var viewModel: ArticleViewModel
    // ...
}
```

### After: @Observable（iOS 17+）

```swift
@Observable
class ArticleViewModel {
    var articles: [Article] = []
    var isLoading = false
    var errorMessage: String?
    
    func fetch() async {
        isLoading = true
        defer { isLoading = false }
        // ...
    }
}

struct ArticleListView: View {
    @State private var viewModel = ArticleViewModel()
    
    var body: some View {
        ChildView(viewModel: viewModel)
    }
}

struct ChildView: View {
    var viewModel: ArticleViewModel // ラッパー不要
    // ...
}
```

## @Bindableの使用

子ビューで双方向バインディングが必要な場合は`@Bindable`を使用。

```swift
@Observable
class FormData {
    var name = ""
    var email = ""
}

struct FormView: View {
    @State private var formData = FormData()
    
    var body: some View {
        FormContent(formData: formData)
    }
}

struct FormContent: View {
    @Bindable var formData: FormData
    
    var body: some View {
        Form {
            TextField("Name", text: $formData.name)
            TextField("Email", text: $formData.email)
        }
    }
}
```

## Environment経由の注入

```swift
// iOS 13-16
struct ContentView: View {
    @EnvironmentObject var settings: AppSettings
}

// iOS 17+
@Observable
class AppSettings {
    var theme: Theme = .light
}

struct ContentView: View {
    @Environment(AppSettings.self) var settings
    
    var body: some View {
        // 双方向バインディングが必要な場合
        @Bindable var settings = settings
        Toggle("Dark Mode", isOn: $settings.isDarkMode)
    }
}

// 注入
ContentView()
    .environment(AppSettings())
```

## パフォーマンス向上

### 選択的な監視

`@Observable`は使用されるプロパティのみを監視し、不要な再描画を防止。

```swift
@Observable
class ViewModel {
    var name = ""      // NameViewのみが監視
    var count = 0      // CountViewのみが監視
    var items: [Item] = []  // ItemsViewのみが監視
}

struct NameView: View {
    var viewModel: ViewModel
    
    var body: some View {
        // nameが変更された時のみ再描画
        // countやitemsの変更では再描画されない
        Text(viewModel.name)
    }
}

struct CountView: View {
    var viewModel: ViewModel
    
    var body: some View {
        // countが変更された時のみ再描画
        Text("\(viewModel.count)")
    }
}
```

### ObservableObjectとの比較

```swift
// ObservableObject: すべての@Publishedプロパティの変更で全ビューが再描画
class OldViewModel: ObservableObject {
    @Published var name = ""
    @Published var count = 0
}

// @Observable: 使用しているプロパティの変更のみで再描画
@Observable
class NewViewModel {
    var name = ""
    var count = 0
}
```

## 注意点

### @State vs @StateObject の違い

```swift
// ⚠️ 注意: @Stateは@StateObjectと異なる動作をする可能性

// @StateObject: ビュー再生成時も同じインスタンスを維持
@StateObject private var viewModel = ViewModel()

// @State with @Observable: 条件付きビューでは再初期化の可能性
@State private var viewModel = ViewModel()
```

**Jesse Squiresの記事より**:
- `@State`で`@Observable`オブジェクトを使用する場合、ビューの条件付き表示で予期しない再初期化が起こる可能性
- 複雑なナビゲーションやモーダル表示では注意が必要

### 監視の除外

特定のプロパティを監視対象から除外する場合:

```swift
@Observable
class ViewModel {
    var trackedProperty = ""
    
    @ObservationIgnored
    var ignoredProperty = ""  // 変更しても再描画されない
}
```

## 移行チェックリスト

1. [ ] `ObservableObject`を`@Observable`に変更
2. [ ] `@Published`を削除
3. [ ] `@StateObject`を`@State`に変更
4. [ ] `@ObservedObject`を削除（直接渡す）
5. [ ] `@EnvironmentObject`を`@Environment(Type.self)`に変更
6. [ ] 双方向バインディングが必要な箇所に`@Bindable`を追加
7. [ ] `@ObservationIgnored`で監視不要なプロパティをマーク
8. [ ] 条件付きビューでの状態維持を確認

## 後方互換性

iOS 17未満をサポートする場合:

```swift
#if swift(>=5.9)
@Observable
class ViewModel {
    var items: [Item] = []
}
#else
class ViewModel: ObservableObject {
    @Published var items: [Item] = []
}
#endif
```

または、iOS 17+のみで`@Observable`を使用し、iOS 16以下では従来のパターンを維持。

# SwiftUI アンチパターン集

## 1. 状態管理のアンチパターン

### 1.1 @Stateで参照型を使用

```swift
// ❌ アンチパターン: @Stateで参照型
@State private var viewModel = MyViewModel() // classの場合

// 問題点:
// - 変更が検知されない
// - メモリリーク、パフォーマンス低下
// - 予期しない動作

// ✅ 解決策: @StateObjectを使用
@StateObject private var viewModel = MyViewModel()
```

### 1.2 導出可能な状態の保持

```swift
// ❌ アンチパターン: 導出可能な状態
@State private var items: [Item] = []
@State private var count: Int = 0 // items.countで計算可能
@State private var isEmpty: Bool = true // items.isEmptyで計算可能

// 問題点:
// - 状態の同期が必要
// - バグの温床
// - SSOT違反

// ✅ 解決策: 計算プロパティを使用
@State private var items: [Item] = []
private var count: Int { items.count }
private var isEmpty: Bool { items.isEmpty }
```

### 1.3 @StateObjectと@ObservedObjectの混同

```swift
// ❌ アンチパターン: 親で@ObservedObject
struct ParentView: View {
    @ObservedObject var viewModel = MyViewModel() // 新規作成
    // ビュー再描画のたびに再作成される可能性
}

// ✅ 解決策: 所有者は@StateObject
struct ParentView: View {
    @StateObject private var viewModel = MyViewModel()
}

struct ChildView: View {
    @ObservedObject var viewModel: MyViewModel // 受け取る場合はOK
}
```

### 1.4 状態の過剰な分散

```swift
// ❌ アンチパターン: 状態があちこちに
struct View1: View {
    @State private var user: User?
}
struct View2: View {
    @State private var user: User? // 重複
}

// ✅ 解決策: 共有状態はEnvironmentまたは親から渡す
class UserStore: ObservableObject {
    @Published var user: User?
}

struct RootView: View {
    @StateObject private var userStore = UserStore()
    
    var body: some View {
        ContentView()
            .environmentObject(userStore)
    }
}
```

## 2. パフォーマンスのアンチパターン

### 2.1 body内での重い計算

```swift
// ❌ アンチパターン: 毎回実行される
var body: some View {
    let sortedItems = items.sorted { $0.date > $1.date } // 毎回ソート
    let filteredItems = sortedItems.filter { $0.isActive } // 毎回フィルタ
    
    List(filteredItems) { item in
        ItemRow(item: item)
    }
}

// ✅ 解決策: 計算を事前に実行
@State private var items: [Item] = []
@State private var processedItems: [Item] = []

var body: some View {
    List(processedItems) { item in
        ItemRow(item: item)
    }
    .onChange(of: items) { _, newItems in
        processedItems = newItems
            .sorted { $0.date > $1.date }
            .filter { $0.isActive }
    }
}
```

### 2.2 Lazyを使わない大量データ

```swift
// ❌ アンチパターン: 全アイテムを即座にレンダリング
ScrollView {
    VStack {
        ForEach(items) { item in // 1000アイテムすべて即座に
            ItemRow(item: item)
        }
    }
}

// ✅ 解決策: LazyVStackを使用（30-40%メモリ削減）
ScrollView {
    LazyVStack {
        ForEach(items) { item in
            ItemRow(item: item)
        }
    }
}
```

### 2.3 GeometryReaderの過剰使用

```swift
// ❌ アンチパターン: リスト内でGeometryReader
List(items) { item in
    GeometryReader { geo in // 各行で再計算
        ItemRow(item: item, width: geo.size.width)
    }
}

// ✅ 解決策: 外側で1回だけ使用
GeometryReader { geo in
    List(items) { item in
        ItemRow(item: item, width: geo.size.width)
    }
}
```

### 2.4 不要な再レンダリング

```swift
// ❌ アンチパターン: 関係ない変更で再レンダリング
class ViewModel: ObservableObject {
    @Published var items: [Item] = []
    @Published var searchText = "" // 変更で全ビューが再描画
}

// ✅ 解決策 (iOS 17+): @Observableで選択的監視
@Observable
class ViewModel {
    var items: [Item] = [] // 使用するビューのみ再描画
    var searchText = ""
}
```

## 3. ビジネスロジックのアンチパターン

### 3.1 View内にビジネスロジック

```swift
// ❌ アンチパターン: View内でロジック
struct ArticleListView: View {
    @State private var articles: [Article] = []
    
    var body: some View {
        List(articles) { ... }
            .onAppear {
                // ネットワーク処理がView内に
                URLSession.shared.dataTask(with: url) { data, _, _ in
                    if let data = data {
                        let decoded = try? JSONDecoder().decode([Article].self, from: data)
                        DispatchQueue.main.async {
                            articles = decoded ?? []
                        }
                    }
                }.resume()
            }
    }
}

// ✅ 解決策: ViewModelに分離
@MainActor
class ArticleListViewModel: ObservableObject {
    @Published var articles: [Article] = []
    
    func fetchArticles() async {
        do {
            articles = try await articleService.fetch()
        } catch {
            // エラーハンドリング
        }
    }
}

struct ArticleListView: View {
    @StateObject private var viewModel = ArticleListViewModel()
    
    var body: some View {
        List(viewModel.articles) { ... }
            .task {
                await viewModel.fetchArticles()
            }
    }
}
```

### 3.2 ハードコードされた依存

```swift
// ❌ アンチパターン: 直接依存
class ViewModel: ObservableObject {
    private let service = ArticleService() // テスト不可
}

// ✅ 解決策: プロトコルと依存性注入
protocol ArticleServiceProtocol {
    func fetch() async throws -> [Article]
}

class ViewModel: ObservableObject {
    private let service: ArticleServiceProtocol
    
    init(service: ArticleServiceProtocol = ArticleService()) {
        self.service = service
    }
}
```

## 4. 非同期処理のアンチパターン

### 4.1 onAppearでの非同期処理

```swift
// ❌ アンチパターン: onAppear + Task
.onAppear {
    Task {
        await viewModel.fetchData()
    }
    // ビュー消失時にキャンセルされない
}

// ✅ 解決策: .taskモディファイア（自動キャンセル）
.task {
    await viewModel.fetchData()
}
```

### 4.2 メインスレッドでの重い処理

```swift
// ❌ アンチパターン: UIスレッドをブロック
func processImages() {
    let processed = images.map { image in
        heavyImageProcessing(image) // UIが固まる
    }
    self.processedImages = processed
}

// ✅ 解決策: バックグラウンドで実行
func processImages() async {
    let processed = await Task.detached(priority: .userInitiated) {
        images.map { heavyImageProcessing($0) }
    }.value
    
    await MainActor.run {
        self.processedImages = processed
    }
}
```

### 4.3 逐次的なawait

```swift
// ❌ アンチパターン: 順番に待機
func fetchAllData() async {
    let users = await fetchUsers()    // 待機
    let posts = await fetchPosts()    // 待機
    let comments = await fetchComments() // 待機
    // 合計: 3つの待機時間の和
}

// ✅ 解決策: 並列実行
func fetchAllData() async {
    async let users = fetchUsers()
    async let posts = fetchPosts()
    async let comments = fetchComments()
    
    let (u, p, c) = await (users, posts, comments)
    // 合計: 最長の待機時間のみ
}
```

## 5. ナビゲーションのアンチパターン

### 5.1 NavigationViewの使用（iOS 16+）

```swift
// ❌ アンチパターン: 非推奨API
NavigationView {
    List(items) { item in
        NavigationLink(destination: DetailView(item: item)) {
            ItemRow(item: item)
        }
    }
}

// ✅ 解決策: NavigationStack
NavigationStack {
    List(items) { item in
        NavigationLink(value: item) {
            ItemRow(item: item)
        }
    }
    .navigationDestination(for: Item.self) { item in
        DetailView(item: item)
    }
}
```

### 5.2 複数のナビゲーション状態

```swift
// ❌ アンチパターン: 分散したナビゲーション状態
@State private var showDetail = false
@State private var showSettings = false
@State private var showProfile = false

// ✅ 解決策: NavigationPathで一元管理
enum Route: Hashable {
    case detail(Item)
    case settings
    case profile
}

@State private var path = NavigationPath()
```

## 6. モディファイアのアンチパターン

### 6.1 スタイルの重複

```swift
// ❌ アンチパターン: 同じスタイルを繰り返し
Text("Title1")
    .font(.headline)
    .foregroundColor(.primary)
    .padding()
    .background(Color.gray.opacity(0.1))
    .cornerRadius(8)

Text("Title2")
    .font(.headline)
    .foregroundColor(.primary)
    .padding()
    .background(Color.gray.opacity(0.1))
    .cornerRadius(8)

// ✅ 解決策: ViewModifierで共通化
struct CardTitleStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .font(.headline)
            .foregroundColor(.primary)
            .padding()
            .background(Color.gray.opacity(0.1))
            .cornerRadius(8)
    }
}

extension View {
    func cardTitleStyle() -> some View {
        modifier(CardTitleStyle())
    }
}

Text("Title1").cardTitleStyle()
Text("Title2").cardTitleStyle()
```

### 6.2 モディファイア順序の無視

```swift
// 順序で結果が変わる
Text("Hello")
    .padding()
    .background(Color.red) // paddingの外側が赤

Text("Hello")
    .background(Color.red)
    .padding() // テキストの背景のみ赤、paddingは透明
```

## 7. エラーハンドリングのアンチパターン

### 7.1 エラーの無視

```swift
// ❌ アンチパターン: エラーを握りつぶす
func fetchData() async {
    do {
        data = try await service.fetch()
    } catch {
        // 何もしない
    }
}

// ✅ 解決策: エラー状態を管理
@Published var error: Error?

func fetchData() async {
    do {
        data = try await service.fetch()
        error = nil
    } catch {
        self.error = error
    }
}

// View側
if let error = viewModel.error {
    ErrorView(error: error, onRetry: { Task { await viewModel.fetchData() } })
}
```

## 8. メモリ管理のアンチパターン

### 8.1 循環参照

```swift
// ❌ アンチパターン: クロージャで強参照
class ViewModel: ObservableObject {
    var onComplete: (() -> Void)?
    
    func setup() {
        onComplete = {
            self.doSomething() // 循環参照
        }
    }
}

// ✅ 解決策: [weak self]を使用
func setup() {
    onComplete = { [weak self] in
        self?.doSomething()
    }
}
```

### 8.2 Combineのキャンセル忘れ

```swift
// ❌ アンチパターン: キャンセルしない
class ViewModel: ObservableObject {
    func subscribe() {
        publisher.sink { value in
            // 処理
        }
        // AnyCancellableを保持していない
    }
}

// ✅ 解決策: cancellablesで保持
private var cancellables = Set<AnyCancellable>()

func subscribe() {
    publisher
        .sink { [weak self] value in
            self?.handle(value)
        }
        .store(in: &cancellables)
}
```

## 9. AnyViewのアンチパターン

### 9.1 AnyViewによる型消去

```swift
// ❌ アンチパターン: AnyViewの使用
func makeView(for type: ViewType) -> AnyView {
    switch type {
    case .text:
        return AnyView(Text("Hello"))
    case .image:
        return AnyView(Image(systemName: "star"))
    case .button:
        return AnyView(Button("Tap") { })
    }
}

var body: some View {
    makeView(for: currentType)
}
```

**問題点**:
- 型情報が消去され、SwiftUIの差分検出（Diffing）が非効率になる
- パフォーマンス低下（SwiftUIがView階層を正しく追跡できない）
- アニメーションが正しく動作しない可能性

```swift
// ✅ 解決策1: @ViewBuilderを使用
@ViewBuilder
func makeView(for type: ViewType) -> some View {
    switch type {
    case .text:
        Text("Hello")
    case .image:
        Image(systemName: "star")
    case .button:
        Button("Tap") { }
    }
}

// ✅ 解決策2: Groupを使用
var body: some View {
    Group {
        switch currentType {
        case .text:
            Text("Hello")
        case .image:
            Image(systemName: "star")
        case .button:
            Button("Tap") { }
        }
    }
}

// ✅ 解決策3: ジェネリクスを使用
struct ContainerView<Content: View>: View {
    let content: Content
    
    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }
    
    var body: some View {
        content
    }
}
```

### 9.2 冗長なビューラッピング

```swift
// ❌ アンチパターン: 不要なラッピング
VStack {
    Color.red
}

// ✅ 解決策: 直接使用
Color.red
```

## 10. ViewのIdentity（同一性）のアンチパターン

SwiftUIは「ある時点のView」と「次の時点のView」が同じか判断するためにIdentityを使用。

### Identity の種類

**明示的Identity (Explicit Identity)**
- `id()` モディファイア、`ForEach` の引数で明示的に指定
- データベースの主キーのように機能

**構造的Identity (Structural Identity)**
- View階層内での位置（パス）によって決定
- `if-else` 分岐は異なる構造的IDを持つ

### 10.1 ForEachでのインデックス使用（🔴 重大）

```swift
// ❌ アンチパターン: インデックスをIDとして使用
struct ItemListView: View {
    @State private var items = ["A", "B", "C"]
    
    var body: some View {
        List {
            ForEach(0..<items.count, id: \.self) { index in
                Text(items[index])
            }
        }
    }
}
// 問題: 要素削除時にインデックスとデータがずれる
// → 状態消失、クラッシュ、アニメーション崩壊

// ✅ 解決策: 安定した一意のIDを持つモデルを使用
struct Item: Identifiable {
    let id = UUID()
    var name: String
}

struct ItemListView: View {
    @State private var items = [Item(name: "A"), Item(name: "B"), Item(name: "C")]
    
    var body: some View {
        List {
            ForEach(items) { item in
                Text(item.name)
            }
        }
    }
}
```

### 10.2 不安定なIDによる状態リセット

```swift
// ❌ アンチパターン: 毎回新しいIDを生成
struct ContentView: View {
    @State private var text = ""
    
    var body: some View {
        TextField("Input", text: $text)
            .id(UUID())  // 毎回新しいID → 状態がリセットされる
    }
}

// ✅ 解決策: 安定したIDを使用
struct ContentView: View {
    @State private var text = ""
    let textFieldId = "mainTextField"
    
    var body: some View {
        TextField("Input", text: $text)
            .id(textFieldId)  // 安定したID
    }
}
```

### 10.3 条件分岐による意図しないIdentity変更

```swift
// ⚠️ 注意: if-elseは構造的に異なるViewを生成
var body: some View {
    if isLoggedIn {
        HomeView()  // 構造的ID: "true分岐"
    } else {
        LoginView() // 構造的ID: "false分岐"
    }
}
// → isLoggedInが変わると完全に別のViewとして扱われる
// → @Stateなどの状態は保持されない（これは通常は期待通りの動作）

// 同じViewで状態を保持したい場合
var body: some View {
    ContentView(isLoggedIn: isLoggedIn)
        .id("content")  // 明示的IDで同一性を維持
}
```

### 10.4 リスト内でのIdentity問題

```swift
// ❌ アンチパターン: Hashableだが不安定
struct Article {
    var title: String
    var content: String
}

extension Article: Hashable {
    func hash(into hasher: inout Hasher) {
        hasher.combine(title)  // titleが変わるとIDが変わる
    }
}

// ✅ 解決策: Identifiableで安定したID
struct Article: Identifiable {
    let id = UUID()  // 不変のID
    var title: String
    var content: String
}
```

## 11. その他のアンチパターン

### 11.1 Computed Propertyでの重い処理

```swift
// ❌ アンチパターン: body内で毎回実行
var body: some View {
    let formatter = DateFormatter()  // 毎回生成（高コスト）
    formatter.dateStyle = .medium
    
    return Text(formatter.string(from: date))
}

// ✅ 解決策: staticでキャッシュ
struct DateView: View {
    let date: Date
    
    private static let formatter: DateFormatter = {
        let f = DateFormatter()
        f.dateStyle = .medium
        return f
    }()
    
    var body: some View {
        Text(Self.formatter.string(from: date))
    }
}
```

### 11.2 onAppearへの過度な依存

```swift
// ❌ アンチパターン: NavigationStackで重複実行
struct DetailView: View {
    @State private var data: Data?
    
    var body: some View {
        content
            .onAppear {
                // 戻る→進むで毎回実行される
                loadData()
            }
    }
}

// ✅ 解決策: taskで初回のみ、または冪等性を担保
struct DetailView: View {
    @State private var data: Data?
    
    var body: some View {
        content
            .task {
                // Viewのライフサイクルに連動、自動キャンセル
                guard data == nil else { return }  // 冪等性
                data = await fetchData()
            }
    }
}
```

## 12. コンポーネント設計のアンチパターン

### 12.1 🔴 子コンポーネントでスペーシングを管理

子Viewで`padding`を使って間隔を設定すると、再利用性が低下し、レイアウトの一貫性が失われる。

```swift
// ❌ アンチパターン: 子がスペーシングを持つ
VStack(spacing: 0) {
    Image(systemName: "swift")
        .padding(.bottom, 8)  // 子がスペーシングを制御
    Text("Swift")
        .padding(.bottom, 8)  // 毎回padding指定が必要
    Text("Programming")
}

// ❌ 問題点:
// - 再利用時に余計なスペースが付いてくる
// - 最後の要素だけpaddingを外す条件分岐が必要
// - レイアウト変更時に全ての子を修正する必要がある

// ✅ 解決策: 親がスペーシングを管理
VStack(spacing: 8) {  // 親が一括管理
    Image(systemName: "swift")
    Text("Swift")
    Text("Programming")
}

// ✅ 異なるスペーシングが必要な場合
VStack(spacing: 0) {
    // グループ1
    VStack(spacing: 4) {
        Image(systemName: "swift")
        Text("Swift")
    }
    
    Spacer().frame(height: 16)  // グループ間のスペース
    
    // グループ2
    VStack(spacing: 4) {
        Image(systemName: "apple.logo")
        Text("Apple")
    }
}
```

**原則**: スペーシングは親コンポーネントの責務。子コンポーネントは自身のコンテンツのみに責任を持つ。

### 12.2 🟡 if文でViewを表示/非表示（Identity変更）

条件分岐でViewを切り替えると、Structural Identityが変わり状態がリセットされる。

```swift
// ❌ アンチパターン: if文で切り替え（Identityが変わる）
struct ProblematicView: View {
    @State private var isVisible = true
    
    var body: some View {
        VStack {
            if isVisible {
                // isVisibleがfalse→trueになると、TextFieldの入力内容がリセット
                InputView()
            }
            
            Toggle("表示", isOn: $isVisible)
        }
    }
}

struct InputView: View {
    @State private var text = ""  // 親のif文でIdentityが変わると消える
    
    var body: some View {
        TextField("入力", text: $text)
    }
}

// ✅ 解決策1: opacityで非表示（Identityを維持）
struct BetterView: View {
    @State private var isVisible = true
    
    var body: some View {
        VStack {
            InputView()
                .opacity(isVisible ? 1 : 0)  // 状態を維持したまま非表示
            
            Toggle("表示", isOn: $isVisible)
        }
    }
}

// ✅ 解決策2: hidden()モディファイアを使用
InputView()
    .hidden(!isVisible)  // iOS 17.5+、hidden(true)で非表示

// ✅ 解決策3: カスタムモディファイア
extension View {
    @ViewBuilder
    func visible(_ isVisible: Bool) -> some View {
        if isVisible {
            self
        } else {
            self.hidden()
        }
    }
}
```

**使い分け**:
| パターン | 状態 | 用途 |
|---------|------|------|
| `if` 文 | リセット | 状態リセットが望ましい場合 |
| `opacity(0)` | 維持 | フォーカス・入力状態を保持したい場合 |
| `hidden()` | 維持 | レイアウトスペースも維持したい場合 |

### 12.3 ユーザー入力の勝手な書き換え

TextFieldなどの入力コンポーネントで、ユーザーの入力値を親が勝手に変更するとUXが悪化。

```swift
// ❌ アンチパターン: 入力中に値を強制変更
struct BadInputView: View {
    @Binding var text: String
    
    var body: some View {
        TextField("金額", text: $text)
            .onChange(of: text) { _, newValue in
                // 入力中にフォーマットすると、カーソル位置がずれる
                text = formatCurrency(newValue)
            }
    }
}

// ✅ 解決策: フォーカスが外れたときにフォーマット
struct GoodInputView: View {
    @Binding var text: String
    @FocusState private var isFocused: Bool
    
    var body: some View {
        TextField("金額", text: $text)
            .focused($isFocused)
            .onChange(of: isFocused) { _, focused in
                if !focused {
                    // 編集完了時にのみフォーマット
                    text = formatCurrency(text)
                }
            }
    }
}
```

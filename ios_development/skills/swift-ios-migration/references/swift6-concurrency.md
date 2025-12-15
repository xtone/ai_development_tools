# Swift 6 並行処理対応ガイド

Swift 6では並行処理の安全性（Data Race Safety）がコンパイラによって厳密に保証される。SwiftUIアプリの設計に直接的な影響を与える。

## @MainActor によるUI保護

### ViewModelへの適用（推奨パターン）

```swift
// ✅ 推奨: ViewModel全体に@MainActorを付与
@MainActor
class ArticleListViewModel: ObservableObject {
    @Published var articles: [Article] = []
    @Published var isLoading = false
    @Published var error: Error?
    
    private let service: ArticleServiceProtocol
    
    init(service: ArticleServiceProtocol = ArticleService()) {
        self.service = service
    }
    
    func fetchArticles() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            // バックグラウンドで実行されるが、
            // 結果の代入は自動的にメインスレッドで行われる
            articles = try await service.fetch()
        } catch {
            self.error = error
        }
    }
}
```

**メリット**:
- プロパティ更新が自動的にメインスレッドで実行
- `DispatchQueue.main.async` が不要
- コンパイラが安全性を保証

### iOS 17+ @Observable での適用

```swift
@MainActor
@Observable
class ArticleListViewModel {
    var articles: [Article] = []
    var isLoading = false
    var error: Error?
    
    func fetchArticles() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            articles = try await service.fetch()
        } catch {
            self.error = error
        }
    }
}
```

### 部分的な@MainActor適用

特定のメソッドのみUIに関連する場合：

```swift
class DataProcessor {
    private var cache: [String: Data] = [:]
    
    // バックグラウンドで実行可能
    func processData(_ input: Data) async -> ProcessedData {
        // 重い処理
        await heavyComputation(input)
    }
    
    // UI更新を伴うメソッドのみ@MainActor
    @MainActor
    func updateUI(with result: ProcessedData) {
        // UI更新処理
    }
}
```

## Sendable プロトコル

### アクター境界を超えるデータ

```swift
// ✅ 値型（Struct）は自動的にSendable
struct Article: Sendable, Identifiable {
    let id: UUID
    let title: String
    let content: String
    let publishedAt: Date
}

// ✅ Enumも自動的にSendable
enum LoadingState: Sendable {
    case idle
    case loading
    case loaded([Article])
    case error(Error)  // ErrorはSendableではないので注意
}

// ⚠️ Errorを含む場合
enum LoadingState<T: Sendable>: Sendable {
    case idle
    case loading
    case loaded(T)
    case error(String)  // Errorの代わりにStringを使用
}
```

### クラスをSendableにする

```swift
// 方法1: finalクラス + 不変プロパティ
final class ImmutableConfig: Sendable {
    let apiKey: String
    let baseURL: URL
    
    init(apiKey: String, baseURL: URL) {
        self.apiKey = apiKey
        self.baseURL = baseURL
    }
}

// 方法2: @unchecked Sendable（手動で安全性を保証）
final class ThreadSafeCache: @unchecked Sendable {
    private let lock = NSLock()
    private var storage: [String: Data] = [:]
    
    func get(_ key: String) -> Data? {
        lock.lock()
        defer { lock.unlock() }
        return storage[key]
    }
    
    func set(_ key: String, value: Data) {
        lock.lock()
        defer { lock.unlock() }
        storage[key] = value
    }
}
```

**⚠️ `@unchecked Sendable` は慎重に使用**
- コンパイラのチェックを無効化
- 手動でスレッドセーフティを保証する責任

## 非同期タスクのパターン

### View内でのTask使用

```swift
struct ArticleListView: View {
    @StateObject private var viewModel = ArticleListViewModel()
    
    var body: some View {
        List(viewModel.articles) { article in
            ArticleRow(article: article)
        }
        .task {
            // ViewModelが@MainActorなら安全
            await viewModel.fetchArticles()
        }
        .refreshable {
            await viewModel.fetchArticles()
        }
    }
}
```

### 明示的なアクター切り替え

```swift
@MainActor
class ViewModel: ObservableObject {
    @Published var result: String = ""
    
    func process() async {
        // メインアクターから離脱してバックグラウンドで実行
        let processed = await Task.detached(priority: .userInitiated) {
            await self.heavyComputation()
        }.value
        
        // 自動的にメインアクターに戻る（ViewModelが@MainActorのため）
        result = processed
    }
    
    // nonisolatedでメインアクター外で実行可能に
    nonisolated func heavyComputation() async -> String {
        // CPU集約的な処理
        return "result"
    }
}
```

## Swift 6移行チェックリスト

### 1. Strict Concurrency Checkingを有効化

Build Settings → Swift Compiler - Upcoming Features → `Strict Concurrency Checking` を `Complete` に設定

### 2. ViewModel

- [ ] `@MainActor` を付与
- [ ] `@Published` プロパティの更新がメインスレッドで行われることを確認
- [ ] 非同期メソッドが適切に `async` マークされている

### 3. データモデル

- [ ] 値型（Struct/Enum）を優先使用
- [ ] `Sendable` 準拠を確認
- [ ] アクター境界を超えるデータの安全性確認

### 4. サービス/リポジトリ層

- [ ] API通信などは `async` 関数として実装
- [ ] 結果型は `Sendable` 準拠

### 5. 警告の解消

```swift
// ⚠️ 警告: Capture of 'self' with non-sendable type
Task {
    await self.doSomething()  // 警告
}

// ✅ 解決: @MainActorを付与するか、Sendable準拠
@MainActor
class ViewModel: ObservableObject {
    func start() {
        Task {
            await self.doSomething()  // OK
        }
    }
}
```

## よくある警告と解決策

### 1. "Non-sendable type captured"

```swift
// ❌ 警告
class MyClass {
    func process() {
        Task {
            print(self)  // Non-sendable type captured
        }
    }
}

// ✅ 解決策1: @MainActorを付与
@MainActor
class MyClass { ... }

// ✅ 解決策2: Sendable準拠
final class MyClass: Sendable { ... }

// ✅ 解決策3: 必要な値だけキャプチャ
class MyClass {
    let id: String
    
    func process() {
        let id = self.id  // Sendableな値をキャプチャ
        Task {
            print(id)
        }
    }
}
```

### 2. "Actor-isolated property cannot be mutated"

```swift
// ❌ エラー
class ViewModel: ObservableObject {
    @Published var data: String = ""
    
    func update() async {
        data = await fetchData()  // エラー: メインアクター外から更新
    }
}

// ✅ 解決: @MainActorを付与
@MainActor
class ViewModel: ObservableObject {
    @Published var data: String = ""
    
    func update() async {
        data = await fetchData()  // OK
    }
}
```

### 3. "Call to main actor-isolated method in a synchronous context"

```swift
// ❌ エラー
@MainActor
class ViewModel {
    func doUIWork() { }
}

func somewhere() {
    let vm = ViewModel()
    vm.doUIWork()  // エラー
}

// ✅ 解決: asyncコンテキストで呼び出し
func somewhere() async {
    let vm = await ViewModel()
    await vm.doUIWork()
}
```

## Actor の活用

### カスタムActorでスレッドセーフを保証

```swift
actor ImageCache {
    private var cache: [URL: UIImage] = [:]
    
    func image(for url: URL) -> UIImage? {
        cache[url]
    }
    
    func setImage(_ image: UIImage, for url: URL) {
        cache[url] = image
    }
    
    func clearCache() {
        cache.removeAll()
    }
}

// 使用
class ImageLoader {
    private let cache = ImageCache()
    
    func loadImage(from url: URL) async -> UIImage? {
        // actorのメソッドはawaitが必要
        if let cached = await cache.image(for: url) {
            return cached
        }
        
        guard let image = await downloadImage(from: url) else {
            return nil
        }
        
        await cache.setImage(image, for: url)
        return image
    }
}
```

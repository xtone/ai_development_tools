# Swift 6.2 / Xcode 26 移行ガイド

## 概要

Swift 6.2（Xcode 26同梱）では「Approachable Concurrency」が導入され、Swift 6の厳格な並行処理チェックをより使いやすくする機能が追加された。

---

## Approachable Concurrency

### 背景

Swift 6のStrict Concurrencyは安全だが、多くのボイラープレートと急な学習曲線が問題だった。Swift 6.2では以下のアプローチで解決：

1. **シングルスレッドコードから開始** - デフォルトでMainActorに分離
2. **必要に応じて並行処理を導入** - 明示的にオプトイン
3. **`@concurrent`で明示的にバックグラウンド実行**

---

## デフォルトアクター分離

### Build Settings設定

```
// Xcode 26 Build Settings
Swift Compiler - Upcoming Features:
  - Approachable Concurrency: Yes
  - Default Actor Isolation: MainActor
```

### 効果

```swift
// Swift 6.2 + Default Actor Isolation = MainActor

// @MainActorを明示的に書く必要がない
class ArticleViewModel: ObservableObject {
    @Published var articles: [Article] = []

    // 暗黙的に@MainActor
    func refresh() async {
        articles = await fetchArticles()
    }
}
```

### 従来のSwift 6との比較

```swift
// Swift 6: 明示的な@MainActorが必要
@MainActor
class ArticleViewModel: ObservableObject {
    @Published var articles: [Article] = []

    func refresh() async {
        articles = await fetchArticles()
    }
}

// Swift 6.2: Default Actor IsolationがMainActorなら省略可能
class ArticleViewModel: ObservableObject {
    @Published var articles: [Article] = []

    func refresh() async {
        articles = await fetchArticles()
    }
}
```

---

## @concurrent

バックグラウンドで実行したい関数に明示的にマーク。

### 基本的な使用法

```swift
// バックグラウンドで実行
@concurrent
func processData(_ data: Data) async -> ProcessedData {
    // 重い処理
    return heavyComputation(data)
}

// 呼び出し側
func updateUI() async {
    let result = await processData(rawData)
    // 結果はMainActorに自動的に戻る（Default Actor IsolationがMainActorの場合）
    displayResult(result)
}
```

### ユースケース

```swift
class ImageProcessor {
    // 画像処理はバックグラウンドで実行
    @concurrent
    func processImage(_ image: UIImage) async -> UIImage {
        // フィルター適用、リサイズなど
    }

    // UI更新はMainActorで（デフォルト）
    func applyFilter() async {
        let processed = await processImage(originalImage)
        self.displayedImage = processed  // MainActorで実行
    }
}
```

---

## 移行チェックリスト

### Swift 6 → Swift 6.2

1. [ ] Xcode 26にアップデート
2. [ ] Build SettingsでApproachable Concurrencyを有効化
3. [ ] Default Actor IsolationをMainActorに設定
4. [ ] 既存の`@MainActor`を確認（削除可能な場合あり）
5. [ ] バックグラウンド処理が必要な関数に`@concurrent`を追加
6. [ ] 既存のSwift 6コードをレビュー・簡略化

### 新規プロジェクト

1. [ ] Xcode 26で新規プロジェクト作成
2. [ ] Approachable Concurrencyがデフォルトで有効
3. [ ] 必要に応じて`@concurrent`を使用

---

## Xcode 26 新機能

### AI Coding Tools

- **ChatGPT統合**: Xcode内でChatGPTを直接使用
- **サードパーティLLM対応**: APIキーで他のLLMも利用可能
- **ローカルモデル実行**: オンデバイスでのAI処理
- **コード生成・バグ修正・ドキュメント生成**

### Playground強化

- **インラインPlayground**: 通常プロジェクト内にPlaygroundコードブロックを埋め込み
- **ライブインタラクション**: Previewのような即時フィードバック
- **APIテストとデモ作成に最適**

### パフォーマンス改善

- **プロジェクト読み込み40%高速化**
- **モジュラー設計**: 必要な部分のみダウンロード
- **Voice Control改善**: Swiftコードのディクテーション精度向上

---

## デバッグ改善

### LLDB強化

- 非同期関数内でスレッド切り替え後も実行継続
- コンパイルモジュールの再利用で評価高速化

### 並行処理デバッグ

- アクター境界を超えるデータフローの可視化
- デッドロック検出の改善

---

## その他のSwift 6.2新機能

### Subprocess パッケージ

スクリプティング用のプロセス実行API。

```swift
import Subprocess

let result = try await Subprocess.run(
    executing: .init(at: "/bin/ls"),
    arguments: ["-la"]
)
print(result.standardOutput)
```

### Swift Testing強化

- **カスタムアタッチメント**: テスト結果に追加データを添付
- **Exit tests**: 終了コードの検証

```swift
@Test
func testProcess() async throws {
    await #expect(exitsWith: .success) {
        // プロセス終了をテスト
    }
}
```

### 相互運用性の改善

- C/C++/Objective-C/Java相互運用の改善
- より多くの型の自動ブリッジング

---

## 互換性

### 対応環境

- Xcode 26以降
- iOS 26 / iPadOS 26 / macOS 26 / watchOS 26 / tvOS 26 / visionOS 26
- 下位バージョンへのデプロイも可能（ただし一部機能制限あり）

### 既存コードとの互換性

- Swift 6コードはそのまま動作
- Approachable Concurrencyは段階的に採用可能
- 既存の`@MainActor`は引き続き有効

---

## 関連ドキュメント

- [What's new in Swift - WWDC25](https://developer.apple.com/videos/play/wwdc2025/245)
- [Swift 6.2 Release Notes](https://swift.org/blog/)
- [Xcode 26 Release Notes](https://developer.apple.com/documentation/xcode-release-notes/)

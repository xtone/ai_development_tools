# プレビューコンポーネント

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | Xcode | 備考 |
|--------------|-----|--------|-------|-------|------|
| #Preview | 17+ | 17+ | 14+ | 15+ | 簡略化されたプレビューマクロ |
| @Previewable | 18+ | 18+ | 15+ | 16+ | プレビュー内で@State使用可能 |

---

## #Preview マクロ (iOS 17+)

従来の`PreviewProvider`プロトコルを置き換える簡略化されたプレビュー構文。

### 基本的な使用法

```swift
// iOS 16以前: PreviewProvider
struct ArticleView_Previews: PreviewProvider {
    static var previews: some View {
        ArticleView(article: .sample)
    }
}

// iOS 17+: #Previewマクロ
#Preview {
    ArticleView(article: .sample)
}
```

### 名前付きプレビュー

```swift
#Preview("通常状態") {
    ContentView(state: .normal)
}

#Preview("エラー状態") {
    ContentView(state: .error)
}

#Preview("ローディング状態") {
    ContentView(state: .loading)
}
```

### ダークモード

```swift
#Preview("ダークモード") {
    ArticleView(article: .sample)
        .preferredColorScheme(.dark)
}
```

### デバイス回転

```swift
#Preview(traits: .landscapeLeft) {
    ArticleView(article: .sample)
}

#Preview(traits: .portrait) {
    ArticleView(article: .sample)
}
```

### 固定サイズ

```swift
#Preview(traits: .fixedLayout(width: 300, height: 200)) {
    CardView(card: .sample)
}
```

### 複数のトレイト

```swift
#Preview(traits: .landscapeLeft, .sizeThatFitsLayout) {
    MyView()
}
```

---

## @Previewable (iOS 18+ / Xcode 16+)

プレビュー内で直接`@State`を使用可能に。ラッパーViewが不要。

### 基本的な使用法

```swift
// iOS 17以前: ラッパーViewが必要だった
struct TogglePreviewWrapper: View {
    @State private var isOn = false

    var body: some View {
        MyToggle(isOn: $isOn)
    }
}

#Preview {
    TogglePreviewWrapper()
}

// iOS 18 / Xcode 16: @Previewableで直接定義
#Preview {
    @Previewable @State var isOn = false
    MyToggle(isOn: $isOn)
}
```

### 複数の状態を持つプレビュー

```swift
#Preview("Form Preview") {
    @Previewable @State var name = ""
    @Previewable @State var email = ""
    @Previewable @State var isSubscribed = true

    Form {
        TextField("Name", text: $name)
        TextField("Email", text: $email)
        Toggle("Subscribe", isOn: $isSubscribed)
    }
}
```

### インタラクティブなプレビュー

```swift
#Preview("Counter") {
    @Previewable @State var count = 0

    VStack(spacing: 20) {
        Text("Count: \(count)")
            .font(.largeTitle)

        HStack {
            Button("-") { count -= 1 }
            Button("+") { count += 1 }
        }
        .buttonStyle(.borderedProminent)
    }
}
```

### 環境値との組み合わせ

```swift
#Preview("Dark Mode") {
    @Previewable @State var text = ""

    TextField("Input", text: $text)
        .preferredColorScheme(.dark)
}

#Preview("Large Text") {
    @Previewable @State var isOn = false

    Toggle("Option", isOn: $isOn)
        .environment(\.sizeCategory, .accessibilityExtraLarge)
}
```

### スライダー付きプレビュー

```swift
#Preview("Adjustable") {
    @Previewable @State var progress: Double = 0.5

    VStack {
        ProgressView(value: progress)
        Slider(value: $progress)
    }
    .padding()
}
```

---

## プレビューのベストプラクティス

### サンプルデータの用意

```swift
extension Article {
    static var sample: Article {
        Article(
            id: UUID(),
            title: "サンプル記事",
            content: "これはプレビュー用のサンプルコンテンツです。"
        )
    }
}

#Preview {
    ArticleView(article: .sample)
}
```

### 複数状態のプレビュー

```swift
#Preview("Empty") {
    ListView(items: [])
}

#Preview("Few Items") {
    ListView(items: Array(repeating: .sample, count: 3))
}

#Preview("Many Items") {
    ListView(items: Array(repeating: .sample, count: 50))
}
```

### 環境設定のバリエーション

```swift
#Preview("Default") {
    MyView()
}

#Preview("Dark Mode") {
    MyView()
        .preferredColorScheme(.dark)
}

#Preview("RTL") {
    MyView()
        .environment(\.layoutDirection, .rightToLeft)
}

#Preview("Large Dynamic Type") {
    MyView()
        .environment(\.sizeCategory, .accessibilityLarge)
}
```

---

## 関連ドキュメント

- [Preview - Apple Developer](https://developer.apple.com/documentation/swiftui/preview())
- [Previewable - Apple Developer](https://developer.apple.com/documentation/swiftui/previewable)

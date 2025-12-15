# スクロールコンポーネント

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | 備考 |
|--------------|-----|--------|-------|------|
| scrollPosition | 17+ | 17+ | 14+ | スクロール位置の取得・設定 |
| scrollTargetBehavior | 17+ | 17+ | 14+ | スナップスクロール |
| scrollTargetLayout | 17+ | 17+ | 14+ | スクロールターゲットレイアウト |
| containerRelativeFrame | 17+ | 17+ | 14+ | 親コンテナ相対サイズ |
| scrollIndicators | 16+ | 16+ | 13+ | スクロールインジケータ制御 |
| scrollClipDisabled | 17+ | 17+ | 14+ | クリッピング無効化 |
| safeAreaPadding | 17+ | 17+ | 14+ | 安全領域余白 |

---

## scrollPosition (iOS 17+)

スクロール位置の取得と設定を可能にする。

### 基本的な使用法

```swift
struct ArticleList: View {
    @State private var scrollPosition: Int?
    let articles: [Article]

    var body: some View {
        ScrollView {
            LazyVStack {
                ForEach(articles) { article in
                    ArticleRow(article: article)
                        .id(article.id)
                }
            }
            .scrollTargetLayout()
        }
        .scrollPosition(id: $scrollPosition)

        // 特定の位置にスクロール
        Button("先頭へ") {
            withAnimation {
                scrollPosition = articles.first?.id
            }
        }
    }
}
```

### String IDでの使用

```swift
struct ScrollableList: View {
    @State private var scrollPosition: String?
    let items = (1...100).map { "Item \($0)" }

    var body: some View {
        VStack {
            // 現在位置の表示
            Text("Current: \(scrollPosition ?? "none")")

            ScrollView {
                LazyVStack {
                    ForEach(items, id: \.self) { item in
                        Text(item)
                            .frame(height: 50)
                    }
                }
                .scrollTargetLayout()
            }
            .scrollPosition(id: $scrollPosition)

            // プログラムでスクロール
            Button("Go to Item 50") {
                withAnimation {
                    scrollPosition = "Item 50"
                }
            }
        }
    }
}
```

---

## scrollTargetBehavior (iOS 17+)

スクロールのスナップ動作を制御。

### ビュー単位のスナップ

```swift
ScrollView(.horizontal) {
    LazyHStack(spacing: 16) {
        ForEach(cards) { card in
            CardView(card: card)
                .containerRelativeFrame(.horizontal)
        }
    }
    .scrollTargetLayout()
}
.scrollTargetBehavior(.viewAligned) // ビュー単位でスナップ
```

### ページング

```swift
ScrollView(.horizontal) {
    LazyHStack(spacing: 0) {
        ForEach(pages) { page in
            PageView(page: page)
                .containerRelativeFrame(.horizontal)
        }
    }
    .scrollTargetLayout()
}
.scrollTargetBehavior(.paging) // ページング動作
```

---

## containerRelativeFrame (iOS 17+)

親コンテナに対する相対的なサイズ指定。

### 基本的な使用法

```swift
ScrollView(.horizontal) {
    LazyHStack {
        ForEach(items) { item in
            ItemView(item: item)
                .containerRelativeFrame(.horizontal, count: 3, spacing: 8)
                // 画面幅を3分割したサイズ
        }
    }
}
```

### カード表示例

```swift
ScrollView(.horizontal) {
    LazyHStack(spacing: 16) {
        ForEach(cards) { card in
            CardView(card: card)
                .containerRelativeFrame(.horizontal) { width, _ in
                    width * 0.85  // 画面幅の85%
                }
        }
    }
    .scrollTargetLayout()
}
.scrollTargetBehavior(.viewAligned)
.contentMargins(.horizontal, 16, for: .scrollContent)
```

---

## scrollIndicators (iOS 16+)

スクロールインジケータの表示制御。

```swift
ScrollView {
    content
}
.scrollIndicators(.hidden) // スクロールインジケータを非表示

.scrollIndicators(.visible, axes: .vertical) // 垂直のみ表示

.scrollIndicators(.automatic) // 自動（デフォルト）
```

---

## scrollClipDisabled (iOS 17+)

スクロールビューのクリッピングを無効化。シャドウやオーバーフロー要素を表示可能に。

```swift
ScrollView(.horizontal) {
    LazyHStack {
        ForEach(cards) { card in
            CardView(card: card)
                .shadow(radius: 10) // シャドウがクリップされない
        }
    }
    .padding(.vertical, 20)
}
.scrollClipDisabled()
```

---

## safeAreaPadding (iOS 17+)

安全領域に余白を追加。フローティングUIの配置に便利。

```swift
ScrollView {
    content
}
.safeAreaPadding(.bottom, 80) // 下部にフローティングボタン用のスペース

// 全方向
.safeAreaPadding(20)

// 特定の辺
.safeAreaPadding(.horizontal, 16)
```

---

## 後方互換性

iOS 16以前をサポートする場合：

```swift
var body: some View {
    if #available(iOS 17.0, *) {
        content
            .scrollPosition(id: $position)
    } else {
        ScrollViewReader { proxy in
            content
                .onChange(of: targetId) { id in
                    proxy.scrollTo(id)
                }
        }
    }
}
```

---

## 関連ドキュメント

- [ScrollPosition - Apple Developer](https://developer.apple.com/documentation/swiftui/scrollposition)
- [scrollTargetBehavior - Apple Developer](https://developer.apple.com/documentation/swiftui/view/scrolltargetbehavior(_:))
- [containerRelativeFrame - Apple Developer](https://developer.apple.com/documentation/swiftui/view/containerrelativeframe(_:count:span:spacing:alignment:))

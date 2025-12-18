# コンテナ値・トランザクション

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | 備考 |
|--------------|-----|--------|-------|------|
| ContainerValues | 18+ | 18+ | 15+ | 子→親への値伝達 |
| @Entry | 18+ | 18+ | 15+ | ContainerValue定義マクロ |
| Transaction | 18+ | 18+ | 15+ | アニメーション制御強化 |

---

## ContainerValues (iOS 18+)

子Viewから親コンテナに構成情報を伝える新しい仕組み。Preference Keyより直感的で型安全。

### 基本的な使い方

```swift
// 1. ContainerValueを定義
extension ContainerValues {
    @Entry var columnSpan: Int = 1
}

// 2. 子Viewで値を設定
struct WideCard: View {
    var body: some View {
        CardContent()
            .containerValue(\.columnSpan, 2)  // 2列分を占有
    }
}

// 3. 親コンテナで値を読み取り
struct CustomGrid: View {
    var body: some View {
        Grid {
            ForEach(subviewOf: self) { subview in
                let span = subview.containerValues.columnSpan
                GridRow {
                    subview
                        .gridCellColumns(span)
                }
            }
        }
    }
}
```

### カスタムコンテナでの活用

```swift
// カスタム値の定義
extension ContainerValues {
    @Entry var priority: Priority = .normal
    @Entry var isHighlighted: Bool = false
}

enum Priority: Int, Comparable {
    case low, normal, high
    static func < (lhs: Priority, rhs: Priority) -> Bool {
        lhs.rawValue < rhs.rawValue
    }
}

// 子Viewで設定
Text("重要なメッセージ")
    .containerValue(\.priority, .high)
    .containerValue(\.isHighlighted, true)

// 親コンテナで読み取り・ソート
struct PriorityList: View {
    @ViewBuilder var content: some View

    var body: some View {
        VStack {
            ForEach(subviewOf: content) { subview in
                let priority = subview.containerValues.priority
                let highlighted = subview.containerValues.isHighlighted

                subview
                    .background(highlighted ? Color.yellow.opacity(0.3) : Color.clear)
            }
        }
    }
}
```

### Preference Key との比較

| 特徴 | ContainerValues | PreferenceKey |
|------|-----------------|---------------|
| 方向 | 子 → 直接の親コンテナ | 子 → 祖先全体 |
| 型安全 | @Entryマクロで簡潔 | 手動でプロトコル準拠 |
| 用途 | レイアウト情報、構成 | 集約値（サイズ、アンカーなど） |
| iOS | 18+ | 13+ |

---

## Transaction (iOS 18+)

アニメーションのコンテキスト自体を操作。親から伝播するアニメーションの無効化や上書きが可能。

### 基本的なTransaction

```swift
struct ContentView: View {
    @State private var isExpanded = false

    var body: some View {
        VStack {
            Button("Toggle") {
                // withAnimationの代わりにTransaction
                var transaction = Transaction(animation: .spring(response: 0.3))
                transaction.disablesAnimations = false

                withTransaction(transaction) {
                    isExpanded.toggle()
                }
            }

            Rectangle()
                .frame(width: isExpanded ? 200 : 100)
        }
    }
}
```

### アニメーションの無効化

親から伝播してきたアニメーションを子で無効化。

```swift
struct ChildView: View {
    let value: Double

    var body: some View {
        Text("\(value, specifier: "%.1f")")
            .transaction { transaction in
                // 親からのアニメーションを無効化
                transaction.disablesAnimations = true
            }
    }
}

// 親View
struct ParentView: View {
    @State private var value = 0.0

    var body: some View {
        VStack {
            // このアニメーションはChildViewには適用されない
            Slider(value: $value)
                .animation(.easeInOut, value: value)

            ChildView(value: value)
        }
    }
}
```

### アニメーションの上書き

```swift
struct ContentView: View {
    @State private var isOn = false

    var body: some View {
        VStack {
            Toggle("Toggle", isOn: $isOn)

            Circle()
                .frame(width: isOn ? 100 : 50)
                .transaction { transaction in
                    // 親のアニメーションを上書き
                    transaction.animation = .bouncy(duration: 0.5)
                }
        }
        .animation(.linear, value: isOn)  // このアニメーションは上書きされる
    }
}
```

### 条件付きアニメーション

```swift
struct SmartAnimationView: View {
    @State private var count = 0
    @Environment(\.accessibilityReduceMotion) var reduceMotion

    var body: some View {
        Text("\(count)")
            .font(.largeTitle)
            .transaction { transaction in
                if reduceMotion {
                    transaction.disablesAnimations = true
                } else {
                    transaction.animation = .spring(response: 0.3)
                }
            }

        Button("Increment") {
            count += 1
        }
    }
}
```

### 特定のビューのみアニメーション

```swift
struct SelectiveAnimationView: View {
    @State private var isExpanded = false

    var body: some View {
        VStack {
            // このビューはアニメーションする
            Rectangle()
                .frame(height: isExpanded ? 200 : 100)
                .animation(.spring, value: isExpanded)

            // このビューはアニメーションしない
            Text("Status: \(isExpanded ? "Expanded" : "Collapsed")")
                .transaction { $0.disablesAnimations = true }

            Button("Toggle") {
                isExpanded.toggle()
            }
        }
    }
}
```

---

## 関連ドキュメント

- [ContainerValues - Apple Developer](https://developer.apple.com/documentation/swiftui/containervalues)
- [Transaction - Apple Developer](https://developer.apple.com/documentation/swiftui/transaction)

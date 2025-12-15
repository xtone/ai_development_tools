# レイアウトコンポーネント

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | 備考 |
|--------------|-----|--------|-------|------|
| Grid | 16+ | 16+ | 13+ | 柔軟なグリッドレイアウト |
| GridRow | 16+ | 16+ | 13+ | グリッド行 |
| ViewThatFits | 16+ | 16+ | 13+ | 自動ビュー選択 |
| AnyLayout | 16+ | 16+ | 13+ | 動的レイアウト切り替え |
| Gauge | 16+ | 16+ | 13+ | 進捗・レベル表示 |
| Table | 16+ | 16+ | 12+ | 表形式データ（主にmacOS/iPadOS） |
| TextField(axis:) | 16+ | 16+ | 13+ | 複数行テキストフィールド |
| ToolbarSpacer | 26+ | 26+ | 26+ | ツールバースペース制御 |
| labelIconToTitleSpacing | 26+ | 26+ | 26+ | Labelスペース調整 |

---

## Grid (iOS 16+)

より柔軟なグリッドレイアウト。LazyVGrid/LazyHGridと異なり、すべてのセルが一度にレンダリングされる。

### 基本的な使用法

```swift
Grid {
    GridRow {
        Text("1")
        Text("2")
        Text("3")
    }
    GridRow {
        Text("4")
        Text("5")
        Text("6")
    }
}
```

### 複数列にまたがるセル

```swift
Grid {
    GridRow {
        Text("1")
        Text("2")
        Text("3")
    }
    GridRow {
        Text("4")
        Text("5")
            .gridCellColumns(2) // 2列分を占有
    }
    Divider()
        .gridCellUnsizedAxes(.horizontal)
    GridRow {
        Text("7")
        Text("8")
        Text("9")
    }
}
```

### アライメント

```swift
Grid(alignment: .leading, horizontalSpacing: 10, verticalSpacing: 10) {
    GridRow {
        Text("Name:")
            .gridColumnAlignment(.trailing)
        Text("John Doe")
    }
    GridRow {
        Text("Email:")
        Text("john@example.com")
    }
}
```

---

## ViewThatFits (iOS 16+)

利用可能なスペースに応じてビューを自動選択。

### 基本的な使用法

```swift
ViewThatFits {
    // 優先度順に試行
    HStack {
        Image(systemName: "star")
        Text("お気に入りに追加")
    }

    // スペースが足りない場合
    HStack {
        Image(systemName: "star")
        Text("追加")
    }

    // さらにスペースが足りない場合
    Image(systemName: "star")
}
```

### 軸を指定

```swift
ViewThatFits(in: .horizontal) {
    // 水平方向のスペースのみをチェック
    WideView()
    NarrowView()
}
```

---

## AnyLayout (iOS 16+)

条件に応じてレイアウトを動的に切り替え。

### 基本的な使用法

```swift
struct AdaptiveView: View {
    @Environment(\.horizontalSizeClass) var sizeClass

    var layout: AnyLayout {
        sizeClass == .compact
            ? AnyLayout(VStackLayout())
            : AnyLayout(HStackLayout())
    }

    var body: some View {
        layout {
            Image(systemName: "photo")
            Text("タイトル")
            Text("説明文")
        }
    }
}
```

### アニメーション付きレイアウト変更

```swift
struct AnimatedLayoutView: View {
    @State private var isGrid = false

    var layout: AnyLayout {
        isGrid
            ? AnyLayout(GridLayout())
            : AnyLayout(VStackLayout(spacing: 10))
    }

    var body: some View {
        layout {
            ForEach(items) { item in
                ItemView(item: item)
            }
        }
        .animation(.spring(), value: isGrid)

        Toggle("Grid View", isOn: $isGrid)
    }
}
```

---

## Gauge (iOS 16+)

進捗やレベルを視覚的に表示。

### 基本的なゲージ

```swift
Gauge(value: 0.7) {
    Text("進捗")
}
```

### 範囲とラベル付き

```swift
Gauge(value: 75, in: 0...100) {
    Text("バッテリー")
} currentValueLabel: {
    Text("75%")
} minimumValueLabel: {
    Text("0")
} maximumValueLabel: {
    Text("100")
}
```

### スタイル

```swift
// 線形
Gauge(value: 0.5) {
    Text("レベル")
}
.gaugeStyle(.linearCapacity)

// 円形アクセサリ
Gauge(value: 0.5) {
    Text("レベル")
}
.gaugeStyle(.accessoryCircular)

// その他のスタイル
// .accessoryLinear
// .accessoryCircularCapacity
```

### カスタムゲージ

```swift
Gauge(value: progress) {
    Image(systemName: "heart.fill")
} currentValueLabel: {
    Text("\(Int(progress * 100))%")
}
.tint(Gradient(colors: [.green, .yellow, .red]))
```

---

## Table (iOS 16+)

表形式のデータ表示。主にmacOSとiPadOS向け。

### 基本的な使用法

```swift
struct Person: Identifiable {
    let id = UUID()
    var name: String
    var age: Int
    var email: String
}

struct PeopleTable: View {
    @State private var people: [Person] = [...]
    @State private var selection: Set<Person.ID> = []
    @State private var sortOrder = [KeyPathComparator(\Person.name)]

    var body: some View {
        Table(people, selection: $selection, sortOrder: $sortOrder) {
            TableColumn("名前", value: \.name)
            TableColumn("年齢") { person in
                Text("\(person.age)")
            }
            TableColumn("メール", value: \.email)
        }
        .onChange(of: sortOrder) { newOrder in
            people.sort(using: newOrder)
        }
    }
}
```

---

## TextField改善 (iOS 16+)

### 軸方向の拡張

```swift
TextField("メッセージ", text: $message, axis: .vertical)
    .lineLimit(3...6) // 3〜6行で自動拡張
```

### フォーカス制御の強化

```swift
enum Field: Hashable {
    case username, password
}

struct LoginForm: View {
    @State private var username = ""
    @State private var password = ""
    @FocusState private var focusedField: Field?

    var body: some View {
        Form {
            TextField("ユーザー名", text: $username)
                .focused($focusedField, equals: .username)
                .submitLabel(.next)
                .onSubmit {
                    focusedField = .password
                }

            SecureField("パスワード", text: $password)
                .focused($focusedField, equals: .password)
                .submitLabel(.done)
        }
    }
}
```

### defaultFocus (iOS 17+)

```swift
struct FormView: View {
    @State private var email = ""
    @State private var password = ""
    @FocusState private var focusedField: Field?

    var body: some View {
        Form {
            TextField("メール", text: $email)
                .focused($focusedField, equals: .email)
            SecureField("パスワード", text: $password)
                .focused($focusedField, equals: .password)
        }
        .defaultFocus($focusedField, .email) // 初期フォーカス
    }
}
```

---

## ToolbarSpacer (iOS 26+)

ツールバーアイテム間のスペース制御。

```swift
struct ContentView: View {
    var body: some View {
        NavigationStack {
            Content()
                .toolbar {
                    ToolbarItemGroup(placement: .primaryAction) {
                        Button("Action 1") { }
                        ToolbarSpacer()
                        Button("Action 2") { }
                    }
                }
        }
    }
}
```

---

## labelIconToTitleSpacing (iOS 26+)

Labelのアイコンとテキスト間のスペース調整。

```swift
Label("Hello", systemImage: "globe")
    .labelIconToTitleSpacing(8)

Label("Settings", systemImage: "gear")
    .labelIconToTitleSpacing(12)
```

---

## 関連ドキュメント

- [Grid - Apple Developer](https://developer.apple.com/documentation/swiftui/grid)
- [ViewThatFits - Apple Developer](https://developer.apple.com/documentation/swiftui/viewthatfits)
- [AnyLayout - Apple Developer](https://developer.apple.com/documentation/swiftui/anylayout)
- [Gauge - Apple Developer](https://developer.apple.com/documentation/swiftui/gauge)
- [Table - Apple Developer](https://developer.apple.com/documentation/swiftui/table)

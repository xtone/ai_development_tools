# SwiftUI Single Source of Truth (SSOT) ガイド

## SSOTとは

Single Source of Truth（単一の信頼できる情報源）は、各データが唯一の場所でのみ管理されるべきという原則。SwiftUIでは状態の重複を避け、データの一貫性を保つために不可欠。

**SSOTの3つの柱**
1. **唯一の所有者**: 各状態は1つのビュー/オブジェクトのみが所有
2. **参照で共有**: 複数ビューで必要な場合は`@Binding`や`@ObservedObject`で参照
3. **導出は計算**: 他の状態から計算できる値は`@State`で持たない

---

## Property Wrapperの選択フローチャート

```
状態を保存する必要がある？
├─ ビューローカル（他のビューは不要）？
│  └─ @State（必ずprivate）
├─ 親が所有し、子が書き込み必要？
│  └─ @Binding
├─ 複雑な共有状態（参照型）？
│  ├─ このビューで作成？
│  │  └─ @StateObject
│  └─ 親から受け取る？
│     └─ @ObservedObject
└─ 深い階層で共有？
   └─ @EnvironmentObject
```

### 所有権の原則

| ラッパー | 所有権 | 用途 |
|---------|--------|------|
| `@State` | 所有 | 値型のローカル状態 |
| `@StateObject` | 所有 | 参照型の作成・所有 |
| `@Binding` | 非所有 | 親の状態への参照 |
| `@ObservedObject` | 非所有 | 参照型を受け取る |
| `@EnvironmentObject` | 非所有 | 深い階層での共有 |

---

## パターン別ガイド

### パターン1: 状態の重複（❌ 最も多いSSO違反）

```swift
// ❌ アンチパターン: 状態の重複
struct ParentView: View {
    @State private var username = ""
    
    var body: some View {
        ChildView(initialUsername: username)
    }
}

struct ChildView: View {
    @State private var username: String  // 重複！
    
    init(initialUsername: String) {
        _username = State(initialValue: initialUsername)
    }
    
    var body: some View {
        TextField("Username", text: $username)
    }
}
// 問題: 子の変更が親に反映されない

// ✅ 解決策: Bindingで参照
struct ParentView: View {
    @State private var username = ""  // 唯一の情報源
    
    var body: some View {
        ChildView(username: $username)  // Bindingで渡す
    }
}

struct ChildView: View {
    @Binding var username: String  // 親の状態への参照
    
    var body: some View {
        TextField("Username", text: $username)
    }
}
```

### パターン2: 導出可能な状態の保持

```swift
// ❌ アンチパターン: 計算可能な値を保持
struct CartView: View {
    @State private var items: [CartItem] = []
    @State private var totalCount = 0      // items.countで計算可能
    @State private var totalPrice = 0.0    // 合計で計算可能
    @State private var isEmpty = true      // items.isEmptyで計算可能
    
    var body: some View {
        // ...
    }
    .onChange(of: items) { _, newItems in
        // 手動同期が必要（バグの温床）
        totalCount = newItems.count
        totalPrice = newItems.reduce(0) { $0 + $1.price }
        isEmpty = newItems.isEmpty
    }
}

// ✅ 解決策: 計算プロパティを使用
struct CartView: View {
    @State private var items: [CartItem] = []  // 唯一の状態
    
    // 導出値は計算プロパティ
    private var totalCount: Int { items.count }
    private var totalPrice: Double { items.reduce(0) { $0 + $1.price } }
    private var isEmpty: Bool { items.isEmpty }
    
    var body: some View {
        // 常に一貫性が保たれる
    }
}
```

### パターン3: 不適切な状態所有（State Lifting）

```swift
// ❌ アンチパターン: 子が共有状態を所有
struct ParentView: View {
    var body: some View {
        VStack {
            CounterView()
            // 子のcounterにアクセスできない！
            Button("リセット") {
                // どうやってリセットする？
            }
        }
    }
}

struct CounterView: View {
    @State private var counter = 0  // 親がアクセス不可
    
    var body: some View {
        Button("\(counter)") { counter += 1 }
    }
}

// ✅ 解決策: 状態を共通の親に引き上げ（State Lifting）
struct ParentView: View {
    @State private var counter = 0  // 親が所有
    
    var body: some View {
        VStack {
            CounterView(counter: $counter)
            Button("リセット") {
                counter = 0  // 親がコントロール可能
            }
        }
    }
}

struct CounterView: View {
    @Binding var counter: Int
    
    var body: some View {
        Button("\(counter)") { counter += 1 }
    }
}
```

### パターン4: 兄弟ビュー間の通信

```swift
// ❌ アンチパターン: 各ビューが独自に状態を持つ
struct MasterDetailView: View {
    var body: some View {
        HStack {
            ItemListView()   // 独自の@State selectedItem
            ItemDetailView() // どうやって選択を知る？
        }
    }
}

// ✅ 解決策: 共通の親で状態管理
struct MasterDetailView: View {
    @State private var selectedItem: Item?  // 共通の親で管理
    
    var body: some View {
        HStack {
            ItemListView(selectedItem: $selectedItem)
            ItemDetailView(item: selectedItem)  // 読み取り専用
        }
    }
}

struct ItemListView: View {
    @Binding var selectedItem: Item?  // 書き込み可能
    let items: [Item]
    
    var body: some View {
        List(items) { item in
            Button(item.name) {
                selectedItem = item
            }
        }
    }
}

struct ItemDetailView: View {
    let item: Item?  // 読み取り専用（変更不要）
    
    var body: some View {
        if let item = item {
            Text(item.description)
        }
    }
}
```

### パターン5: 深い階層での共有（EnvironmentObject）

```swift
// ❌ アンチパターン: プロップドリリング
struct RootView: View {
    @StateObject private var userSettings = UserSettings()
    
    var body: some View {
        Level1View(settings: userSettings)  // 渡す
    }
}

struct Level1View: View {
    @ObservedObject var settings: UserSettings
    var body: some View {
        Level2View(settings: settings)  // また渡す
    }
}

struct Level2View: View {
    @ObservedObject var settings: UserSettings
    var body: some View {
        Level3View(settings: settings)  // また渡す...
    }
}
// 問題: 中間ビューが不要な依存を持つ

// ✅ 解決策: EnvironmentObjectで注入
struct RootView: View {
    @StateObject private var userSettings = UserSettings()
    
    var body: some View {
        Level1View()
            .environmentObject(userSettings)  // 1回だけ注入
    }
}

struct Level1View: View {
    var body: some View {
        Level2View()  // settingsを渡す必要なし
    }
}

struct Level3View: View {
    @EnvironmentObject var settings: UserSettings  // 必要な場所で取得
    
    var body: some View {
        Toggle("Dark Mode", isOn: $settings.isDarkMode)
    }
}
```

---

## SSOT違反の検出方法

### コードスメル（警告サイン）

**1. イニシャライザでの@State設定**
```swift
// ❌ 警告: _プロパティ構文
init(value: String) {
    _localValue = State(initialValue: value)
}
```

**2. onChange での状態同期**
```swift
// ❌ 警告: 手動同期
.onChange(of: sourceValue) { _, newValue in
    targetValue = newValue  // 同期コード
}
```

**3. 似た名前の@Stateが複数ビューに存在**
```swift
// ❌ 警告: 同じ名前の状態
struct ViewA: View { @State private var username = "" }
struct ViewB: View { @State private var username = "" }  // 重複？
```

**4. .constant() の使用**
```swift
// ❌ 警告: Bindingのワークアラウンド
Toggle("Option", isOn: .constant(true))  // 本来は@Binding
```

### 検索パターン

レビュー時に以下を検索:
- `_.*= State(initialValue:` - イニシャライザでの@State設定
- `.onChange.*=` - 状態同期の可能性
- `@State private var` - 重複の可能性を確認

---

## iOS 17+ @Observable での SSOT

```swift
// iOS 17+: より簡潔なSSO実装
@Observable
class AppState {
    var user: User?
    var settings: Settings = Settings()
    
    // 導出プロパティもそのまま使用可能
    var isLoggedIn: Bool { user != nil }
}

struct RootView: View {
    @State private var appState = AppState()  // @Stateで所有
    
    var body: some View {
        ContentView(appState: appState)
            .environment(appState)  // 深い階層用
    }
}

struct ContentView: View {
    var appState: AppState  // ラッパー不要
    
    var body: some View {
        // appState.userが変更された時のみ再描画
        if appState.isLoggedIn {
            MainView()
        } else {
            LoginView()
        }
    }
}

struct SettingsView: View {
    @Environment(AppState.self) var appState
    
    var body: some View {
        @Bindable var appState = appState  // 書き込み用
        Toggle("Notifications", isOn: $appState.settings.notificationsEnabled)
    }
}
```

---

## レビューチェックリスト

### 🔴 必須（Critical）

- [ ] @Stateが複数ビューで重複していないか
- [ ] イニシャライザで@Stateを外部値から設定していないか
- [ ] onChangeで状態同期をしていないか
- [ ] 子が所有すべきでない共有状態を@Stateで持っていないか
- [ ] @Bindingが必要な場所で値渡しになっていないか

### 🟡 推奨（Important）

- [ ] 計算可能な値を@Stateで保持していないか
- [ ] @StateObjectが作成ビューで使われているか
- [ ] @ObservedObjectが受け取りビューで使われているか
- [ ] 深い階層でプロップドリリングになっていないか

### 🟢 提案（Optional）

- [ ] 状態が適切なレベルで所有されているか
- [ ] UI状態とビジネスロジック状態が分離されているか
- [ ] 状態の粒度は適切か（更新範囲の最小化）

---

## 修正例テンプレート

```markdown
## SSOT違反: [場所]

**問題**: [何が問題か]

**現在のコード**:
```swift
// 問題のあるコード
```

**修正後**:
```swift
// 修正されたコード
```

**理由**: [なぜこれがSSOT違反で、修正により何が改善されるか]
```

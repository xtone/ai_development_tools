# TipKit

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | 備考 |
|--------------|-----|--------|-------|------|
| TipKit | 17+ | 17+ | 14+ | 機能発見ヒント表示 |
| TipView | 17+ | 17+ | 14+ | インラインTip表示 |
| popoverTip | 17+ | 17+ | 14+ | ポップオーバーTip表示 |
| Tip Rules | 17+ | 17+ | 14+ | 表示条件制御 |

---

## 概要

TipKitは、アプリの機能発見を促進するヒント表示フレームワーク。ユーザーに機能を教えるための統一されたUIを提供。

---

## 基本的なTip定義

```swift
import TipKit

struct FavoriteTip: Tip {
    var title: Text {
        Text("お気に入りに追加")
    }

    var message: Text? {
        Text("星をタップして記事をお気に入りに保存できます")
    }

    var image: Image? {
        Image(systemName: "star")
    }
}
```

---

## Tipの表示

### インラインTip（TipView）

```swift
struct ArticleView: View {
    let favoriteTip = FavoriteTip()

    var body: some View {
        VStack {
            TipView(favoriteTip)

            // コンテンツ
            ArticleContent()
        }
    }
}
```

### ポップオーバーTip

```swift
struct ArticleView: View {
    let favoriteTip = FavoriteTip()

    var body: some View {
        Button(action: addToFavorites) {
            Image(systemName: "star")
        }
        .popoverTip(favoriteTip)
    }
}
```

---

## TipKitの設定

アプリ起動時に設定が必要。

```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .task {
                    try? Tips.configure([
                        .displayFrequency(.immediate),
                        .datastoreLocation(.applicationDefault)
                    ])
                }
        }
    }
}
```

### 表示頻度オプション

```swift
// 即時表示
.displayFrequency(.immediate)

// 1時間ごと
.displayFrequency(.hourly)

// 1日ごと
.displayFrequency(.daily)

// 1週間ごと
.displayFrequency(.weekly)

// 1ヶ月ごと
.displayFrequency(.monthly)
```

---

## Tipのルールと条件

### イベントベースのルール

ユーザーのアクション回数に基づいて表示。

```swift
struct AdvancedTip: Tip {
    // イベント定義
    static let articleViewedEvent = Event(id: "articleViewed")

    var rules: [Rule] {
        // 3回以上記事を見た後に表示
        #Rule(Self.articleViewedEvent) { $0.donations.count >= 3 }
    }

    var title: Text {
        Text("もっと便利に")
    }
}

// イベントの発火
Button("記事を見る") {
    AdvancedTip.articleViewedEvent.donate()
}
```

### パラメータベースのルール

アプリの状態に基づいて表示。

```swift
struct LoginRequiredTip: Tip {
    @Parameter
    static var isLoggedIn: Bool = false

    var rules: [Rule] {
        #Rule(Self.$isLoggedIn) { $0 == true }
    }

    var title: Text {
        Text("プレミアム機能")
    }
}

// パラメータの更新
func onLogin() {
    LoginRequiredTip.isLoggedIn = true
}
```

### 複合ルール

```swift
struct ComplexTip: Tip {
    static let usageEvent = Event(id: "usage")

    @Parameter
    static var isPremiumUser: Bool = false

    var rules: [Rule] {
        #Rule(Self.usageEvent) { $0.donations.count >= 5 }
        #Rule(Self.$isPremiumUser) { $0 == true }
    }

    var title: Text {
        Text("上級者向け機能")
    }
}
```

---

## Tipの無効化

### 手動で無効化

```swift
let favoriteTip = FavoriteTip()

// ユーザーがアクションを実行した時
func addToFavorites() {
    // 処理
    favoriteTip.invalidate(reason: .actionPerformed)
}
```

### 無効化理由

```swift
// ユーザーがアクションを実行
.actionPerformed

// ユーザーがTipを閉じた
.tipClosed

// 最大表示回数に達した
.maxDisplayCountExceeded
```

### データストアのリセット（開発用）

```swift
// 全てのTipをリセット
try? Tips.resetDatastore()
```

---

## カスタマイズ

### TipViewのスタイル

```swift
TipView(favoriteTip, arrowEdge: .top)

TipView(favoriteTip)
    .tipBackground(Color.blue.opacity(0.1))
```

### アクション付きTip

```swift
struct ActionTip: Tip {
    var title: Text {
        Text("新機能")
    }

    var message: Text? {
        Text("この機能を試してみませんか？")
    }

    var actions: [Action] {
        Action(id: "try", title: "試してみる")
        Action(id: "later", title: "後で")
    }
}

// アクションの処理
TipView(actionTip) { action in
    if action.id == "try" {
        // 機能を実行
    }
    actionTip.invalidate(reason: .actionPerformed)
}
```

---

## 移行チェックリスト

### TipKit導入

1. [ ] `import TipKit`を追加
2. [ ] `Tips.configure()`をアプリ起動時に呼び出し
3. [ ] Tip構造体を定義
4. [ ] `TipView`または`.popoverTip()`で表示
5. [ ] 適切なタイミングで`invalidate()`を呼び出し

---

## 関連ドキュメント

- [TipKit - Apple Developer](https://developer.apple.com/documentation/tipkit)
- [Tip - Apple Developer](https://developer.apple.com/documentation/tipkit/tip)
- [TipView - Apple Developer](https://developer.apple.com/documentation/tipkit/tipview)

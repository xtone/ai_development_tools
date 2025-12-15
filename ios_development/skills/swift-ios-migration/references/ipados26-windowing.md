# iPadOS 26 ウィンドウシステム

iPadOS 26では、iPadが本格的なウィンドウシステムを採用し、macOSに近いマルチタスク体験を提供するようになりました。このドキュメントでは、新しいウィンドウシステムへの対応方法を解説します。

## 主要な変更点

### UIRequiresFullScreen の廃止

iPadOS 26より、`UIRequiresFullScreen` Info.plistキーとその関連する互換モードは非推奨となり、将来のリリースで無視されるようになります。

**重要**: このキーに依存しているアプリは、システムがマルチタスクシナリオに対応するためにシーンをリサイズする際に、以下の問題が発生する可能性があります：
- レイアウトの崩れ
- UI要素の位置ずれ  
- コンテンツの切り詰め

### 新しいウィンドウモード

iPadOS 26では、より柔軟なウィンドウ管理が可能になりました：
- 自由なウィンドウサイズ変更
- 複数ウィンドウの重なり表示
- すべてのiPadモデルでStage Managerが利用可能
- メニューバーのサポート強化

---

## 移行手順

### 1. UIRequiresFullScreen の削除

リサイズ可能なシーンをサポートするために、アプリが以下の条件を満たすことを確認してください：

1. **Launch Storyboardの提供** - Info.plistで起動画面を指定
2. **すべてのサイズクラスのサポート** - Compact/Regularの両方に対応
3. **UIRequiresFullScreen キーの削除** - Info.plistまたはビルド設定から削除

```xml
<!-- 削除すべきエントリ -->
<key>UIRequiresFullScreen</key>
<true/>
```

### 2. Auto Layoutへの移行

固定サイズのレイアウトから、制約ベースのレイアウトに移行してください。

```swift
// ❌ 避けるべき: 固定フレーム
view.frame = CGRect(x: 0, y: 0, width: 1024, height: 768)

// ✅ 推奨: Auto Layout制約
NSLayoutConstraint.activate([
    contentView.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor),
    contentView.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor),
    contentView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
    contentView.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor)
])
```

---

## シーンジオメトリの監視

### UIWindowSceneDelegate でのジオメトリ変更検知

`windowScene(_:didUpdateEffectiveGeometry:)` を使用して、シーンのジオメトリ変更を監視します。

```swift
class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var previousSceneSize = CGSize.zero
    
    func windowScene(
        _ windowScene: UIWindowScene,
        didUpdateEffectiveGeometry previousGeometry: UIWindowScene.Geometry
    ) {
        let geometry = windowScene.effectiveGeometry
        let sceneSize = geometry.coordinateSpace.bounds.size
        
        // インタラクティブリサイズ中かどうかを確認
        if !geometry.isInteractivelyResizing && sceneSize != previousSceneSize {
            previousSceneSize = sceneSize
            // リサイズ完了後の処理
            updateLayoutForSize(sceneSize)
        }
    }
    
    private func updateLayoutForSize(_ size: CGSize) {
        // レイアウト更新処理
    }
}
```

### UIWindowScene.Geometry プロパティ

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `systemFrame` | `CGRect` | システム座標でのシーンフレーム |
| `coordinateSpace` | `UICoordinateSpace` | シーンの座標空間 |
| `interfaceOrientation` | `UIInterfaceOrientation` | 現在のインターフェース方向 |
| `isInterfaceOrientationLocked` | `Bool` | 方向がロックされているか |
| `isInteractivelyResizing` | `Bool` | リサイズ操作中かどうか |
| `minimumSize` | `CGSize` | 最小サイズ |
| `maximumSize` | `CGSize` | 最大サイズ |
| `resizingRestrictions` | `UIWindowSceneResizingRestrictions` | リサイズ制限 |

---

## シーンサイズ制限の設定

### UISceneSizeRestrictions

`UISceneSizeRestrictions` を使用して、ウィンドウの最小・最大サイズを指定します。

```swift
class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    
    func scene(
        _ scene: UIScene,
        willConnectTo session: UISceneSession,
        options connectionOptions: UIScene.ConnectionOptions
    ) {
        guard let windowScene = scene as? UIWindowScene else { return }
        
        // 最小サイズの設定
        windowScene.sizeRestrictions?.minimumSize = CGSize(width: 500, height: 400)
        
        // 最大サイズの設定（オプション）
        windowScene.sizeRestrictions?.maximumSize = CGSize(width: 1200, height: 900)
        
        // フルスクリーン許可の設定
        windowScene.sizeRestrictions?.allowsFullScreen = true
    }
}
```

### SwiftUI での設定

```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 500, maxWidth: 1200, 
                       minHeight: 400, maxHeight: 900)
        }
        .windowResizability(.contentMinSize)
    }
}
```

#### windowResizability オプション

| 値 | 説明 |
|----|------|
| `.automatic` | システムが自動的に決定 |
| `.contentSize` | コンテンツサイズに基づく |
| `.contentMinSize` | コンテンツの最小サイズを使用 |

---

## インターフェース方向のロック

特定の状況で方向をロックする必要がある場合（例：ゲーム、カメラアプリ）：

```swift
class MyViewController: UIViewController {
    
    var isDriving: Bool = false {
        didSet {
            if isDriving != oldValue {
                setNeedsUpdateOfPrefersInterfaceOrientationLocked()
            }
        }
    }
    
    override var prefersInterfaceOrientationLocked: Bool {
        return isDriving
    }
}
```

### 方向ロック状態の監視

```swift
func windowScene(
    _ windowScene: UIWindowScene,
    didUpdateEffectiveGeometry previousGeometry: UIWindowScene.Geometry
) {
    let wasLocked = previousGeometry.isInterfaceOrientationLocked
    let isLocked = windowScene.effectiveGeometry.isInterfaceOrientationLocked
    
    if wasLocked != isLocked {
        // 方向ロック状態が変化した
        handleOrientationLockChange(isLocked: isLocked)
    }
}
```

---

## SwiftUI でのリサイズ対応

### onInteractiveResizeChange

```swift
struct ContentView: View {
    @State private var isResizing = false
    
    var body: some View {
        GeometryReader { geometry in
            MainContent(size: geometry.size)
                .overlay {
                    if isResizing {
                        ResizeOverlay()
                    }
                }
        }
        .onInteractiveResizeChange { isResizing in
            self.isResizing = isResizing
        }
    }
}
```

### GeometryReader でのサイズ適応

```swift
struct AdaptiveLayout: View {
    var body: some View {
        GeometryReader { geometry in
            if geometry.size.width > 600 {
                HStack {
                    Sidebar()
                    MainContent()
                }
            } else {
                VStack {
                    MainContent()
                }
            }
        }
    }
}
```

---

## メニューバー対応

iPadOS 26では、外部キーボード接続時にメニューバーが表示されるようになりました。

### SwiftUI でのメニューバー構築

```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .commands {
            // サイドバーコマンド
            SidebarCommands()
            
            // カスタムメニュー
            CommandMenu("Actions") {
                Button("Run", systemImage: "play.fill") {
                    // アクション
                }
                .keyboardShortcut("R")
                
                Button("Stop", systemImage: "stop.fill") {
                    // アクション
                }
                .keyboardShortcut(".")
            }
            
            // 既存メニューの拡張
            CommandGroup(after: .newItem) {
                Button("New from Template...") {
                    // アクション
                }
            }
        }
    }
}
```

### UIKit でのメニュー構築

```swift
class AppDelegate: UIResponder, UIApplicationDelegate {
    
    override func buildMenu(with builder: UIMenuBuilder) {
        super.buildMenu(with: builder)
        
        guard builder.system == .main else { return }
        
        // カスタムメニューの追加
        let actionsMenu = UIMenu(
            title: "Actions",
            children: [
                UIKeyCommand(
                    title: "Run",
                    action: #selector(runAction),
                    input: "R",
                    modifierFlags: .command
                ),
                UIKeyCommand(
                    title: "Stop",
                    action: #selector(stopAction),
                    input: ".",
                    modifierFlags: .command
                )
            ]
        )
        
        builder.insertSibling(actionsMenu, afterMenu: .view)
    }
    
    @objc func runAction() { }
    @objc func stopAction() { }
}
```

---

## マルチウィンドウ対応

### 複数シーンのサポート有効化

Info.plist で `UIApplicationSupportsMultipleScenes` を `true` に設定：

```xml
<key>UIApplicationSceneManifest</key>
<dict>
    <key>UIApplicationSupportsMultipleScenes</key>
    <true/>
    <key>UISceneConfigurations</key>
    <dict>
        <key>UIWindowSceneSessionRoleApplication</key>
        <array>
            <dict>
                <key>UISceneConfigurationName</key>
                <string>Default Configuration</string>
                <key>UISceneDelegateClassName</key>
                <string>$(PRODUCT_MODULE_NAME).SceneDelegate</string>
            </dict>
        </array>
    </dict>
</dict>
```

### 新規ウィンドウの作成

```swift
// UIKit
func createNewWindow() {
    let activity = NSUserActivity(activityType: "com.example.newWindow")
    
    UIApplication.shared.requestSceneSessionActivation(
        nil,
        userActivity: activity,
        options: nil
    )
}

// SwiftUI
@Environment(\.openWindow) private var openWindow

Button("New Window") {
    openWindow(id: "secondary")
}
```

---

## Trait Collection による適応

### 自動トラッキング

iOS 17以降では、トレイトの自動トラッキングが利用可能です：

```swift
class MyViewController: UIViewController {
    
    override func viewWillLayoutSubviews() {
        super.viewWillLayoutSubviews()
        
        // 自動的にトレイトの変更を検知
        updateLayoutForTraits()
    }
    
    private func updateLayoutForTraits() {
        let horizontalClass = traitCollection.horizontalSizeClass
        let verticalClass = traitCollection.verticalSizeClass
        
        switch (horizontalClass, verticalClass) {
        case (.compact, .regular):
            // iPhone縦向き / iPad Split View狭幅
            configureCompactLayout()
        case (.regular, .regular):
            // iPad全画面 / iPad Split View広幅
            configureRegularLayout()
        default:
            configureDefaultLayout()
        }
    }
}
```

### トレイト変更の手動登録

```swift
override func viewDidLoad() {
    super.viewDidLoad()
    
    registerForTraitChanges([
        UITraitHorizontalSizeClass.self,
        UITraitVerticalSizeClass.self
    ]) { (self: Self, previousTraitCollection) in
        self.updateLayoutForTraits()
    }
}
```

---

## 移行チェックリスト

### 必須対応

- [ ] `UIRequiresFullScreen` をInfo.plistから削除
- [ ] Launch Storyboardを設定
- [ ] すべてのサイズクラスでのレイアウトをテスト
- [ ] Auto Layoutまたはサイズ適応レイアウトを使用

### 推奨対応

- [ ] `windowScene(_:didUpdateEffectiveGeometry:)` でジオメトリ変更を監視
- [ ] `UISceneSizeRestrictions` で適切な最小サイズを設定
- [ ] メニューバー対応（外部キーボード使用時）
- [ ] マルチウィンドウシナリオのテスト

### テスト項目

- [ ] Split View（50/50、75/25、25/75）
- [ ] Slide Over
- [ ] Stage Manager（対応デバイス）
- [ ] 外部ディスプレイ接続
- [ ] 画面回転
- [ ] フルスクリーン⇔ウィンドウ切り替え

---

## 関連リソース

### Apple ドキュメント

- [TN3192: Migrating your iPad app from the deprecated UIRequiresFullScreen key](https://developer.apple.com/documentation/technotes/tn3192-migrating-your-app-from-the-deprecated-uirequiresfullscreen-key/)
- [Multitasking on iPad, Mac, and Apple Vision Pro](https://developer.apple.com/documentation/uikit/multitasking-on-ipad-mac-and-apple-vision-pro/)
- [Supporting multiple windows on iPad](https://developer.apple.com/documentation/uikit/supporting-multiple-windows-on-ipad/)
- [UIWindowScene.Geometry](https://developer.apple.com/documentation/uikit/uiwindowscene/geometry/)
- [UISceneSizeRestrictions](https://developer.apple.com/documentation/uikit/uiscenesizerestrictions/)
- [Building and customizing the menu bar with SwiftUI](https://developer.apple.com/documentation/swiftui/building-and-customizing-the-menu-bar-with-swiftui/)

### WWDC25 セッション

- [WWDC25 Session 282: UIKit scenes and container view controllers](https://developer.apple.com/videos/play/wwdc2025/282/) - シーンとコンテナビューコントローラの活用
- [WWDC25 Session 284: Updating UIKit apps for the new design](https://developer.apple.com/videos/play/wwdc2025/284/) - UIKitアプリの新デザイン対応

### Human Interface Guidelines

- [Multitasking](https://developer.apple.com/design/human-interface-guidelines/multitasking/)
- [The menu bar](https://developer.apple.com/design/human-interface-guidelines/the-menu-bar/)

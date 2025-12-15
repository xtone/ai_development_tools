# WebViewコンポーネント

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | 備考 |
|--------------|-----|--------|-------|------|
| WebView | 26+ | 26+ | 26+ | SwiftUIネイティブWebView |

---

## WebView (iOS 26+)

SwiftUIネイティブのWebView。従来のWKWebViewラッパーが不要に。

### 基本的な使用法

```swift
import SwiftUI

struct WebContent: View {
    var body: some View {
        WebView(url: URL(string: "https://example.com")!)
    }
}
```

### ナビゲーション制御

```swift
WebView(url: url)
    .webViewAllowsBackForwardNavigation(true)
```

### リーダーモード

```swift
WebView(url: url)
    .webViewReaderMode(enabled: true)
```

### カスタマイズ例

```swift
struct BrowserView: View {
    @State private var url = URL(string: "https://apple.com")!
    @State private var isLoading = false

    var body: some View {
        VStack {
            if isLoading {
                ProgressView()
            }

            WebView(url: url)
                .webViewAllowsBackForwardNavigation(true)
                .onWebViewStartLoading {
                    isLoading = true
                }
                .onWebViewFinishLoading {
                    isLoading = false
                }
        }
    }
}
```

---

## Scene Bridging (iOS 26+)

UIKit/AppKitアプリにSwiftUIシーンを統合。完全な書き換え不要で段階的移行が可能。

### ユースケース

- 既存UIKitアプリへの新機能追加
- 段階的なSwiftUI移行
- 複数ウィンドウ対応

### 概念

```swift
// 既存のUIKitアプリにSwiftUIシーンを追加
// SceneDelegateやAppDelegateからSwiftUIシーンを起動可能
```

---

## 従来のWKWebViewラッパー（iOS 25以前）

iOS 26未満をサポートする必要がある場合：

```swift
import SwiftUI
import WebKit

struct LegacyWebView: UIViewRepresentable {
    let url: URL

    func makeUIView(context: Context) -> WKWebView {
        WKWebView()
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        let request = URLRequest(url: url)
        webView.load(request)
    }
}
```

### 後方互換性

```swift
var body: some View {
    if #available(iOS 26.0, *) {
        WebView(url: url)
    } else {
        LegacyWebView(url: url)
    }
}
```

---

## 関連ドキュメント

- [WebView - Apple Developer](https://developer.apple.com/documentation/swiftui/webview)
- [WKWebView - Apple Developer](https://developer.apple.com/documentation/webkit/wkwebview)

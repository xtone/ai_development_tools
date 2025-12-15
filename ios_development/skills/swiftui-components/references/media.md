# メディア・共有コンポーネント

## バージョン対応表

| コンポーネント | iOS | iPadOS | macOS | 備考 |
|--------------|-----|--------|-------|------|
| PhotosPicker | 16+ | 16+ | 13+ | 権限不要の写真選択 |
| ShareLink | 16+ | 16+ | 13+ | 標準シェア機能 |
| Transferable | 16+ | 16+ | 13+ | データ転送プロトコル |

---

## PhotosPicker (iOS 16+)

写真ライブラリへのアクセス権限なしで写真を選択可能。

### 基本的な使用法

```swift
import PhotosUI

struct PhotoSelectorView: View {
    @State private var selectedItem: PhotosPickerItem?
    @State private var selectedImage: Image?

    var body: some View {
        VStack {
            if let image = selectedImage {
                image
                    .resizable()
                    .scaledToFit()
            }

            PhotosPicker(
                selection: $selectedItem,
                matching: .images
            ) {
                Label("写真を選択", systemImage: "photo")
            }
        }
        .onChange(of: selectedItem) { newItem in
            Task {
                if let data = try? await newItem?.loadTransferable(type: Data.self),
                   let uiImage = UIImage(data: data) {
                    selectedImage = Image(uiImage: uiImage)
                }
            }
        }
    }
}
```

### 複数選択

```swift
@State private var selectedItems: [PhotosPickerItem] = []
@State private var selectedImages: [Image] = []

PhotosPicker(
    selection: $selectedItems,
    maxSelectionCount: 5,
    matching: .images
) {
    Text("最大5枚選択")
}
.onChange(of: selectedItems) { newItems in
    Task {
        selectedImages = []
        for item in newItems {
            if let data = try? await item.loadTransferable(type: Data.self),
               let uiImage = UIImage(data: data) {
                selectedImages.append(Image(uiImage: uiImage))
            }
        }
    }
}
```

### フィルタリング

```swift
// 画像のみ（スクリーンショット除外）
PhotosPicker(
    selection: $selectedItems,
    matching: .any(of: [.images, .not(.screenshots)])
) { ... }

// 動画のみ
PhotosPicker(
    selection: $selectedItems,
    matching: .videos
) { ... }

// ライブフォト
PhotosPicker(
    selection: $selectedItems,
    matching: .livePhotos
) { ... }

// 画像と動画
PhotosPicker(
    selection: $selectedItems,
    matching: .any(of: [.images, .videos])
) { ... }
```

---

## ShareLink (iOS 16+)

標準のシェア機能をSwiftUIで簡単に実装。

### 基本的な使用法

```swift
// URL共有
ShareLink(item: URL(string: "https://example.com")!)

// カスタムラベル
ShareLink(item: article.url) {
    Label("共有", systemImage: "square.and.arrow.up")
}

// プレビュー付き
ShareLink(
    item: photo,
    subject: Text("写真を共有"),
    message: Text("この写真を見てください"),
    preview: SharePreview(
        photo.title,
        image: photo.image
    )
)
```

### Transferableプロトコル

カスタム型をシェア可能にする。

```swift
struct Article: Transferable {
    var title: String
    var body: String
    var url: URL

    static var transferRepresentation: some TransferRepresentation {
        ProxyRepresentation(exporting: \.url)
    }
}

// 使用
ShareLink(item: article, preview: SharePreview(article.title))
```

### 複数のTransferRepresentation

```swift
struct Document: Transferable {
    var title: String
    var content: String
    var pdfData: Data

    static var transferRepresentation: some TransferRepresentation {
        // PDF形式
        DataRepresentation(exportedContentType: .pdf) { document in
            document.pdfData
        }

        // プレーンテキスト形式
        CodableRepresentation(contentType: .plainText)

        // URL形式（フォールバック）
        ProxyRepresentation(exporting: \.shareURL)
    }

    var shareURL: URL {
        URL(string: "https://example.com/doc/\(title)")!
    }
}
```

---

## 移行チェックリスト

### PhotosPicker導入

1. [ ] `import PhotosUI`を追加
2. [ ] `PHPhotoLibrary`の許可リクエストが不要に
3. [ ] `UIImagePickerController`を置換
4. [ ] 非同期で画像データをロード

### ShareLink導入

1. [ ] 共有するデータ型を`Transferable`に準拠
2. [ ] 適切なプレビューを提供
3. [ ] `UIActivityViewController`を置換

---

## 関連ドキュメント

- [PhotosPicker - Apple Developer](https://developer.apple.com/documentation/photosui/photospicker)
- [ShareLink - Apple Developer](https://developer.apple.com/documentation/swiftui/sharelink)
- [Transferable - Apple Developer](https://developer.apple.com/documentation/coretransferable/transferable)

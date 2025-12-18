# SwiftUI アクセシビリティガイド

## 主要なモディファイア

### accessibilityLabel

要素の説明ラベル。VoiceOverが読み上げる内容。

```swift
// 画像のみのボタンには必須
Button(action: { }) {
    Image(systemName: "heart.fill")
}
.accessibilityLabel("お気に入りに追加")

// アイコン付きテキスト
HStack {
    Image(systemName: "star.fill")
    Text("4.5")
}
.accessibilityElement(children: .combine)
.accessibilityLabel("評価 4.5")
```

### accessibilityHint

追加情報（アクション結果等）。ラベルの後に読み上げられる。

```swift
Button("削除") {
    deleteItem()
}
.accessibilityLabel("アイテムを削除")
.accessibilityHint("ダブルタップで削除します")
```

### accessibilityValue

現在の値（スライダー、トグル、カスタムコントロール等）。

```swift
Slider(value: $volume, in: 0...100)
    .accessibilityValue("\(Int(volume))パーセント")

// カスタム進捗表示
ProgressCircle(progress: 0.75)
    .accessibilityLabel("ダウンロード進捗")
    .accessibilityValue("75パーセント完了")
```

### accessibilityAddTraits

要素の特性を追加。

```swift
// onTapGestureを使う場合はボタン特性を追加
Text("タップしてください")
    .onTapGesture { /* ... */ }
    .accessibilityAddTraits(.isButton)

// 見出しとしてマーク
Text("設定")
    .font(.title)
    .accessibilityAddTraits(.isHeader)

// 選択状態
Text(item.title)
    .accessibilityAddTraits(item.isSelected ? [.isSelected] : [])
```

主な特性:
- `.isButton`: ボタンとして動作
- `.isHeader`: 見出し（ナビゲーションで使用）
- `.isSelected`: 選択中
- `.isImage`: 画像
- `.playsSound`: 音を再生
- `.isModal`: モーダル
- `.updatesFrequently`: 頻繁に更新

### accessibilityElement

複数要素のグループ化。

```swift
// 複数要素を1つにまとめる
HStack {
    Image("avatar")
    VStack(alignment: .leading) {
        Text("山田太郎")
        Text("エンジニア")
    }
}
.accessibilityElement(children: .combine)

// 子要素を無視
DecorativeView()
    .accessibilityElement(children: .ignore)

// 子要素を含める（デフォルト）
Container()
    .accessibilityElement(children: .contain)
```

## VoiceOver対応

### 画像のみボタン

```swift
// ❌ ラベルなし
Button(action: { }) {
    Image(systemName: "trash")
}

// ✅ ラベル付き
Button(action: { }) {
    Image(systemName: "trash")
}
.accessibilityLabel("削除")
```

### カスタムアクション

```swift
ArticleRow(article: article)
    .accessibilityAction(named: "お気に入りに追加") {
        addToFavorites(article)
    }
    .accessibilityAction(named: "共有") {
        shareArticle(article)
    }
```

### ローター用カスタムコンテンツ

```swift
List(articles) { article in
    ArticleRow(article: article)
        .accessibilityCustomContent("著者", article.author)
        .accessibilityCustomContent("公開日", article.formattedDate)
}
```

## Dynamic Type対応

### システムフォント使用

```swift
// ✅ 自動対応
Text("タイトル")
    .font(.title)

Text("本文テキスト")
    .font(.body)

// ❌ 固定サイズ（避ける）
Text("テキスト")
    .font(.system(size: 16))
```

### 現在のサイズカテゴリ取得

```swift
struct AdaptiveView: View {
    @Environment(\.sizeCategory) var sizeCategory
    
    var body: some View {
        if sizeCategory >= .accessibilityMedium {
            // 大きいテキストサイズ向けレイアウト
            VStack { /* ... */ }
        } else {
            // 通常レイアウト
            HStack { /* ... */ }
        }
    }
}
```

### スケーラブルテキスト

```swift
Text("テキスト")
    .dynamicTypeSize(.small ... .accessibility3)
    // small〜accessibility3の範囲でスケール
```

## 色のコントラスト

### システムカラー使用

```swift
// ✅ 推奨: システムカラー
Text("テキスト")
    .foregroundColor(.primary)

Text("補足テキスト")
    .foregroundColor(.secondary)

// ダークモード自動対応
Color(.systemBackground)
Color(.secondarySystemBackground)
```

### 色だけで情報を伝えない

```swift
// ❌ 色のみ
Circle()
    .fill(status == .error ? .red : .green)

// ✅ 色 + アイコン/テキスト
HStack {
    Image(systemName: status == .error ? "xmark.circle" : "checkmark.circle")
    Text(status == .error ? "エラー" : "成功")
}
.foregroundColor(status == .error ? .red : .green)
```

## reduce Motion対応

```swift
struct AnimatedView: View {
    @Environment(\.accessibilityReduceMotion) var reduceMotion
    
    var body: some View {
        Button("タップ") { /* ... */ }
            .animation(reduceMotion ? nil : .spring(), value: isExpanded)
    }
}
```

## テストとツール

### VoiceOverテスト

1. 設定 → アクセシビリティ → VoiceOver を有効化
2. 実機でアプリを操作
3. すべての要素が適切に読み上げられるか確認
4. ナビゲーションが論理的か確認

### Accessibility Inspector

Xcode → Open Developer Tool → Accessibility Inspector

- 各要素のアクセシビリティ情報を確認
- コントラスト比のチェック
- 問題の特定

### チェックリスト

- [ ] すべての画像ボタンにaccessibilityLabel設定
- [ ] onTapGestureにはaccessibilityTraits追加
- [ ] 関連要素をグループ化
- [ ] 見出しに.isHeader特性
- [ ] カスタムコントロールにaccessibilityValue
- [ ] Dynamic Type対応（システムフォント使用）
- [ ] 色だけで情報を伝えていない
- [ ] VoiceOverで実機テスト済み
- [ ] reduce Motion対応

## 実装例: アクセシブルなカード

```swift
struct ArticleCard: View {
    let article: Article
    let onFavorite: () -> Void
    let onShare: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 画像
            AsyncImage(url: article.imageURL) { image in
                image.resizable().aspectRatio(contentMode: .fill)
            } placeholder: {
                Color.gray
            }
            .frame(height: 200)
            .accessibilityHidden(true) // 装飾的な画像
            
            // コンテンツ
            VStack(alignment: .leading, spacing: 4) {
                Text(article.title)
                    .font(.headline)
                    .accessibilityAddTraits(.isHeader)
                
                Text(article.author)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                Text(article.formattedDate)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel("\(article.title)、\(article.author)、\(article.formattedDate)")
        }
        .accessibilityAction(named: "お気に入りに追加") {
            onFavorite()
        }
        .accessibilityAction(named: "共有") {
            onShare()
        }
    }
}
```

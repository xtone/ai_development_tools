# Figma → Compose 変換ルール詳細

## 概要

このドキュメントは、Figmaデザインの各要素をJetpack Composeコードに変換する際の詳細なルールを提供します。

## Color変換

### rgba → Color形式

#### 基本変換式

```
Figma: rgba(R, G, B, A)
↓
Compose: Color(0xAARRGGBB)

変換：
- A (Alpha): 0.0-1.0 → 0x00-0xFF
- R (Red): 0-255 → 0x00-0xFF
- G (Green): 0-255 → 0x00-0xFF
- B (Blue): 0-255 → 0x00-0xFF
```

#### 具体例

```kotlin
// Example 1: 完全不透明
Figma: rgba(0,116,196,1.0)
Compose: Color(0xFF0074C4)
       ↑ ↑ ↑ ↑ ↑ ↑
       A A R R G G B B
       F F 00 74 C4

// Example 2: 半透明
Figma: rgba(102,102,102,0.5)
Compose: Color(0x80666666)
       ↑ ↑
       80 = 0.5 * 255 = 127.5 ≈ 128 = 0x80

// Example 3: グレースケール
Figma: rgba(245,245,245,1.0)
Compose: Color(0xFFF5F5F5)
```

#### Figma API からの抽出

```python
# Figma API Response
{
  "backgroundColor": {
    "r": 0.0,        # 0.0-1.0
    "g": 0.4588,     # 0.0-1.0
    "b": 0.7686,     # 0.0-1.0
    "a": 1.0         # 0.0-1.0
  }
}

# 変換
r = int(0.0 * 255) = 0 = 0x00
g = int(0.4588 * 255) = 117 = 0x75
b = int(0.7686 * 255) = 196 = 0xC4
a = int(1.0 * 255) = 255 = 0xFF

# 結果
Color(0xFF0075C4)
```

#### Color定数の命名規則

```kotlin
// ❌ 悪い例：意味不明な名前
val color1 = Color(0xFF0074C4)
val blueColor = Color(0xFF0074C4)

// ✅ 良い例：用途を示す名前
object MyListColors {
    val tabActive = Color(0xFF0074C4)        // タブ選択状態
    val tabInactive = Color(0xFF666666)      // タブ非選択状態
    val imagePlaceholder = Color(0xFFF5F5F5) // 画像プレースホルダー
    val titleText = Color(0xFF333333)        // タイトルテキスト
    val metaText = Color(0xFF999999)         // メタ情報テキスト
}
```

## Typography変換

### font-size → fontSize

```
Figma: font-size: 17px
↓
Compose: fontSize = 17.sp
```

### font-weight → FontWeight

#### 変換表

```kotlin
Figma fontWeight → Compose FontWeight

100 → FontWeight.Thin
200 → FontWeight.ExtraLight
300 → FontWeight.Light
400 → FontWeight.Normal
500 → FontWeight.Medium
600 → FontWeight.SemiBold
700 → FontWeight.Bold
800 → FontWeight.ExtraBold
900 → FontWeight.Black
```

#### 具体例

```kotlin
// Example 1: Bold
Figma: font-weight: 700
Compose: fontWeight = FontWeight.Bold

// Example 2: Medium
Figma: font-weight: 500
Compose: fontWeight = FontWeight.Medium

// Example 3: SemiBold
Figma: font-weight: 600
Compose: fontWeight = FontWeight.SemiBold
```

### line-height → lineHeight

#### 比率形式（推奨）

```kotlin
// Figma: line-height: 1.35
// 計算: fontSize × lineHeight
Figma:
  font-size: 17px
  line-height: 1.35

Compose:
  fontSize = 17.sp
  lineHeight = (17 * 1.35).sp // = 22.95.sp
```

#### ピクセル形式

```kotlin
// Figma: line-height: 23px
Figma:
  font-size: 17px
  line-height: 23px

Compose:
  fontSize = 17.sp
  lineHeight = 23.sp
```

### font-family → FontFamily

```kotlin
// Figma: font-family: Inter
Compose: fontFamily = FontFamily.SansSerif

// Figma: font-family: "Hiragino Kaku Gothic"
Compose: fontFamily = FontFamily.SansSerif // Android標準

// カスタムフォント（プロジェクト固有）
Compose: fontFamily = HiraginoKakuGothic // リソースから読み込み
```

### Typography定数の作成

```kotlin
object MyListTypography {
    val headerTitle = TextStyle(
        fontFamily = Inter,
        fontSize = 17.sp,                    // Figma: font-size: 17px
        fontWeight = FontWeight.Bold,        // Figma: font-weight: 700
        lineHeight = 22.95.sp                // Figma: line-height: 1.35
    )

    val tabText = TextStyle(
        fontFamily = Inter,
        fontSize = 15.sp,                    // Figma: font-size: 15px
        fontWeight = FontWeight.Bold,        // Figma: font-weight: 700 (active)
        lineHeight = 20.25.sp                // Figma: line-height: 1.35
    )

    val articleTitle = TextStyle(
        fontFamily = HiraginoKakuGothic,
        fontSize = 16.sp,                    // Figma: font-size: 16px
        fontWeight = FontWeight.SemiBold,    // Figma: font-weight: 600
        lineHeight = 22.4.sp                 // Figma: line-height: 1.4
    )

    val metaText = TextStyle(
        fontFamily = HiraginoKakuGothic,
        fontSize = 12.sp,                    // Figma: font-size: 12px
        fontWeight = FontWeight.Light,       // Figma: font-weight: 300
        lineHeight = 16.8.sp                 // Figma: line-height: 1.4
    )
}
```

## Layout変換

### padding → Modifier.padding

#### 全方向同じ

```kotlin
// Figma: padding: 20px
Compose: .padding(20.dp)
```

#### 方向別

```kotlin
// Figma:
//   padding-left: 10px
//   padding-right: 10px
//   padding-top: 20px
//   padding-bottom: 20px

Compose: .padding(
    start = 10.dp,
    end = 10.dp,
    top = 20.dp,
    bottom = 20.dp
)

// または水平・垂直で指定
Compose: .padding(
    horizontal = 10.dp,
    vertical = 20.dp
)
```

### margin → Spacer

```kotlin
// Figma: margin-bottom: 10px
// ↓
Compose: Spacer(modifier = Modifier.height(10.dp))

// Figma: margin-right: 10px
// ↓
Compose: Spacer(modifier = Modifier.width(10.dp))
```

### gap → Arrangement.spacedBy

```kotlin
// Figma: gap: 10px (Row/Column内の要素間隔)
// ↓
Compose:
Row(
    horizontalArrangement = Arrangement.spacedBy(10.dp)
)

Column(
    verticalArrangement = Arrangement.spacedBy(10.dp)
)
```

### border-radius → RoundedCornerShape

```kotlin
// Figma: border-radius: 4px
Compose: shape = RoundedCornerShape(4.dp)

// Figma: 角ごとに異なる（稀）
//   border-top-left-radius: 8px
//   border-top-right-radius: 8px
//   border-bottom-left-radius: 0px
//   border-bottom-right-radius: 0px
Compose: shape = RoundedCornerShape(
    topStart = 8.dp,
    topEnd = 8.dp,
    bottomStart = 0.dp,
    bottomEnd = 0.dp
)
```

### width/height → Modifier.size

```kotlin
// Figma:
//   width: 100px
//   height: 76px

Compose: .size(width = 100.dp, height = 76.dp)

// または
Compose:
    .width(100.dp)
    .height(76.dp)
```

### Layout定数の管理（重要）

#### ❌ 悪い例：魔法の数字

```kotlin
Box(
    modifier = Modifier
        .size(100.dp, 76.dp)
        .background(Color(0xFFF5F5F5))
)

Spacer(modifier = Modifier.width(12.dp))

Box(
    modifier = Modifier.padding(start = 92.dp)  // この92はどこから？
)
```

#### ✅ 良い例：計算式で表現

```kotlin
private object LayoutDimensions {
    // 基本値（Figma直接取得）
    val imagePadding = 10.dp          // Figma: padding-left: 10px
    val imageWidth = 72.dp            // Figma: width: 72px
    val imageHeight = 76.dp           // Figma: height: 76px
    val imageSpacing = 12.dp          // Figma: gap: 12px

    // 計算値（魔法の数字を排除）
    val dividerStartPadding = imagePadding + imageWidth + imageSpacing  // 94.dp
}

// 使用例
Box(
    modifier = Modifier
        .size(LayoutDimensions.imageWidth, LayoutDimensions.imageHeight)
        .background(Color(0xFFF5F5F5))
)

Spacer(modifier = Modifier.width(LayoutDimensions.imageSpacing))

Box(
    modifier = Modifier.padding(start = LayoutDimensions.dividerStartPadding)
)
```

## レイアウト階層の変換

### Figma Frame → Compose Column/Row

#### 基本パターン

```kotlin
// Figma:
//   Frame (vertical layout, gap: 10px)
//     ├─ Text
//     ├─ Text
//     └─ Text

// Compose:
Column(
    verticalArrangement = Arrangement.spacedBy(10.dp)
) {
    Text("...")
    Text("...")
    Text("...")
}
```

#### ネストパターン

```kotlin
// Figma:
//   Frame (horizontal layout)
//     ├─ Image
//     └─ Frame (vertical layout)
//          ├─ Text (meta)
//          └─ Text (title)

// Compose:
Row(
    horizontalArrangement = Arrangement.spacedBy(12.dp)
) {
    AsyncImage(...)

    Column(
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Text("meta")
        Text("title")
    }
}
```

## 条件分岐の実装

### 最後のアイテムでのdivider表示

```kotlin
// Figma仕様:
// - 通常: テキスト開始位置からdivider
// - 最後のアイテム: 全幅divider

if (isLastItem) {
    // 全幅のdivider
    HorizontalDivider(
        color = colors.divider,       // Figma確認
        thickness = 1.dp,             // Figma確認
    )
} else {
    // テキスト開始位置からのdivider
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(start = LayoutDimensions.textStartPosition)  // 計算値
    ) {
        HorizontalDivider(
            color = colors.divider,
            thickness = 1.dp,
        )
    }
}
```

### お気に入りアイコンの状態

```kotlin
// Figma仕様:
// - お気に入り済: 塗りつぶしアイコン + activeColor
// - 未お気に入り: アウトラインアイコン + inactiveColor

IconButton(
    onClick = onFavoriteClick,
    modifier = Modifier.size(24.dp)  // Figma確認
) {
    Icon(
        painter = painterResource(
            if (article.isFavorited) {
                R.drawable.ic_favorite_filled      // Figma確認
            } else {
                R.drawable.ic_favorite_outline     // Figma確認
            }
        ),
        contentDescription = "お気に入り",
        tint = if (article.isFavorited) {
            MyListColors.tabActive                 // Figma確認
        } else {
            MyListColors.metaText                  // Figma確認
        }
    )
}
```

## よくある変換ミス

### 1. 角丸の推測

```kotlin
// ❌ 推測
shape = RoundedCornerShape(8.dp)

// ✅ Figma確認
shape = RoundedCornerShape(4.dp)  // Figma: border-radius: 4px
```

### 2. スペーシングの目視判断

```kotlin
// ❌ 目視
.padding(16.dp)

// ✅ Figma確認
.padding(20.dp)  // Figma: padding: 20px
```

### 3. フォントサイズの近似

```kotlin
// ❌ 近似
fontSize = 16.sp

// ✅ Figma確認
fontSize = 17.sp  // Figma: font-size: 17px
```

### 4. line-heightの計算ミス

```kotlin
// ❌ 計算ミス
lineHeight = 20.sp  // 15 * 1.35 = 20.25 なのに20にしている

// ✅ 正確な計算
lineHeight = 20.25.sp  // Figma: line-height: 1.35, font-size: 15px
```

## Material Design 3 準拠

### Cardの実装

```kotlin
Card(
    modifier = modifier,
    shape = RoundedCornerShape(LayoutDimensions.cornerRadius),  // Figma確認
    colors = CardDefaults.cardColors(
        containerColor = MyListColors.backgroundColor  // Figma確認
    ),
    elevation = CardDefaults.cardElevation(
        defaultElevation = 0.dp  // Figmaで影が指定されていない場合
    )
) {
    // Content
}
```

### Buttonの実装

```kotlin
Button(
    onClick = onClick,
    shape = RoundedCornerShape(LayoutDimensions.buttonRadius),  // Figma確認
    colors = ButtonDefaults.buttonColors(
        containerColor = MyListColors.buttonBackground,  // Figma確認
        contentColor = MyListColors.buttonText           // Figma確認
    )
) {
    Text("ボタンテキスト")
}
```

## プレビューの実装

```kotlin
@Preview(showBackground = true)
@Composable
private fun ArticleCardPreview() {
    MaterialTheme {
        ArticleCard(
            article = Article(
                imageUrl = "",
                publishDate = "2時間前",
                title = "サンプルタイトルテキスト",
                isFavorited = false
            ),
            onFavoriteClick = {}
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun ArticleCardFavoritedPreview() {
    MaterialTheme {
        ArticleCard(
            article = Article(
                imageUrl = "",
                publishDate = "2時間前",
                title = "サンプルタイトルテキスト",
                isFavorited = true  // お気に入り済状態
            ),
            onFavoriteClick = {}
        )
    }
}
```

## まとめ

- **推測禁止**：全ての値はFigmaから正確に取得
- **計算式表現**：魔法の数字を避け、基本値の計算式で表現
- **命名規則**：用途を明確にした定数名
- **段階的確認**：Color → Typography → Layout の順で確認
- **プレビュー**：複数の状態でビジュアル確認

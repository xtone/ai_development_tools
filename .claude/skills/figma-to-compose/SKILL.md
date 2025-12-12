---
name: figma-to-compose
description: Figmaデザインから高精度Jetpack Composeコードを生成するスキル。推測を排除し、Figma APIから正確な値を取得することで、95%以上の準拠率を実現。バイブコーディングを禁止し、Figma仕様に忠実な実装を保証する。
---

# Figma To Compose - 高精度UI生成スキル

## 目的

FigmaデザインからJetpack Composeコードを**95%以上の準拠率**で自動生成する。
推測を完全に排除し、Figma APIから取得した正確な値のみを使用することで、デザイナーの意図を100%反映した実装を実現する。

## 使用タイミング

このスキルは以下の場合に自動的に起動する：
- ユーザーがFigma URLを提供した時
- "Figmaから〜を生成"、"Compose画面を作成"のような指示があった時
- `/figma-to-compose` コマンドが実行された時

## 核心原則：推測とバイブコーディングの完全禁止

### 絶対禁止事項

#### 1. 推測による実装の禁止
❌ **悪い例**：デザインを見て「8dpくらいだろう」と推測
```kotlin
RoundedCornerShape(8.dp) // なぜ8dp？根拠なし
```

✅ **良い例**：`get_code` でFigmaから正確な値を取得
```kotlin
RoundedCornerShape(4.dp) // Figmaで `rounded-[4px]` を確認
```

#### 2. バイブコーディングの禁止

**バイブコーディング**とは：Figmaで明示的に指定されていない要素を勝手に追加・変更する行為

❌ **禁止される行為**：
- Figmaで指定されていない角丸を勝手に追加
- Figmaで指定されていない文字サイズの変更
- Figmaで指定されていないレイアウト調整
- Figmaで指定されていないColor/Padding/Marginの追加
- 「見た目が良いから」という理由での独自改変

✅ **正しい実装**：
- Figmaで明示的に指定された部分**のみ**を実装
- 仕様が不明な場合は、ユーザーに確認を求める
- 全ての値がFigma由来であることを証明できる状態を保つ

#### 3. 魔法の数字（ハードコード値）の禁止

❌ **悪い例**：
```kotlin
val dividerStartPadding = 92.dp // この92はどこから？
```

✅ **良い例**：
```kotlin
private object LayoutDimensions {
    val imagePadding = 10.dp      // Figma: padding-left: 10px
    val imageWidth = 72.dp         // Figma: width: 72px
    val imageSpacing = 10.dp       // Figma: gap: 10px
    val dividerStartPadding = imagePadding + imageWidth + imageSpacing // = 92.dp
}
```

#### 4. Figma要素の省略禁止

**省略**とは：Figmaに存在する要素を「不要」と判断して実装しないこと

❌ **禁止される行為**：
- Figmaに存在する要素を「不要」と判断して省略する
- 「システムUIが描画する」という理由で空間を確保しない
- 「見た目に影響しない」という理由でスペーサーを省略する

✅ **正しい実装**：
- Figmaの全ての要素に対応するCompose要素を作成
- 描画しない要素でも、**スペースは確保**する
- 不明な場合はユーザーに確認を求める

**例：ステータスバーの扱い**：
```kotlin
// ステータスバー - 描画はシステムUIに任せるが、スペースは確保
Spacer(modifier = Modifier.height(52.dp)) // Figma: status-bar height: 52px
```

**実際に発生した問題**：
```kotlin
❌ // ステータスバーを省略 → 後続コンテンツが上に詰まる
Column(modifier = Modifier.fillMaxSize()) {
    LockScreenClock(...) // 時計が画面上部に寄りすぎ
}

✅ // スペースを確保 → レイアウト維持
Column(modifier = Modifier.fillMaxSize()) {
    Spacer(modifier = Modifier.height(52.dp)) // Figma: status-bar
    LockScreenClock(...) // 正しい位置に配置
}
```

## 実行フロー（必須順序）

### Phase 1: Figma仕様の抽出（効果測定の基盤）

#### Step 1-1: URL解析
```
入力例：https://www.figma.com/design/[file-id]?node-id=[node-id]&m=dev
抽出：
  - file-id: デザインファイルID
  - node-id: コンポーネントID（例：29434-393401）
```

#### Step 1-2: Figma MCP Tools呼び出し（必須順序）

**重要**: このスキルは **Figma MCP Tools** を使用することを前提としています。

**必須ツール使用順序**：
1. **`get_code`** - **最優先・必須**：正確な値とスタイル情報の取得
   ```
   Tool: get_code
   Parameters:
     node_url: https://www.figma.com/design/[file-id]?node-id=[node-id]
   ```

2. **`get_image`** - **推奨**：ビジュアル確認
   ```
   Tool: get_image
   Parameters:
     node_url: https://www.figma.com/design/[file-id]?node-id=[node-id]
   ```

3. **`get_metadata`** - **任意**：ノード構造の概要把握
   ```
   Tool: get_metadata
   Parameters:
     node_url: https://www.figma.com/design/[file-id]?node-id=[node-id]
   ```

**重要事項**：
- ✅ Figma MCP Toolsがメインアプローチ
- ✅ `get_code` を省略してはならない（準拠率95%以上の鍵）
- ⚠️ MCP接続失敗時のみ、直接API呼び出しにフォールバック（詳細は `references/figma-api-patterns.md` 参照）

#### Step 1-3: Figma仕様レポートの生成

取得した値を構造化して記録：
```markdown
## Figma Design Specification Report

### Node: [Component Name] ([node-id])
### Generated: [timestamp]

#### Colors (Figma仕様)
- primaryColor: rgba(0,116,196,1.0) → Color(0xFF0074C4)
- secondaryColor: rgba(102,102,102,1.0) → Color(0xFF666666)
- backgroundColor: rgba(245,245,245,1.0) → Color(0xFFF5F5F5)

#### Typography (Figma仕様)
- titleText: fontSize=17px, fontWeight=700, lineHeight=1.35
- bodyText: fontSize=15px, fontWeight=500, lineHeight=1.4

#### Layout (Figma仕様)
- padding: 20px → 20.dp
- cornerRadius: 4px → 4.dp
- gap: 10px → 10.dp
```

このレポートは効果測定の**Before/After比較**に使用される。

### Phase 2: 検証（推測・バイブコーディングの排除）

実装前に以下を必ず確認：

#### チェックリスト
- [ ] `get_code` で全ての値を取得したか
- [ ] 推測している箇所はないか（角丸、文字サイズ、色等）
- [ ] Figma仕様に記載のない要素を追加していないか
- [ ] **Figma仕様に存在する要素を省略していないか**
- [ ] **システムUI要素（ステータスバー等）のスペースを確保しているか**
- [ ] 全ての値がFigma由来であることを証明できるか
- [ ] 魔法の数字を使っていないか（計算式で表現しているか）

**不明な仕様がある場合**：
```
ユーザーに確認：
"Figmaで[要素名]の[プロパティ]が確認できませんでした。
 以下のいずれかをお選びください：
 1. Figmaで該当箇所を確認して値を教えてください
 2. この要素は実装しない（Figma仕様外のため）
 3. デフォルト値を使用（Material Design 3準拠）"
```

### Phase 3: Compose生成

#### 注意: システムUI要素の扱い

Figmaデザインにはしばしばステータスバー、ナビゲーションバーなどのシステムUI要素が含まれます。これらは：

1. **描画**: システムが行うため、Compose側での描画は不要
2. **スペース**: **必ず確保する**（Spacer または padding）

```kotlin
// 例: ステータスバー 52px がFigmaにある場合
Spacer(modifier = Modifier.height(52.dp)) // 描画せず、スペースのみ確保
```

この処理を省略すると、後続のコンテンツが上に詰まり、デザインとの不一致が発生します。

#### Step 3-1: Color定数生成

Figma仕様のrgba値をAndroid Color形式に変換：

```kotlin
// Figmaから取得したColor定義
object [ComponentName]Colors {
    val primaryColor = Color(0xFF0074C4)        // rgba(0,116,196,1.0) - Figma取得
    val secondaryColor = Color(0xFF666666)      // rgba(102,102,102,1.0) - Figma取得
    val backgroundColor = Color(0xFFF5F5F5)     // rgba(245,245,245,1.0) - Figma取得
}
```

**変換ルール**：
```
rgba(R, G, B, A) → Color(0xAARRGGBB)
  例：rgba(0,116,196,1.0) → Color(0xFF0074C4)
       ↑   ↑   ↑    ↑           ↑  ↑  ↑  ↑
       R   G   B    A          A  R  G  B
```

#### Step 3-2: Typography定数生成

Figma仕様のフォント設定をTextStyleに変換：

```kotlin
// Figmaから取得したTypography定義
object [ComponentName]Typography {
    val titleText = TextStyle(
        fontSize = 17.sp,                    // Figma: font-size: 17px
        fontWeight = FontWeight.Bold,        // Figma: font-weight: 700
        lineHeight = 22.95.sp                // Figma: line-height: 1.35 → 17 * 1.35
    )

    val bodyText = TextStyle(
        fontSize = 15.sp,                    // Figma: font-size: 15px
        fontWeight = FontWeight.Medium,      // Figma: font-weight: 500
        lineHeight = 21.sp                   // Figma: line-height: 1.4 → 15 * 1.4
    )
}
```

**FontWeight変換表**：
```
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

#### Step 3-3: Layout定数生成（計算式ベース）

```kotlin
// Figmaから取得したLayout定義（計算式で表現）
private object LayoutDimensions {
    // 基本値（Figma直接取得）
    val imagePadding = 10.dp                 // Figma: padding-left: 10px
    val imageWidth = 72.dp                   // Figma: width: 72px
    val imageSpacing = 10.dp                 // Figma: gap: 10px
    val cornerRadius = 4.dp                  // Figma: border-radius: 4px

    // 計算値（魔法の数字を排除）
    val dividerStartPadding = imagePadding + imageWidth + imageSpacing  // 92.dp
}
```

#### Step 3-4: Composable関数生成

```kotlin
@Composable
fun [ComponentName](
    // パラメータはFigmaのデータ構造に基づく
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(LayoutDimensions.cornerRadius),  // Figma: 4px
        colors = CardDefaults.cardColors(
            containerColor = [ComponentName]Colors.backgroundColor  // Figma取得
        )
    ) {
        Row(
            modifier = Modifier.padding(LayoutDimensions.imagePadding),  // Figma: 10px
            horizontalArrangement = Arrangement.spacedBy(LayoutDimensions.imageSpacing)  // Figma: 10px
        ) {
            // Figmaのレイアウト階層を忠実に再現
        }
    }
}

@Preview
@Composable
private fun [ComponentName]Preview() {
    MaterialTheme {
        [ComponentName]()
    }
}
```

### Phase 4: 準拠率レポート生成

生成したComposeコードとFigma仕様を照合：

```markdown
## Implementation Compliance Report

### Component: [ComponentName]
### Generated: [timestamp]

#### Color Compliance: 100% ✅
- primaryColor: ✅ Color(0xFF0074C4) (Figma一致)
- secondaryColor: ✅ Color(0xFF666666) (Figma一致)
- backgroundColor: ✅ Color(0xFFF5F5F5) (Figma一致)

#### Typography Compliance: 100% ✅
- titleText: ✅ 17.sp, FontWeight.Bold, lineHeight=22.95.sp (Figma一致)
- bodyText: ✅ 15.sp, FontWeight.Medium, lineHeight=21.sp (Figma一致)

#### Layout Compliance: 100% ✅
- padding: ✅ 10.dp (Figma一致)
- cornerRadius: ✅ 4.dp (Figma一致)
- gap: ✅ 10.dp (Figma一致)

#### Unauthorized Elements: 0 ✅
- 勝手な角丸追加: なし
- 勝手なサイズ変更: なし
- Figma未指定の要素追加: なし

### Overall Compliance Score: 100%
```

## デザイントークンの解釈

### CSS → Android Compose変換ルール

```css
/* Figmaコード例 */
padding: 20px;
border-radius: 4px;
font-size: 15px;
line-height: 1.35;
gap: 10px;

/* Android Compose実装 */
.padding(20.dp)
.rounded(4.dp)
fontSize = 15.sp
lineHeight = 20.25.sp // 15 * 1.35
Arrangement.spacedBy(10.dp)
```

### よくある間違いと対策

#### 1. 角丸（Corner Radius）のハルシネーション

**問題**：デザインを見て「これは8dpくらい」と推測してしまう

**対策**：
- 必ず `get_code` でFigmaの実際の値を確認
- `rounded-[Npx]` または `border-radius: Npx` の記述を探す
- 不明な場合は再度Figmaデータを問い合わせる

**実際に発生した例**：
```kotlin
❌ shape = RoundedCornerShape(8.dp) // 推測
✅ shape = RoundedCornerShape(4.dp) // Figma確認後
```

#### 2. スペーシング値の不正確さ

**問題**：パディングやマージンを目視で判断

**対策**：
- `gap-N`、`p-N`、`padding: Npx` などのCSSクラスを確認
- `get_code` で正確な値を読み取る

#### 3. フォントサイズとline-heightの計算ミス

**問題**：line-heightの計算を間違える

**対策**：
```kotlin
// line-height: 1.35の場合
fontSize = 15.sp
lineHeight = (15 * 1.35).sp // = 20.25.sp（明示的に計算）
```

## 実装パターン（ベストプラクティス）

### dividerの実装パターン

最後のアイテムで異なるdivider表示：

```kotlin
if (isLastItem) {
    // 全幅のdivider（Figma仕様）
    HorizontalDivider(
        color = colors.divider,
        thickness = 1.dp,  // Figma確認
    )
} else {
    // テキスト開始位置からのdivider（Figma仕様）
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(start = LayoutDimensions.textStartPosition)  // 計算値
    ) {
        HorizontalDivider(
            color = colors.divider,
            thickness = 1.dp,  // Figma確認
        )
    }
}
```

## 検証手順

### 1. Figmaデータの取得と検証

```bash
# 1. URLからnode-idを正確に抽出
nodeId = "29434-393401"  # URLから抽出

# 2. get_codeでスタイル情報を取得（必須）
# 3. get_imageでビジュアル確認（推奨）
# 4. 不明な点があれば再度問い合わせ
```

### 2. 実装後の確認

- [ ] プレビューでのビジュアル確認
- [ ] Figma画像との並列比較
- [ ] 異なるケース（お気に入り有無、最後のアイテムなど）での検証
- [ ] 準拠率レポートで100%確認

## トラブルシューティング

### Q: Figmaの値が不明確な場合
A: より大きなコンポーネントや親要素の `get_code` (MCP Tool) を実行して文脈を取得

### Q: 複雑なレイアウトの実装方針が分からない場合
A: 既存の類似コンポーネントのパターンを参考にする

### Q: デザインとプレビューが一致しない場合
A: Figmaの `get_image` (MCP Tool) とプレビューの並列表示で詳細比較

### Q: Figma MCP接続が失敗する場合

**対処方法**：
1. **MCP接続確認**: Claude Code MCPの状態を確認
2. **フォールバック**: 直接API呼び出しに切り替え（詳細は `references/figma-api-patterns.md` 参照）

**注意**: 基本的にはFigma MCP Toolsを使用してください。直接APIアクセスはMCP接続失敗時の代替手段です。

### Q: ステータスバーやナビゲーションバーなどのシステムUI要素がある場合

A: **描画は省略可能だが、スペースは必ず確保する**。

Figmaで52pxのステータスバーがある場合：
- ❌ 完全に省略 → レイアウトが崩れる（後続コンテンツが上に詰まる）
- ✅ `Spacer(52.dp)` でスペース確保 → レイアウト維持

```kotlin
// 正しい実装例
Column(modifier = Modifier.fillMaxSize()) {
    // Figma: status-bar (52px) - 描画はシステムに任せ、スペースのみ確保
    Spacer(modifier = Modifier.height(52.dp))

    // メインコンテンツ
    MainContent(...)
}
```

## 効果測定

### Before（口頭指示）vs After（スキル使用）の比較

**Before計測**（ベースライン）：
```
口頭指示: "〇〇画面のArticleCardを作って"
→ 生成されたCompose
→ Figma仕様との差分を計算
→ 準拠率: 例えば60%
```

**After計測**（スキル使用）：
```
/figma-to-compose https://figma.com/.../node-id=29434-393401
→ 生成されたCompose
→ Figma仕様との差分を計算
→ 準拠率: 目標95%以上
```

### 準拠率の計算方法

詳細は `scripts/compliance-calculator.py` を参照。

基本的な計算：
```
準拠率 = (Figma一致項目数 / Figma仕様項目総数) × 100

項目例：
- Color値の一致
- フォントサイズの一致
- fontWeightの一致
- line-heightの一致
- paddingの一致
- marginの一致
- corner radiusの一致
- レイアウト構造の一致
```

## 段階的精度向上

### Phase 1（初期実装）: 基本的な値の正確性
- Color/Typography/Layoutの正確な変換
- 目標準拠率: **80%**

### Phase 2（改善）: 構造の忠実性
- レイアウト階層の正確な再現
- 目標準拠率: **90%**

### Phase 3（最適化）: エッジケース対応
- dividerパターン、条件分岐等
- 目標準拠率: **95%以上**

## まとめ

このスキルは以下を実現する：
- **推測禁止**：必ずFigmaから正確な値を取得
- **バイブコーディング禁止**：Figma仕様外の要素を追加しない
- **段階的アプローチ**：get_code → 検証 → 生成 → レポート
- **相対レイアウト**：ハードコード値ではなく計算式ベースの実装
- **効果測定**：準拠率レポートで品質を可視化
- **検証徹底**：実装後のビジュアル確認を怠らない

これらのプラクティスに従うことで、Figmaデザインに正確に準拠した高品質なUI実装が可能になる。

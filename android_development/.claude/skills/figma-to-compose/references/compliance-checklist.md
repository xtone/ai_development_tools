# Figma準拠率チェックリスト

## 概要

このドキュメントは、生成されたComposeコードがFigma仕様にどれだけ準拠しているかを評価するための詳細なチェックリストを提供します。

## 準拠率の計算式

```
準拠率 = (一致項目数 / 総項目数) × 100

目標：95%以上
```

## チェック項目カテゴリ

### 1. Color準拠（30%）

#### 1-1. Color定義の正確性

- [ ] **背景色**：Figma rgba値と完全一致
  ```kotlin
  // Figma: rgba(245,245,245,1.0)
  // Compose: Color(0xFFF5F5F5)
  一致: ✅ / 不一致: ❌
  ```

- [ ] **テキスト色**：Figma rgba値と完全一致
  ```kotlin
  // Figma: rgba(51,51,51,1.0)
  // Compose: Color(0xFF333333)
  一致: ✅ / 不一致: ❌
  ```

- [ ] **アクセントカラー**：Figma rgba値と完全一致
  ```kotlin
  // Figma: rgba(0,116,196,1.0)
  // Compose: Color(0xFF0074C4)
  一致: ✅ / 不一致: ❌
  ```

- [ ] **Color定数命名**：用途を明確に表現
  ```kotlin
  ❌ color1, blueColor
  ✅ tabActive, titleText, imagePlaceholder
  ```

**配点**：
- 色値の完全一致: 各5点（最大20点）
- 命名の適切性: 10点

---

### 2. Typography準拠（30%）

#### 2-1. Font Size

- [ ] **fontSize**: Figma px値と完全一致（px → sp変換）
  ```kotlin
  // Figma: font-size: 17px
  // Compose: fontSize = 17.sp
  一致: ✅ / 不一致: ❌
  ```

#### 2-2. Font Weight

- [ ] **fontWeight**: Figma値に対応するFontWeightを使用
  ```kotlin
  // Figma: font-weight: 700
  // Compose: fontWeight = FontWeight.Bold
  一致: ✅ / 不一致: ❌
  ```

#### 2-3. Line Height

- [ ] **lineHeight**: 正確な計算（比率またはpx）
  ```kotlin
  // Figma: line-height: 1.35, font-size: 17px
  // Compose: lineHeight = 22.95.sp  // 17 * 1.35
  一致: ✅ / 不一致: ❌
  ```

#### 2-4. Font Family

- [ ] **fontFamily**: Figma指定フォントまたは適切な代替
  ```kotlin
  // Figma: font-family: Inter
  // Compose: fontFamily = Inter
  一致: ✅ / 不一致: ❌
  ```

**配点**：
- fontSize一致: 8点
- fontWeight一致: 8点
- lineHeight一致: 8点
- fontFamily適切性: 6点

---

### 3. Layout準拠（30%）

#### 3-1. Padding

- [ ] **padding**: Figma px値と完全一致（px → dp変換）
  ```kotlin
  // Figma: padding: 20px
  // Compose: .padding(20.dp)
  一致: ✅ / 不一致: ❌
  ```

- [ ] **方向別padding**: 各方向が正確
  ```kotlin
  // Figma: padding-left: 10px, padding-top: 20px
  // Compose: .padding(start = 10.dp, top = 20.dp)
  一致: ✅ / 不一致: ❌
  ```

#### 3-2. Spacing（gap/margin）

- [ ] **gap**: 要素間隔がFigmaと一致
  ```kotlin
  // Figma: gap: 10px
  // Compose: Arrangement.spacedBy(10.dp)
  一致: ✅ / 不一致: ❌
  ```

#### 3-3. Corner Radius

- [ ] **border-radius**: Figma値と完全一致（推測なし）
  ```kotlin
  // Figma: border-radius: 4px
  // Compose: RoundedCornerShape(4.dp)
  一致: ✅ / 不一致: ❌
  ```

#### 3-4. Size（width/height）

- [ ] **width/height**: Figma値と一致
  ```kotlin
  // Figma: width: 100px, height: 76px
  // Compose: .size(100.dp, 76.dp)
  一致: ✅ / 不一致: ❌
  ```

#### 3-5. Layout定数（重要）

- [ ] **魔法の数字排除**: ハードコード値を使用していない
  ```kotlin
  ❌ .padding(start = 92.dp)  // この92はどこから？
  ✅ .padding(start = LayoutDimensions.dividerStartPadding)
     // = imagePadding + imageWidth + imageSpacing
  ```

**配点**：
- padding一致: 6点
- spacing一致: 6点
- cornerRadius一致: 6点
- size一致: 6点
- 魔法の数字排除: 6点

---

### 4. バイブコーディング禁止（10%）

#### 4-1. 未承認要素の追加

- [ ] **Figma未指定の角丸追加なし**
  ```kotlin
  ❌ Figmaで指定なしなのに .rounded(8.dp) を追加
  ✅ Figma指定分のみ実装
  ```

- [ ] **Figma未指定のサイズ変更なし**
  ```kotlin
  ❌ Figmaで fontSize: 17px なのに 16.sp に変更
  ✅ Figma仕様通り 17.sp
  ```

- [ ] **Figma未指定のレイアウト調整なし**
  ```kotlin
  ❌ 「見た目が良いから」という理由で padding 追加
  ✅ Figma仕様のpadding のみ
  ```

**配点**：
- 未承認要素なし: 10点

---

## 準拠率スコアカード

### 基本情報

```markdown
## Compliance Scorecard

### Component: [ComponentName]
### Node ID: [node-id]
### Generated: [timestamp]
### Evaluated By: [evaluator]
```

### 詳細スコア

```markdown
#### 1. Color準拠: XX / 30点

| 項目 | Figma仕様 | Compose実装 | 一致 | 配点 | 獲得点 |
|------|----------|------------|------|------|--------|
| 背景色 | rgba(245,245,245,1.0) | Color(0xFFF5F5F5) | ✅ | 5 | 5 |
| タイトル色 | rgba(51,51,51,1.0) | Color(0xFF333333) | ✅ | 5 | 5 |
| アクセント色 | rgba(0,116,196,1.0) | Color(0xFF0074C4) | ✅ | 5 | 5 |
| メタ情報色 | rgba(153,153,153,1.0) | Color(0xFF999999) | ✅ | 5 | 5 |
| 命名の適切性 | - | tabActive, titleText等 | ✅ | 10 | 10 |

**小計**: 30 / 30点 (100%)

---

#### 2. Typography準拠: XX / 30点

| 項目 | Figma仕様 | Compose実装 | 一致 | 配点 | 獲得点 |
|------|----------|------------|------|------|--------|
| fontSize (title) | 17px | 17.sp | ✅ | 8 | 8 |
| fontWeight (title) | 700 | FontWeight.Bold | ✅ | 8 | 8 |
| lineHeight (title) | 1.35 (22.95px) | 22.95.sp | ✅ | 8 | 8 |
| fontFamily (title) | Inter | Inter | ✅ | 6 | 6 |

**小計**: 30 / 30点 (100%)

---

#### 3. Layout準拠: XX / 30点

| 項目 | Figma仕様 | Compose実装 | 一致 | 配点 | 獲得点 |
|------|----------|------------|------|------|--------|
| padding | 20px | 20.dp | ✅ | 6 | 6 |
| gap | 10px | spacedBy(10.dp) | ✅ | 6 | 6 |
| cornerRadius | 4px | RoundedCornerShape(4.dp) | ✅ | 6 | 6 |
| imageSize | 100x76px | size(100.dp, 76.dp) | ✅ | 6 | 6 |
| 魔法の数字排除 | - | LayoutDimensions使用 | ✅ | 6 | 6 |

**小計**: 30 / 30点 (100%)

---

#### 4. バイブコーディング禁止: XX / 10点

| 項目 | チェック内容 | 結果 | 配点 | 獲得点 |
|------|------------|------|------|--------|
| 未承認要素追加 | Figma未指定の角丸/サイズ変更なし | ✅ | 10 | 10 |

**小計**: 10 / 10点 (100%)
```

### 総合スコア

```markdown
## Overall Compliance Score

### Total: 100 / 100点 (100%)

#### カテゴリ別
- Color準拠: 30 / 30点 (100%)
- Typography準拠: 30 / 30点 (100%)
- Layout準拠: 30 / 30点 (100%)
- バイブコーディング禁止: 10 / 10点 (100%)

### 判定
✅ **EXCELLENT** (95%以上)
⚠️ **GOOD** (80%以上95%未満) - 要改善
❌ **POOR** (80%未満) - 再実装推奨
```

## Before/After比較

### Before（口頭指示）

```markdown
### Before: 口頭指示による実装

指示: "マイリスト画面のArticleCardを作って"

#### 生成されたコード（抜粋）
```kotlin
Card(
    shape = RoundedCornerShape(8.dp),  // ❌ 推測（Figmaは4dp）
    colors = CardDefaults.cardColors(
        containerColor = Color(0xFFF0F0F0)  // ❌ 推測（Figmaは0xFFF5F5F5）
    )
) {
    Row(modifier = Modifier.padding(16.dp)) {  // ❌ 推測（Figmaは20dp）
        // ...
        Text(
            text = title,
            fontSize = 16.sp,  // ❌ 推測（Figmaは17sp）
            fontWeight = FontWeight.Medium  // ❌ 推測（FigmaはBold）
        )
    }
}
```

#### 準拠率
- Color準拠: 15 / 30点 (50%)
- Typography準拠: 18 / 30点 (60%)
- Layout準拠: 18 / 30点 (60%)
- バイブコーディング: 5 / 10点 (50%)
- **総合: 56 / 100点 (56%)** ❌ POOR
```

### After（Skillプラグイン使用）

```markdown
### After: /figma-to-compose 使用

指示: `/figma-to-compose https://figma.com/.../node-id=29434-393401`

#### 生成されたコード（抜粋）
```kotlin
Card(
    shape = RoundedCornerShape(4.dp),  // ✅ Figma確認
    colors = CardDefaults.cardColors(
        containerColor = Color(0xFFF5F5F5)  // ✅ Figma rgba(245,245,245,1.0)
    )
) {
    Row(modifier = Modifier.padding(20.dp)) {  // ✅ Figma確認
        // ...
        Text(
            text = title,
            fontSize = 17.sp,  // ✅ Figma確認
            fontWeight = FontWeight.Bold,  // ✅ Figma 700
            lineHeight = 22.95.sp  // ✅ Figma 1.35計算
        )
    }
}
```

#### 準拠率
- Color準拠: 30 / 30点 (100%)
- Typography準拠: 30 / 30点 (100%)
- Layout準拠: 30 / 30点 (100%)
- バイブコーディング: 10 / 10点 (100%)
- **総合: 100 / 100点 (100%)** ✅ EXCELLENT
```

### 改善効果

```markdown
## 改善効果サマリー

| カテゴリ | Before | After | 改善 |
|---------|--------|-------|------|
| Color準拠 | 50% | 100% | +50% |
| Typography準拠 | 60% | 100% | +40% |
| Layout準拠 | 60% | 100% | +40% |
| バイブコーディング禁止 | 50% | 100% | +50% |
| **総合** | **56%** | **100%** | **+44%** |

### 品質向上の定量評価
- 準拠率: 56% → 100% (+44ポイント)
- 判定: POOR → EXCELLENT
- Figma一致項目: 14/25 → 25/25
- 推測による実装: 11箇所 → 0箇所
```

## チェックリスト実施手順

### 1. Figma仕様レポートの作成

```markdown
## Figma Design Specification Report

### Node: ArticleCard (29434-393401)

#### Colors
- backgroundColor: rgba(245,245,245,1.0) → Color(0xFFF5F5F5)
- titleColor: rgba(51,51,51,1.0) → Color(0xFF333333)
...

#### Typography
- titleText: fontSize=17px, fontWeight=700, lineHeight=1.35
...

#### Layout
- padding: 20px
- cornerRadius: 4px
- gap: 10px
...
```

### 2. Composeコードの評価

```markdown
## Implementation Review

### Color評価
- backgroundColor: Color(0xFFF5F5F5) ✅ 一致
- titleColor: Color(0xFF333333) ✅ 一致
...

### Typography評価
- fontSize: 17.sp ✅ 一致
- fontWeight: FontWeight.Bold ✅ 一致 (700)
...

### Layout評価
- padding: 20.dp ✅ 一致
- cornerRadius: 4.dp ✅ 一致
...
```

### 3. スコアカードの生成

```python
# scripts/compliance-calculator.py を使用
python scripts/compliance-calculator.py \
  --figma-spec figma-spec.json \
  --compose-impl ArticleCard.kt \
  --output compliance-report.md
```

### 4. 改善が必要な項目の特定

```markdown
## Improvement Required

### 不一致項目
- [ ] cornerRadius: 8.dp → 4.dp に修正 (Figma仕様)
- [ ] fontSize: 16.sp → 17.sp に修正 (Figma仕様)

### 推定箇所
- [ ] padding値の根拠を明確化（Figmaで再確認）
```

## まとめ

- **定量評価**: 100点満点での評価で客観性を確保
- **カテゴリ別**: Color/Typography/Layout/バイブコーディングを個別評価
- **Before/After**: 口頭指示とスキル使用の効果を明確に比較
- **改善指針**: 不一致項目を明確化し、修正箇所を特定
- **目標**: 95%以上の準拠率を達成

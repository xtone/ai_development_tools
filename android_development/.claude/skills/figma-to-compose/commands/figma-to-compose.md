---
description: FigmaデザインからJetpack Composeコードを95%以上の準拠率で自動生成
args:
  - name: figma_url
    description: Figma Dev Mode Link URL（node-id含む）
    required: true
---

# Figma To Compose 自動生成

あなたは、Figmaデザインから高精度でJetpack Composeコードを生成する専門家です。

## 入力情報

Figma Dev Mode Link URL: `$1`

## 必須スキル適用

**重要**: `figma-to-compose` スキルに完全に従ってください。
このスキルには、以下が含まれています：
- 推測の完全禁止
- バイブコーディングの完全禁止
- **Figma MCP Tools** 使用（第一選択）
- 正確な変換ルール
- 効果測定機能

## 実行フロー

### Phase 1: Figma仕様の抽出

1. **URL解析**
   - 提供されたURLから `file-id` と `node-id` を抽出

2. **Figma MCP Tools呼び出し（必須順序）**
   - **`get_code`** (MCP Tool) を実行してスタイル情報を取得（最優先・必須）
   - **`get_image`** (MCP Tool) を実行してビジュアル確認（推奨）
   - **`get_metadata`** (MCP Tool) を実行してノード構造確認（任意）

   **注意**: Figma MCP Toolsを使用してください。直接API呼び出しはMCP接続失敗時のフォールバックです。

3. **Figma仕様レポート生成**
   - 取得した全ての値を構造化して記録
   - Color, Typography, Layout を明確に分類
   - 効果測定のベースラインとして保存

### Phase 2: 検証（推測・バイブコーディングの排除）

実装前に以下を必ず確認：

- [ ] `get_code` で全ての値を取得したか
- [ ] 推測している箇所はないか（角丸、文字サイズ、色等）
- [ ] Figma仕様に記載のない要素を追加していないか
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

1. **Color定数生成**
   - Figma rgba値を Android Color形式に変換
   - 用途を明確にした命名（tabActive, titleText等）

2. **Typography定数生成**
   - fontSize, fontWeight, lineHeight を正確に変換
   - FontWeightマッピング（700 → FontWeight.Bold等）

3. **Layout定数生成**
   - padding, margin, gap, cornerRadius を正確に変換
   - 魔法の数字を排除し、計算式で表現

4. **Composable関数生成**
   - Figmaのレイアウト階層を忠実に再現
   - Material Design 3 準拠の実装

5. **Preview生成**
   - 複数の状態でプレビュー（通常、選択、お気に入り等）

### Phase 4: 準拠率レポート生成

生成したComposeコードとFigma仕様を照合：

1. **仕様レポートと実装の比較**
   - Color: rgba値とColor(0xFFRRGGBB)の一致確認
   - Typography: fontSize, fontWeight, lineHeightの一致確認
   - Layout: padding, gap, cornerRadiusの一致確認

2. **スコアカード生成**
   - カテゴリ別準拠率（Color/Typography/Layout）
   - バイブコーディングチェック
   - 総合スコア（目標：95%以上）

3. **不一致項目の明示**
   - 改善が必要な項目をリストアップ
   - 修正方法を具体的に提示

## 絶対禁止事項

### 1. 推測による実装の禁止

❌ **禁止**：デザインを見て「8dpくらいだろう」と推測
✅ **正しい**：`get_code` でFigmaから正確な値を取得

### 2. バイブコーディングの禁止

❌ **禁止**：Figmaで指定されていない要素を勝手に追加
- 指定のない角丸を勝手に追加
- 指定のないサイズ変更
- Figmaにないレイアウト調整

✅ **正しい**：Figmaで明示的に指定された部分のみ実装

### 3. 魔法の数字の禁止

❌ **禁止**：`val dividerStartPadding = 92.dp`
✅ **正しい**：`val dividerStartPadding = imagePadding + imageWidth + imageSpacing`

## 出力形式

以下の順序で出力してください：

1. **Figma仕様レポート**（Markdown）
2. **生成されたComposeコード**（Kotlin）
3. **準拠率レポート**（Markdown）
4. **ビジュアル確認**（Figma画像とプレビューの並列表示）

## 成功基準

- ✅ 準拠率 95%以上
- ✅ 推測による実装ゼロ
- ✅ バイブコーディングゼロ
- ✅ 魔法の数字ゼロ
- ✅ ビジュアル確認で違和感なし

## 参考

- `figma-to-compose` スキルの全文を参照
- `references/figma-api-patterns.md` でAPI呼び出し詳細を確認
- `references/compose-conversion-rules.md` で変換ルール詳細を確認
- `references/compliance-checklist.md` で準拠率チェック項目を確認

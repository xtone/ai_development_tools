# Figma MCP Tools & API 呼び出しパターン

## 概要

このドキュメントは、**Figma MCP Tools**を使用してデザイン仕様を取得する際の詳細なパターンとベストプラクティスを提供します。

**重要**: このスキルは **Figma MCP Tools** を第一選択として使用します。直接API呼び出しは、MCP接続失敗時のフォールバックとしてのみ使用してください。

## アプローチの優先順位

### 1. 第一選択: Figma MCP Tools（推奨）

✅ **使用すべき状況**:
- 通常のすべてのケース
- Claude Code環境でFigma MCPが利用可能な場合

✅ **メリット**:
- シンプルな呼び出し（URL指定のみ）
- 自動的なエラーハンドリング
- Claude Code環境に最適化

### 2. フォールバック: 直接API呼び出し（例外的）

⚠️ **使用すべき状況**:
- MCP接続が失敗した場合のみ
- デバッグ・検証目的

⚠️ **デメリット**:
- API Token管理が必要
- エラーハンドリングを手動実装
- より複雑な実装

## Figma API Token（フォールバック用）

**注意**: MCP Tools使用時は不要です。直接API呼び出し時のみ必要。

```bash
# 環境変数でトークンを設定（フォールバック用）
export FIGMA_API_TOKEN="your-figma-api-token"

# 権限: file_content:read (実装に必要な情報は完全取得可能)
```

## URL構造の理解

### Figma Dev Mode Link の構造

```
https://www.figma.com/design/[file-id]/[file-name]?node-id=[node-id]&m=dev

例：
https://www.figma.com/design/abc123/MyDesign?node-id=29434-393401&m=dev

抽出：
- file-id: abc123
- node-id: 29434-393401 (20902-14441 のような形式)
```

### Node ID の特性

- **親要素を指す**：Figma UI上で子要素を選択しても、URLは表示可能な親要素を指す
- **API経由で子要素取得**：親要素から子要素詳細まで一括取得可能
- **結果的に完全**：必要な情報は完全に取得可能

## MCP Tools の使用順序

### 1. get_code（最優先・必須）

**目的**：正確な値とスタイル情報の取得

**使用例**：
```
Tool: get_code
Parameters:
  node_url: https://www.figma.com/design/abc123/MyDesign?node-id=29434-393401
```

**取得できる情報**：
- CSS/Tailwindスタイル
- Color値（rgba形式）
- Typography（fontSize, fontWeight, lineHeight）
- Layout（padding, margin, gap, border-radius）
- レイアウト階層構造

**出力例**：
```css
/* Colors */
background-color: rgba(245,245,245,1.0);
color: rgba(51,51,51,1.0);

/* Typography */
font-family: Inter;
font-size: 17px;
font-weight: 700;
line-height: 1.35;

/* Layout */
padding: 20px;
border-radius: 4px;
gap: 10px;

/* Tailwind Classes */
.rounded-[4px]
.p-5
.gap-2.5
```

### 2. get_image（推奨）

**目的**：ビジュアル確認

**使用例**：
```
Tool: get_image
Parameters:
  node_url: https://www.figma.com/design/abc123/MyDesign?node-id=29434-393401
```

**用途**：
- 実装後のプレビューとの比較
- レイアウト構造の視覚的確認
- 細かい要素の見落とし防止

### 3. get_metadata（任意）

**目的**：ノード構造の概要把握

**使用例**：
```
Tool: get_metadata
Parameters:
  node_url: https://www.figma.com/design/abc123/MyDesign?node-id=29434-393401
```

**用途**：
- 複雑なコンポーネントの階層理解
- 子要素の一覧確認
- ネーミング規則の確認

---

## 直接API呼び出しパターン（MCP失敗時の代替）

**⚠️ 重要**: 以下のセクションは **MCP接続失敗時のフォールバック** としてのみ使用してください。

**通常は上記のFigma MCP Toolsを使用すべきです。**

### 基本的なAPI呼び出し

```bash
# Node情報の取得
curl -H "X-FIGMA-TOKEN: $FIGMA_API_TOKEN" \
  -s "https://api.figma.com/v1/files/[file-id]/nodes?ids=[node-id]" | jq '.'

# 例
curl -H "X-FIGMA-TOKEN: $FIGMA_API_TOKEN" \
  -s "https://api.figma.com/v1/files/abc123/nodes?ids=29434-393401" | jq '.'
```

### レスポンス構造

```json
{
  "nodes": {
    "29434-393401": {
      "document": {
        "id": "29434:393401",
        "name": "ArticleCard",
        "type": "FRAME",
        "children": [...],
        "backgroundColor": {
          "r": 0.96,
          "g": 0.96,
          "b": 0.96,
          "a": 1
        },
        "absoluteBoundingBox": {
          "x": 100,
          "y": 200,
          "width": 375,
          "height": 120
        },
        "cornerRadius": 4,
        "paddingLeft": 10,
        "paddingRight": 10,
        "paddingTop": 20,
        "paddingBottom": 20,
        "itemSpacing": 10,
        "fills": [...],
        "strokes": [...],
        "effects": [...],
        "style": {
          "fontSize": 17,
          "fontWeight": 700,
          "lineHeightPx": 22.95,
          "letterSpacing": 0
        }
      }
    }
  }
}
```

## 値の抽出パターン

### Color抽出

```json
// Figma API Response
"backgroundColor": {
  "r": 0.0,
  "g": 0.4588,
  "b": 0.7686,
  "a": 1.0
}

// 変換
rgba(0, 117, 196, 1.0)

// Compose
Color(0xFF0075C4)
```

**変換式**：
```python
r = int(color["r"] * 255)
g = int(color["g"] * 255)
b = int(color["b"] * 255)
a = int(color["a"] * 255)

compose_color = f"Color(0x{a:02X}{r:02X}{g:02X}{b:02X})"
```

### Typography抽出

```json
// Figma API Response
"style": {
  "fontSize": 17,
  "fontWeight": 700,
  "lineHeightPx": 22.95,
  "fontFamily": "Inter",
  "letterSpacing": 0
}

// Compose
TextStyle(
    fontSize = 17.sp,
    fontWeight = FontWeight.Bold,
    lineHeight = 22.95.sp,
    fontFamily = FontFamily.SansSerif,
    letterSpacing = 0.sp
)
```

### Layout抽出

```json
// Figma API Response
"paddingLeft": 10,
"paddingRight": 10,
"paddingTop": 20,
"paddingBottom": 20,
"itemSpacing": 10,
"cornerRadius": 4,
"absoluteBoundingBox": {
  "width": 375,
  "height": 120
}

// Compose
.padding(
    start = 10.dp,
    end = 10.dp,
    top = 20.dp,
    bottom = 20.dp
)
.size(width = 375.dp, height = 120.dp)
Arrangement.spacedBy(10.dp)
RoundedCornerShape(4.dp)
```

## 値が不明確な場合の対処

### 1. 親要素から再取得

```bash
# より大きなコンポーネントや親要素のnode-idで再度取得
# 例：個別要素が不明な場合、親Frameを取得
```

### 2. 複数node-idの同時取得

```bash
# カンマ区切りで複数指定可能
curl -H "X-FIGMA-TOKEN: $FIGMA_API_TOKEN" \
  -s "https://api.figma.com/v1/files/[file-id]/nodes?ids=node1,node2,node3"
```

### 3. ユーザーへの確認

```
Figmaで[要素名]の[プロパティ]が確認できませんでした。
以下のいずれかをお選びください：
1. Figmaで該当箇所を確認して値を教えてください
2. この要素は実装しない（Figma仕様外のため）
3. デフォルト値を使用（Material Design 3準拠）
```

## トラブルシューティング

### Q: MCP接続が失敗する

```bash
# MCP接続確認（Failed to connectでも問題なし）
claude mcp list

# 直接API アクセスで代替
curl -H "X-FIGMA-TOKEN: $FIGMA_API_TOKEN" \
  -s "https://api.figma.com/v1/files/[file-id]"
```

### Q: node-idが見つからない

```
エラー: 404 Not Found

原因：
1. file-idが間違っている
2. node-idのフォーマットが間違っている（ハイフン必須）
3. アクセス権限がない

対策：
1. URLを再確認
2. node-id形式を確認（例：29434-393401）
3. Figmaファイルの共有設定を確認
```

### Q: 色変換の不正確性

```kotlin
// ❌ 目視での近似値
val primaryColor = Color(0xFF0066CC)

// ✅ Figma仕様の正確な反映
val primaryColor = Color(0xFF0074C4) // rgba(0,116,196,1.0)から変換
```

### Q: フォント設定の不整合

```kotlin
// ❌ 推測値
fontSize = 16.sp,
fontWeight = FontWeight.Medium

// ✅ Figma仕様
fontSize = 17.sp, // Figma fontSize値
fontWeight = FontWeight.Bold // Figma fontWeight: 700
```

## ベストプラクティス

### 1. 必ず Figma MCP Tools の `get_code` から開始

**重要**: Figma MCP Toolsを使用してください。

```
手順：
1. get_code (MCP Tool) でスタイル情報取得（必須）
2. 値を記録（Figma仕様レポート作成）
3. get_image (MCP Tool) でビジュアル確認（推奨）
4. 不明点があれば再度 get_code (MCP Tool) で確認
5. ⚠️ MCP接続失敗時のみ直接API呼び出しにフォールバック
```

### 2. レスポンスの完全な記録

```markdown
## Figma API Response Record

### Node: ArticleCard (29434-393401)
### API Call: 2025-11-10 15:30:00

#### Raw Response
[Full JSON response]

#### Extracted Values
- backgroundColor: rgba(245,245,245,1.0)
- fontSize: 17px
- fontWeight: 700
- padding: 10px
- cornerRadius: 4px
```

### 3. 段階的な確認

```
Phase 1: Color抽出 → 確認
Phase 2: Typography抽出 → 確認
Phase 3: Layout抽出 → 確認
Phase 4: Compose生成 → 確認
```

## まとめ

- **Figma MCP Tools が第一選択**：`get_code` で実装に必要な値をほぼ全て取得可能
- **MCP優先、直接APIはフォールバック**：MCP接続失敗時のみ直接API呼び出しを使用
- **値の記録**：効果測定のため、全てのFigma値を記録
- **段階的確認**：各フェーズで値の正確性を確認
- **推測禁止**：必ずFigma MCP Toolsまたは直接APIから正確な値を取得

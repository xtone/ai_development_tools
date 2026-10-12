# Figma MCP を使った実装サンプルログ

## 概要
Claude Code で Figma MCP (Model Context Protocol) を使い、FigmaデザインからFlutter UIを実装した際の実際の会話ログです。

---

## 1. ユーザーのプロンプト

```
今のブランチにて、 @lib/ui/reservation/widgets/use_start_preparation_page.dart  のデザインを下記の様に変えてほしいです。

仕様として変更は以下のとおりです。

- 画面下部固定の「利用開始」ボタンの活性化条件は以下の通り
  - チェックボックスに全てチェックが入ると活性化
  - 元々の画面を最後までスクロールが到達するという条件判定は削除してください。

C4_01-01.利用開始_開錠前
https://www.figma.com/design/6nSnL8VRmxHmbMj0nwCUtq/三井のカーシェアーズ_デザイン（LightMode）?node-id=18364-916699&m=dev

C4_01-02.利用開始_開錠前
https://www.figma.com/design/6nSnL8VRmxHmbMj0nwCUtq/三井のカーシェアーズ_デザイン（LightMode）?node-id=4981-781555&m=dev

一旦利用開始前ので実装計画を立ててもらっていいですか？
```

---

## 2. Claude の応答（Figma MCP ツール呼び出し）

### ステップ1: デザインコンテキストの取得
```
🤖 Claude: Figmaのデザインを確認して、実装計画を立てます。
```

**ツール呼び出し 1: `get_design_context`**
```json
{
  "nodeId": "18364:916699",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

**ツール呼び出し 2: `get_design_context`**
```json
{
  "nodeId": "4981:781555",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

### ステップ2: スクリーンショットの取得
**ツール呼び出し 3: `get_screenshot`**
```json
{
  "nodeId": "18364:916699",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

**ツール呼び出し 4: `get_screenshot`**
```json
{
  "nodeId": "4981:781555",
  "clientLanguages": "dart",
  "clientFrameworks": "flutter"
}
```

---

## 3. Figma MCPから取得される情報

`get_design_context` ツールは以下のような情報を返します：

- **レイアウト情報**: 要素の配置、サイズ、パディング、マージン
- **色情報**: 背景色、テキスト色（HEXコード）
- **タイポグラフィ**: フォントサイズ、フォントウェイト、行間
- **コンポーネント構造**: 親子関係、コンテナ構造
- **Flutter/Dartに特化した情報**: 使用言語・フレームワークを指定すると最適化された情報

`get_screenshot` ツールは：
- 指定したnodeIdのスクリーンショット画像を返す
- Claudeがビジュアル的にデザインを確認できる

---

## 4. Claude による実装計画の作成

```
🤖 Claude: デザインとコードベースの構造を把握しました。計画を作成します。
```

### 生成された実装計画

```markdown
# use_start_preparation_page.dart チェックリスト追加計画

## 概要
利用開始前の出発準備画面にチェックボックスセクションを追加し、
ボタン活性化条件をスクロール位置判定からチェックボックス全チェックに変更する。
また、STEP 1-4のご利用ガイドをアコーディオン（ExpansionTile）で折りたたみ可能にする。

## 変更ファイル
- lib/ui/reservation/widgets/use_start_preparation_page.dart
- lib/domain/constants/dictionary_ids.dart

## 変更内容

### 1. スクロール判定ロジックの削除
- scrollControllerのスクロール位置リスナーを削除
- isButtonEnabledのスクロール位置による制御を削除

### 2. チェックボックス状態管理の追加
- 3つのチェックボックス用にuseState<bool>を3つ追加
- ボタン活性化条件: check1.value && check2.value && check3.value

### 3. チェックセクションUIの追加
Figmaデザインに基づき以下を追加:
- 説明文
- 注意文（赤色）: ※チェックをすることで利用開始ボタンが有効になります
- チェックボックスコンテナ（背景色: #e5ecf5、角丸8px）
  1. ☐ 予約者以外が運転する際は、利用開始前に運転者交代を申請。
  2. ☐ 万が一、予約時間終了までに戻れない場合はサポートセンターに連絡。
  3. ☐ 返却時、給油残量が半分以下の場合は車内の給油カードにて給油。

### 4. ご利用ガイドのアコーディオン化
- 既存のSTEP 1-4をExpansionTileで囲む
- デフォルトは折りたたみ状態
```

---

## 5. Figma MCP の利点

1. **デザイン情報の自動取得**: FigmaのURLからnode-idを抽出し、レイアウト・色・フォント情報を自動取得
2. **言語/フレームワーク最適化**: `clientLanguages`と`clientFrameworks`を指定することで、Flutter/Dartに最適化された情報を取得
3. **視覚的確認**: スクリーンショットを取得してClaude が視覚的にデザインを確認
4. **正確な実装**: 色コード（例: `#e5ecf5`）やサイズを正確に取得し、デザイン通りの実装が可能

---

## 6. MCP サーバー設定例

`~/.claude/claude_desktop_config.json` または Claude Code の MCP 設定:

```json
{
  "mcpServers": {
    "figma-dev-mode-mcp-server": {
      "command": "npx",
      "args": ["-y", "figma-dev-mode-mcp-server"],
      "env": {
        "FIGMA_ACCESS_TOKEN": "your-figma-access-token"
      }
    }
  }
}
```

---

## 7. 使用可能なFigma MCPツール

| ツール名 | 説明 |
|---------|------|
| `get_design_context` | 指定したnodeのデザイン情報（レイアウト、色、フォント等）を取得 |
| `get_screenshot` | 指定したnodeのスクリーンショットを取得 |
| `get_node` | Figmaファイルの特定ノードの詳細情報を取得 |

---

## まとめ

Figma MCPを使うことで：
- **プロンプト**: FigmaのURLを貼り付けて変更内容を説明するだけ
- **Claude**: 自動でデザイン情報を取得し、コードベースを確認して実装計画を作成
- **結果**: デザイン通りの正確なUI実装が可能

セッションID: `395116d6-75b2-46f2-861f-76ddbbcc16d5`
日時: 2026-01-29

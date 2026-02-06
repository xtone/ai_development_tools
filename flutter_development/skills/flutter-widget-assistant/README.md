# Flutter Widget Assistant

Flutter Widget実装のためのインタラクティブなアシスタントです。構造化された質問を通じて、最適なWidgetアーキテクチャを決定します。

## 主な機能

- 状態管理の必要性を判断（StatefulWidget vs StatelessWidget）
- Widget種別の決定（Screen vs Component）
- 状態共有の判断（Riverpod使用 vs 不使用）
- 構造化された実装仕様書の生成
- Flutter/AutoRoute/Riverpod のベストプラクティスに基づいた設計支援

## 使い方

### 起動方法

```bash
# Claude Codeで以下を実行
/skill flutter-widget-assistant

# または直接説明と共に
"ログイン画面を実装したいです。設計を手伝ってください。"
```

### インタビューに回答

アシスタントが3つの重要な質問を順番に行います：

1. **状態管理の必要性** → StatefulWidget / StatelessWidget
2. **Widget種別** → 画面/ページ / コンポーネント/部品
3. **画面間の状態共有** → Riverpod使用 / 不使用

### 実装仕様書の取得

アシスタントが構造化された仕様書を生成します。仕様書には以下が含まれます：

- Widget情報（名前、説明）
- アーキテクチャの決定事項
- 実装チェックリスト
- コード構造テンプレート

### 実装の実行

```bash
"この仕様書に基づいてLoginScreenを実装してください"
```

## 使用例

### 例1: シンプルなボタンコンポーネント

```
User: "カスタムボタンコンポーネントを作りたいです"
Assistant: "了解しました。いくつか質問させてください。"

Q1: 状態管理 → "いいえ（クリック時のコールバックのみ）"
Q2: Widget種別 → "コンポーネント"
Q3: 状態共有 → "いいえ"

結果: StatelessWidget（props駆動のシンプルなコンポーネント）
```

### 例2: ログイン画面

```
User: "ログイン画面を実装したいです"
Assistant: "了解しました。いくつか質問させてください。"

Q1: 状態管理 → "はい（フォーム入力、バリデーション）"
Q2: Widget種別 → "画面"
Q3: 状態共有 → "はい（認証状態を他の画面でも使用）"

結果: HooksConsumerWidget + AutoRoute + ViewModel + UIState + Riverpod
```

### 例3: カウンターウィジェット

```
User: "カウンターウィジェットを作りたいです"
Assistant: "了解しました。いくつか質問させてください。"

Q1: 状態管理 → "はい（カウンター値）"
Q2: Widget種別 → "コンポーネント"
Q3: 状態共有 → "いいえ（ローカル状態のみ）"

結果: StatefulWidget（ローカル状態管理のシンプルなコンポーネント）
```

## 技術スタック

- **フレームワーク:** Flutter
- **ナビゲーション:** AutoRoute
- **状態管理:** Riverpod（オプション）
- **フック:** flutter_hooks（オプション）
- **アーキテクチャ:** MVVM（画面レベル）

<style>
table {
  width: 100%;
}
</style>

# 画面定義書: {画面名}

## 基本情報

- **画面ID**: {画面を識別するID}
- **画面名**: {画面の名称}
- **ファイルパス**: `{ファイルパス}`
- **最終更新日**: {YYYY-MM-DD}

<!-- SECTION: screenshot -->
## 画面スクリーンショット

<!-- 単一画像の場合 -->
| 画面全体 |
|:--:|
| <img src="../screenshots/{screen_name}_page/overview.png" alt="画面全体" width="300"> |

<!-- 複数画像の場合（最大4列、5枚以上は行を追加）
| 通常状態 | 状態A | 状態B |
|:--:|:--:|:--:|
| <img src="../screenshots/{screen_name}_page/overview.png" alt="通常状態" width="250"> | <img src="../screenshots/{screen_name}_page/state_a.png" alt="状態A" width="250"> | <img src="../screenshots/{screen_name}_page/state_b.png" alt="状態B" width="250"> |
-->

<!-- 縦長画面の分割表示（2スクロール分以上の画面）
### 通常状態

| ヘッダー部 | 詳細情報部 | アクション部 |
|:--:|:--:|:--:|
| <img src="../screenshots/{screen_name}_page/header.png" alt="ヘッダー部" width="250"> | <img src="../screenshots/{screen_name}_page/detail.png" alt="詳細情報部" width="250"> | <img src="../screenshots/{screen_name}_page/action.png" alt="アクション部" width="250"> |

### {バリエーション名}（{該当部分}）

| {状態名} |
|:--:|
| <img src="../screenshots/{screen_name}_page/{variation}.png" alt="{状態名}" width="300"> |
-->
<!-- /SECTION: screenshot -->

<!-- SECTION: display_items -->
## 表示項目

| 番号 | 要素名 | 表示条件 | テキスト取得元 | 備考 |
|------|--------|---------|---------------|------|
| 1    |        |         |               |      |
| 2    |        |         |               |      |
| 3    |        |         |               |      |
<!-- /SECTION: display_items -->

<!-- SECTION: event_items -->
## イベント項目

| 番号 | トリガー名 | 発火条件 | アクション内容 | 遷移先 | API | 備考 |
|------|----------|---------|---------------|--------|-----|------|
| 1    |          |         |               |        |     |      |
| 2    |          |         |               |        |     |      |
| 3    |          |         |               |        |     |      |
<!-- /SECTION: event_items -->

<!-- SECTION: navigation_events -->
## 本画面遷移時のイベント

| 番号 | イベント概要 | 内容 | API | 備考 |
|------|------------|------|-----|------|
| 1    |            |      |     |      |
| 2    |            |      |     |      |
<!-- /SECTION: navigation_events -->

<!-- SECTION: process_flow -->
## 処理フロー

このセクションでは、API通信や状態変更を伴う主要な処理のフローを記載します。

#### {処理名}

1. {ステップ1}
2. {ステップ2}
3. **成功時**: {成功時の動作}
4. **失敗時**: {失敗時の動作}
<!-- /SECTION: process_flow -->

<!-- SECTION: remarks -->
## 備考

### 画面の特徴
{画面固有の特徴を記載}
- 例: タブ構成、特殊なUI要素、認証状態による表示切り替えなど

### その他の特記事項
{その他に記載すべき情報があれば追加}
<!-- /SECTION: remarks -->

---

## ファイル配置ガイド

このテンプレートを使用する際は、以下のようなディレクトリ構造で管理してください：

```
docs/
└── screen_specs/
    ├── template.md  # このファイル
    ├── {module_name}/  # 例: map, reservation, notification など
    │   ├── documents/
    │   │   └── {screen_name}_page.md  # 実際の画面定義書
    │   └── screenshots/
    │       └── {screen_name}_page/  # 画面ごとのスクリーンショット
    │           ├── overview.png  # 画面全体
    │           └── state_example.png  # 特定の状態
```

## 記入のヒント

### スクリーンショット

スクリーンショットはテーブル形式で記載します。ヘッダー行にキャプション、データ行に画像を配置します。

#### 単一画像の場合
```markdown
| 画面全体 |
|:--:|
| <img src="../screenshots/{screen_name}_page/overview.png" alt="画面全体" width="300"> |
```
- `width="300"` で幅を300pxに指定
- キャプションは「画面全体」をデフォルトとする

#### 複数画像の場合（最大4列）
```markdown
| 通常状態 | ログイン後 | エラー時 |
|:--:|:--:|:--:|
| <img src="..." width="250"> | <img src="..." width="250"> | <img src="..." width="250"> |
```
- 複数画像の場合は `width="250"` 推奨
- 最大4列まで横並び可能
- 5枚以上の場合は行を追加して対応

#### 縦長画面の分割表示（2スクロール分以上の画面）

縦に長い画面は、分割して横に並べて表示します。

**キャプションの命名:**
- 優先: 画面の内容に基づいた名前（例：「ヘッダー部」「クルマ情報部」「アクション部」）
- 代替: 位置ベースの名前（「上部」「中部」「下部」）

**通常状態の分割表示:**
```markdown
### 通常状態

| ヘッダー部 | 詳細情報部 | アクション部 |
|:--:|:--:|:--:|
| <img src="..." width="250"> | <img src="..." width="250"> | <img src="..." width="250"> |
```

**バリエーションがある場合（通常状態の下にセクションを追加）:**
```markdown
### エラー時（アクション部）

| エラー表示 |
|:--:|
| <img src="..." width="300"> |
```

### 表示項目テーブル

#### テキスト取得元
- APIレスポンスやアプリ内保持データの場合: 「アプリ内保持: {API名} APIから取得した{説明}（{フィールドパス}から抽出）」
  - **API名はPascalCase形式**（例: GetUserInfo, Login, RetrieveList）
  - 例: 「アプリ内保持: Login APIから取得したユーザー名（output.user.nameから抽出）」
- 固定値の場合は「固定値」または「ハードコード」
- その他の場合は「-」

### イベント項目テーブル

#### 遷移先
- 遷移先の画面名とファイル名を記載
- 形式: 「画面名<br>(ファイル名.dart)」
- 遷移しない場合は「-」または空欄

#### 備考
- **重要**: 非エンジニア向けに分かりやすく記載
- 技術的なメソッド名やコードは避け、一般的な言葉で説明

### 処理フロー

#### いつ記載すべきか
- API通信を伴う処理
- 3ステップ以上の処理
- 成功と失敗で異なる動作をする処理
- エラーハンドリングが重要な処理

#### 記載方法
- 見出しは #### (レベル4) を使用
- 番号付きリストで手順を記載
- **成功時** と **失敗時** を太字で明示

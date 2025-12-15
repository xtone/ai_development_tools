---
name: screen-spec-generator
description: |
  Flutterプロジェクトの画面定義書（screen specification）を作成・管理するスキル。

  以下のような発言で発動します：
  - 「画面定義書を作成したい」「screen specを生成」「画面仕様書を書きたい」
  - 「画面定義書の環境をセットアップ」「screen specを導入したい」
  - 「〇〇画面の定義書を作って」「〇〇ページのspec」
  - 「画面の仕様をドキュメント化したい」

  このスキルは：
  1. プロジェクト構造を自動解析して確認
  2. 必要なセクションを会話で選択
  3. テンプレートとカスタムコマンドを生成
  4. 個別の画面定義書を生成
  することができます。
---

# 画面定義書ジェネレーター スキル

このスキルは、Flutterプロジェクトにおける画面定義書の作成環境をセットアップし、個別の画面定義書を生成する機能を提供します。

## 動作モード

このスキルには2つの動作モードがあります：

### モード1: 初期セットアップ（環境が未構築の場合）

プロジェクトに `docs/screen_specs/template.md` が存在しない場合、セットアップモードで動作します。

### モード2: 画面定義書生成（環境構築済みの場合）

プロジェクトに `docs/screen_specs/template.md` が存在する場合、生成モードで動作します。

---

## モード1: 初期セットアップの手順

### ステップ1: プロジェクト解析

まず、プロジェクトの構造を解析します。

#### CLAUDE.md がある場合

1. CLAUDE.md を読み込み、以下の情報を取得：
   - フレームワーク（Flutter）
   - 状態管理（Riverpod, BLoC, Provider等）
   - ルーティングライブラリ（auto_route, go_router等）
   - アーキテクチャパターン

2. 具体的なパス構造を自動解析：
   - UI層のパス（`lib/ui/`, `lib/presentation/` など）
   - ViewModel/Stateのパス
   - ルーターファイルの場所
   - API定義の場所

3. 解析結果を簡潔に確認：
   ```
   「CLAUDE.mdを確認しました。Flutter + Riverpod + auto_route のプロジェクトですね。

   プロジェクト構造を解析したところ、以下のようになっています：
   - UI層: lib/ui/{module}/widgets/
   - ViewModel: lib/ui/{module}/view_models/
   - ルーター: lib/routing/routes/app_router.dart

   この認識で合っていますか？」
   ```

#### CLAUDE.md がない場合

1. pubspec.yaml を読み込み、以下を検出：
   - フレームワーク（flutter SDK）
   - 状態管理（flutter_riverpod, flutter_bloc, provider等）
   - ルーティング（auto_route, go_router等）
   - HTTP通信（dio, retrofit, http等）

2. ディレクトリ構造を解析：
   ```bash
   # UI層を探索
   ls lib/ui/ または lib/presentation/ または lib/features/

   # ルーターファイルを探索
   find lib -name "*router*.dart"

   # API定義を探索
   find lib -name "*api*.dart"
   ```

3. 検出結果をすべてユーザーに確認：
   ```
   「画面定義書の作成をお手伝いします。
   プロジェクトの構造を解析しました。

   pubspec.yaml から以下を検出しました：
   - フレームワーク: Flutter
   - 状態管理: flutter_riverpod
   - ルーティング: auto_route

   ディレクトリ構造から以下を推測しました：
   - UI層: lib/ui/{module}/widgets/
   - ViewModel: lib/ui/{module}/view_models/
   - ルーター: lib/routing/routes/app_router.dart

   この認識で合っていますか？修正点があれば教えてください。」
   ```

### ステップ2: セクション選択

画面定義書に含めるセクションを会話で選択します。

```
「では、画面定義書に含めるセクションを選びましょう。
デフォルトは以下の通りです：

1. ✅ 基本情報（必須）- 画面ID、画面名、ファイルパス、最終更新日
2. ✅ スクリーンショット - 画面キャプチャの配置領域
3. ✅ 表示項目 - 静的な表示要素の一覧
4. ✅ イベント項目 - ユーザー操作によるイベント
5. ⬜ 本画面遷移時イベント - 画面表示時の自動イベント
6. ⬜ 処理フロー - API通信等の詳細フロー
7. ✅ 備考 - 特記事項

変更したい項目はありますか？」
```

### ステップ3: カスタマイズ確認

```
「他に追加したいセクションや、テーブルの列をカスタマイズしたい点はありますか？

例：
- イベント項目に analytics 列を追加
- 表示項目にデザイントークン列を追加
- 独自のセクションを追加
」
```

### ステップ4: ファイル生成

確認が完了したら、以下のファイルを生成します：

1. `.claude/commands/screen-spec.md` - カスタムコマンド
2. `docs/screen_specs/template.md` - テンプレート
3. `docs/screen_specs/README.md` - 使い方ガイド

```
「以下のファイルを生成しました：
- .claude/commands/screen-spec.md
- docs/screen_specs/template.md
- docs/screen_specs/README.md

これで `/screen-spec lib/ui/xxx/widgets/xxx_page.dart` で
画面定義書を生成できるようになりました。」
```

---

## モード2: 画面定義書生成の手順

### 前提条件

- `docs/screen_specs/template.md` が存在すること
- `.claude/commands/screen-spec.md` が存在すること

### 生成方法

ユーザーが以下のように発言した場合：
- 「〇〇画面の定義書を作って」
- 「lib/ui/xxx/widgets/xxx_page.dart の画面定義書を生成して」

1. 対象ファイルを特定
2. `docs/screen_specs/template.md` を読み込み
3. `.claude/commands/screen-spec.md` の手順に従って生成

---

## テンプレートファイルの参照

セクション別テンプレートは以下を参照：

- 基本テンプレート: `templates/base_template.md`
- 生成コマンドテンプレート: `templates/screen_spec_command.md`
- 表示項目セクション: `templates/sections/display_items.md`
- イベント項目セクション: `templates/sections/event_items.md`
- 本画面遷移時イベントセクション: `templates/sections/navigation_events.md`
- 処理フローセクション: `templates/sections/process_flow.md`

---

## 注意事項

- 既存ファイルを上書きする前に必ずユーザーに確認すること
- プロジェクト固有の設定（辞書DB等）は汎用スキルでは扱わない
- 生成される定義書は日本語で出力

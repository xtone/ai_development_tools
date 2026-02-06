---
name: screen-spec-generator
description:
  Flutterプロジェクトの画面定義書（screen specification）を作成・管理するスキル。
---

# 画面定義書ジェネレーター スキル

このスキルは、Flutterプロジェクトにおける画面定義書の作成環境をセットアップし、個別の画面定義書を生成・更新する機能を提供します。

## 発動トリガー

以下のような発言で発動します：
- 「画面定義書を作成したい」「screen specを生成」「画面仕様書を書きたい」
- 「画面定義書の環境をセットアップ」「screen specを導入したい」
- 「〇〇画面の定義書を作って」「〇〇ページのspec」
- 「画面の仕様をドキュメント化したい」
- 「画面定義書を更新して」「定義書を最新化」

## 機能概要

このスキルは以下を行います：
1. プロジェクト構造を自動解析して確認
2. 必要なセクションを会話で選択
3. テンプレートとカスタムコマンドを生成
4. 個別の画面定義書を生成
5. 既存の画面定義書を差分検出して更新

## 重要: 会話の進め方

**各ステップで必ずユーザーの回答を待ってから次のステップに進むこと。**

- ステップ1で質問したら、ユーザーの回答を待つ
- ユーザーが回答したら、次のステップに進む
- 複数の質問を一度にしない

これにより、ユーザーが混乱せず、段階的に設定を進められます。

---

## 動作モード

このスキルには3つの動作モードがあります：

### モード1: 初期セットアップ（環境が未構築の場合）

プロジェクトに `docs/screen_specs/template.md` が存在しない場合、セットアップモードで動作します。

### モード2: 画面定義書生成（環境構築済み、定義書未作成の場合）

プロジェクトに `docs/screen_specs/template.md` が存在し、対象画面の定義書が存在しない場合、新規生成モードで動作します。

### モード3: 画面定義書更新（定義書が既に存在する場合）

対象画面の定義書が既に存在する場合、更新モードで動作します。コードを再解析し、差分を検出してユーザーに提示します。

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

4. **ここでユーザーの回答を待つ。次のステップに進まない。**

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

   ※ Claude Codeの場合は、Bashコマンドではなく専用ツール（Glob, Grep等）の使用を推奨します。

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

4. **ここでユーザーの回答を待つ。次のステップに進まない。**

### ステップ2: セクション選択

**ステップ1でユーザーが「はい」「OK」などと回答したら、このステップに進む。**

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

**ここでユーザーの回答を待つ。次のステップに進まない。**

### ステップ3: カスタマイズ確認

**ステップ2でユーザーが回答したら、このステップに進む。**

```
「他に追加したいセクションや、テーブルの列をカスタマイズしたい点はありますか？

例：
- イベント項目に analytics 列を追加
- 表示項目にデザイントークン列を追加
- 独自のセクションを追加
」
```

**ここでユーザーの回答を待つ。次のステップに進まない。**

### ステップ4: ファイル生成

**ステップ3でユーザーが回答したら、このステップに進む。**

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
画面定義書を生成できるようになりました。

是非、実際に1つ画面定義書を作成してみてください。
作成後、修正点があったら教えてください。」
```

---

## モード2: 画面定義書生成の手順

### 前提条件

- `docs/screen_specs/template.md` が存在すること
- `.claude/commands/screen-spec.md` が存在すること
- 対象画面の定義書が存在しないこと

### 生成方法

ユーザーが以下のように発言した場合：
- 「〇〇画面の定義書を作って」
- 「lib/ui/xxx/widgets/xxx_page.dart の画面定義書を生成して」

1. 対象ファイルを特定
2. `docs/screen_specs/template.md` を読み込み
3. `.claude/commands/screen-spec.md` の手順に従って生成

---

## モード3: 画面定義書更新の手順

### 前提条件

- 対象画面の定義書が既に存在すること

### 更新方法

ユーザーが以下のように発言した場合：
- 「〇〇画面の定義書を更新して」
- `/screen-spec lib/ui/xxx/widgets/xxx_page.dart`（既存ファイルに対して）

1. 既存の定義書をパース
2. コードを再解析
3. 差分を検出（追加・削除・変更）
4. 差分をユーザーに提示
5. 確認後、定義書を更新
6. HTML版も同期更新

### 強制新規作成

既存の定義書を無視して新規作成したい場合：
```
/screen-spec lib/ui/xxx/widgets/xxx_page.dart --new
```

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
- 更新モードでは差分を必ずユーザーに提示し、確認を取ること

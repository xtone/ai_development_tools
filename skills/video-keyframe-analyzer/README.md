# Video Keyframe Analyzer

動画からキーフレームを抽出してClaude Codeで分析するスキル。

## 概要

通常、5秒の動画を全フレーム（30fps）でClaudeに読み込ませると約450円かかりますが、このスキルを使うことで**約24円（93%削減）**まで削減できます。

### コスト削減の仕組み

1. **差分検出**: フレーム間の変化が大きい部分のみを抽出
2. **画質調整**: 画像サイズを1/2に縮小、JPEG品質を50%に設定
3. **最適化**: 最大20フレームまでに制限

| 方法 | フレーム数 | コスト |
|-----|-----------|--------|
| 全フレーム（30fps、5秒） | 150枚 | 約450円 |
| キーフレーム抽出 | 8-10枚 | 約24-30円 |

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. スキルの登録

```bash
# プロジェクトディレクトリから実行
ln -s $(pwd)/skills/video-keyframe-analyzer \
      ~/.claude/skills/video-keyframe-analyzer
```

## 使い方

### Claude Codeでの使用

```
/video-keyframe-analyzer

画面遷移の動画を分析したい。
動画: ~/Downloads/screen_recording.mp4
```

### コマンドラインでの直接実行

```bash
# 基本的な使い方
python extract_keyframes.py screen_recording.mp4

# パラメータをカスタマイズ
python extract_keyframes.py video.mp4 \
  --threshold 40 \      # 変化が大きいフレームのみ抽出
  --quality 60 \        # 画質を上げる
  --max-frames 15       # 最大フレーム数を制限
```

### パラメータ

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| `--threshold` | 30 | 差分閾値（0-255）。大きいほど変化が大きいフレームのみ抽出 |
| `--quality` | 50 | JPEG品質（0-100）。低いほどファイルサイズ小 |
| `--max-frames` | 20 | 最大抽出フレーム数 |
| `--resize-ratio` | 0.5 | リサイズ比率（0.5で半分のサイズ） |
| `--output-dir` | /tmp/claude-code-video | 出力ディレクトリ |
| `--timestamps` | - | 特定のタイムスタンプでフレームを抽出（カンマ区切り、例: "0.0,0.5,1.0"） |
| `--ensure-full-coverage` | False | 動画全体のカバレッジを保証（各セグメントから必ず1フレーム抽出） |
| `--with-speech` | False | 音声認識を実行（Whisperを使用） |
| `--speech-model` | base | Whisperモデルサイズ（tiny/base/small/medium） |

## タイムスタンプ指定による抽出

`--timestamps` オプションで、特定のタイミングのフレームを正確に抽出できます。

### 基本的な使い方

```bash
# 特定のタイムスタンプでフレームを抽出
python extract_keyframes.py video.mp4 --timestamps "0.0,0.5,1.0,1.5"

# 画質を上げる
python extract_keyframes.py video.mp4 --timestamps "0.0,1.0,2.0" --quality 70
```

### 推奨される用途

✅ **有効なケース**:
- アニメーション仕様書に記載されたタイミング（例: 0.37秒でワナビー出現）を検証
- 特定のアニメーションポイントを確認
- 仕様動画と実装動画を同じタイミングで比較
- バグが発生する正確なタイミングを確認

### 使用例

```bash
# アニメーション仕様の検証
python extract_keyframes.py spec_video.mp4 --timestamps "0.0,0.37,0.57,0.83"

# 実装動画と仕様動画を同じタイミングで比較
python extract_keyframes.py spec.mp4 --timestamps "0.0,0.5,1.0" --output-dir spec_frames/
python extract_keyframes.py impl.mp4 --timestamps "0.0,0.5,1.0" --output-dir impl_frames/

# ロック画面アニメーションの状態遷移を確認
python extract_keyframes.py lock_screen.mp4 --timestamps "0.0,1.69,2.67,4.92,11.7"
```

## 動画全体のカバレッジ保証

`--ensure-full-coverage` オプションで、動画全体から均等にフレームを抽出できます。

### 基本的な使い方

```bash
# 差分閾値に関係なく動画全体からフレームを抽出
python extract_keyframes.py video.mp4 --ensure-full-coverage --max-frames 30

# distributedモードと組み合わせ
python extract_keyframes.py video.mp4 --mode distributed --ensure-full-coverage
```

### 推奨される用途

✅ **有効なケース**:
- フェードイン/フェードアウトなど緩やかな変化のアニメーション
- 変化が小さいUI仕様動画
- 動画の後半部分がスキップされる場合

## 音声認識機能（オプション）

`--with-speech` オプションで、動画の音声も文字起こしして分析できます。

### 基本的な使い方

```bash
# 音声認識を有効化（baseモデル）
python extract_keyframes.py video.mp4 --with-speech

# より高精度なモデルを使用
python extract_keyframes.py video.mp4 --with-speech --speech-model small

# autoモードと組み合わせ
python extract_keyframes.py video.mp4 --with-speech --auto
```

### 初回のみ: モデルダウンロード

初回実行時のみ、Whisperモデルがダウンロードされます：
- `tiny`: 約39MB
- `base`: 約74MB（デフォルト）
- `small`: 約244MB
- `medium`: 約769MB

### 推奨される用途

✅ **有効なケース**:
- ナレーション付きデモ動画
- プレゼンテーション録画
- チュートリアル動画
- 口頭コメント付きUIテスト録画
- デザイナーからの参考動画（音声解説付き）

⚠️ **限界**:
- 一人称視点の動画では、撮影者と話者の特定が困難
- 音声品質に依存（雑音、早口、方言は認識精度が下がる）
- キーフレーム+音声だけでは、人物関係の推測には限界がある

### 出力フォーマット

音声認識を有効にすると、`video_analysis.md`が生成されます：

```markdown
# Video Analysis Report

## 概要
- 動画時間: 36.00秒
- 言語: ja
- 抽出キーフレーム数: 20
- 音声セグメント数: 7

## タイムライン分析
各キーフレームと、その時点での音声内容:

### [1.47s] Frame 1
**視覚情報:**
- 画像: `keyframe_001.jpg`
- 差分値: 305.94

**音声情報:**
> 「おくちみして」
> （0.00s - 2.00s）

## 全文文字起こし
**0.00s - 2.00s**
おくちみして
...
```

Claude Codeで`Read: /tmp/claude-code-video/video_analysis.md`を実行すれば、視覚+音声の統合分析が可能になります。

## 動画の長さ制限

**このスキルは10分以内の動画に最適化されています。**

開発用途（画面操作録画、UIテスト、デモ動画など）を想定した設計です。

### 推奨設定

| 動画の長さ | 推奨max-frames | 処理時間目安 | 用途 |
|-----------|---------------|-------------|------|
| 〜10秒 | 15-20 | 数秒 | 画面遷移バグ検証 |
| 10秒〜1分 | 20-30 | 20-60秒 | UIテスト結果確認 |
| 1-5分 | 30-40 | 1-5分 | E2Eテスト録画 |
| 5-10分 | 40-50 | 5-10分 | 長時間操作録画 |

### 10分以上の動画

処理時間が長くなるため、以下の対応を推奨：
- 必要な部分だけトリミングしてから処理
- 動画を分割して処理

## ユースケース

### 1. 画面遷移のバグ修正

```
/video-keyframe-analyzer

このNavigation Composeの画面遷移で、
中間のフレームが一瞬白くなるバグがあります。
どのフレームで問題が起きているか特定して修正方法を提案してください。

動画: ~/Desktop/navigation_bug.mp4
```

### 2. UIテスト結果の確認

```
/video-keyframe-analyzer

このE2Eテストの実行結果動画から、
期待通りの画面遷移ができているか確認したい。

期待される遷移:
1. ログイン画面
2. ホーム画面
3. 記事一覧
4. 記事詳細

動画: ~/test_results/e2e_test.mp4
```

### 3. デザイン実装の確認

```
/video-keyframe-analyzer

デザイナーから受け取った画面遷移の参考動画と、
現在の実装を比較して、差分を教えてください。

参考動画: ~/design/reference.mp4
実装動画: ~/recordings/current_implementation.mp4
```

### 4. 「ログでは分からない問題」の発見

**実案件での成功事例（DOCOMO AI HOME Issue #303）**

```bash
python extract_keyframes.py ~/Desktop/screen_recording.mp4 \
  --threshold 20 \
  --quality 60 \
  --max-frames 25
```

**課題**:
ユーザーから「カード切り替え時に2回フェードアウトが走る」という報告。
ログでは「Skipping fade-out」と正しく出力されているのに、UIでは問題が再現。

**発見した根本原因**:
動画分析により、以下の問題を視覚的に特定：
1. Frame 9-10: AIメッセージがフェードアウト（意図通り）
2. Frame 11: AIメッセージが消えた状態（修正が効いている）
3. **Frame 12-13: ContentRecommendが再びスケール表示**（これが問題！）
4. Frame 14-15: Ticketカードに収束

→ 「別のコンポーネント（ContentRecommendExpandedContent内のAIメッセージ領域）が原因」と判明

**成果**:
- ログだけでは絶対に分からなかった問題を30分で解決
- 手作業での試行錯誤なら2-3時間かかっていた可能性
- ユーザーの主観的なフィードバック（「違和感がある」）を客観的に分析

## 出力例

```
Video info:
  Duration: 5.23s
  FPS: 30.00
  Total frames: 157
  Threshold: 30
  Max frames: 20

[Frame    1] Keyframe #1 (first frame) -> keyframe_001.jpg
[Frame   15] Keyframe #2 (diff=45.32) -> keyframe_002.jpg
[Frame   28] Keyframe #3 (diff=52.18) -> keyframe_003.jpg
[Frame   42] Keyframe #4 (diff=38.91) -> keyframe_004.jpg
...

Extraction complete!
  Total frames processed: 157
  Keyframes extracted: 9
  Reduction rate: 94.3%
  Output directory: /tmp/claude-code-video
```

## トラブルシューティング

### エラー: python: command not found

macOSやLinuxの一部環境では、`python`コマンドではなく`python3`を使用する必要があります。

```bash
# エラーが出る場合
python extract_keyframes.py video.mp4

# python3を使用
python3 extract_keyframes.py video.mp4
```

### エラー: Required package not found

```bash
# Python 3を使用している場合
pip3 install opencv-python pillow numpy

# または
pip install opencv-python pillow numpy
```

### 抽出されるフレームが多すぎる

`--threshold` を大きくしてください（例: 40-50）

### 抽出されるフレームが少なすぎる

`--threshold` を小さくしてください（例: 15-20）

### 画質が悪い

`--quality` を上げてください（例: 70-80）
※ コストは増加します

## 今後の拡張予定

- [ ] パラメータ設定UI（対話的に調整）
- [ ] プレビュー機能（抽出前に確認）
- [ ] バッチ処理（複数動画を一度に処理）
- [ ] MCP Server化（リアルタイムプレビュー）

## 関連ドキュメント

- プロジェクト概要: `~/.config/claude-code/project-knowledge/ai_development_tools/CONTEXT.md`
- スキル登録ガイド: `~/.config/claude-code/project-knowledge/ai_development_tools/skills/SKILL_REGISTRATION_GUIDE.md`

## ライセンス

MIT

## 作成者

石原正也（2026-01-22）

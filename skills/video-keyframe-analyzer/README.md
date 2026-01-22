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
ln -s /Users/m.ishihara/WS/ai_development_tools/skills/video-keyframe-analyzer \
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

### エラー: Required package not found

```bash
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

- プロジェクト概要: `/Users/m.ishihara/.config/claude-code/project-knowledge/ai_development_tools/CONTEXT.md`
- スキル登録ガイド: `/Users/m.ishihara/.config/claude-code/project-knowledge/ai_development_tools/skills/SKILL_REGISTRATION_GUIDE.md`

## ライセンス

MIT

## 作成者

石原正也（2026-01-22）

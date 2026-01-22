#!/usr/bin/env python3
"""
動画からキーフレームを抽出するスクリプト（改善版）

使い方:
    python extract_keyframes.py <video_path> [options]

例:
    # 自動モード（推奨）
    python extract_keyframes.py screen_recording.mp4 --auto

    # プリセット使用
    python extract_keyframes.py video.mp4 --preset scroll

    # 手動設定
    python extract_keyframes.py video.mp4 --threshold 35 --quality 60 --max-frames 15
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"Error: Required package not found: {e}")
    print("Please install dependencies:")
    print("  pip install opencv-python pillow numpy")
    sys.exit(1)


# パラメータプリセット定義
PRESETS = {
    "scroll": {
        "threshold": 80,
        "quality": 50,
        "max_frames": 15,
        "resize_ratio": 0.5,
        "description": "スクロール動画用（差分が大きいフレームのみ）"
    },
    "ui-transition": {
        "threshold": 40,
        "quality": 50,
        "max_frames": 20,
        "resize_ratio": 0.5,
        "description": "画面遷移用（デフォルト）"
    },
    "high-quality": {
        "threshold": 30,
        "quality": 75,
        "max_frames": 25,
        "resize_ratio": 0.7,
        "description": "高品質分析用（コスト増）"
    },
    "cost-optimize": {
        "threshold": 60,
        "quality": 40,
        "max_frames": 10,
        "resize_ratio": 0.4,
        "description": "コスト最優先（品質低）"
    }
}


def calculate_frame_difference(frame1, frame2):
    """2つのフレーム間の差分を計算（MSE: Mean Squared Error）"""
    # グレースケール変換
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # MSEを計算
    mse = np.mean((gray1.astype(float) - gray2.astype(float)) ** 2)
    return mse


def analyze_video_samples(video_path, sample_count=30):
    """
    動画の最初のサンプルフレームを分析して統計情報を取得

    Args:
        video_path: 動画ファイルのパス
        sample_count: サンプルフレーム数

    Returns:
        差分値のリスト
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    diffs = []
    prev_frame = None
    count = 0

    while cap.isOpened() and count < sample_count:
        ret, frame = cap.read()
        if not ret:
            break

        if prev_frame is not None:
            diff = calculate_frame_difference(prev_frame, frame)
            diffs.append(diff)

        prev_frame = frame
        count += 1

    cap.release()
    return diffs


def auto_adjust_threshold(video_path, sample_count=30):
    """
    動画のサンプルフレームから適切な閾値を自動計算

    Args:
        video_path: 動画ファイルのパス
        sample_count: サンプルフレーム数

    Returns:
        推奨閾値
    """
    diffs = analyze_video_samples(video_path, sample_count)

    if not diffs:
        return 30  # デフォルト値

    # 中央値の30%を閾値に設定
    median_diff = np.median(diffs)
    threshold = max(20, min(100, median_diff * 0.3))

    return threshold


def detect_video_type(video_path, sample_count=30):
    """
    動画の差分パターンから動画タイプを自動判定

    Args:
        video_path: 動画ファイルのパス
        sample_count: サンプルフレーム数

    Returns:
        動画タイプ（"scroll", "transition", "static"）
    """
    diffs = analyze_video_samples(video_path, sample_count)

    if not diffs:
        return "transition"  # デフォルト

    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs)
    max_diff = np.max(diffs)

    # 判定ロジック
    if mean_diff > 800:  # 平均差分が大きい
        return "scroll"
    elif std_diff > 500:  # 標準偏差が大きい（急激な変化）
        return "transition"
    elif max_diff < 100:  # 変化が小さい
        return "static"
    else:
        return "transition"


def extract_keyframes_distributed(video_path, output_dir, quality=50, max_frames=20, resize_ratio=0.5, threshold=None):
    """
    動画を時間軸で均等に分割し、各区間から差分が最大のフレームを抽出

    Args:
        video_path: 動画ファイルのパス
        output_dir: 出力ディレクトリ
        quality: JPEG品質（0-100）
        max_frames: 最大抽出フレーム数
        resize_ratio: リサイズ比率
        threshold: 最小差分閾値（None なら自動）

    Returns:
        抽出されたキーフレームのパスリスト
    """
    # 動画を開く
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video: {video_path}")

    # 出力ディレクトリ作成
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 動画情報
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    # 閾値の自動調整
    if threshold is None:
        threshold = auto_adjust_threshold(video_path)
        print(f"Auto-adjusted threshold: {threshold:.2f}")

    # 動画タイプの自動判定
    video_type = detect_video_type(video_path)
    print(f"Detected video type: {video_type}")

    print(f"\nVideo info:")
    print(f"  Duration: {duration:.2f}s")
    print(f"  FPS: {fps:.2f}")
    print(f"  Total frames: {total_frames}")
    print(f"  Threshold: {threshold:.2f}")
    print(f"  Max frames: {max_frames}")
    print(f"  Extraction mode: Distributed (均等分割)")
    print()

    # 動画を max_frames 個の区間に分割
    segment_size = total_frames // max_frames
    if segment_size < 1:
        segment_size = 1

    keyframe_paths = []
    keyframe_count = 0

    for segment_idx in range(max_frames):
        # 区間の開始・終了フレーム
        start_frame = segment_idx * segment_size
        end_frame = min(start_frame + segment_size, total_frames)

        if start_frame >= total_frames:
            break

        # 区間内で差分が最大のフレームを探す
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        max_diff = -1
        max_diff_frame = None
        max_diff_frame_idx = start_frame
        prev_frame = None

        for frame_idx in range(start_frame, end_frame):
            ret, frame = cap.read()
            if not ret:
                break

            if prev_frame is not None:
                diff = calculate_frame_difference(prev_frame, frame)
                if diff > max_diff:
                    max_diff = diff
                    max_diff_frame = frame.copy()
                    max_diff_frame_idx = frame_idx
            else:
                # 最初のフレーム
                max_diff_frame = frame.copy()
                max_diff_frame_idx = frame_idx
                max_diff = 0

            prev_frame = frame

        # 閾値を超えていれば保存
        if max_diff_frame is not None and (max_diff >= threshold or segment_idx == 0):
            keyframe_count += 1
            output_path = save_frame(max_diff_frame, output_dir, keyframe_count, quality, resize_ratio)
            keyframe_paths.append(output_path)

            timestamp = max_diff_frame_idx / fps if fps > 0 else 0
            print(f"[Frame {max_diff_frame_idx:4d} @ {timestamp:5.2f}s] "
                  f"Keyframe #{keyframe_count} (diff={max_diff:.2f}) -> {output_path.name}")

    cap.release()

    print()
    print(f"Extraction complete!")
    print(f"  Total frames: {total_frames}")
    print(f"  Keyframes extracted: {keyframe_count}")
    print(f"  Reduction rate: {(1 - keyframe_count/total_frames) * 100:.1f}%")
    print(f"  Coverage: {(keyframe_count / max_frames) * 100:.1f}% of target")
    print(f"  Output directory: {output_dir}")

    return keyframe_paths


def extract_keyframes_sequential(video_path, output_dir, threshold=30, quality=50, max_frames=20, resize_ratio=0.5):
    """
    動画から順次キーフレームを抽出（従来の方式）

    Args:
        video_path: 動画ファイルのパス
        output_dir: 出力ディレクトリ
        threshold: 差分閾値
        quality: JPEG品質
        max_frames: 最大抽出フレーム数
        resize_ratio: リサイズ比率

    Returns:
        抽出されたキーフレームのパスリスト
    """
    # 動画を開く
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video: {video_path}")

    # 出力ディレクトリ作成
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 動画情報
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    print(f"Video info:")
    print(f"  Duration: {duration:.2f}s")
    print(f"  FPS: {fps:.2f}")
    print(f"  Total frames: {total_frames}")
    print(f"  Threshold: {threshold}")
    print(f"  Max frames: {max_frames}")
    print(f"  Extraction mode: Sequential (順次)")
    print()

    prev_frame = None
    keyframe_paths = []
    frame_count = 0
    keyframe_count = 0

    while cap.isOpened() and keyframe_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # 最初のフレームは必ず保存
        if prev_frame is None:
            keyframe_count += 1
            output_path = save_frame(frame, output_dir, keyframe_count, quality, resize_ratio)
            keyframe_paths.append(output_path)
            timestamp = frame_count / fps if fps > 0 else 0
            print(f"[Frame {frame_count:4d} @ {timestamp:5.2f}s] "
                  f"Keyframe #{keyframe_count} (first frame) -> {output_path.name}")
            prev_frame = frame
            continue

        # 前フレームとの差分を計算
        diff = calculate_frame_difference(prev_frame, frame)

        # 閾値を超えたらキーフレームとして保存
        if diff > threshold:
            keyframe_count += 1
            output_path = save_frame(frame, output_dir, keyframe_count, quality, resize_ratio)
            keyframe_paths.append(output_path)
            timestamp = frame_count / fps if fps > 0 else 0
            print(f"[Frame {frame_count:4d} @ {timestamp:5.2f}s] "
                  f"Keyframe #{keyframe_count} (diff={diff:.2f}) -> {output_path.name}")
            prev_frame = frame

    cap.release()

    print()
    print(f"Extraction complete!")
    print(f"  Total frames processed: {frame_count}")
    print(f"  Keyframes extracted: {keyframe_count}")
    print(f"  Reduction rate: {(1 - keyframe_count/frame_count) * 100:.1f}%")
    print(f"  Output directory: {output_dir}")

    return keyframe_paths


def save_frame(frame, output_dir, frame_number, quality, resize_ratio):
    """フレームを画質を下げて保存"""
    # BGR -> RGB変換
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # PIL Imageに変換
    img = Image.fromarray(rgb_frame)

    # リサイズ
    if resize_ratio != 1.0:
        new_size = (int(img.width * resize_ratio), int(img.height * resize_ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # 保存
    output_path = output_dir / f"keyframe_{frame_number:03d}.jpg"
    img.save(output_path, "JPEG", quality=quality, optimize=True)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="動画からキーフレームを抽出してコストを削減（改善版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  # 自動モード（推奨）- 動画タイプを自動判定して最適なパラメータを設定
  python extract_keyframes.py screen_recording.mp4 --auto

  # プリセット使用
  python extract_keyframes.py video.mp4 --preset scroll
  python extract_keyframes.py video.mp4 --preset ui-transition
  python extract_keyframes.py video.mp4 --preset high-quality

  # 手動設定
  python extract_keyframes.py video.mp4 --threshold 50 --quality 60

  # 均等分割モード（デフォルト）vs 順次モード
  python extract_keyframes.py video.mp4 --mode distributed
  python extract_keyframes.py video.mp4 --mode sequential

プリセット一覧:
  scroll          - スクロール動画用（閾値高、フレーム数少）
  ui-transition   - 画面遷移用（デフォルト）
  high-quality    - 高品質分析用（コスト増）
  cost-optimize   - コスト最優先（品質低）
        """
    )

    parser.add_argument("video_path", help="動画ファイルのパス")
    parser.add_argument("--output-dir", "-o", default="/tmp/claude-code-video",
                        help="出力ディレクトリ（デフォルト: /tmp/claude-code-video）")

    # 自動モード
    parser.add_argument("--auto", "-a", action="store_true",
                        help="自動モード：動画タイプを判定して最適なパラメータを設定")

    # プリセット
    parser.add_argument("--preset", "-p", choices=list(PRESETS.keys()),
                        help="パラメータプリセット")

    # 手動設定
    parser.add_argument("--threshold", "-t", type=float,
                        help="差分閾値（範囲: 0-255、autoモードでは無視）")
    parser.add_argument("--quality", "-q", type=int,
                        help="JPEG品質（範囲: 0-100）")
    parser.add_argument("--max-frames", "-m", type=int,
                        help="最大抽出フレーム数")
    parser.add_argument("--resize-ratio", "-r", type=float,
                        help="リサイズ比率（1.0で元サイズ）")

    # 抽出モード
    parser.add_argument("--mode", choices=["distributed", "sequential"], default="distributed",
                        help="抽出モード: distributed（均等分割、推奨）/ sequential（順次）")

    args = parser.parse_args()

    # 動画ファイルの存在確認
    if not os.path.exists(args.video_path):
        print(f"Error: Video file not found: {args.video_path}")
        sys.exit(1)

    # パラメータ決定
    params = {
        "threshold": 30,
        "quality": 50,
        "max_frames": 20,
        "resize_ratio": 0.5
    }

    # プリセット適用
    if args.preset:
        preset = PRESETS[args.preset]
        params.update(preset)
        print(f"Using preset: {args.preset}")
        print(f"  {preset['description']}")
        print()

    # 自動モード
    elif args.auto:
        video_type = detect_video_type(args.video_path)
        print(f"Auto mode: Detected video type = {video_type}")

        # 動画タイプに応じたプリセットを適用
        preset_map = {
            "scroll": "scroll",
            "transition": "ui-transition",
            "static": "cost-optimize"
        }
        preset_name = preset_map.get(video_type, "ui-transition")
        preset = PRESETS[preset_name]
        params.update(preset)
        print(f"  Applying preset: {preset_name}")
        print(f"  {preset['description']}")
        print()

    # 手動設定で上書き
    if args.threshold is not None:
        params["threshold"] = args.threshold
    if args.quality is not None:
        params["quality"] = args.quality
    if args.max_frames is not None:
        params["max_frames"] = args.max_frames
    if args.resize_ratio is not None:
        params["resize_ratio"] = args.resize_ratio

    # キーフレーム抽出
    try:
        if args.mode == "distributed":
            # 均等分割モード
            keyframe_paths = extract_keyframes_distributed(
                video_path=args.video_path,
                output_dir=args.output_dir,
                quality=params["quality"],
                max_frames=params["max_frames"],
                resize_ratio=params["resize_ratio"],
                threshold=params["threshold"] if not args.auto else None
            )
        else:
            # 順次モード
            keyframe_paths = extract_keyframes_sequential(
                video_path=args.video_path,
                output_dir=args.output_dir,
                threshold=params["threshold"],
                quality=params["quality"],
                max_frames=params["max_frames"],
                resize_ratio=params["resize_ratio"]
            )

        print()
        print("次のステップ:")
        print("  1. Claude Codeで以下のコマンドを実行して画像を確認:")
        print(f"     ls -lh {args.output_dir}")
        print("  2. 各キーフレームを読み込んで分析:")
        for i, path in enumerate(keyframe_paths[:5], 1):
            print(f"     Read: {path}")
        if len(keyframe_paths) > 5:
            print(f"     ... (and {len(keyframe_paths) - 5} more)")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

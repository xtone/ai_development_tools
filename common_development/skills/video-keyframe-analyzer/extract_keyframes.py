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

    try:
        while cap.isOpened() and count < sample_count:
            ret, frame = cap.read()
            if not ret:
                break

            if prev_frame is not None:
                diff = calculate_frame_difference(prev_frame, frame)
                diffs.append(diff)

            prev_frame = frame
            count += 1
    finally:
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


def extract_keyframes_distributed(video_path, output_dir, quality=50, max_frames=20, resize_ratio=0.5, threshold=None, ensure_coverage=False):
    """
    動画を時間軸で均等に分割し、各区間から差分が最大のフレームを抽出

    Args:
        video_path: 動画ファイルのパス
        output_dir: 出力ディレクトリ
        quality: JPEG品質（0-100）
        max_frames: 最大抽出フレーム数
        resize_ratio: リサイズ比率
        threshold: 最小差分閾値（None なら自動）
        ensure_coverage: 全体カバレッジを保証（各セグメントから必ず1フレーム抽出、閾値無視）

    Returns:
        抽出されたキーフレームのパスリスト
    """
    # 動画を開く
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video: {video_path}")

    try:
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

        keyframes = []  # パスだけでなく詳細情報を格納
        keyframe_count = 0

        for segment_idx in range(max_frames):
            # 区間の開始・終了フレーム
            start_frame = segment_idx * segment_size
            # 最後のセグメントは残り全てを処理
            if segment_idx == max_frames - 1:
                end_frame = total_frames
            else:
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

            # 閾値を超えていれば保存（ensure_coverageの場合は閾値無視）
            if max_diff_frame is not None and (ensure_coverage or max_diff >= threshold or segment_idx == 0):
                keyframe_count += 1
                output_path = save_frame(max_diff_frame, output_dir, keyframe_count, quality, resize_ratio)
                timestamp = max_diff_frame_idx / fps if fps > 0 else 0

                keyframes.append({
                    'path': output_path,
                    'filename': output_path.name,
                    'timestamp': timestamp,
                    'frame_number': max_diff_frame_idx,
                    'diff': max_diff
                })

                print(f"[Frame {max_diff_frame_idx:4d} @ {timestamp:5.2f}s] "
                      f"Keyframe #{keyframe_count} (diff={max_diff:.2f}) -> {output_path.name}")

        # 時間軸カバレッジを計算
        if keyframes:
            last_timestamp = keyframes[-1]['timestamp']
            time_coverage = (last_timestamp / duration * 100) if duration > 0 else 0
        else:
            last_timestamp = 0
            time_coverage = 0

        print()
        print(f"Extraction complete!")
        print(f"  Total frames: {total_frames}")
        print(f"  Keyframes extracted: {keyframe_count}")
        print(f"  Reduction rate: {(1 - keyframe_count/total_frames) * 100:.1f}%")
        print(f"  Coverage: {(keyframe_count / max_frames) * 100:.1f}% of target")
        print(f"  Time coverage: {time_coverage:.1f}% (0.00s-{last_timestamp:.2f}s / {duration:.2f}s)")
        if time_coverage < 95 and not ensure_coverage:
            print(f"  ⚠️  Warning: Last {duration - last_timestamp:.2f}s ({100 - time_coverage:.1f}%) not covered")
            print(f"      Try: --ensure-full-coverage or lower --threshold")
        print(f"  Output directory: {output_dir}")

        return keyframes
    finally:
        cap.release()


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

    try:
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
        keyframes = []  # パスだけでなく詳細情報を格納
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
                timestamp = frame_count / fps if fps > 0 else 0

                keyframes.append({
                    'path': output_path,
                    'filename': output_path.name,
                    'timestamp': timestamp,
                    'frame_number': frame_count,
                    'diff': 0
                })

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
                timestamp = frame_count / fps if fps > 0 else 0

                keyframes.append({
                    'path': output_path,
                    'filename': output_path.name,
                    'timestamp': timestamp,
                    'frame_number': frame_count,
                    'diff': diff
                })

                print(f"[Frame {frame_count:4d} @ {timestamp:5.2f}s] "
                      f"Keyframe #{keyframe_count} (diff={diff:.2f}) -> {output_path.name}")
                prev_frame = frame

        print()
        print(f"Extraction complete!")
        print(f"  Total frames processed: {frame_count}")
        print(f"  Keyframes extracted: {keyframe_count}")
        print(f"  Reduction rate: {(1 - keyframe_count/frame_count) * 100:.1f}%")
        print(f"  Output directory: {output_dir}")

        return keyframes
    finally:
        cap.release()


def extract_keyframes_by_timestamps(video_path, output_dir, timestamps, quality=50, resize_ratio=0.5):
    """
    指定されたタイムスタンプでフレームを抽出

    Args:
        video_path: 動画ファイルのパス
        output_dir: 出力ディレクトリ
        timestamps: タイムスタンプのリスト（秒単位）
        quality: JPEG品質（0-100）
        resize_ratio: リサイズ比率

    Returns:
        抽出されたキーフレーム情報のリスト
    """
    # 動画を開く
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video: {video_path}")

    try:
        # 出力ディレクトリ作成
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 動画情報取得
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        print(f"\nVideo info:")
        print(f"  Duration: {duration:.2f}s")
        print(f"  FPS: {fps:.2f}")
        print(f"  Total frames: {total_frames}")
        print(f"  Timestamps: {len(timestamps)}")
        print(f"  Extraction mode: Timestamp-based")
        print()

        keyframes = []
        keyframe_count = 0

        # タイムスタンプを時系列順にソート
        sorted_timestamps = sorted(timestamps)

        for time_s in sorted_timestamps:
            # タイムスタンプをフレーム番号に変換
            frame_num = int(time_s * fps)

            # 動画の範囲外チェック
            if frame_num >= total_frames:
                print(f"⚠️  Warning: Timestamp {time_s:.2f}s exceeds video duration ({duration:.2f}s), using last frame")
                frame_num = total_frames - 1
            elif frame_num < 0:
                print(f"⚠️  Warning: Timestamp {time_s:.2f}s is negative, using first frame")
                frame_num = 0

            # フレームを取得
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()

            if not ret:
                print(f"❌ Error: Failed to read frame at {time_s:.2f}s (frame {frame_num})")
                continue

            # フレーム保存
            keyframe_count += 1
            output_path = save_frame(frame, output_dir, keyframe_count, quality, resize_ratio)

            keyframes.append({
                'path': output_path,
                'filename': output_path.name,
                'timestamp': time_s,
                'frame_number': frame_num,
                'diff': 0  # タイムスタンプ指定なので差分は計算しない
            })

            print(f"[Frame {frame_num:4d} @ {time_s:5.2f}s] "
                  f"Keyframe #{keyframe_count} -> {output_path.name}")

        print()
        print(f"Extraction complete!")
        print(f"  Total frames: {total_frames}")
        print(f"  Keyframes extracted: {keyframe_count}")
        print(f"  Reduction rate: {(1 - keyframe_count/total_frames) * 100:.1f}%")
        print(f"  Time coverage: {sorted_timestamps[0]:.2f}s - {sorted_timestamps[-1]:.2f}s")
        print(f"  Output directory: {output_dir}")

        return keyframes
    finally:
        cap.release()


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


def transcribe_audio_with_whisper(video_path, model_name="base"):
    """
    Whisperを使用して動画の音声を文字起こし

    Args:
        video_path: 動画ファイルのパス
        model_name: Whisperモデル名 (tiny/base/small/medium/large)

    Returns:
        dict: Whisperの文字起こし結果
    """
    try:
        import whisper
    except ImportError:
        print("Error: openai-whisper not installed")
        print("Install with: pip install openai-whisper")
        return None

    print(f"\nTranscribing audio with Whisper ({model_name} model)...")
    print("Note: First run will download the model (~74MB for 'base')")

    model = whisper.load_model(model_name)
    result = model.transcribe(video_path, language="ja", verbose=False)

    print(f"Transcription complete!")
    print(f"  Detected language: {result.get('language', 'unknown')}")
    print(f"  Segments: {len(result['segments'])}")

    return result


def map_speech_to_keyframes(keyframes, transcription):
    """
    キーフレームと音声セグメントをマッピング

    Args:
        keyframes: キーフレーム情報のリスト
        transcription: Whisperの文字起こし結果

    Returns:
        list: 音声情報が追加されたキーフレームリスト
    """
    if not transcription or 'segments' not in transcription:
        return keyframes

    segments = transcription['segments']

    for frame in keyframes:
        frame_time = frame['timestamp']

        # このフレームの前後100ms以内の音声を検索
        nearby_speech = []
        for seg in segments:
            seg_start = seg['start']
            seg_end = seg['end']

            # フレーム時間がセグメント内、またはセグメント開始の直後（500ms以内）
            if (seg_start <= frame_time <= seg_end) or \
               (abs(frame_time - seg_start) < 0.5):
                nearby_speech.append({
                    'text': seg['text'].strip(),
                    'start': seg_start,
                    'end': seg_end
                })

        frame['speech'] = nearby_speech if nearby_speech else None

    return keyframes


def save_analysis_markdown(keyframes, transcription, output_dir, video_duration=0):
    """
    キーフレームと音声分析結果をマークダウンで保存

    Args:
        keyframes: キーフレーム情報のリスト
        transcription: Whisperの文字起こし結果
        output_dir: 出力ディレクトリ
        video_duration: 動画の長さ（秒）
    """
    output_dir = Path(output_dir)
    md_path = output_dir / "video_analysis.md"

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Video Analysis Report\n\n")
        f.write("このレポートは video-keyframe-analyzer スキルによって自動生成されました。\n\n")

        # Overview
        f.write("## 概要\n\n")
        f.write(f"- 動画時間: {video_duration:.2f}秒\n")
        if transcription:
            f.write(f"- 言語: {transcription.get('language', '不明')}\n")
        f.write(f"- 抽出キーフレーム数: {len(keyframes)}\n")
        if transcription:
            f.write(f"- 音声セグメント数: {len(transcription.get('segments', []))}\n")
        f.write("\n")

        # Timeline
        f.write("## タイムライン分析\n\n")
        f.write("各キーフレームと、その時点での音声内容:\n\n")

        for i, frame in enumerate(keyframes, 1):
            f.write(f"### [{frame['timestamp']:.2f}s] Frame {i}\n\n")
            f.write(f"**視覚情報:**\n")
            f.write(f"- 画像: `{frame.get('filename', 'N/A')}`\n")
            if 'diff' in frame:
                f.write(f"- 差分値: {frame['diff']:.2f}\n")
            f.write("\n")

            f.write(f"**音声情報:**\n")
            if frame.get('speech'):
                for speech in frame['speech']:
                    f.write(f"> 「{speech['text']}」\n")
                    f.write(f"> （{speech['start']:.2f}s - {speech['end']:.2f}s）\n\n")
            else:
                f.write("> （無音または音声なし）\n\n")

        # Full transcription
        if transcription and 'segments' in transcription:
            f.write("---\n\n")
            f.write("## 全文文字起こし\n\n")
            for seg in transcription['segments']:
                start = seg['start']
                end = seg['end']
                text = seg['text'].strip()
                f.write(f"**{start:.2f}s - {end:.2f}s**  \n")
                f.write(f"{text}\n\n")

    print(f"\n📄 Analysis report saved: {md_path}")
    print(f"   Claude Codeで確認: cat {md_path}")

    return md_path


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

    # パラメータバリデーション関数
    def validate_threshold(value):
        fvalue = float(value)
        if fvalue < 0 or fvalue > 255:
            raise argparse.ArgumentTypeError(f"threshold must be between 0 and 255, got {fvalue}")
        return fvalue

    def validate_quality(value):
        ivalue = int(value)
        if ivalue < 0 or ivalue > 100:
            raise argparse.ArgumentTypeError(f"quality must be between 0 and 100, got {ivalue}")
        return ivalue

    def validate_max_frames(value):
        ivalue = int(value)
        if ivalue < 1:
            raise argparse.ArgumentTypeError(f"max_frames must be at least 1, got {ivalue}")
        return ivalue

    def validate_resize_ratio(value):
        fvalue = float(value)
        if fvalue <= 0 or fvalue > 2.0:
            raise argparse.ArgumentTypeError(f"resize_ratio must be between 0 and 2.0, got {fvalue}")
        return fvalue

    # 手動設定
    parser.add_argument("--threshold", "-t", type=validate_threshold,
                        help="差分閾値（範囲: 0-255、autoモードでは無視）")
    parser.add_argument("--quality", "-q", type=validate_quality,
                        help="JPEG品質（範囲: 0-100）")
    parser.add_argument("--max-frames", "-m", type=validate_max_frames,
                        help="最大抽出フレーム数")
    parser.add_argument("--resize-ratio", "-r", type=validate_resize_ratio,
                        help="リサイズ比率（1.0で元サイズ）")

    # 抽出モード
    parser.add_argument("--mode", choices=["distributed", "sequential"], default="distributed",
                        help="抽出モード: distributed（均等分割、推奨）/ sequential（順次）")

    # 全体カバレッジ保証
    parser.add_argument("--ensure-full-coverage", action="store_true",
                        help="動画全体のカバレッジを保証（各セグメントから必ず1フレーム抽出、閾値無視）")

    # タイムスタンプ指定
    parser.add_argument("--timestamps", type=str,
                        help="特定のタイムスタンプでフレームを抽出（カンマ区切り、例: \"0.0,0.5,1.0\"）")

    # 音声認識（オプション）
    parser.add_argument("--with-speech", action="store_true",
                        help="音声認識を実行（Whisperを使用、初回のみモデルダウンロード ~74MB）")
    parser.add_argument("--speech-model", choices=["tiny", "base", "small", "medium"], default="base",
                        help="Whisperモデルサイズ（デフォルト: base）")

    args = parser.parse_args()

    # 動画ファイルの存在確認と検証
    video_path = Path(args.video_path).resolve()

    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    if not video_path.is_file():
        print(f"Error: Path is not a file: {video_path}")
        sys.exit(1)

    # サポートされている拡張子を確認
    supported_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.flv', '.wmv'}
    if video_path.suffix.lower() not in supported_extensions:
        print(f"Warning: File extension '{video_path.suffix}' may not be supported.")
        print(f"Supported formats: {', '.join(sorted(supported_extensions))}")
        print("Attempting to process anyway...")

    # 以降はstr型のパスを使用
    args.video_path = str(video_path)

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
        # タイムスタンプモードの判定
        if args.timestamps:
            # タイムスタンプをパース
            try:
                timestamps = [float(t.strip()) for t in args.timestamps.split(',')]
            except ValueError:
                print("Error: Invalid timestamp format. Use comma-separated numbers (e.g., '0.0,0.5,1.0')")
                sys.exit(1)

            # タイムスタンプモードでキーフレーム抽出
            keyframes = extract_keyframes_by_timestamps(
                video_path=args.video_path,
                output_dir=args.output_dir,
                timestamps=timestamps,
                quality=params["quality"],
                resize_ratio=params["resize_ratio"]
            )
        elif args.mode == "distributed":
            # 均等分割モード
            keyframes = extract_keyframes_distributed(
                video_path=args.video_path,
                output_dir=args.output_dir,
                quality=params["quality"],
                max_frames=params["max_frames"],
                resize_ratio=params["resize_ratio"],
                threshold=params["threshold"] if not args.auto else None,
                ensure_coverage=args.ensure_full_coverage
            )
        else:
            # 順次モード
            keyframes = extract_keyframes_sequential(
                video_path=args.video_path,
                output_dir=args.output_dir,
                threshold=params["threshold"],
                quality=params["quality"],
                max_frames=params["max_frames"],
                resize_ratio=params["resize_ratio"]
            )

        # 音声認識（オプション）
        transcription = None
        if args.with_speech:
            transcription = transcribe_audio_with_whisper(
                args.video_path,
                model_name=args.speech_model
            )

            if transcription:
                # マッピング（keyframesには既にタイムスタンプ情報が含まれている）
                keyframes_with_speech = map_speech_to_keyframes(keyframes, transcription)

                # 動画の長さを取得
                cap = cv2.VideoCapture(args.video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = total_frames / fps if fps > 0 else 0
                cap.release()

                # マークダウン保存
                save_analysis_markdown(keyframes_with_speech, transcription, args.output_dir, duration)

        print()
        print("次のステップ:")
        if args.with_speech and transcription:
            print("  1. 音声付き分析レポートを確認:")
            print(f"     cat {args.output_dir}/video_analysis.md")
            print("  2. 各キーフレームを読み込んで分析:")
        else:
            print("  1. Claude Codeで以下のコマンドを実行して画像を確認:")
            print(f"     ls -lh {args.output_dir}")
            print("  2. 各キーフレームを読み込んで分析:")
        for i, kf in enumerate(keyframes[:5], 1):
            print(f"     Read: {kf['path']}")
        if len(keyframes) > 5:
            print(f"     ... (and {len(keyframes) - 5} more)")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

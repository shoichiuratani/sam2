#!/usr/bin/env python3
"""
動画をJPEGフレームに変換するスクリプト
Usage: python video_to_frames.py <input_video> <output_dir>
"""

import os
import sys
import cv2
import argparse
from pathlib import Path
from tqdm import tqdm


def video_to_frames(video_path, output_dir, quality=2):
    """
    動画をJPEGフレームに変換する
    
    Args:
        video_path (str): 入力動画ファイルのパス
        output_dir (str): 出力ディレクトリのパス
        quality (int): JPEG品質 (2 = 高品質)
    
    Returns:
        int: 変換されたフレーム数
    """
    
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    
    # 動画を開く
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"動画ファイルを開けません: {video_path}")
    
    # 動画情報を取得
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"動画情報:")
    print(f"  総フレーム数: {total_frames}")
    print(f"  FPS: {fps:.2f}")
    print(f"  解像度: {width}x{height}")
    print(f"  出力ディレクトリ: {output_dir}")
    
    frame_count = 0
    
    # プログレスバー付きでフレームを抽出
    with tqdm(total=total_frames, desc="フレーム抽出中", unit="frame") as pbar:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # フレームファイル名（5桁でゼロパディング）
            filename = f"{frame_count:05d}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            # JPEG品質設定でフレームを保存
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            frame_count += 1
            pbar.update(1)
    
    cap.release()
    
    print(f"変換完了: {frame_count}フレーム")
    return frame_count


def main():
    parser = argparse.ArgumentParser(
        description="動画をJPEGフレームに変換します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python video_to_frames.py input.mp4 output/frames/
  python video_to_frames.py /path/to/video.mov frames_dir/
        """
    )
    
    parser.add_argument("input_video", help="入力動画ファイル")
    parser.add_argument("output_dir", help="出力ディレクトリ")
    parser.add_argument("--quality", "-q", type=int, default=95,
                        help="JPEG品質 (1-100, デフォルト: 95)")
    
    args = parser.parse_args()
    
    # 入力ファイルの存在チェック
    if not os.path.exists(args.input_video):
        print(f"エラー: 入力ファイルが見つかりません: {args.input_video}")
        sys.exit(1)
    
    try:
        frame_count = video_to_frames(args.input_video, args.output_dir, args.quality)
        print(f"成功: {frame_count}フレームを {args.output_dir} に保存しました")
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
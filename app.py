#!/usr/bin/env python3
"""
SAM2 動画追跡アプリケーション - メインエントリーポイント
"""

import os
import sys
import argparse
from pathlib import Path

# プロジェクトルートを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.sam2_basic_demo import run_basic_sam2_demo
from src.sam2_video_tracker import run_complete_video_tracking
from scripts.video_to_frames import video_to_frames


def show_help():
    """ヘルプメッセージを表示"""
    print("""
SAM2 動画内物体検出・追跡アプリケーション
==========================================

使用方法:
  python app.py <コマンド> [オプション]

コマンド:
  frames     動画をJPEGフレームに分割
  demo       基本デモ（1フレームの物体検出）
  track      完全な動画追跡
  help       このヘルプを表示

各コマンドの詳細:

1. フレーム分割:
   python app.py frames <動画ファイル> <出力ディレクトリ>
   
   例:
   python app.py frames input.mp4 input/dog_images/

2. 基本デモ:
   python app.py demo <フレームディレクトリ> [--point <x,y>] [--model <サイズ>]
   
   例:
   python app.py demo input/dog_images/ --point 539.9,408.1 --model tiny

3. 完全な動画追跡:
   python app.py track <フレームディレクトリ> <出力ディレクトリ> [オプション]
   
   例:
   python app.py track input/dog_images/ result/tracked/ --point 539.9,408.1 --model tiny

オプション:
  --point <x,y>        追跡する座標点 (デフォルト: 300,300)
  --negative <x,y>     負の座標点（除外する領域）
  --model <サイズ>      使用モデル (tiny/small/base_plus/large, デフォルト: tiny)
  --quality <1-100>    JPEG品質 (フレーム分割時, デフォルト: 95)

使用例の流れ:
  1. python app.py frames input.mp4 input/dog_images/
  2. python app.py track input/dog_images/ result/tracked/ --point 539.9,408.1
    """)


def parse_point(point_str):
    """座標文字列をパース"""
    try:
        x, y = map(float, point_str.split(','))
        return [x, y]
    except:
        raise ValueError(f"座標の形式が正しくありません: {point_str} (例: 300,300)")


def main():
    """メイン関数"""
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help" or command == "--help" or command == "-h":
        show_help()
        return
    
    elif command == "frames":
        # 動画フレーム分割
        if len(sys.argv) < 4:
            print("エラー: 引数が不足しています")
            print("使用法: python app.py frames <動画ファイル> <出力ディレクトリ>")
            return
        
        input_video = sys.argv[2]
        output_dir = sys.argv[3]
        
        # オプション解析
        quality = 95
        for i in range(4, len(sys.argv) - 1):
            if sys.argv[i] == "--quality":
                quality = int(sys.argv[i + 1])
        
        if not os.path.exists(input_video):
            print(f"エラー: 動画ファイルが見つかりません: {input_video}")
            return
        
        try:
            frame_count = video_to_frames(input_video, output_dir, quality)
            print(f"完了: {frame_count}フレームを {output_dir} に保存しました")
        except Exception as e:
            print(f"エラー: {e}")
    
    elif command == "demo":
        # 基本デモ
        if len(sys.argv) < 3:
            print("エラー: 引数が不足しています")
            print("使用法: python app.py demo <フレームディレクトリ> [オプション]")
            return
        
        video_dir = sys.argv[2]
        
        if not os.path.exists(video_dir):
            print(f"エラー: フレームディレクトリが見つかりません: {video_dir}")
            return
        
        # デフォルト値
        point_coords = [[300, 300]]
        point_labels = [1]
        model_size = "tiny"
        
        # オプション解析
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--point" and i + 1 < len(sys.argv):
                try:
                    point_coords = [parse_point(sys.argv[i + 1])]
                    i += 2
                except ValueError as e:
                    print(f"エラー: {e}")
                    return
            elif sys.argv[i] == "--negative" and i + 1 < len(sys.argv):
                try:
                    neg_point = parse_point(sys.argv[i + 1])
                    point_coords.append(neg_point)
                    point_labels.append(0)
                    i += 2
                except ValueError as e:
                    print(f"エラー: {e}")
                    return
            elif sys.argv[i] == "--model" and i + 1 < len(sys.argv):
                model_size = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        try:
            run_basic_sam2_demo(
                video_dir=video_dir,
                model_size=model_size,
                point_coords=point_coords,
                point_labels=point_labels
            )
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
    
    elif command == "track":
        # 完全な動画追跡
        if len(sys.argv) < 4:
            print("エラー: 引数が不足しています")
            print("使用法: python app.py track <フレームディレクトリ> <出力ディレクトリ> [オプション]")
            return
        
        video_dir = sys.argv[2]
        output_dir = sys.argv[3]
        
        if not os.path.exists(video_dir):
            print(f"エラー: フレームディレクトリが見つかりません: {video_dir}")
            return
        
        # デフォルト値
        point_coords = [[300, 300]]
        point_labels = [1]
        model_size = "tiny"
        
        # オプション解析
        i = 4
        while i < len(sys.argv):
            if sys.argv[i] == "--point" and i + 1 < len(sys.argv):
                try:
                    point_coords = [parse_point(sys.argv[i + 1])]
                    point_labels = [1]  # リセット
                    i += 2
                except ValueError as e:
                    print(f"エラー: {e}")
                    return
            elif sys.argv[i] == "--negative" and i + 1 < len(sys.argv):
                try:
                    neg_point = parse_point(sys.argv[i + 1])
                    point_coords.append(neg_point)
                    point_labels.append(0)
                    i += 2
                except ValueError as e:
                    print(f"エラー: {e}")
                    return
            elif sys.argv[i] == "--model" and i + 1 < len(sys.argv):
                model_size = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        # 追跡対象オブジェクト設定
        objects_to_track = [{
            "frame": 0,
            "id": 0,
            "points": point_coords,
            "labels": point_labels
        }]
        
        try:
            analysis = run_complete_video_tracking(
                video_dir=video_dir,
                output_dir=output_dir,
                objects_to_track=objects_to_track,
                model_size=model_size
            )
            
            print(f"\\n追跡完了！結果は {output_dir} に保存されました。")
            
        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print(f"エラー: 不明なコマンド '{command}'")
        print("使用可能なコマンド: frames, demo, track, help")
        print("詳細は 'python app.py help' を参照してください")


if __name__ == "__main__":
    main()
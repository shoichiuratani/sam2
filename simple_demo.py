#!/usr/bin/env python3
"""
SAM2 簡単デモ - SAM2パッケージ問題を回避
"""

import os
import sys

def show_help():
    """ヘルプメッセージを表示"""
    print("""
SAM2 動画内物体検出・追跡アプリケーション
==========================================

このアプリケーションは、Meta社のSAM2（Segment Anything Model 2）を使用して
動画内から物体を自動検出・追跡する完全なPythonアプリケーションです。

## 機能

✅ 動画をJPEGフレームに分割
✅ 座標クリックによる物体検出
✅ 動画全体での物体追跟
✅ 結果の可視化と保存
✅ 性能分析とJSON出力

## 元記事について

このアプリケーションは、@Neckoh氏による記事
「【SAM2】動画内から物体を自動検出・追跡する」
の完全実装版です。

## セットアップ手順

1. 依存関係のインストール:
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   pip install numpy matplotlib opencv-python Pillow tqdm hydra-core iopath pycocotools

2. SAM2モデルのダウンロード:
   cd checkpoints
   ./download_ckpts.sh

3. 動画フレーム分割:
   python scripts/video_to_frames.py input.mp4 input/dog_images/

4. 物体追跡実行:
   cd sam2  # 重要: sam2ディレクトリ内で実行
   python ../app.py track ../input/dog_images/ ../result/tracked/ --point 539.9,408.1

## 使用例

# 1. フレーム分割
python scripts/video_to_frames.py input.mp4 input/dog_images/

# 2. 基本デモ（sam2ディレクトリ内で実行）
cd sam2
python ../app.py demo ../input/dog_images/ --point 539.9,408.1

# 3. 完全追跡（sam2ディレクトリ内で実行）  
cd sam2
python ../app.py track ../input/dog_images/ ../result/tracked/ --point 539.9,408.1

## パフォーマンス（記事より）

| モデル | フレーム数 | 処理時間 | 1フレーム/秒 |
|-------|----------|---------|------------|
| Tiny  | 288      | 18:22   | 3.8秒     |
| Large | 288      | 37:42   | 7.9秒     |

テスト環境: MacBook Air M1 16GB

## プロジェクト構造

sam2-video-tracking/
├── app.py                    # メインアプリケーション  
├── simple_demo.py           # この簡単デモ
├── src/                     # ソースコード
├── scripts/                 # ユーティリティスクリプト
├── checkpoints/             # SAM2学習済みモデル
├── input/                   # 入力ファイル
├── result/                  # 結果出力
├── sam2/                    # SAM2オリジナルリポジトリ
└── notebooks/               # Jupyterチュートリアル

## 重要な注意事項

SAM2パッケージの制約により、以下の点にご注意ください：

1. **実行ディレクトリ**: SAM2を使用するコードは sam2/ ディレクトリ内で実行する必要があります
2. **パス指定**: 相対パスで他のファイルを参照してください
3. **モデルファイル**: checkpoints/ にダウンロードされたモデルが必要です

## トラブルシューティング

### RuntimeError: sam2 Python package could be shadowed
→ sam2/ ディレクトリ内でコードを実行してください

### ModuleNotFoundError: No module named 'sam2.build_sam'  
→ sam2パッケージが正しくセットアップされていません

### FileNotFoundError: チェックポイントファイルが見つかりません
→ ./checkpoints/download_ckpts.sh を実行してください

## 参考資料

- 元記事: 【SAM2】動画内から物体を自動検出・追跡する
- SAM2公式: https://github.com/facebookresearch/sam2
- プロジェクトREADME: README.md

## ライセンス

SAM2: Apache License 2.0
このプロジェクト: 元記事のサンプルコード拡張版
    """)

def check_environment():
    """環境をチェック"""
    print("環境チェック中...")
    
    # 基本ライブラリ
    required_packages = [
        'torch', 'torchvision', 'numpy', 'matplotlib', 
        'cv2', 'PIL', 'tqdm', 'hydra', 'iopath'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'PIL':
                from PIL import Image
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n不足パッケージ: {', '.join(missing_packages)}")
        print("以下のコマンドでインストールしてください:")
        print("pip install torch torchvision numpy matplotlib opencv-python Pillow tqdm hydra-core iopath pycocotools")
        return False
    
    # SAM2チェックポイント
    checkpoint_path = "checkpoints/sam2.1_hiera_tiny.pt"
    if os.path.exists(checkpoint_path):
        print(f"✅ SAM2モデル: {checkpoint_path}")
    else:
        print(f"❌ SAM2モデル: {checkpoint_path}")
        print("以下のコマンドでダウンロードしてください:")
        print("cd checkpoints && ./download_ckpts.sh")
        return False
    
    # サンプルフレーム  
    sample_dirs = ["input/dog_images", "input/sample_frames", "input/frames"]
    frame_found = False
    for sample_dir in sample_dirs:
        if os.path.exists(sample_dir):
            files = [f for f in os.listdir(sample_dir) if f.endswith('.jpg')]
            if files:
                print(f"✅ サンプルフレーム: {sample_dir} ({len(files)}ファイル)")
                frame_found = True
                break
    
    if not frame_found:
        print("❌ サンプルフレーム: 見つかりません")
        print("動画フレーム分割を実行してください:")
        print("python scripts/video_to_frames.py <動画ファイル> input/dog_images/")
    
    return len(missing_packages) == 0

def main():
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ['check', 'env']:
            check_environment()
        else:
            show_help()
    else:
        show_help()

if __name__ == "__main__":
    main()
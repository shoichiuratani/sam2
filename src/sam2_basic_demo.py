#!/usr/bin/env python3
"""
SAM2基本デモ - 元記事のコードを再現
"""

import os
import numpy as np
import torch
import matplotlib.pyplot as plt
from PIL import Image
import datetime
import sys

# プロジェクトルートを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.sam2_utils import (
    show_mask, show_points, show_box, get_frame_names, 
    load_sam2_predictor, display_frame_with_points
)


def run_basic_sam2_demo(video_dir, model_size="tiny", point_coords=None, point_labels=None):
    """
    基本的なSAM2デモを実行
    
    Args:
        video_dir (str): JPEGフレームが格納されているディレクトリ
        model_size (str): 使用するモデルサイズ ("tiny", "small", "base_plus", "large")
        point_coords (list): 指定する座標 [[x, y], ...]
        point_labels (list): 座標のラベル [1 (positive), 0 (negative), ...]
    """
    
    print("=== SAM2 基本デモ開始 ===")
    start_time = datetime.datetime.now()
    
    # デバイス設定
    device = torch.device("cpu")
    print(f"使用デバイス: {device}")
    
    # モデル設定
    model_configs = {
        "tiny": ("configs/sam2.1/sam2.1_hiera_t.yaml", "checkpoints/sam2.1_hiera_tiny.pt"),
        "small": ("configs/sam2.1/sam2.1_hiera_s.yaml", "checkpoints/sam2.1_hiera_small.pt"),
        "base_plus": ("configs/sam2.1/sam2.1_hiera_b+.yaml", "checkpoints/sam2.1_hiera_base_plus.pt"),
        "large": ("configs/sam2.1/sam2.1_hiera_l.yaml", "checkpoints/sam2.1_hiera_large.pt")
    }
    
    if model_size not in model_configs:
        raise ValueError(f"サポートされていないモデルサイズ: {model_size}")
    
    model_cfg, sam2_checkpoint = model_configs[model_size]
    
    # 相対パスを絶対パスに変換
    model_cfg = os.path.join(project_root, model_cfg)
    sam2_checkpoint = os.path.join(project_root, sam2_checkpoint)
    
    print(f"モデル設定: {model_cfg}")
    print(f"チェックポイント: {sam2_checkpoint}")
    
    # チェックポイントファイルの存在確認
    if not os.path.exists(sam2_checkpoint):
        raise FileNotFoundError(f"チェックポイントファイルが見つかりません: {sam2_checkpoint}")
    
    # SAM2予測器を読み込む
    print("SAM2予測器を読み込み中...")
    predictor = load_sam2_predictor(model_cfg, sam2_checkpoint, device="cpu")
    print("SAM2予測器の読み込み完了")
    
    # フレームファイルを取得
    frame_names = get_frame_names(video_dir)
    if not frame_names:
        raise ValueError(f"JPEGフレームが見つかりません: {video_dir}")
    
    print(f"フレーム数: {len(frame_names)}")
    
    # 動画解析状態を初期化
    print("動画解析状態を初期化中...")
    inference_state = predictor.init_state(video_path=video_dir)
    print("初期化完了")
    
    # デフォルトの座標とラベルを設定（記事の例に基づく）
    if point_coords is None:
        point_coords = [[539.9, 408.1]]  # 犬の座標
    if point_labels is None:
        point_labels = [1]  # Positive
    
    # numpy配列に変換
    points = np.array(point_coords, dtype=np.float32)
    labels = np.array(point_labels, dtype=np.int32)
    
    print(f"指定座標: {points}")
    print(f"ラベル: {labels} (1=Positive, 0=Negative)")
    
    # 最初のフレームで物体検出
    ann_frame_idx = 0  # 最初のフレーム
    ann_obj_id = 0     # オブジェクトID
    
    print(f"フレーム {ann_frame_idx} で物体検出を実行中...")
    _, out_obj_ids, out_mask_logits = predictor.add_new_points_or_box(
        inference_state=inference_state,
        frame_idx=ann_frame_idx,
        obj_id=ann_obj_id,
        points=points,
        labels=labels,
    )
    
    # 最初のフレームの結果を表示
    print("最初のフレームの検出結果を表示中...")
    plt.figure(figsize=(9, 6))
    plt.title(f"Frame {ann_frame_idx} - 物体検出結果")
    
    # 元画像を表示
    image_path = os.path.join(video_dir, frame_names[ann_frame_idx])
    image = Image.open(image_path)
    plt.imshow(image)
    
    # 指定座標を表示
    show_points(points, labels, plt.gca())
    
    # セグメンテーションマスクを表示
    mask = (out_mask_logits[0] > 0.0).cpu().numpy()
    show_mask(mask, plt.gca(), obj_id=out_obj_ids[0])
    
    plt.axis('off')
    plt.tight_layout()
    
    # 結果ディレクトリに保存
    result_dir = os.path.join(project_root, "result")
    os.makedirs(result_dir, exist_ok=True)
    result_path = os.path.join(result_dir, f"frame_{ann_frame_idx:05d}_detection.png")
    plt.savefig(result_path, bbox_inches='tight', dpi=150)
    plt.show()
    
    print(f"検出結果を保存: {result_path}")
    
    # 処理時間を表示
    elapsed_time = datetime.datetime.now() - start_time
    print(f"処理時間: {elapsed_time}")
    print("=== SAM2 基本デモ完了 ===")
    
    return predictor, inference_state, out_obj_ids, frame_names


def main():
    """メイン関数"""
    
    # サンプルフレームディレクトリ（存在する場合）
    sample_dirs = [
        "input/dog_images",
        "input/sample_frames",
        "input/frames"
    ]
    
    video_dir = None
    for dir_path in sample_dirs:
        full_path = os.path.join(project_root, dir_path)
        if os.path.exists(full_path) and os.listdir(full_path):
            video_dir = full_path
            break
    
    if video_dir is None:
        print("フレームディレクトリが見つかりません。")
        print("以下のいずれかのディレクトリにJPEGフレームを配置してください:")
        for dir_path in sample_dirs:
            print(f"  - {dir_path}")
        print("\n動画フレーム分割スクリプトの使用例:")
        print("  python scripts/video_to_frames.py input.mp4 input/dog_images/")
        return
    
    print(f"使用するフレームディレクトリ: {video_dir}")
    
    try:
        # デフォルト座標で基本デモを実行
        run_basic_sam2_demo(
            video_dir=video_dir,
            model_size="tiny",
            point_coords=[[300, 300]],  # 中央付近の座標
            point_labels=[1]             # Positive
        )
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        print("まず動画をフレーム分割してください:")
        print("  python scripts/video_to_frames.py <動画ファイル> input/dog_images/")


if __name__ == "__main__":
    main()
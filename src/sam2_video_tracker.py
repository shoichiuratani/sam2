#!/usr/bin/env python3
"""
SAM2完全動画追跡アプリケーション - 元記事の完全実装
"""

import os
import cv2
import numpy as np
import torch
import matplotlib.pyplot as plt
from PIL import Image
import datetime
import sys
from tqdm import tqdm
import json

# プロジェクトルートを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.sam2_utils import (
    show_mask, show_points, show_box, get_frame_names, 
    load_sam2_predictor, save_frame_with_mask
)


class SAM2VideoTracker:
    """SAM2動画追跡クラス"""
    
    def __init__(self, model_size="tiny", device="cpu"):
        """
        初期化
        
        Args:
            model_size (str): モデルサイズ ("tiny", "small", "base_plus", "large")
            device (str): 使用デバイス
        """
        self.model_size = model_size
        self.device = torch.device(device)
        self.predictor = None
        self.inference_state = None
        
        # モデル設定
        self.model_configs = {
            "tiny": ("configs/sam2.1/sam2.1_hiera_t.yaml", "checkpoints/sam2.1_hiera_tiny.pt"),
            "small": ("configs/sam2.1/sam2.1_hiera_s.yaml", "checkpoints/sam2.1_hiera_small.pt"),
            "base_plus": ("configs/sam2.1/sam2.1_hiera_b+.yaml", "checkpoints/sam2.1_hiera_base_plus.pt"),
            "large": ("configs/sam2.1/sam2.1_hiera_l.yaml", "checkpoints/sam2.1_hiera_large.pt")
        }
        
        self._load_model()
    
    def _load_model(self):
        """SAM2モデルを読み込む"""
        if self.model_size not in self.model_configs:
            raise ValueError(f"サポートされていないモデルサイズ: {self.model_size}")
        
        model_cfg, sam2_checkpoint = self.model_configs[self.model_size]
        
        # 相対パスを絶対パスに変換
        model_cfg = os.path.join(project_root, model_cfg)
        sam2_checkpoint = os.path.join(project_root, sam2_checkpoint)
        
        if not os.path.exists(sam2_checkpoint):
            raise FileNotFoundError(f"チェックポイントファイルが見つかりません: {sam2_checkpoint}")
        
        print(f"SAM2モデル読み込み中: {self.model_size}")
        print(f"  設定ファイル: {model_cfg}")
        print(f"  チェックポイント: {sam2_checkpoint}")
        
        self.predictor = load_sam2_predictor(model_cfg, sam2_checkpoint, str(self.device))
        print("モデル読み込み完了")
    
    def initialize_video(self, video_dir):
        """
        動画解析を初期化
        
        Args:
            video_dir (str): JPEGフレームディレクトリ
        
        Returns:
            list: フレームファイル名のリスト
        """
        print(f"動画フレーム読み込み中: {video_dir}")
        
        frame_names = get_frame_names(video_dir)
        if not frame_names:
            raise ValueError(f"JPEGフレームが見つかりません: {video_dir}")
        
        print(f"フレーム数: {len(frame_names)}")
        
        # 動画解析状態を初期化
        self.inference_state = self.predictor.init_state(video_path=video_dir)
        print("動画解析状態初期化完了")
        
        return frame_names
    
    def add_object_points(self, frame_idx, obj_id, points, labels):
        """
        座標指定で物体を追加
        
        Args:
            frame_idx (int): フレームインデックス
            obj_id (int): オブジェクトID
            points (list or np.ndarray): 座標リスト [[x, y], ...]
            labels (list or np.ndarray): ラベルリスト [1 (positive), 0 (negative), ...]
        
        Returns:
            tuple: (out_frame_idx, out_obj_ids, out_mask_logits)
        """
        if isinstance(points, list):
            points = np.array(points, dtype=np.float32)
        if isinstance(labels, list):
            labels = np.array(labels, dtype=np.int32)
        
        print(f"物体追加: フレーム{frame_idx}, オブジェクトID{obj_id}")
        print(f"  座標: {points}")
        print(f"  ラベル: {labels}")
        
        return self.predictor.add_new_points_or_box(
            inference_state=self.inference_state,
            frame_idx=frame_idx,
            obj_id=obj_id,
            points=points,
            labels=labels,
        )
    
    def add_object_box(self, frame_idx, obj_id, box):
        """
        矩形指定で物体を追加
        
        Args:
            frame_idx (int): フレームインデックス
            obj_id (int): オブジェクトID
            box (list or np.ndarray): 矩形座標 [x_min, y_min, x_max, y_max]
        
        Returns:
            tuple: (out_frame_idx, out_obj_ids, out_mask_logits)
        """
        if isinstance(box, list):
            box = np.array(box, dtype=np.float32)
        
        print(f"物体追加（矩形）: フレーム{frame_idx}, オブジェクトID{obj_id}")
        print(f"  矩形: {box}")
        
        return self.predictor.add_new_points_or_box(
            inference_state=self.inference_state,
            frame_idx=frame_idx,
            obj_id=obj_id,
            box=box,
        )
    
    def propagate_in_video(self):
        """
        動画全体に追跡を伝播
        
        Returns:
            dict: フレーム毎のセグメンテーション結果
        """
        print("動画全体に追跡を伝播中...")
        
        video_segments = {}
        
        # プログレスバー付きで伝播処理
        propagation_iter = self.predictor.propagate_in_video(self.inference_state)
        
        for out_frame_idx, out_obj_ids, out_mask_logits in tqdm(propagation_iter, 
                                                               desc="フレーム処理", unit="frame"):
            video_segments[out_frame_idx] = {
                out_obj_id: (out_mask_logits[i] > 0.0).cpu().numpy()
                for i, out_obj_id in enumerate(out_obj_ids)
            }
        
        print(f"伝播完了: {len(video_segments)}フレーム処理")
        return video_segments
    
    def save_results(self, video_dir, frame_names, video_segments, output_dir, 
                    show_initial_points=None, show_initial_labels=None):
        """
        結果を保存
        
        Args:
            video_dir (str): 元フレームディレクトリ
            frame_names (list): フレームファイル名リスト
            video_segments (dict): セグメンテーション結果
            output_dir (str): 出力ディレクトリ
            show_initial_points (np.ndarray, optional): 初期座標点
            show_initial_labels (np.ndarray, optional): 初期座標ラベル
        """
        print(f"結果保存中: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 全フレームを保存
        for frame_idx in tqdm(range(len(frame_names)), desc="結果保存", unit="frame"):
            # 最初のフレームのみ初期座標を表示
            points_to_show = show_initial_points if frame_idx == 0 else None
            labels_to_show = show_initial_labels if frame_idx == 0 else None
            
            save_frame_with_mask(
                video_dir=video_dir,
                frame_names=frame_names,
                frame_idx=frame_idx,
                video_segments=video_segments,
                output_dir=output_dir,
                show_points_coords=points_to_show,
                show_points_labels=labels_to_show
            )
        
        print(f"保存完了: {len(frame_names)}フレーム")
    
    def analyze_results(self, video_segments, frame_names):
        """
        結果を分析
        
        Args:
            video_segments (dict): セグメンテーション結果
            frame_names (list): フレームファイル名リスト
        
        Returns:
            dict: 分析結果
        """
        analysis = {
            "total_frames": len(frame_names),
            "processed_frames": len(video_segments),
            "objects_detected": {},
            "mask_coverage": {}
        }
        
        for frame_idx, segments in video_segments.items():
            analysis["mask_coverage"][frame_idx] = {}
            
            for obj_id, mask in segments.items():
                if obj_id not in analysis["objects_detected"]:
                    analysis["objects_detected"][obj_id] = 0
                analysis["objects_detected"][obj_id] += 1
                
                # マスクのカバレッジを計算
                mask_area = np.sum(mask)
                total_area = mask.shape[0] * mask.shape[1]
                coverage = mask_area / total_area * 100
                
                analysis["mask_coverage"][frame_idx][obj_id] = coverage
        
        return analysis


def run_complete_video_tracking(video_dir, output_dir, objects_to_track, model_size="tiny"):
    """
    完全な動画追跡を実行
    
    Args:
        video_dir (str): JPEGフレームディレクトリ
        output_dir (str): 出力ディレクトリ
        objects_to_track (list): 追跡対象オブジェクトのリスト
            例: [{"frame": 0, "id": 0, "points": [[539.9, 408.1]], "labels": [1]}]
        model_size (str): モデルサイズ
    
    Returns:
        dict: 実行結果
    """
    start_time = datetime.datetime.now()
    
    print("=" * 50)
    print("SAM2 完全動画追跡開始")
    print("=" * 50)
    
    # トラッカーを初期化
    tracker = SAM2VideoTracker(model_size=model_size, device="cpu")
    
    # 動画を初期化
    frame_names = tracker.initialize_video(video_dir)
    
    # 追跡対象オブジェクトを追加
    initial_points = None
    initial_labels = None
    
    for obj_config in objects_to_track:
        frame_idx = obj_config["frame"]
        obj_id = obj_config["id"]
        
        if "points" in obj_config:
            points = obj_config["points"]
            labels = obj_config["labels"]
            tracker.add_object_points(frame_idx, obj_id, points, labels)
            
            # 最初のオブジェクトの座標を保存（表示用）
            if initial_points is None:
                initial_points = np.array(points, dtype=np.float32)
                initial_labels = np.array(labels, dtype=np.int32)
                
        elif "box" in obj_config:
            box = obj_config["box"]
            tracker.add_object_box(frame_idx, obj_id, box)
    
    # 動画全体に追跡を伝播
    video_segments = tracker.propagate_in_video()
    
    # 結果を保存
    tracker.save_results(
        video_dir=video_dir,
        frame_names=frame_names,
        video_segments=video_segments,
        output_dir=output_dir,
        show_initial_points=initial_points,
        show_initial_labels=initial_labels
    )
    
    # 結果を分析
    analysis = tracker.analyze_results(video_segments, frame_names)
    
    # 処理時間計算
    end_time = datetime.datetime.now()
    processing_time = end_time - start_time
    
    # 分析結果を保存
    analysis["processing_time"] = str(processing_time)
    analysis["model_size"] = model_size
    analysis["frames_per_second"] = len(frame_names) / processing_time.total_seconds()
    
    analysis_file = os.path.join(output_dir, "analysis_result.json")
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print("=" * 50)
    print("処理完了")
    print(f"処理時間: {processing_time}")
    print(f"フレーム数: {analysis['total_frames']}")
    print(f"処理済みフレーム数: {analysis['processed_frames']}")
    print(f"検出オブジェクト数: {len(analysis['objects_detected'])}")
    print(f"1フレームあたりの処理時間: {processing_time.total_seconds() / len(frame_names):.2f}秒")
    print(f"結果保存先: {output_dir}")
    print(f"分析結果: {analysis_file}")
    print("=" * 50)
    
    return analysis


def main():
    """メイン関数"""
    
    # サンプルフレームディレクトリを探す
    sample_dirs = [
        "input/dog_images",
        "input/sample_frames", 
        "input/frames"
    ]
    
    video_dir = None
    for dir_path in sample_dirs:
        full_path = os.path.join(project_root, dir_path)
        if os.path.exists(full_path) and get_frame_names(full_path):
            video_dir = full_path
            break
    
    if video_dir is None:
        print("フレームディレクトリが見つかりません。")
        print("以下のいずれかのディレクトリにJPEGフレームを配置してください:")
        for dir_path in sample_dirs:
            print(f"  - {dir_path}")
        print("\n動画フレーム分割の例:")
        print("  python scripts/video_to_frames.py input.mp4 input/dog_images/")
        return
    
    print(f"使用するフレームディレクトリ: {video_dir}")
    
    # 出力ディレクトリ
    output_dir = os.path.join(project_root, "result", "tracked_frames")
    
    # 追跡対象オブジェクト設定（記事の例）
    objects_to_track = [
        {
            "frame": 0,         # 最初のフレーム
            "id": 0,           # オブジェクトID
            "points": [[539.9, 408.1], [645, 415]],  # 座標（記事の例）
            "labels": [1, 0]   # 1=Positive, 0=Negative
        }
    ]
    
    try:
        # 完全な動画追跡を実行
        analysis = run_complete_video_tracking(
            video_dir=video_dir,
            output_dir=output_dir,
            objects_to_track=objects_to_track,
            model_size="tiny"
        )
        
        print("\n実行が完了しました！")
        print(f"追跡結果は {output_dir} に保存されました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
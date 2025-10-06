#!/usr/bin/env python3
"""
SAM2ユーティリティ関数
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import torch
import sys

# SAM2パッケージのパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sam2_package_path = os.path.join(os.path.dirname(current_dir), "sam2_package")
sys.path.insert(0, sam2_package_path)

try:
    from build_sam import build_sam2_video_predictor
except ImportError as e:
    print(f"SAM2のインポートに失敗しました: {e}")
    print(f"SAM2パッケージパス: {sam2_package_path}")
    # エラーを無視して継続（テスト時など）
    def build_sam2_video_predictor(*args, **kwargs):
        raise RuntimeError("SAM2モデルが利用できません。sam2_packageをセットアップしてください。")


def show_mask(mask, ax, obj_id=None, random_color=False):
    """
    SAM2の実行結果のセグメンテーションをマスクとして描画する。

    Args:
        mask (numpy.ndarray): 実行結果のセグメンテーション
        ax (matplotlib.axes._axes.Axes): matplotlibのAxis
        obj_id (int): オブジェクトID
        random_color (bool): マスクの色をランダムにするかどうか
    """
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        cmap = plt.get_cmap("tab10")
        cmap_idx = 0 if obj_id is None else obj_id
        color = np.array([*cmap(cmap_idx)[:3], 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)


def show_points(coords, labels, ax, marker_size=200):
    """
    指定した座標に星を描画する。
    labelsがPositiveの場合は緑、Negativeの場合は赤。

    Args:
        coords (numpy.ndarray): 指定した座標
        labels (numpy.ndarray): Positive or Negative
        ax (matplotlib.axes._axes.Axes): matplotlibのAxis
        marker_size (int, optional): マーカーのサイズ
    """
    pos_points = coords[labels==1]
    neg_points = coords[labels==0]
    ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', 
               s=marker_size, edgecolor='white', linewidth=1.25)
    ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', 
               s=marker_size, edgecolor='white', linewidth=1.25)


def show_box(box, ax):
    """
    指定された矩形を描画する

    Args:
        box (numpy.ndarray): 矩形の座標情報（x_min, y_min, x_max, y_max）
        ax (matplotlib.axes._axes.Axes): matplotlibのAxis
    """
    x0, y0 = box[0], box[1]
    w, h = box[2] - box[0], box[3] - box[1]
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor='green', 
                               facecolor=(0, 0, 0, 0), lw=2))


def get_frame_names(video_dir):
    """
    ディレクトリ内のJPEGファイルをスキャンして、ソートされたファイル名リストを返す
    
    Args:
        video_dir (str): JPEGフレームが格納されているディレクトリ
    
    Returns:
        list: ソートされたファイル名のリスト
    """
    frame_names = [
        p for p in os.listdir(video_dir)
        if os.path.splitext(p)[-1] in [".jpg", ".jpeg", ".JPG", ".JPEG"]
    ]
    frame_names.sort(key=lambda p: int(os.path.splitext(p)[0]))
    return frame_names


def load_sam2_predictor(model_cfg, sam2_checkpoint, device="cpu"):
    """
    SAM2予測器を読み込む
    
    Args:
        model_cfg (str): モデル設定ファイルパス
        sam2_checkpoint (str): チェックポイントファイルパス
        device (str): 使用するデバイス ("cpu" または "cuda")
    
    Returns:
        SAM2VideoPredictor: SAM2予測器インスタンス
    """
    device = torch.device(device)
    predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint, device=device)
    return predictor


def display_frame_with_points(video_dir, frame_names, frame_idx, points=None, labels=None):
    """
    指定されたフレームを表示し、オプションで座標点も表示する
    
    Args:
        video_dir (str): フレームディレクトリ
        frame_names (list): フレームファイル名のリスト
        frame_idx (int): 表示するフレームのインデックス
        points (numpy.ndarray, optional): 表示する座標点
        labels (numpy.ndarray, optional): 座標点のラベル
    
    Returns:
        PIL.Image: 読み込まれた画像
    """
    image_path = os.path.join(video_dir, frame_names[frame_idx])
    image = Image.open(image_path)
    
    plt.figure(figsize=(9, 6))
    plt.title(f"Frame {frame_idx}")
    plt.imshow(image)
    
    if points is not None and labels is not None:
        show_points(points, labels, plt.gca())
    
    plt.axis('off')
    plt.tight_layout()
    return image


def save_frame_with_mask(video_dir, frame_names, frame_idx, video_segments, 
                        output_dir, show_points_coords=None, show_points_labels=None):
    """
    フレームとマスクを重ねた画像を保存する
    
    Args:
        video_dir (str): 元のフレームディレクトリ
        frame_names (list): フレームファイル名のリスト
        frame_idx (int): フレームインデックス
        video_segments (dict): セグメンテーション結果
        output_dir (str): 出力ディレクトリ
        show_points_coords (numpy.ndarray, optional): 表示する座標点
        show_points_labels (numpy.ndarray, optional): 座標点のラベル
    """
    import cv2
    
    plt.figure(figsize=(6, 4))
    plt.title(f"frame {frame_idx}")
    plt.axis('off')
    plt.tight_layout(pad=0)

    # cv2はデフォルトがBGRのため、RGBに変換してから出力する
    image_path = os.path.join(video_dir, frame_names[frame_idx])
    image = cv2.imread(image_path)
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    # 座標点の表示
    if show_points_coords is not None and show_points_labels is not None:
        show_points(show_points_coords, show_points_labels, plt.gca())

    # マスクの描画
    if frame_idx in video_segments:
        for out_obj_id, out_mask in video_segments[frame_idx].items():
            show_mask(out_mask, plt.gca(), obj_id=out_obj_id)

    # マスク済みの画像を出力する
    os.makedirs(output_dir, exist_ok=True)
    file_name = os.path.basename(frame_names[frame_idx])
    output_path = os.path.join(output_dir, file_name)
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, dpi=150)
    plt.close()
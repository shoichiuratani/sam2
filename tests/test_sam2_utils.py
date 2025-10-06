#!/usr/bin/env python3
"""
SAM2ユーティリティ関数のテスト
"""

import unittest
import os
import sys
import numpy as np
import tempfile
from PIL import Image

# プロジェクトルートを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.sam2_utils import get_frame_names, show_points, show_mask


class TestSAM2Utils(unittest.TestCase):
    """SAM2ユーティリティ関数のテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = tempfile.mkdtemp()
        
        # テスト用のダミーJPEGファイルを作成
        self.test_files = ["00000.jpg", "00001.jpg", "00002.jpg", "test.txt", "00003.jpeg"]
        
        for filename in self.test_files:
            filepath = os.path.join(self.temp_dir, filename)
            if filename.endswith(('.jpg', '.jpeg')):
                # 簡単なダミー画像を作成
                img = Image.new('RGB', (100, 100), color='red')
                img.save(filepath)
            else:
                # テキストファイルを作成
                with open(filepath, 'w') as f:
                    f.write("test")
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_frame_names(self):
        """get_frame_names関数のテスト"""
        frame_names = get_frame_names(self.temp_dir)
        
        # JPEGファイルのみが返されることを確認
        expected_files = ["00000.jpg", "00001.jpg", "00002.jpg", "00003.jpeg"]
        self.assertEqual(len(frame_names), len(expected_files))
        
        # ソートされていることを確認
        self.assertEqual(frame_names[0], "00000.jpg")
        self.assertEqual(frame_names[1], "00001.jpg")
        self.assertEqual(frame_names[2], "00002.jpg")
        self.assertEqual(frame_names[3], "00003.jpeg")
    
    def test_get_frame_names_empty_dir(self):
        """空のディレクトリでのget_frame_namesのテスト"""
        empty_dir = tempfile.mkdtemp()
        try:
            frame_names = get_frame_names(empty_dir)
            self.assertEqual(len(frame_names), 0)
        finally:
            os.rmdir(empty_dir)
    
    def test_show_points_data_types(self):
        """show_points関数の入力データ型テスト"""
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots()
        
        # numpy配列でのテスト
        coords = np.array([[100.0, 200.0], [150.0, 250.0]])
        labels = np.array([1, 0])
        
        # エラーが発生しないことを確認
        try:
            show_points(coords, labels, ax)
            test_passed = True
        except Exception as e:
            test_passed = False
            print(f"show_points テストエラー: {e}")
        
        plt.close(fig)
        self.assertTrue(test_passed)
    
    def test_show_mask_dimensions(self):
        """show_mask関数のマスク次元テスト"""
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots()
        
        # 2Dマスクでのテスト
        mask = np.random.rand(100, 100) > 0.5
        
        # エラーが発生しないことを確認
        try:
            show_mask(mask, ax, obj_id=1)
            test_passed = True
        except Exception as e:
            test_passed = False
            print(f"show_mask テストエラー: {e}")
        
        plt.close(fig)
        self.assertTrue(test_passed)


class TestVideoToFrames(unittest.TestCase):
    """動画フレーム分割のテストクラス"""
    
    def test_import_video_to_frames(self):
        """video_to_frames関数のインポートテスト"""
        try:
            from scripts.video_to_frames import video_to_frames
            import_success = True
        except ImportError:
            import_success = False
        
        self.assertTrue(import_success, "video_to_frames関数をインポートできませんでした")


if __name__ == "__main__":
    # テストを実行
    print("SAM2ユーティリティ関数のテストを開始...")
    
    unittest.main(verbosity=2)
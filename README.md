# SAM2 動画内物体検出・追跡アプリケーション

Meta社が開発したSAM2（Segment Anything Model 2）を使用して、動画内から物体を自動検出・追跡するPythonアプリケーションです。

![SAM2 Logo](https://github.com/facebookresearch/sam2/raw/main/assets/sam2_logo.png)

## 機能

- 🎥 **動画フレーム分割**: MP4動画を高品質JPEGフレームに変換
- 🎯 **物体検出**: 座標クリックまたは矩形選択による物体の自動検出
- 📹 **動画追跡**: 全フレームに渡る物体の自動追跡
- 📊 **結果分析**: 追跡結果の統計分析とJSON出力
- 🖼️ **視覚化**: セグメンテーション結果の画像保存

## 元記事について

このアプリケーションは、@Neckoh氏による記事「【SAM2】動画内から物体を自動検出・追跡する」（Qiita）のサンプルコードを完全実装したものです。

記事の内容：
- SAM2の基本的な使用方法
- 動画フレーム分割からセグメンテーションまでの完全な流れ
- CPU環境での性能測定結果
- 実際のコード例と詳細な解説

## インストール

### 1. リポジトリのクローン

```bash
git clone <this-repository>
cd sam2-video-tracking
```

### 2. 依存関係のインストール

```bash
# 基本的なライブラリ
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install numpy matplotlib opencv-python Pillow tqdm hydra-core iopath pycocotools

# または requirements.txtから
pip install -r requirements.txt
```

### 3. SAM2学習済みモデルのダウンロード

```bash
# Tinyモデル（軽量・高速）
cd checkpoints
./download_ckpts.sh
```

利用可能なモデル：
- `sam2.1_hiera_tiny.pt` (149MB) - 軽量・高速
- `sam2.1_hiera_small.pt` - 小サイズ
- `sam2.1_hiera_base_plus.pt` - 中サイズ
- `sam2.1_hiera_large.pt` - 大サイズ・高精度

## 使用方法

### 基本的な使用の流れ

1. **動画をフレーム分割**
2. **物体を検出・追跡**
3. **結果を確認**

### 1. 動画フレーム分割

```bash
# MP4動画をJPEGフレームに変換
python app.py frames input.mp4 input/dog_images/

# 品質指定
python app.py frames input.mp4 input/dog_images/ --quality 95
```

### 2. 基本デモ（1フレーム検出）

```bash
# デフォルト座標で検出
python app.py demo input/dog_images/

# 座標指定で検出
python app.py demo input/dog_images/ --point 539.9,408.1

# 除外領域も指定
python app.py demo input/dog_images/ --point 539.9,408.1 --negative 645,415
```

### 3. 完全な動画追跡

```bash
# 基本的な追跡
python app.py track input/dog_images/ result/tracked/

# 座標指定での追跡
python app.py track input/dog_images/ result/tracked/ --point 539.9,408.1

# 高精度モデルでの追跡
python app.py track input/dog_images/ result/tracked/ --point 539.9,408.1 --model large
```

## コマンドリファレンス

### 基本コマンド

| コマンド | 説明 |
|---------|------|
| `frames` | 動画をJPEGフレームに分割 |
| `demo` | 基本デモ（1フレーム検出） |
| `track` | 完全な動画追跡 |
| `help` | ヘルプ表示 |

### オプション

| オプション | 説明 | 例 |
|-----------|------|-----|
| `--point <x,y>` | 検出する座標点 | `--point 539.9,408.1` |
| `--negative <x,y>` | 除外する座標点 | `--negative 645,415` |
| `--model <size>` | モデルサイズ | `--model tiny` |
| `--quality <1-100>` | JPEG品質 | `--quality 95` |

### モデルサイズ

| サイズ | ファイルサイズ | 処理速度 | 精度 | 用途 |
|--------|-------------|---------|------|------|
| `tiny` | 149MB | 最高速 | 良好 | テスト・プロトタイプ |
| `small` | - | 高速 | 良好 | 一般的な用途 |
| `base_plus` | - | 中程度 | 高い | 高精度が必要 |
| `large` | - | 低速 | 最高 | 最高品質 |

## プロジェクト構造

```
sam2-video-tracking/
├── app.py                    # メインアプリケーション
├── src/
│   ├── __init__.py
│   ├── sam2_utils.py         # SAM2ユーティリティ関数
│   ├── sam2_basic_demo.py    # 基本デモ
│   └── sam2_video_tracker.py # 完全な動画追跡
├── scripts/
│   └── video_to_frames.py    # 動画フレーム分割スクリプト
├── checkpoints/              # SAM2学習済みモデル
│   ├── download_ckpts.sh
│   └── *.pt
├── configs/                  # SAM2設定ファイル
├── input/                    # 入力ファイル
├── result/                   # 結果出力
├── sam2/                     # SAM2オリジナルリポジトリ
└── requirements.txt
```

## 出力ファイル

### 追跡結果画像

- **場所**: `result/tracked_frames/`
- **形式**: JPEG
- **内容**: 元フレーム + セグメンテーションマスク + 座標点

### 分析結果

- **ファイル**: `result/tracked_frames/analysis_result.json`
- **内容**: 
  - 処理時間
  - フレーム数
  - オブジェクト検出統計
  - マスクカバレッジ

```json
{
  "total_frames": 288,
  "processed_frames": 288,
  "processing_time": "0:18:22.243981",
  "model_size": "tiny",
  "frames_per_second": 0.26,
  "objects_detected": {
    "0": 250
  }
}
```

## 性能について

### CPU性能（記事より）

| モデル | フレーム数 | 処理時間 | 1フレーム/秒 |
|-------|----------|---------|------------|
| Tiny | 288 | 18:22 | 3.8秒 |
| Large | 288 | 37:42 | 7.9秒 |

**テスト環境**: MacBook Air M1 16GB

### GPU使用時の性能向上

CUDA対応環境では大幅な高速化が期待できます：

```bash
# GPU版PyTorchのインストール例
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## トラブルシューティング

### よくある問題

1. **モデルファイルが見つからない**
   ```bash
   cd checkpoints
   ./download_ckpts.sh
   ```

2. **フレームディレクトリが空**
   ```bash
   python app.py frames input.mp4 input/dog_images/
   ```

3. **メモリ不足**
   - より小さいモデル（tiny）を使用
   - フレーム数を減らす
   - 解像度を下げる

4. **処理が遅い**
   - GPU環境の使用を検討
   - tinyモデルの使用
   - フレーム間引きの実装

### エラーメッセージ

| エラー | 原因 | 解決方法 |
|-------|------|---------|
| `FileNotFoundError: checkpoint` | モデル未ダウンロード | `./download_ckpts.sh`実行 |
| `ValueError: no JPEG frames` | フレーム分割未実行 | `app.py frames`コマンド実行 |
| `CUDA out of memory` | GPU メモリ不足 | CPU モード使用または小モデル |

## カスタマイズ

### 独自座標での追跡

```python
# src/sam2_video_tracker.py内で設定
objects_to_track = [
    {
        "frame": 0,
        "id": 0,
        "points": [[あなたのx座標, あなたのy座標]],
        "labels": [1]  # 1=Positive, 0=Negative
    }
]
```

### 複数オブジェクトの同時追跡

```python
objects_to_track = [
    {"frame": 0, "id": 0, "points": [[100, 100]], "labels": [1]},
    {"frame": 0, "id": 1, "points": [[200, 200]], "labels": [1]},
]
```

### 矩形選択での追跡

```python
objects_to_track = [
    {
        "frame": 0,
        "id": 0,
        "box": [x_min, y_min, x_max, y_max]
    }
]
```

## 参考資料

- [元記事: 【SAM2】動画内から物体を自動検出・追跡する](https://qiita.com/Neckoh/items/xxx)
- [SAM2公式リポジトリ](https://github.com/facebookresearch/sam2)
- [SAM2論文](https://ai.meta.com/research/publications/sam-2-segment-anything-in-images-and-videos/)
- [Meta AI Blog](https://ai.meta.com/blog/segment-anything-2/)

## ライセンス

このプロジェクトは元記事のサンプルコードを基に作成されています。
SAM2自体は[Apache License 2.0](https://github.com/facebookresearch/sam2/blob/main/LICENSE)の下で提供されています。

## 貢献

改善提案やバグレポートはIssueまたはPull Requestでお願いします。

## 謝辞

- [@Neckoh](https://qiita.com/Neckoh)氏による詳細な解説記事
- Meta社によるSAM2の開発と公開
- オープンソースコミュニティの皆様

---

**注意**: このアプリケーションは教育・研究目的で作成されています。商用利用の際は適切なライセンス確認を行ってください。
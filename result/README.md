# 結果出力ディレクトリ

このディレクトリにはSAM2による物体検出・追跡の結果が保存されます。

## ディレクトリ構造

```
result/
├── README.md                   # このファイル
├── tracked_frames/             # 追跡結果のフレーム画像
│   ├── 00000.jpg              # セグメンテーション付きフレーム
│   ├── 00001.jpg
│   ├── ...
│   └── analysis_result.json   # 分析結果
├── notebook_results/          # Jupyter Notebook実行結果
└── detection_results/         # 単体検出結果
```

## 出力ファイルの説明

### 1. 追跡結果画像

各フレームにセグメンテーションマスクが重ね合わせられた画像：

- **ファイル名**: 元フレームと同じ（`00000.jpg`など）
- **内容**: 
  - 元の動画フレーム
  - セグメンテーションマスク（半透明オーバーレイ）
  - 座標点（最初のフレームのみ、緑=Positive, 赤=Negative）

### 2. 分析結果JSON

`analysis_result.json`には以下の情報が含まれます：

```json
{
  "total_frames": 288,
  "processed_frames": 288,
  "processing_time": "0:18:22.243981",
  "model_size": "tiny",
  "frames_per_second": 0.26,
  "objects_detected": {
    "0": 250
  },
  "mask_coverage": {
    "0": {"0": 5.2},
    "1": {"0": 5.4},
    ...
  }
}
```

#### JSONフィールドの説明

- `total_frames`: 総フレーム数
- `processed_frames`: 処理されたフレーム数
- `processing_time`: 総処理時間
- `model_size`: 使用したモデルサイズ
- `frames_per_second`: 1秒あたりの処理フレーム数
- `objects_detected`: オブジェクトID別の検出フレーム数
- `mask_coverage`: フレーム別・オブジェクト別のマスクカバレッジ（%）

## 使用例

### 結果の確認

```bash
# 結果ディレクトリの内容確認
ls -la result/tracked_frames/

# 分析結果の表示
cat result/tracked_frames/analysis_result.json | python -m json.tool
```

### 結果の統計

```bash
# 処理されたフレーム数を確認
ls result/tracked_frames/*.jpg | wc -l

# ファイルサイズの確認
du -sh result/tracked_frames/
```

## 結果の活用

### 1. アニメーションGIF作成

```bash
# ImageMagickを使用（別途インストール必要）
convert -delay 10 -loop 0 result/tracked_frames/*.jpg result/animation.gif
```

### 2. 動画への再変換

```bash
# ffmpegを使用（別途インストール必要）
ffmpeg -framerate 30 -i result/tracked_frames/%05d.jpg -c:v libx264 -pix_fmt yuv420p result/tracked_video.mp4
```

### 3. 統計分析

```python
import json
import matplotlib.pyplot as plt

# 分析結果を読み込み
with open('result/tracked_frames/analysis_result.json', 'r') as f:
    analysis = json.load(f)

# マスクカバレッジの推移をプロット
frames = []
coverages = []
for frame_str, frame_data in analysis['mask_coverage'].items():
    frames.append(int(frame_str))
    coverages.append(list(frame_data.values())[0])

plt.plot(frames, coverages)
plt.xlabel('Frame')
plt.ylabel('Coverage (%)')
plt.title('Mask Coverage Over Time')
plt.show()
```

## 注意事項

- 結果ファイルは大きなサイズになる場合があります
- `.gitignore`により結果ファイルはGitから除外されています
- 同じ出力ディレクトリに複数回実行すると、ファイルが上書きされます

## トラブルシューティング

### 結果が生成されない場合

1. **入力フレームの確認**:
   ```bash
   ls input/dog_images/*.jpg | head -5
   ```

2. **権限の確認**:
   ```bash
   ls -ld result/
   mkdir -p result/tracked_frames/
   ```

3. **ディスク容量の確認**:
   ```bash
   df -h .
   ```

### 分析結果の確認

```python
import json

# 分析結果を読み込み
with open('result/tracked_frames/analysis_result.json', 'r') as f:
    analysis = json.load(f)

print(f"処理時間: {analysis['processing_time']}")
print(f"総フレーム数: {analysis['total_frames']}")
print(f"1フレームあたり: {analysis['processing_time'].split(':')[-1]}秒")
```
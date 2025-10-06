# 入力ファイルディレクトリ

このディレクトリには入力ファイル（動画ファイルやフレーム画像）を配置します。

## ディレクトリ構造

```
input/
├── README.md              # このファイル
├── dog_images/            # 犬の動画フレーム（記事の例）
├── sample_frames/         # サンプルフレーム
└── frames/               # その他のフレーム
```

## 使用方法

### 1. 動画ファイルの配置

動画ファイル（MP4, MOV, AVIなど）をこのディレクトリに配置してください。

例：
```
input/
├── sample_video.mp4
└── dog_running.mov
```

### 2. 動画のフレーム分割

動画をJPEGフレームに分割します：

```bash
# 基本的な使用法
python scripts/video_to_frames.py input/sample_video.mp4 input/dog_images/

# または メインアプリを使用
python app.py frames input/sample_video.mp4 input/dog_images/
```

### 3. フレーム分割後の構造

```
input/
├── sample_video.mp4
└── dog_images/
    ├── 00000.jpg
    ├── 00001.jpg
    ├── 00002.jpg
    └── ...
```

## サンプルデータについて

元記事で使用されている犬の動画データは、以下のような特徴があります：

- **総フレーム数**: 288フレーム
- **内容**: ボールを追いかける犬
- **追跡対象座標**: [539.9, 408.1]（犬の位置）
- **除外座標**: [645, 415]（背景の部分）

## 注意事項

- JPEGフレームファイル名は `00000.jpg`, `00001.jpg` のように5桁の連番にしてください
- 動画ファイルは大きいため、`.gitignore`で除外されています
- フレーム分割後の画像も `.gitignore` で除外されています

## トラブルシューティング

### フレームが見つからない場合

```bash
# ディレクトリ内容の確認
ls -la input/dog_images/

# フレーム数の確認
ls input/dog_images/*.jpg | wc -l
```

### 対応動画形式

- MP4
- MOV
- AVI
- WMV
- その他OpenCVで読み込み可能な形式

### フレーム分割の品質設定

```bash
# 高品質（ファイルサイズ大）
python app.py frames input.mp4 input/frames/ --quality 95

# 標準品質
python app.py frames input.mp4 input/frames/ --quality 85

# 低品質（ファイルサイズ小）
python app.py frames input.mp4 input/frames/ --quality 70
```
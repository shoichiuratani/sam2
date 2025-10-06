#!/bin/bash

# SAM2のチェックポイントダウンロードスクリプト
# オリジナル: https://github.com/facebookresearch/sam2

echo "Downloading SAM2 model checkpoints..."

# SAM2.1 Hiera-Large モデル
if [ ! -f "sam2.1_hiera_large.pt" ]; then
    echo "Downloading SAM2.1 Hiera-Large..."
    wget -O sam2.1_hiera_large.pt "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt"
fi

# SAM2.1 Hiera-Base-Plus モデル  
if [ ! -f "sam2.1_hiera_base_plus.pt" ]; then
    echo "Downloading SAM2.1 Hiera-Base-Plus..."
    wget -O sam2.1_hiera_base_plus.pt "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt"
fi

# SAM2.1 Hiera-Small モデル
if [ ! -f "sam2.1_hiera_small.pt" ]; then
    echo "Downloading SAM2.1 Hiera-Small..."
    wget -O sam2.1_hiera_small.pt "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt"
fi

# SAM2.1 Hiera-Tiny モデル
if [ ! -f "sam2.1_hiera_tiny.pt" ]; then
    echo "Downloading SAM2.1 Hiera-Tiny..."
    wget -O sam2.1_hiera_tiny.pt "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt"
fi

echo "All model checkpoints downloaded successfully!"
echo "Available models:"
ls -lh *.pt
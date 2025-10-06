# SAM2 動画追跡 Webアプリ デプロイ手順

## 🚀 Webアプリケーション完成！

**アクセスURL**: https://5000-i87ay04fecmxmdhwfopkp-6532622b.e2b.dev/

## 📱 Webアプリ機能

### ✅ 実装完了機能

1. **🎥 動画アップロード**
   - ドラッグ&ドロップ対応
   - 対応形式: MP4, MOV, AVI, WMV, MKV
   - 最大ファイルサイズ: 100MB

2. **✂️ フレーム分割**
   - リアルタイムプログレス表示
   - バックグラウンド処理
   - 自動品質調整

3. **🎯 座標選択**
   - インタラクティブなキャンバス
   - 追跡対象（緑）・除外領域（赤）の選択
   - 座標の追加・削除・クリア機能

4. **🤖 SAM2追跡**
   - モデルサイズ選択（Tiny/Small/Base+/Large）
   - リアルタイムステータス更新
   - プログレス表示

5. **📊 結果表示**
   - 統計サマリー
   - ZIPファイルダウンロード
   - セッション管理

### 🎨 UI/UX特徴

- **レスポンシブデザイン**: モバイル・デスクトップ対応
- **Bootstrap 5**: モダンなデザインシステム
- **ステップバイステップ**: 直感的な5段階プロセス
- **リアルタイム更新**: Ajax/WebSocket風の体験
- **プログレス表示**: 各処理の進行状況を可視化

## 🛠️ ローカル実行手順

### 1. 依存関係のインストール

```bash
# 基本依存関係
pip install -r requirements_web.txt

# SAM2モデルのダウンロード
cd checkpoints
./download_ckpts.sh
```

### 2. 開発サーバー起動

```bash
# 開発モード（デバッグ有効）
python web_app.py

# アクセス: http://localhost:5000
```

### 3. プロダクション起動

```bash
# Gunicornを使用（推奨）
gunicorn --bind 0.0.0.0:5000 --workers 2 web_app:app

# または
gunicorn --bind 0.0.0.0:5000 --worker-class sync --workers 2 --timeout 300 web_app:app
```

## 🌐 クラウドデプロイ

### Heroku デプロイ

1. **Procfile作成**:
```bash
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 web_app:app
```

2. **runtime.txt作成**:
```
python-3.12.11
```

3. **デプロイコマンド**:
```bash
heroku create sam2-video-tracking
git add .
git commit -m "Deploy SAM2 web app"
git push heroku main
```

### Docker デプロイ

1. **Dockerfile作成**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements_web.txt .
RUN pip install -r requirements_web.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "web_app:app"]
```

2. **ビルド・実行**:
```bash
docker build -t sam2-web-app .
docker run -p 5000:5000 sam2-web-app
```

## ⚙️ 設定

### 環境変数

```bash
# Flask設定
export FLASK_ENV=production
export FLASK_SECRET_KEY=your-secret-key

# アップロード設定
export MAX_CONTENT_LENGTH=104857600  # 100MB
export UPLOAD_FOLDER=web_uploads

# SAM2設定
export SAM2_MODEL_PATH=checkpoints/
export DEFAULT_MODEL_SIZE=tiny
```

### nginx設定（プロダクション用）

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

## 🔧 トラブルシューティング

### よくある問題

1. **SAM2モデルが見つからない**
   ```bash
   cd checkpoints
   ./download_ckpts.sh
   ```

2. **アップロードファイルサイズ制限**
   - nginx: `client_max_body_size 100M;`
   - Flask: `app.config['MAX_CONTENT_LENGTH']`

3. **処理タイムアウト**
   - Gunicorn: `--timeout 300`
   - nginx: `proxy_read_timeout 300s;`

4. **メモリ不足**
   - Workerプロセス数を減らす: `--workers 1`
   - Tinyモデルを使用

### ログ確認

```bash
# 開発モード
tail -f web_app.log

# プロダクション
journalctl -u sam2-webapp -f
```

## 📝 API エンドポイント

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/` | GET | メインページ |
| `/upload` | POST | 動画アップロード |
| `/extract_frames/<session_id>` | POST | フレーム分割 |
| `/get_frames/<session_id>` | GET | フレーム一覧取得 |
| `/select_points/<session_id>` | POST | 座標選択 |
| `/start_tracking/<session_id>` | POST | 追跡開始 |
| `/status/<session_id>` | GET | 処理状況確認 |
| `/download_results/<session_id>` | GET | 結果ダウンロード |

## 🎯 使用方法（エンドユーザー向け）

### ステップ1: 動画アップロード
1. Webページにアクセス
2. 動画ファイルをドラッグ&ドロップまたは選択
3. アップロード完了を待つ

### ステップ2: フレーム分割
1. 「フレーム分割を開始」ボタンをクリック
2. 進行状況を確認
3. 完了まで数分待機

### ステップ3: 座標選択
1. プレビューフレームで追跡したい物体をクリック
2. 追跡対象（緑）・除外領域（赤）を選択
3. 「座標確定」ボタンをクリック

### ステップ4: SAM2追跡
1. モデルサイズを選択（Tiny推奨）
2. 「SAM2追跡を開始」ボタンをクリック
3. 処理完了まで数分〜数十分待機

### ステップ5: 結果確認
1. 追跡統計を確認
2. ZIPファイルをダウンロード
3. 新しいセッションを開始可能

## 💡 注意事項

### 制限事項
- **CPU処理**: GPU未対応（デモ版）
- **ファイルサイズ**: 最大100MB
- **同時セッション**: 制限あり
- **処理時間**: フレーム数に依存

### パフォーマンス
- **Tinyモデル**: 約3.8秒/フレーム
- **推奨**: 短い動画（<1分）での使用
- **GPU**: 利用可能な場合は大幅高速化

### セキュリティ
- **ファイル検証**: 拡張子・MIME タイプチェック
- **セッション管理**: UUID ベース
- **自動クリーンアップ**: 古いセッションの削除

## 📚 参考資料

- **元記事**: @Neckoh「【SAM2】動画内から物体を自動検出・追跡する」
- **SAM2公式**: https://github.com/facebookresearch/sam2
- **Flask公式**: https://flask.palletsprojects.com/
- **Bootstrap**: https://getbootstrap.com/

---

**🎉 Webアプリケーション完成！ブラウザから簡単にSAM2の動画追跡が体験できます！**
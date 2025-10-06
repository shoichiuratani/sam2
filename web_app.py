#!/usr/bin/env python3
"""
SAM2 動画追跡 Webアプリケーション
Flask + JavaScript でブラウザから簡単に使用可能
"""

import os
import sys
import json
import uuid
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import zipfile
import shutil
import numpy as np

# プロジェクトルートを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# SAM2のディレクトリ制約に対応するため、sam2ディレクトリに移動してインポート
original_cwd = os.getcwd()
sam2_dir = os.path.join(current_dir, 'sam2')

def import_sam2_components():
    """SAM2コンポーネントを安全にインポート"""
    os.chdir(sam2_dir)
    sys.path.insert(0, sam2_dir)
    try:
        from src.sam2_video_tracker import SAM2VideoTracker
        return SAM2VideoTracker
    finally:
        os.chdir(original_cwd)

# SAM2VideoTrackerをインポート
SAM2VideoTracker = None

from scripts.video_to_frames import video_to_frames

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sam2-video-tracking-web-app'
app.config['UPLOAD_FOLDER'] = 'web_uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

# アップロードフォルダを作成
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('web_results', exist_ok=True)

# 許可されるファイル拡張子
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'wmv', 'mkv'}

# セッション管理
processing_sessions = {}

def run_complete_video_tracking_with_progress(video_dir, output_dir, objects_to_track, model_size="tiny", progress_callback=None):
    """
    プログレスコールバック付きの完全な動画追跡を実行
    """
    # 正しいディレクトリでSAM2を実行
    original_cwd = os.getcwd()
    sam2_dir = os.path.join(current_dir, 'sam2')
    
    try:
        # sam2ディレクトリに移動
        os.chdir(sam2_dir)
        sys.path.insert(0, sam2_dir)
        
        # SAM2 componentsをインポート
        from src.sam2_video_tracker import run_complete_video_tracking
        
        if progress_callback:
            progress_callback("初期化", 10, "SAM2実行環境を準備中...")
        
        # 絶対パスに変換
        video_dir = os.path.abspath(video_dir)
        output_dir = os.path.abspath(output_dir)
        
        if progress_callback:
            progress_callback("実行", 20, "SAM2による物体追跡を開始...")
        
        # SAM2のパスを修正してから実行
        # SAM2VideoTrackerクラスを直接使用してパス問題を回避
        import datetime
        start_time = datetime.datetime.now()
        
        from src.sam2_video_tracker import SAM2VideoTracker
        
        # トラッカーを初期化（sam2ディレクトリ内で実行）
        tracker = SAM2VideoTracker(model_size=model_size, device="cpu")
        
        if progress_callback:
            progress_callback("初期化", 30, "動画フレームを初期化中...")
        
        # 動画を初期化
        frame_names = tracker.initialize_video(video_dir)
        
        if progress_callback:
            progress_callback("物体追加", 40, "追跡対象オブジェクトを設定中...")
        
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
        
        if progress_callback:
            progress_callback("追跡", 60, "動画全体に追跡を伝播中...")
        
        # 動画全体に追跡を伝播
        video_segments = tracker.propagate_in_video()
        
        if progress_callback:
            progress_callback("保存", 80, "結果を保存中...")
        
        # 結果を保存
        tracker.save_results(
            video_dir=video_dir,
            frame_names=frame_names,
            video_segments=video_segments,
            output_dir=output_dir,
            show_initial_points=initial_points,
            show_initial_labels=initial_labels
        )
        
        if progress_callback:
            progress_callback("分析", 90, "結果を分析中...")
        
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
        
        if progress_callback:
            progress_callback("完了", 100, "SAM2追跡が完了しました")
        
        return analysis
        
    finally:
        # 元のディレクトリに戻す
        os.chdir(original_cwd)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

class ProcessingSession:
    """処理セッションを管理するクラス"""
    def __init__(self, session_id):
        self.session_id = session_id
        self.status = "initialized"
        self.progress = 0
        self.message = ""
        self.video_path = None
        self.frames_dir = None
        self.frame_count = 0
        self.frame_list = []
        self.selected_points = []
        self.tracking_results = None
        self.result_dir = None
        self.error = None
        self.created_at = datetime.now()

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    """動画ファイルのアップロード"""
    if 'video' not in request.files:
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    if file and allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
        # セッションIDを生成
        session_id = str(uuid.uuid4())
        
        # ファイルを保存
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(video_path)
        
        # セッションを作成
        session = ProcessingSession(session_id)
        session.video_path = video_path
        session.status = "uploaded"
        session.message = f"動画アップロード完了: {filename}"
        
        processing_sessions[session_id] = session
        
        return jsonify({
            'session_id': session_id,
            'filename': filename,
            'message': session.message
        })
    
    return jsonify({'error': 'サポートされていないファイル形式です'}), 400

@app.route('/extract_frames/<session_id>', methods=['POST'])
def extract_frames(session_id):
    """フレーム分割を実行"""
    if session_id not in processing_sessions:
        return jsonify({'error': 'セッションが見つかりません'}), 404
    
    session = processing_sessions[session_id]
    
    if session.status not in ["uploaded", "extracting"]:
        if session.status == "frames_ready":
            return jsonify({'message': 'フレーム分割は既に完了しています'}), 200
        else:
            return jsonify({'error': f'現在の状態({session.status})ではフレーム分割を実行できません'}), 400
    
    # 既に処理中の場合は重複実行を防ぐ
    if session.status == "extracting":
        return jsonify({'message': 'フレーム分割が既に実行中です'}), 200
    
    def process_frames():
        try:
            session.status = "extracting"
            session.message = "フレーム分割中..."
            session.progress = 10
            
            # フレーム出力ディレクトリを作成
            frames_dir = os.path.join('web_results', session_id, 'frames')
            os.makedirs(frames_dir, exist_ok=True)
            session.frames_dir = frames_dir
            
            session.progress = 20
            session.message = "フレーム抽出を開始..."
            
            # フレーム分割実行
            frame_count = video_to_frames(session.video_path, frames_dir, quality=85)
            
            session.progress = 80
            session.message = "フレームファイルを確認中..."
            
            # フレームファイル一覧を取得
            frame_files = [f for f in os.listdir(frames_dir) if f.endswith('.jpg')]
            frame_files.sort()
            
            session.frame_count = len(frame_files)
            session.frame_list = frame_files
            session.progress = 100
            session.status = "frames_ready"
            session.message = f"フレーム分割完了: {frame_count}フレーム"
            
        except Exception as e:
            session.status = "error"
            session.error = str(e)
            session.message = f"エラー: {e}"
    
    # バックグラウンドで処理を実行
    thread = threading.Thread(target=process_frames)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'フレーム分割を開始しました'})

@app.route('/get_frames/<session_id>')
def get_frames(session_id):
    """フレーム一覧を取得"""
    if session_id not in processing_sessions:
        return jsonify({'error': 'セッションが見つかりません'}), 404
    
    session = processing_sessions[session_id]
    
    if session.status != "frames_ready":
        return jsonify({'error': 'フレームがまだ準備されていません'}), 400
    
    # 最初の数フレームのプレビューを作成
    preview_frames = []
    for i, frame_name in enumerate(session.frame_list[:20]):  # 最初の20フレーム
        preview_frames.append({
            'index': i,
            'filename': frame_name,
            'url': url_for('get_frame_image', session_id=session_id, frame_name=frame_name)
        })
    
    return jsonify({
        'total_frames': session.frame_count,
        'preview_frames': preview_frames,
        'status': session.status
    })

@app.route('/frame_image/<session_id>/<frame_name>')
def get_frame_image(session_id, frame_name):
    """フレーム画像を取得"""
    if session_id not in processing_sessions:
        return "セッションが見つかりません", 404
    
    session = processing_sessions[session_id]
    frame_path = os.path.join(session.frames_dir, frame_name)
    
    if not os.path.exists(frame_path):
        return "フレームが見つかりません", 404
    
    return send_file(frame_path)

@app.route('/select_points/<session_id>', methods=['POST'])
def select_points(session_id):
    """追跡対象の座標を設定"""
    if session_id not in processing_sessions:
        return jsonify({'error': 'セッションが見つかりません'}), 404
    
    session = processing_sessions[session_id]
    data = request.get_json()
    
    if not data or 'points' not in data:
        return jsonify({'error': '座標データが不正です'}), 400
    
    session.selected_points = data['points']
    session.status = "points_selected"
    session.message = f"{len(session.selected_points)}個の座標が選択されました"
    
    return jsonify({
        'message': session.message,
        'points': session.selected_points
    })

@app.route('/start_tracking/<session_id>', methods=['POST'])
def start_tracking(session_id):
    """SAM2追跡を開始"""
    if session_id not in processing_sessions:
        return jsonify({'error': 'セッションが見つかりません'}), 404
    
    session = processing_sessions[session_id]
    
    if session.status != "points_selected":
        return jsonify({'error': '先に追跡対象の座標を選択してください'}), 400
    
    data = request.get_json()
    model_size = data.get('model_size', 'tiny')
    
    def process_tracking():
        try:
            session.status = "tracking"
            session.message = "SAM2による物体追跡を開始..."
            session.progress = 10
            
            # 結果ディレクトリを作成
            result_dir = os.path.join('web_results', session_id, 'tracked')
            os.makedirs(result_dir, exist_ok=True)
            session.result_dir = result_dir
            
            session.progress = 20
            session.message = "SAM2モデルを読み込み中..."
            
            # 追跡対象オブジェクトを作成
            objects_to_track = []
            print(f"Debug - selected_points type: {type(session.selected_points)}")
            print(f"Debug - selected_points content: {session.selected_points}")
            
            # 座標データの正しい形式を取得
            if isinstance(session.selected_points, dict) and 'coords' in session.selected_points:
                coords = session.selected_points['coords']
                labels = session.selected_points.get('labels', [1] * len(coords))
                
                for i, coord in enumerate(coords):
                    objects_to_track.append({
                        "frame": 0,  # 最初のフレーム
                        "id": i,    # オブジェクトID
                        "points": [coord],  # 座標 [x, y]
                        "labels": [labels[i] if i < len(labels) else 1]  # ラベル
                    })
            else:
                # 旧形式への対応
                for i, point in enumerate(session.selected_points):
                    if isinstance(point, dict) and 'x' in point and 'y' in point:
                        objects_to_track.append({
                            "frame": 0,  # 最初のフレーム
                            "id": i,    # オブジェクトID
                            "points": [[float(point['x']), float(point['y'])]],  # 座標
                            "labels": [1]  # Positive
                        })
            
            print(f"Debug - objects_to_track: {objects_to_track}")
            
            session.progress = 30
            session.message = f"{len(objects_to_track)}個のオブジェクトを追跡中..."
            
            # プログレス更新用のコールバック関数を作成
            def update_progress(stage, progress, message):
                session.progress = min(30 + int(progress * 0.65), 95)  # 30-95%の範囲
                session.message = f"{stage}: {message}"
            
            # 実際のSAM2追跡を実行
            analysis = run_complete_video_tracking_with_progress(
                video_dir=session.frames_dir,
                output_dir=result_dir,
                objects_to_track=objects_to_track,
                model_size=model_size,
                progress_callback=update_progress
            )
            
            session.tracking_results = analysis
            session.progress = 100
            session.status = "completed"
            session.message = "追跡完了！"
            
        except Exception as e:
            session.status = "error"
            session.error = str(e)
            session.message = f"エラー: {e}"
            print(f"SAM2追跡エラー: {e}")
            import traceback
            traceback.print_exc()
    
    # バックグラウンドで処理を実行
    thread = threading.Thread(target=process_tracking)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'SAM2追跡を開始しました'})

@app.route('/status/<session_id>')
def get_status(session_id):
    """セッション状態を取得"""
    if session_id not in processing_sessions:
        return jsonify({'error': 'セッションが見つかりません'}), 404
    
    session = processing_sessions[session_id]
    
    return jsonify({
        'session_id': session_id,
        'status': session.status,
        'progress': session.progress,
        'message': session.message,
        'frame_count': session.frame_count,
        'error': session.error,
        'tracking_results': session.tracking_results
    })

@app.route('/download_results/<session_id>')
def download_results(session_id):
    """結果をZIPでダウンロード"""
    if session_id not in processing_sessions:
        return "セッションが見つかりません", 404
    
    session = processing_sessions[session_id]
    
    if session.status != "completed":
        return "まだ処理が完了していません", 400
    
    # ZIPファイルを作成
    zip_path = os.path.join('web_results', f"{session_id}_results.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        # 元フレームを追加（最初の20フレームのみ）
        for frame_name in session.frame_list[:20]:
            frame_path = os.path.join(session.frames_dir, frame_name)
            if os.path.exists(frame_path):
                zip_file.write(frame_path, f"frames/{frame_name}")
        
        # 追跡結果フレームを追加
        if session.result_dir and os.path.exists(session.result_dir):
            for root, dirs, files in os.walk(session.result_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, session.result_dir)
                    zip_file.write(file_path, f"tracked_results/{arcname}")
        
        # 結果データを追加
        if session.tracking_results:
            result_json = json.dumps(session.tracking_results, indent=2, ensure_ascii=False)
            zip_file.writestr("analysis_result.json", result_json)
        
        # README を追加
        readme_content = f"""SAM2 動画追跡結果
===================

セッションID: {session_id}
処理日時: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}
フレーム数: {session.frame_count}
選択座標: {session.selected_points}
モデルサイズ: {session.tracking_results.get('model_size', 'N/A') if session.tracking_results else 'N/A'}

結果:
{json.dumps(session.tracking_results, indent=2, ensure_ascii=False) if session.tracking_results else 'エラーが発生しました'}

使用方法:
1. frames/ - 元の動画フレーム（一部のみ含まれています）
2. tracked_results/ - SAM2による追跡結果フレーム
3. analysis_result.json - 詳細な解析結果データ
"""
        zip_file.writestr("README.txt", readme_content)
    
    return send_file(zip_path, as_attachment=True, download_name=f"sam2_results_{session_id}.zip")

@app.route('/cleanup/<session_id>', methods=['POST'])
def cleanup_session(session_id):
    """セッションをクリーンアップ"""
    if session_id in processing_sessions:
        session = processing_sessions[session_id]
        
        # ファイルを削除
        try:
            if session.video_path and os.path.exists(session.video_path):
                os.remove(session.video_path)
            
            session_dir = os.path.join('web_results', session_id)
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
        except Exception as e:
            print(f"クリーンアップエラー: {e}")
        
        # セッションを削除
        del processing_sessions[session_id]
    
    return jsonify({'message': 'セッションをクリーンアップしました'})

if __name__ == '__main__':
    print("SAM2 動画追跡 Webアプリケーションを開始...")
    print("ブラウザで http://localhost:5001 にアクセスしてください")
    app.run(host='0.0.0.0', port=5001, debug=True)
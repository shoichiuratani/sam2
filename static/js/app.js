// SAM2 動画追跡 Webアプリ JavaScript

class SAM2WebApp {
    constructor() {
        this.sessionId = null;
        this.currentStep = 1;
        this.selectedPoints = [];
        this.pointMode = 'positive'; // 'positive' or 'negative'
        this.currentFrame = null;
        this.frameCanvas = null;
        this.frameContext = null;
        this.statusCheckInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupCanvas();
    }
    
    setupEventListeners() {
        // ファイル選択
        const fileInput = document.getElementById('video-file');
        const selectFileBtn = document.getElementById('select-file-btn');
        const uploadArea = document.getElementById('upload-area');
        
        selectFileBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));
        
        // ドラッグ&ドロップ
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        
        // フレーム分割
        document.getElementById('extract-frames-btn').addEventListener('click', this.extractFrames.bind(this));
        
        // 座標選択モード
        document.getElementById('add-positive-btn').addEventListener('click', () => this.setPointMode('positive'));
        document.getElementById('add-negative-btn').addEventListener('click', () => this.setPointMode('negative'));
        document.getElementById('clear-points-btn').addEventListener('click', this.clearPoints.bind(this));
        document.getElementById('confirm-points-btn').addEventListener('click', this.confirmPoints.bind(this));
        
        // 追跡開始
        document.getElementById('start-tracking-btn').addEventListener('click', this.startTracking.bind(this));
        
        // 結果ダウンロード
        document.getElementById('download-results-btn').addEventListener('click', this.downloadResults.bind(this));
        document.getElementById('new-session-btn').addEventListener('click', this.newSession.bind(this));
    }
    
    setupCanvas() {
        this.frameCanvas = document.getElementById('frame-canvas');
        if (this.frameCanvas) {
            this.frameContext = this.frameCanvas.getContext('2d');
            this.frameCanvas.addEventListener('click', this.handleCanvasClick.bind(this));
        }
    }
    
    // ファイル処理
    handleFileSelect(file) {
        if (!file) return;
        this.uploadFile(file);
    }
    
    handleDragOver(e) {
        e.preventDefault();
        document.getElementById('upload-area').classList.add('drag-over');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        document.getElementById('upload-area').classList.remove('drag-over');
    }
    
    handleDrop(e) {
        e.preventDefault();
        document.getElementById('upload-area').classList.remove('drag-over');
        
        const file = e.dataTransfer.files[0];
        if (file) {
            this.uploadFile(file);
        }
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('video', file);
        
        this.showUploadProgress(true);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.sessionId = data.session_id;
                this.showMessage('アップロード完了: ' + data.filename, 'success');
                this.nextStep();
            } else {
                throw new Error(data.error || 'アップロードに失敗しました');
            }
        } catch (error) {
            this.showMessage('エラー: ' + error.message, 'error');
        } finally {
            this.showUploadProgress(false);
        }
    }
    
    async extractFrames() {
        if (!this.sessionId) {
            this.showMessage('先に動画をアップロードしてください', 'error');
            return;
        }
        
        try {
            const response = await fetch('/extract_frames/' + this.sessionId, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showMessage(data.message, 'info');
                this.startStatusCheck();
            } else {
                throw new Error(data.error || 'フレーム分割に失敗しました');
            }
        } catch (error) {
            this.showMessage('エラー: ' + error.message, 'error');
        }
    }
    
    async startStatusCheck() {
        this.statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch('/status/' + this.sessionId);
                const data = await response.json();
                
                this.updateProgress(data);
                
                if (data.status === 'frames_ready') {
                    clearInterval(this.statusCheckInterval);
                    await this.loadFramePreview();
                    this.nextStep();
                } else if (data.status === 'completed') {
                    clearInterval(this.statusCheckInterval);
                    this.showResults(data.tracking_results);
                    this.nextStep();
                } else if (data.status === 'error') {
                    clearInterval(this.statusCheckInterval);
                    this.showMessage('エラー: ' + data.error, 'error');
                }
            } catch (error) {
                console.error('Status check error:', error);
            }
        }, 2000);
    }
    
    async loadFramePreview() {
        try {
            const response = await fetch('/get_frames/' + this.sessionId);
            const data = await response.json();
            
            if (response.ok) {
                document.getElementById('total-frames').textContent = data.total_frames;
                
                if (data.preview_frames.length > 0) {
                    await this.loadFrame(data.preview_frames[0].url);
                }
            }
        } catch (error) {
            this.showMessage('エラー: ' + error.message, 'error');
        }
    }
    
    async loadFrame(frameUrl) {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                // キャンバスサイズを調整
                const maxWidth = 800;
                const maxHeight = 600;
                const scale = Math.min(maxWidth / img.width, maxHeight / img.height);
                
                this.frameCanvas.width = img.width * scale;
                this.frameCanvas.height = img.height * scale;
                
                // 画像を描画
                this.frameContext.clearRect(0, 0, this.frameCanvas.width, this.frameCanvas.height);
                this.frameContext.drawImage(img, 0, 0, this.frameCanvas.width, this.frameCanvas.height);
                
                this.currentFrame = img;
                this.redrawPoints();
                resolve();
            };
            img.src = frameUrl;
        });
    }
    
    // 座標選択
    setPointMode(mode) {
        this.pointMode = mode;
        
        // ボタンの状態更新
        document.getElementById('add-positive-btn').classList.toggle('active', mode === 'positive');
        document.getElementById('add-negative-btn').classList.toggle('active', mode === 'negative');
        
        // カーソル変更
        this.frameCanvas.style.cursor = mode === 'positive' ? 'crosshair' : 'not-allowed';
    }
    
    handleCanvasClick(e) {
        const rect = this.frameCanvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (this.frameCanvas.width / rect.width);
        const y = (e.clientY - rect.top) * (this.frameCanvas.height / rect.height);
        
        // 座標を追加
        this.addPoint(x, y, this.pointMode);
    }
    
    addPoint(x, y, type) {
        const point = {
            x: Math.round(x),
            y: Math.round(y),
            type: type, // 'positive' or 'negative'
            id: Date.now() // 簡単なID
        };
        
        this.selectedPoints.push(point);
        this.updatePointsList();
        this.redrawPoints();
        
        // 確定ボタンを有効化
        document.getElementById('confirm-points-btn').disabled = this.selectedPoints.length === 0;
    }
    
    removePoint(pointId) {
        this.selectedPoints = this.selectedPoints.filter(p => p.id !== pointId);
        this.updatePointsList();
        this.redrawPoints();
        
        // 確定ボタンの状態更新
        document.getElementById('confirm-points-btn').disabled = this.selectedPoints.length === 0;
    }
    
    clearPoints() {
        this.selectedPoints = [];
        this.updatePointsList();
        this.redrawPoints();
        document.getElementById('confirm-points-btn').disabled = true;
    }
    
    updatePointsList() {
        const container = document.getElementById('selected-points');
        
        if (this.selectedPoints.length === 0) {
            container.innerHTML = '<p class="text-muted">座標を選択してください</p>';
            return;
        }
        
        container.innerHTML = this.selectedPoints.map(point => 
            '<div class="point-item ' + point.type + '">' +
                '<div class="point-coords">' +
                    (point.type === 'positive' ? '✓' : '✗') + ' ' +
                    '(' + point.x + ', ' + point.y + ')' +
                '</div>' +
                '<span class="point-remove" onclick="app.removePoint(' + point.id + ')">' +
                    '<i class="fas fa-times"></i>' +
                '</span>' +
            '</div>'
        ).join('');
    }
    
    redrawPoints() {
        if (!this.currentFrame) return;
        
        // フレームを再描画
        this.frameContext.clearRect(0, 0, this.frameCanvas.width, this.frameCanvas.height);
        this.frameContext.drawImage(this.currentFrame, 0, 0, this.frameCanvas.width, this.frameCanvas.height);
        
        // 座標点を描画
        this.selectedPoints.forEach(point => {
            this.frameContext.beginPath();
            this.frameContext.arc(point.x, point.y, 8, 0, 2 * Math.PI);
            this.frameContext.fillStyle = point.type === 'positive' ? '#198754' : '#dc3545';
            this.frameContext.fill();
            this.frameContext.strokeStyle = 'white';
            this.frameContext.lineWidth = 2;
            this.frameContext.stroke();
        });
    }
    
    async confirmPoints() {
        if (this.selectedPoints.length === 0) return;
        
        try {
            const points = this.selectedPoints.map(p => [p.x, p.y]);
            const labels = this.selectedPoints.map(p => p.type === 'positive' ? 1 : 0);
            
            const response = await fetch('/select_points/' + this.sessionId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ points: { coords: points, labels: labels } })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showMessage(data.message, 'success');
                this.updateTrackingPointsSummary();
                this.nextStep();
            } else {
                throw new Error(data.error || '座標の設定に失敗しました');
            }
        } catch (error) {
            this.showMessage('エラー: ' + error.message, 'error');
        }
    }
    
    updateTrackingPointsSummary() {
        const container = document.getElementById('tracking-points-summary');
        
        const positiveCount = this.selectedPoints.filter(p => p.type === 'positive').length;
        const negativeCount = this.selectedPoints.filter(p => p.type === 'negative').length;
        
        container.innerHTML = 
            '<div class="alert alert-info">' +
                '<strong>選択済み座標:</strong><br>' +
                '<i class="fas fa-check text-success"></i> 追跡対象: ' + positiveCount + '個<br>' +
                '<i class="fas fa-times text-danger"></i> 除外領域: ' + negativeCount + '個' +
            '</div>';
    }
    
    async startTracking() {
        if (!this.sessionId) return;
        
        const modelSize = document.getElementById('model-size').value;
        
        try {
            const response = await fetch('/start_tracking/' + this.sessionId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ model_size: modelSize })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showMessage(data.message, 'info');
                this.startStatusCheck();
            } else {
                throw new Error(data.error || '追跡開始に失敗しました');
            }
        } catch (error) {
            this.showMessage('エラー: ' + error.message, 'error');
        }
    }
    
    showResults(results) {
        const container = document.getElementById('results-summary');
        
        container.innerHTML = 
            '<div class="row">' +
                '<div class="col-md-3">' +
                    '<div class="result-stat">' +
                        '<h4>' + results.total_frames + '</h4>' +
                        '<p>総フレーム数</p>' +
                    '</div>' +
                '</div>' +
                '<div class="col-md-3">' +
                    '<div class="result-stat">' +
                        '<h4>' + results.processed_frames + '</h4>' +
                        '<p>処理フレーム数</p>' +
                    '</div>' +
                '</div>' +
                '<div class="col-md-3">' +
                    '<div class="result-stat">' +
                        '<h4>' + results.processing_time + '</h4>' +
                        '<p>処理時間</p>' +
                    '</div>' +
                '</div>' +
                '<div class="col-md-3">' +
                    '<div class="result-stat">' +
                        '<h4>' + results.model_size + '</h4>' +
                        '<p>使用モデル</p>' +
                    '</div>' +
                '</div>' +
            '</div>' +
            '<div class="mt-3">' +
                '<h5>検出統計</h5>' +
                '<div class="alert alert-success">' +
                    Object.entries(results.objects_detected)
                        .map(([id, count]) => 'オブジェクト' + id + ': ' + count + 'フレームで検出')
                        .join('<br>') +
                '</div>' +
            '</div>' +
            (results.demo_mode ? 
                '<div class="alert alert-warning">' +
                    '<i class="fas fa-info-circle me-2"></i>' +
                    '<strong>注意:</strong> これはデモ版の結果です。実際のSAM2追跡を実行するには、' +
                    'sam2ディレクトリ内でCLIアプリケーションを使用してください。' +
                '</div>' : ''
            );
    }
    
    downloadResults() {
        if (!this.sessionId) return;
        
        window.location.href = '/download_results/' + this.sessionId;
    }
    
    newSession() {
        if (this.sessionId) {
            fetch('/cleanup/' + this.sessionId, { method: 'POST' });
        }
        
        // リセット
        this.sessionId = null;
        this.selectedPoints = [];
        this.currentStep = 1;
        
        // UI リセット
        this.resetUI();
    }
    
    // UI ヘルパーメソッド
    nextStep() {
        this.currentStep++;
        this.updateStepUI();
    }
    
    updateStepUI() {
        // ステップインジケーター更新
        for (let i = 1; i <= 5; i++) {
            const stepEl = document.getElementById('step-' + i);
            stepEl.classList.remove('active', 'completed');
            
            if (i < this.currentStep) {
                stepEl.classList.add('completed');
            } else if (i === this.currentStep) {
                stepEl.classList.add('active');
            }
        }
        
        // セクション表示切り替え
        const sections = ['upload', 'frames', 'preview', 'tracking', 'results'];
        sections.forEach((section, index) => {
            const sectionEl = document.getElementById(section + '-section');
            sectionEl.style.display = index + 1 === this.currentStep ? 'block' : 'none';
        });
    }
    
    updateProgress(data) {
        const progressBars = document.querySelectorAll('.progress-bar');
        const statusSpans = document.querySelectorAll('[id$="-status"]');
        
        progressBars.forEach(bar => {
            bar.style.width = data.progress + '%';
        });
        
        statusSpans.forEach(span => {
            span.textContent = data.message;
        });
    }
    
    showUploadProgress(show) {
        const progressEl = document.getElementById('upload-progress');
        progressEl.style.display = show ? 'block' : 'none';
    }
    
    showMessage(message, type) {
        type = type || 'info';
        const alertEl = document.getElementById('status-alert');
        const messageEl = document.getElementById('status-message');
        
        alertEl.className = 'alert alert-' + (type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info');
        messageEl.textContent = message;
        alertEl.style.display = 'block';
        
        // 3秒後に自動で非表示
        setTimeout(() => {
            alertEl.style.display = 'none';
        }, 3000);
    }
    
    resetUI() {
        // フォームリセット
        document.getElementById('video-file').value = '';
        
        // プログレスバーリセット
        document.querySelectorAll('.progress-bar').forEach(bar => {
            bar.style.width = '0%';
        });
        
        // ステップリセット
        this.updateStepUI();
        
        // キャンバスクリア
        if (this.frameContext) {
            this.frameContext.clearRect(0, 0, this.frameCanvas.width, this.frameCanvas.height);
        }
        
        // 座標リストクリア
        this.clearPoints();
        
        // アラート非表示
        document.getElementById('status-alert').style.display = 'none';
    }
}

// アプリケーション初期化
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new SAM2WebApp();
});
from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'}

# Создаем папку для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Файл для хранения данных
DATA_FILE = 'user_status.json'

# Начальные данные
DEFAULT_DATA = {
    "user_name": "Иван Иванов",
    "status": "доступен",
    "current_activity": "Работаю над проектом",
    "custom_message": "",
    "media_file": "",
    "media_type": "none",  # none, image, gif, video
    "last_updated": "",
    "status_history": []
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    """Загрузка данных из файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return DEFAULT_DATA
    return DEFAULT_DATA

def save_data(data):
    """Сохранение данных в файл"""
    data['last_updated'] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    """Главная страница (для планшета)"""
    data = load_data()
    return render_template('index.html', **data)

@app.route('/admin')
def admin():
    """Страница администрирования (для ПК)"""
    data = load_data()
    return render_template('admin.html', **data)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Отдача загруженных файлов"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/status', methods=['GET'])
def get_status():
    """API для получения текущего статуса"""
    data = load_data()
    return jsonify(data)

@app.route('/api/update_status', methods=['POST'])
def update_status():
    """API для обновления статуса"""
    data = load_data()
    
    # Обновляем текстовые данные
    if request.form.get('user_name'):
        data['user_name'] = request.form.get('user_name')
    if request.form.get('status'):
        data['status'] = request.form.get('status')
    if request.form.get('current_activity'):
        data['current_activity'] = request.form.get('current_activity')
    if request.form.get('custom_message'):
        data['custom_message'] = request.form.get('custom_message')
    
    # Обрабатываем загрузку файла
    if 'media_file' in request.files:
        file = request.files['media_file']
        if file and file.filename != '' and allowed_file(file.filename):
            # Удаляем старый файл если есть
            if data['media_file'] and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], data['media_file'])):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], data['media_file']))
            
            # Сохраняем новый файл
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            data['media_file'] = filename
            
            # Определяем тип медиа
            ext = filename.rsplit('.', 1)[1].lower()
            if ext in ['gif']:
                data['media_type'] = 'gif'
            elif ext in ['mp4', 'webm']:
                data['media_type'] = 'video'
            else:
                data['media_type'] = 'image'
    
    # Добавляем в историю
    status_change = {
        'timestamp': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        'status': data['status'],
        'activity': data['current_activity']
    }
    data['status_history'].insert(0, status_change)
    data['status_history'] = data['status_history'][:10]  # Храним только 10 последних
    
    save_data(data)
    return jsonify({'success': True, 'data': data})

@app.route('/api/clear_media', methods=['POST'])
def clear_media():
    """API для удаления медиа"""
    data = load_data()
    
    if data['media_file'] and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], data['media_file'])):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], data['media_file']))
    
    data['media_file'] = ""
    data['media_type'] = "none"
    save_data(data)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
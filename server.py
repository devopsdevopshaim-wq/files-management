#!/usr/bin/env python3
"""
שרת אירוח קבצי HTML אוטומטי
מעלה, מאחסן, ומציג קבצי HTML
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, Response
from flask_cors import CORS
import zipfile
import threading
import subprocess
import signal
import sys

app = Flask(__name__, template_folder='.', static_folder='static')
CORS(app)

# הגדרות
UPLOAD_FOLDER = 'uploads'
CONFIG_FILE = 'config.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# טעינת הגדרות
def load_config():
    default_config = {
        'server': {
            'port': 5000,
            'host': '0.0.0.0',
            'debug': False
        },
        'storage': {
            'max_size_mb': 100,
            'allowed_extensions': ['.html', '.htm', '.css', '.js']
        },
        'deployment': {
            'docker_port': 8080,
            'aws_region': 'us-east-1',
            'ec2_type': 't2.micro'
        }
    }
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            default_config.update(loaded)
    
    return default_config

config = load_config()

# שמירת הגדרות
def save_config():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# נתיבים
@app.route('/')
def index():
    """דף הבית"""
    return send_file('index.html') if os.path.exists('index.html') else '''
    <!DOCTYPE html>
    <html>
    <body>
        <h1>שרת אירוח HTML</h1>
        <p>השרת פועל! השתמש בממשק הניהול.</p>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    """העלאת קובץ"""
    if 'file' not in request.files:
        return jsonify({'error': 'לא נבחר קובץ'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'לא נבחר קובץ'}), 400
    
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # בדיקת סיומת
    if not any(filename.endswith(ext) for ext in config['storage']['allowed_extensions']):
        return jsonify({'error': 'סוג קובץ לא מותר'}), 400
    
    # שמירת הקובץ
    file.save(filepath)
    
    # יצירת מטא-דאטה
    metadata = {
        'filename': filename,
        'size': os.path.getsize(filepath),
        'size_kb': round(os.path.getsize(filepath) / 1024, 2),
        'upload_date': datetime.now().isoformat(),
        'url': f'/view/{filename}',
        'direct_url': f'{request.host_url}view/{filename}'
    }
    
    # שמירת מטא-דאטה
    meta_file = os.path.join(UPLOAD_FOLDER, f'{filename}.meta.json')
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return jsonify(metadata)

@app.route('/view/<filename>')
def view_file(filename):
    """הצגת קובץ"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'קובץ לא נמצא'}), 404
    
    # אם זה קובץ HTML, מחזיר את התוכן
    if filename.endswith(('.html', '.htm')):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return render_template('viewer.html', 
                             content=content,
                             filename=filename,
                             size=os.path.getsize(filepath) / 1024)
    
    # אחרת, מחזיר את הקובץ עצמו
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/files')
def list_files():
    """רשימת כל הקבצים"""
    files = []
    for f in os.listdir(UPLOAD_FOLDER):
        if not f.endswith('.meta.json'):
            filepath = os.path.join(UPLOAD_FOLDER, f)
            meta_file = os.path.join(UPLOAD_FOLDER, f'{f}.meta.json')
            
            if os.path.isfile(filepath):
                metadata = {
                    'filename': f,
                    'size': os.path.getsize(filepath),
                    'size_kb': round(os.path.getsize(filepath) / 1024, 2),
                    'upload_date': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                    'url': f'/view/{f}'
                }
                
                if os.path.exists(meta_file):
                    with open(meta_file, 'r', encoding='utf-8') as mf:
                        metadata.update(json.load(mf))
                
                files.append(metadata)
    
    return jsonify({'files': files})

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """מחיקת קובץ"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    meta_file = os.path.join(UPLOAD_FOLDER, f'{filename}.meta.json')
    
    if os.path.exists(filepath):
        os.remove(filepath)
    
    if os.path.exists(meta_file):
        os.remove(meta_file)
    
    return jsonify({'success': True})

@app.route('/stats')
def get_stats():
    """סטטיסטיקות"""
    files = []
    total_size = 0
    
    for f in os.listdir(UPLOAD_FOLDER):
        if not f.endswith('.meta.json'):
            filepath = os.path.join(UPLOAD_FOLDER, f)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
                files.append(f)
    
    return jsonify({
        'total_files': len(files),
        'total_size_kb': round(total_size / 1024, 2),
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'server_status': 'running',
        'uptime': get_uptime()
    })

@app.route('/deploy/docker', methods=['POST'])
def deploy_docker():
    """פריסה עם Docker"""
    data = request.json or {}
    port = data.get('port', config['deployment']['docker_port'])
    
    # יצירת Dockerfile
    dockerfile_content = f'''
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install flask flask-cors
EXPOSE {port}
CMD ["python", "server.py"]
'''
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    # יצירת docker-compose.yml
    compose_content = f'''
version: '3.8'
services:
  web:
    build: .
    ports:
      - "{port}:{port}"
    volumes:
      - ./uploads:/app/uploads
    restart: always
'''
    
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_content)
    
    return jsonify({
        'success': True,
        'message': 'קבצי Docker נוצרו',
        'port': port,
        'commands': [
            'docker-compose build',
            'docker-compose up -d'
        ]
    })

@app.route('/config', methods=['GET', 'PUT'])
def handle_config():
    """ניהול הגדרות"""
    if request.method == 'PUT':
        new_config = request.json
        config.update(new_config)
        save_config()
        return jsonify({'success': True})
    
    return jsonify(config)

def get_uptime():
    """חישוב זמן פעילות"""
    if not hasattr(app, 'start_time'):
        app.start_time = datetime.now()
    
    delta = datetime.now() - app.start_time
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    if days > 0:
        return f'{days} ימים, {hours} שעות'
    elif hours > 0:
        return f'{hours} שעות, {minutes} דקות'
    else:
        return f'{minutes} דקות'

def cleanup_old_files():
    """ניקוי קבצים ישנים"""
    max_age_days = 30
    for f in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, f)
        if os.path.isfile(filepath):
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(filepath))
            if file_age.days > max_age_days:
                os.remove(filepath)
                meta_file = filepath + '.meta.json'
                if os.path.exists(meta_file):
                    os.remove(meta_file)

if __name__ == '__main__':
    # הרצת ניקוי בהתחלה
    cleanup_old_files()
    
    # הרצת השרת
    port = config['server']['port']
    host = config['server']['host']
    debug = config['server']['debug']
    
    print(f"""
    🚀 שרת אירוח HTML מתחיל...
    
    📍 כתובת: http://{host}:{port}
    📁 תיקיית קבצים: {UPLOAD_FOLDER}
    ⚙️ מצב debug: {debug}
    
    לחיצה על Ctrl+C לעצירת השרת
    """)
    
    app.run(host=host, port=port, debug=debug)
#!/usr/bin/env python3
from flask import Flask, render_template_string, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import time
import secrets
import json
import os
import sqlite3
from collections import defaultdict
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)  # فعال کردن CORS برای استفاده از دامنه‌های مختلف

# تنظیمات پایگاه داده
DATABASE = 'api_creator.db'
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['DATABASE'] = DATABASE

# Anti-DDoS و محدودیت درخواست
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"]
)

def get_db():
    db = getattr(app, '_database', None)
    if db is None:
        db = app._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # ایجاد جداول مورد نیاز
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                path TEXT NOT NULL,
                method TEXT NOT NULL,
                response_template TEXT NOT NULL,
                is_public BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(path, method)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT,
                response_status INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (endpoint_id) REFERENCES endpoints (id)
            )
        ''')
        
        db.commit()

# HTML و رابط کاربری (کوتاه شده برای تمرکز بر عملکرد اصلی)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>API Creator Pro</title>
    <!-- استایل‌ها و اسکریپت‌های مشابه نسخه قبلی -->
</head>
<body>
    <!-- رابط کاربری بهبود یافته -->
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# سیستم احراز هویت پیشرفته
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    hashed_password = generate_password_hash(password)
    api_key = secrets.token_hex(16)
    
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, api_key) VALUES (?, ?, ?)",
            (username, hashed_password, api_key)
        )
        db.commit()
        return jsonify({"api_key": api_key}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    return jsonify({"api_key": user['api_key']})

# سیستم مدیریت API پیشرفته
@app.route('/api/_create', methods=['POST'])
@limiter.limit("10 per minute")
def api_create():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({"error": "API key required"}), 401
    
    db = get_db()
    user = db.execute(
        "SELECT id FROM users WHERE api_key = ?", (api_key,)
    ).fetchone()
    
    if not user:
        return jsonify({"error": "Invalid API key"}), 401
    
    data = request.json
    method = data.get('method', 'GET').upper()
    path = data.get('path')
    response_template = data.get('response_template')
    
    if not path or not path.startswith('/'):
        return jsonify({"error": "Invalid path"}), 400
    
    try:
        json.loads(response_template)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON template"}), 400
    
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO endpoints (user_id, path, method, response_template) VALUES (?, ?, ?, ?)",
            (user['id'], path, method, response_template)
        )
        db.commit()
        
        # ثبت خودکار مسیر در Flask
        app.add_url_rule(
            path,
            endpoint=f"dynamic_{path}_{method}_{user['id']}",
            view_func=create_dynamic_view(path, method, user['id']),
            methods=[method]
        )
        
        return jsonify({
            "status": "success",
            "path": path,
            "method": method
        })
    except sqlite3.IntegrityError:
        return jsonify({"error": "Endpoint already exists"}), 400

# سایر endpointها و توابع کمکی...

if __name__ == '__main__':
    # ایجاد دایرکتوری داده اگر وجود ندارد
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # مقداردهی اولیه پایگاه داده
    init_db()
    
    # ایجاد کاربر ادمین پیش‌فرض اگر وجود ندارد
    db = get_db()
    admin = db.execute("SELECT * FROM users WHERE is_admin = TRUE").fetchone()
    if not admin:
        api_key = secrets.token_hex(16)
        db.execute(
            "INSERT INTO users (username, password_hash, api_key, is_admin) VALUES (?, ?, ?, ?)",
            ("admin", generate_password_hash("admin123"), api_key, True)
        )
        db.commit()
        print(f"Admin user created. API Key: {api_key}")
    
    app.run(host='0.0.0.0', port=5000)

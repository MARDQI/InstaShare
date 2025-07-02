from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from utils import hash_password, process_file_async

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Configuración
UPLOAD_FOLDER = '../uploads'
PROCESSED_FOLDER = '../processed'
DATABASE = '../instashare.db'

# Crear directorios si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def init_db():
    """Inicializar base de datos"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de archivos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_size INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'uploading',
            zip_filename TEXT,
            download_count INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()



@app.route('/api/register', methods=['POST'])
def register():
    """Registrar nuevo usuario"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Usuario y contraseña requeridos'}), 400

        if len(password) < 4:
            return jsonify({'error': 'La contraseña debe tener al menos 4 caracteres'}), 400

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        # Verificar si el usuario ya existe
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'El usuario ya existe'}), 400

        # Crear usuario
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        ''', (username, password_hash))

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'user': {'id': user_id, 'username': username}
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Iniciar sesión"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Usuario y contraseña requeridos'}), 400

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        password_hash = hash_password(password)
        cursor.execute('''
            SELECT id, username FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))

        user = cursor.fetchone()
        conn.close()

        if not user:
            return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

        return jsonify({
            'message': 'Login exitoso',
            'user': {'id': user[0], 'username': user[1]}
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Subir archivo"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se seleccionó archivo'}), 400

        file = request.files['file']
        user_id = request.form.get('user_id')

        if not user_id:
            return jsonify({'error': 'Usuario requerido'}), 400

        if file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400

        if file:
            # Generar nombre único para el archivo
            original_filename = secure_filename(file.filename)
            file_extension = os.path.splitext(original_filename)[1]
            stored_filename = f"{secrets.token_urlsafe(16)}{file_extension}"
            file_path = os.path.join(UPLOAD_FOLDER, stored_filename)

            # Guardar archivo
            file.save(file_path)
            file_size = os.path.getsize(file_path)

            # Registrar en base de datos
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO files (user_id, original_filename, stored_filename, file_size)
                VALUES (?, ?, ?, ?)
            ''', (user_id, original_filename, stored_filename, file_size))

            file_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Procesar archivo de forma asíncrona
            process_file_async(file_id, file_path, original_filename)

            return jsonify({
                'message': 'Archivo subido exitosamente',
                'file_id': file_id
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<int:user_id>')
def get_user_files(user_id):
    """Obtener archivos del usuario"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, original_filename, file_size, upload_date, status, download_count
            FROM files
            WHERE user_id = ?
            ORDER BY upload_date DESC
        ''', (user_id,))

        files = []
        for row in cursor.fetchall():
            files.append({
                'id': row[0],
                'original_filename': row[1],
                'file_size': row[2],
                'upload_date': row[3],
                'status': row[4],
                'download_count': row[5]
            })

        conn.close()
        return jsonify({'files': files})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<int:file_id>')
def download_file(file_id):
    """Descargar archivo procesado"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT zip_filename, original_filename, status
            FROM files
            WHERE id = ?
        ''', (file_id,))

        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Archivo no encontrado'}), 404

        zip_filename, original_filename, status = result

        if status != 'processed' or not zip_filename:
            conn.close()
            return jsonify({'error': 'Archivo no está listo para descarga'}), 400

        # Incrementar contador de descargas
        cursor.execute('UPDATE files SET download_count = download_count + 1 WHERE id = ?', (file_id,))
        conn.commit()
        conn.close()

        zip_path = os.path.join(PROCESSED_FOLDER, zip_filename)
        if not os.path.exists(zip_path):
            return jsonify({'error': 'Archivo procesado no encontrado'}), 404

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"{os.path.splitext(original_filename)[0]}.zip"
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando InstaShare...")
    print("📊 Inicializando base de datos...")
    init_db()
    print("✅ Base de datos lista")
    print("🌐 Servidor corriendo en: http://localhost:5000")
    print("📁 Directorio de uploads:", UPLOAD_FOLDER)
    print("🗜️  Directorio de archivos procesados:", PROCESSED_FOLDER)

    app.run(debug=True, host='0.0.0.0', port=5000)

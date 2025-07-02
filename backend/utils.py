import hashlib
import secrets
import os
import zipfile
import threading
import time
from datetime import datetime
from werkzeug.utils import secure_filename

def hash_password(password):
    """Hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def process_file_async(file_id, file_path, original_filename, DATABASE, PROCESSED_FOLDER):
    """Procesar archivo de forma asíncrona (comprimir con ZIP)"""
    def process():
        time.sleep(1)  # Simular procesamiento

        try:
            # Crear archivo ZIP
            zip_filename = f"processed_{file_id}_{secrets.token_urlsafe(8)}.zip"
            zip_path = os.path.join(PROCESSED_FOLDER, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, original_filename)

            # Actualizar base de datos
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE files
                SET status = 'processed', zip_filename = ?
                WHERE id = ?
            ''', (zip_filename, file_id))
            conn.commit()
            conn.close()

            print(f"Archivo {file_id} procesado exitosamente")

        except Exception as e:
            print(f"Error procesando archivo {file_id}: {e}")
            # Marcar como error
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('UPDATE files SET status = "error" WHERE id = ?', (file_id,))
            conn.commit()
            conn.close()

    # Ejecutar en hilo separado
    thread = threading.Thread(target=process)
    thread.daemon = True
    thread.start()

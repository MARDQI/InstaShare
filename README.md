# InstaShare

InstaShare es una aplicación web para compartir archivos con compresión automática. Permite a los usuarios registrarse, iniciar sesión, subir archivos y descargar versiones comprimidas de los mismos.

## Características

- Registro e inicio de sesión de usuarios
- Subida de archivos con compresión automática a ZIP
- Visualización del estado de procesamiento de los archivos
- Descarga de archivos comprimidos
- Interfaz de usuario intuitiva y responsiva

## Estructura del Proyecto

- `backend/`: Contiene el código del servidor backend.
  - `main.py`: Archivo principal del servidor Flask.
  - `utils.py`: Funciones de utilidad, como hashing de contraseñas y procesamiento de archivos.

- `frontend/`: Contiene el código del cliente frontend.
  - `index.html`: Archivo HTML principal con la interfaz de usuario.

- `uploads/`: Directorio donde se almacenan los archivos subidos por los usuarios.

- `processed/`: Directorio donde se almacenan los archivos comprimidos procesados.

- `instashare.db`: Base de datos SQLite para almacenar información de usuarios y archivos.

## Configuración

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Iniciar el servidor**:
   ```bash
   python backend/main.py
   ```

3. **Acceder a la aplicación**:
   Abre el archivo `frontend/index.html`

## Uso

1. **Registro e inicio de sesión**:
   - Regístrate con un nombre de usuario y contraseña.
   - Inicia sesión con tus credenciales.

2. **Subir archivos**:
   - Selecciona un archivo y haz clic en "Subir y Procesar".
   - El archivo se comprimirá automáticamente y se almacenará en el servidor.

3. **Descargar archivos**:
   - Una vez que el archivo esté procesado, aparecerá un enlace para descargar el archivo comprimido.

## Tecnologías Utilizadas

- **Backend**: Flask, SQLite, Werkzeug
- **Frontend**: HTML, CSS, JavaScript
- **Base de Datos**: SQLite
- **Compresión**: ZIP

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o envía un pull request para cualquier mejora o corrección.

## PD

Esta es para uso local :)
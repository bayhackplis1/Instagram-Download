import os
import logging
from flask import Flask, render_template, request, jsonify, send_file
from downloader import InstagramDownloader

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

downloader = InstagramDownloader()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check-content', methods=['POST'])
def check_content():
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'Por favor, proporciona una URL de Instagram'}), 400

        # Validar URL
        if not downloader.is_valid_instagram_url(url):
            return jsonify({'error': 'URL de Instagram inválida'}), 400

        # Obtener información del contenido
        info = downloader.get_content_info(url)
        if not info:
            return jsonify({'error': 'No se pudo obtener información del contenido'}), 400

        return jsonify(info)

    except Exception as e:
        logger.error(f"Error al verificar contenido: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url')
        format_type = data.get('format', 'mp4')

        logger.info(f"URL recibida: {url}, formato: {format_type}")

        if not url:
            return jsonify({'error': 'Por favor, proporciona una URL de Instagram'}), 400

        # Validar URL
        if not downloader.is_valid_instagram_url(url):
            return jsonify({'error': 'URL de Instagram inválida'}), 400

        # Descargar contenido
        file_path = downloader.download(url, format_type)

        if file_path:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=os.path.basename(file_path)
            )
        else:
            return jsonify({'error': 'No se pudo descargar el contenido'}), 500

    except Exception as e:
        logger.error(f"Error durante la descarga: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/progress')
def progress():
    progress = downloader.get_progress()
    return jsonify({'progress': progress})
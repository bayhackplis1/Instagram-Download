import os
import re
import time
import logging
import tempfile
from urllib.parse import urlparse, unquote
import yt_dlp

logger = logging.getLogger(__name__)

class InstagramDownloader:
    def __init__(self):
        self.progress = 0
        self.temp_dir = tempfile.mkdtemp()

    def _progress_hook(self, d):
        """Maneja el progreso de la descarga"""
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total:
                    self.progress = int((downloaded / total) * 100)
            except:
                pass
        elif d['status'] == 'finished':
            self.progress = 100

    def is_valid_instagram_url(self, url):
        """Valida si la URL es de Instagram de manera más flexible"""
        try:
            url = unquote(url)
            logger.debug(f"URL decodificada: {url}")

            parsed = urlparse(url)
            logger.debug(f"URL parseada - netloc: {parsed.netloc}, path: {parsed.path}")

            if not bool(re.match(r'^(?:www\.)?instagram\.com', parsed.netloc)):
                return False

            patterns = [
                r'/p/[\w-]+',           # Posts
                r'/reel/[\w-]+',        # Reels
                r'/tv/[\w-]+',          # IGTV
                r'/stories/[\w-]+/[\w-]+', # Stories
                r'/share/[\w-]+',       # Shared content
            ]

            clean_path = re.sub(r'/+', '/', parsed.path).rstrip('/')
            return any(re.search(pattern, clean_path) for pattern in patterns)

        except Exception as e:
            logger.error(f"Error validando URL: {str(e)}")
            return False

    def get_progress(self):
        return self.progress

    def get_content_info(self, url):
        """Obtiene información detallada del contenido"""
        try:
            with yt_dlp.YoutubeDL({
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Sin título'),
                    'description': info.get('description', 'Sin descripción'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'comment_count': info.get('comment_count', 0),
                    'uploader': info.get('uploader', 'Desconocido'),
                    'upload_date': info.get('upload_date', 'Desconocido'),
                    'is_video': info.get('is_video', False),
                    'thumbnail': info.get('thumbnail', None),
                }
        except Exception as e:
            logger.error(f"Error obteniendo información: {str(e)}")
            return None

    def download(self, url, format_type='mp4'):
        """Descarga contenido de Instagram usando yt-dlp"""
        try:
            logger.info(f"Iniciando descarga de URL: {url} en formato {format_type}")
            self.progress = 0

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [self._progress_hook],
                'outtmpl': os.path.join(self.temp_dir, '%(id)s.%(ext)s'),
            }

            if format_type == 'mp3':
                from pydub import AudioSegment
                ydl_opts.update({
                    'format': 'bestaudio',
                })
                # Descargar como audio primero
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    audio_path = ydl.prepare_filename(info)
                    # Convertir a MP3 usando pydub
                    audio = AudioSegment.from_file(audio_path)
                    mp3_path = os.path.join(self.temp_dir, f"{info['id']}.mp3")
                    audio.export(mp3_path, format="mp3")
                    return mp3_path
            else:
                ydl_opts['format'] = 'best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if not info:
                    raise Exception("No se pudo extraer la información del contenido")

                if format_type == 'mp3':
                    filepath = os.path.join(self.temp_dir, f"{info['id']}.mp3")
                else:
                    filepath = ydl.prepare_filename(info)

                if not os.path.exists(filepath):
                    raise FileNotFoundError("El archivo descargado no se encuentra")

                logger.info(f"Archivo descargado exitosamente: {filepath}")
                self.progress = 100
                return filepath

        except Exception as e:
            logger.error(f"Error en la descarga: {str(e)}")
            raise Exception(f"Error al descargar: {str(e)}")
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('downloadForm');
    const formatSelector = document.getElementById('formatSelector');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const statusMessage = document.getElementById('statusMessage');
    const errorContainer = document.getElementById('errorContainer');
    const contentInfo = document.getElementById('contentInfo');
    const contentDetails = document.getElementById('contentDetails');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const urlInput = document.getElementById('url').value;

        if (!urlInput) {
            showError('Por favor, ingrese una URL de Instagram');
            return;
        }

        try {
            // Obtener información del contenido primero
            const infoResponse = await fetch('/check-content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: urlInput })
            });

            if (!infoResponse.ok) {
                const errorData = await infoResponse.json();
                throw new Error(errorData.error || 'Error verificando contenido');
            }

            const info = await infoResponse.json();

            // Mostrar información del contenido
            contentDetails.innerHTML = `
                <p><strong>Título:</strong> ${info.title}</p>
                <p><strong>Autor:</strong> ${info.uploader}</p>
                <p><strong>Fecha:</strong> ${formatDate(info.upload_date)}</p>
                ${info.duration ? `<p><strong>Duración:</strong> ${formatDuration(info.duration)}</p>` : ''}
                <p><strong>Vistas:</strong> ${formatNumber(info.view_count)}</p>
                <p><strong>Me gusta:</strong> ${formatNumber(info.like_count)}</p>
                <p><strong>Comentarios:</strong> ${formatNumber(info.comment_count)}</p>
            `;

            contentInfo.style.display = 'block';
            formatSelector.style.display = info.is_video ? 'block' : 'none';

            // Mostrar selector de formato y esperar selección
            contentInfo.style.display = 'block';
            formatSelector.style.display = 'block';
            
            // Esperar a que el usuario seleccione un formato
            const format = document.querySelector('input[name="format"]:checked')?.value || 'mp4';
            
            // Iniciar la descarga
            progressContainer.classList.remove('d-none');
            errorContainer.classList.add('d-none');
            progressBar.style.width = '0%';
            progressBar.textContent = '0%';
            statusMessage.textContent = 'Iniciando descarga...';

            const downloadResponse = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: urlInput, format })
            });

            if (!downloadResponse.ok) {
                const errorData = await downloadResponse.json();
                throw new Error(errorData.error || 'Error en la descarga');
            }

            // Iniciar seguimiento del progreso
            let progress = 0;
            const progressInterval = setInterval(async () => {
                const progressResponse = await fetch('/progress');
                const progressData = await progressResponse.json();
                progress = progressData.progress;

                progressBar.style.width = `${progress}%`;
                progressBar.textContent = `${progress}%`;

                if (progress >= 100) {
                    clearInterval(progressInterval);
                    statusMessage.textContent = '¡Descarga completada!';
                }
            }, 1000);

            // Descargar el archivo
            const blob = await downloadResponse.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = 'instagram-content';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);

        } catch (error) {
            showError(error.message);
            progressContainer.classList.add('d-none');
        }
    });

    function showError(message) {
        errorContainer.classList.remove('d-none');
        errorContainer.textContent = message;
    }

    function formatDate(dateStr) {
        if (!dateStr || dateStr === 'Desconocido') return 'Desconocido';
        const year = dateStr.slice(0, 4);
        const month = dateStr.slice(4, 6);
        const day = dateStr.slice(6, 8);
        return `${day}/${month}/${year}`;
    }

    function formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    function formatNumber(num) {
        if (!num) return '0';
        return num.toLocaleString('es-ES');
    }
});
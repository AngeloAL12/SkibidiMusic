# Usamos la imagen híbrida oficial
FROM nikolaik/python-nodejs:python3.11-nodejs20

# 1. Instalar FFmpeg y herramientas
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# 2. HACK DE SEGURIDAD: Crear enlace manual de 'node'
# A veces yt-dlp busca 'node' en /usr/local/bin y no lo ve
RUN ln -s $(which node) /usr/local/bin/node || true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

CMD ["python", "main.py"]
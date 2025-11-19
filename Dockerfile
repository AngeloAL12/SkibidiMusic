# Usamos una imagen que YA TIENE Python 3.11 y Node.js 20
# Esto garantiza que yt-dlp encuentre el runtime de JS
FROM nikolaik/python-nodejs:python3.11-nodejs20

# Solo necesitamos instalar FFmpeg (Node y Python ya están)
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# El flag --break-system-packages es necesario en versiones nuevas de Python/Debian
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

CMD ["python", "main.py"]
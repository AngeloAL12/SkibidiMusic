# Usamos la imagen que trae Python y Node preinstalados
FROM nikolaik/python-nodejs:python3.11-nodejs20

# Instalamos FFmpeg y Git
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Instalamos dependencias
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

CMD ["python", "main.py"]
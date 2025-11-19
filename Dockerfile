# Imagen híbrida oficial
FROM nikolaik/python-nodejs:python3.11-nodejs20

# Instalar FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# --- FIX DEFINITIVO PARA NODE.JS ---
# Creamos enlaces en todas las rutas posibles donde yt-dlp podría buscar
RUN ln -sf $(which node) /usr/local/bin/node || true && \
    ln -sf $(which node) /usr/bin/node || true && \
    ln -sf $(which node) /bin/node || true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

CMD ["python", "main.py"]
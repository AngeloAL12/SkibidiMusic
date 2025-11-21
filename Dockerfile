# Usamos la imagen híbrida
FROM nikolaik/python-nodejs:python3.11-nodejs20

# Instalar FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# --- LA SOLUCIÓN DEFINITIVA ---
# Enlazamos Node a /usr/bin (la carpeta que NUNCA falla)
# Aunque Node viva en /usr/local/bin, creamos un espejo en /usr/bin
RUN ln -sf /usr/local/bin/node /usr/bin/node && \
    ln -sf /usr/local/bin/node /usr/bin/nodejs

# Verificación durante la construcción (para que veas que sí se hizo)
RUN ls -l /usr/bin/node

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

CMD ["python", "main.py"]
# Imagen base híbrida (Python + Node)
FROM nikolaik/python-nodejs:python3.11-nodejs20

# 1. Instalar FFmpeg y herramientas
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# 2. EL FIX MAESTRO: Enlaces simbólicos a la fuerza
# Esto asegura que 'node' y 'nodejs' existan en /usr/bin y /usr/local/bin
RUN ln -sf /usr/local/bin/node /usr/bin/node && \
    ln -sf /usr/local/bin/node /usr/bin/nodejs && \
    ln -sf /usr/local/bin/node /usr/local/bin/nodejs

# 3. Imprimir la ubicación para confirmar en el log de construcción
RUN which node && node -v

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

CMD ["python", "main.py"]
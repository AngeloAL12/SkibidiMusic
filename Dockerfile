FROM python:3.11-bookworm

# 1. Instalar utilidades
RUN apt-get update && \
    apt-get install -y ffmpeg curl gnupg git && \
    rm -rf /var/lib/apt/lists/*

# 2. INSTALAR NODE.JS (Versión 18 LTS)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# 3. TRUCO FINAL: Crear enlace simbólico para que yt-dlp encuentre 'node'
# Esto soluciona el WARNING amarillo en Debian/Linux
RUN ln -s /usr/bin/nodejs /usr/local/bin/node || true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]
FROM nikolaik/python-nodejs:python3.11-nodejs20

RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

RUN ln -sf $(which node) /usr/local/bin/node || true && \
    ln -sf $(which node) /usr/bin/node || true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

CMD ["python", "main.py"]
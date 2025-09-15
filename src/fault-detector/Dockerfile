FROM python:3.7-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential iproute2 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir numpy==1.21.6 cython
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
FROM python:3.7-slim

ENV PYTHONWARNINGS="ignore::DeprecationWarning"

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential iproute2 && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "/bin/bash" ]
FROM python:3.10-slim

ARG CONFIG_FILE

WORKDIR /app

RUN apt update && apt install iproute2 -y
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY sensors/ ./sensors/
COPY images/ ./images/
COPY ${CONFIG_FILE} ./config.json

CMD [ "/bin/bash" ]
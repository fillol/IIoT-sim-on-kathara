FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt update && apt install iproute2 -y #iputils-ping netcat-openbsd -y

COPY . .
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]

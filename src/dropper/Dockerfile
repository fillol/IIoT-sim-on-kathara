FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# This dependency is useful for network diagnostics within the container
RUN apt update && apt install iproute2 -y

COPY . .

RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
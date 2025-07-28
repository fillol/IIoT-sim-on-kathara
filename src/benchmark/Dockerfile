FROM python:3.10-slim
RUN apt-get update && apt-get install -y apache2-utils curl && rm -rf /var/lib/apt/lists/*
RUN pip install numpy
WORKDIR /app
COPY . .
RUN chmod +x ./benchmark.sh
ENTRYPOINT ["./benchmark.sh"]
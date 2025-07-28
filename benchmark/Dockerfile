FROM python:3.10-slim

# Install dependencies: apache-utils for 'ab' and curl
RUN apt-get update && apt-get install -y apache2-utils curl && rm -rf /var/lib/apt/lists/*
RUN pip install numpy

WORKDIR /app

# Copy only the benchmark execution script
COPY benchmark.sh .
RUN chmod +x ./benchmark.sh

# The entrypoint runs the benchmark tests
ENTRYPOINT ["./benchmark.sh"]

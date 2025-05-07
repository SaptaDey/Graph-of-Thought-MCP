FROM python:3.11-slim-bookworm AS base

WORKDIR /app

# Update packages and install dependencies with latest security patches
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gfortran \
    libopenblas-dev \
    pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Update setuptools to address CVE-2024-6345
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --upgrade pip setuptools>=70.0.0 && \
    pip install --no-cache-dir -r requirements.txt

RUN mkdir -p client config logs

COPY config/ config/
COPY client/ client/
COPY src/ src/
COPY index.html ./
COPY start.sh ./

RUN chmod +x start.sh

EXPOSE 8082

ENV PYTHONUNBUFFERED=1 \
    MCP_SERVER_PORT=8082 \
    LOG_LEVEL=INFO

CMD ["sh", "-c", "cd src && python server.py"]
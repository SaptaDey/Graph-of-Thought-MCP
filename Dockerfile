# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies (including gfortran for scipy)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl gfortran pkg-config libopenblas-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt with bind mount for better caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p logs client config

# Copy the rest of the application code
COPY config/ config/
COPY client/ client/
COPY src/ src/
COPY index.html ./
COPY start.sh ./

# Make scripts executable
RUN chmod +x start.sh

# Expose the API port
EXPOSE 8082

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    MCP_SERVER_PORT=8082 \
    LOG_LEVEL=INFO

# Default command: run the FastAPI server
CMD ["sh", "-c", "cd src && python server.py"]

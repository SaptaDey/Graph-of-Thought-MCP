#!/bin/bash

# Create necessary directories
mkdir -p logs

# Build and start the Docker container
echo "Building and starting ASR-GoT MCP Server..."
docker-compose up --build -d

# Wait for the server to start
echo "Waiting for server to start..."
sleep 5

# Check if the server is running (note port 8082 is used for external access)
if curl -s http://localhost:8082/health | grep -q "healthy"; then
    echo "ASR-GoT MCP Server is running!"
    echo "API available at: http://localhost:8082/api/v1"
    echo "Test client available at: http://localhost:80"
else
    echo "Server startup failed. Check logs with: docker-compose logs"
fi

echo "Use Ctrl+C to stop watching logs, or run 'docker-compose down' to stop the server"
docker-compose logs -f
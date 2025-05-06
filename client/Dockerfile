# syntax=docker/dockerfile:1

# This Dockerfile serves static assets for the client.
FROM nginx:alpine

# Copy static assets into nginx html directory
COPY script.js styles.css /usr/share/nginx/html/

# Create a simple index.html if it doesn't exist
RUN echo '<!DOCTYPE html><html><head><title>ASR-GoT MCP Client</title><link rel="stylesheet" href="styles.css"></head><body><h1>ASR-GoT MCP Client</h1><div id="app"></div><script src="script.js"></script></body></html>' > /usr/share/nginx/html/index.html

# Expose nginx default port
EXPOSE 80

# Start nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]

# syntax=docker/dockerfile:1

# This Dockerfile serves static assets for the client.
FROM nginx:alpine

# Copy static assets into nginx html directory
COPY script.js styles.css /usr/share/nginx/html/

# Copy index.html directly from this directory
COPY index.html /usr/share/nginx/html/index.html

# Expose nginx default port
EXPOSE 80

# Start nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]

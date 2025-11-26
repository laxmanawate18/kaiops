#!/bin/sh
# Frontend entrypoint script
# Validates nginx configuration and starts the server
# All proxy configurations are already in nginx.conf

echo "✅ Starting KaiOPS Frontend..."

echo "Validating nginx configuration..."
nginx -t
if [ $? -ne 0 ]; then
    echo "❌ nginx configuration validation failed!"
    exit 1
fi

echo "✅ nginx configuration is valid"
echo "Starting nginx daemon..."

# Start nginx in foreground (required for Docker containers)
exec nginx -g "daemon off;"

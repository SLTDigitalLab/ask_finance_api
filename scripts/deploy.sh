#!/bin/bash
set -euo pipefail

echo "🚀 Starting ASK Finance API deployment..."

cd ~/ask-finance

echo "📦 Pulling latest code..."
git fetch origin main
git reset --hard origin/main


echo "🛑 Stopping and removing old containers, networks, and volumes..."
docker compose down -v || echo "⚠️ No containers/networks/volumes to remove, continuing..."

# Optional: Check if ports are in use
PORTS=(8000 5432 6333) # Add all exposed ports here
for PORT in "${PORTS[@]}"; do
    if lsof -i :"$PORT" &>/dev/null; then
        echo "⚠️ Port $PORT is in use. Attempting to free it..."
        PID=$(lsof -ti :"$PORT")
        kill -9 $PID || echo "⚠️ Failed to kill process on port $PORT. Deployment may fail."
    fi
done

echo "💻 Building frontend (Vite)..."
cd client/theaisleai
npm install
npm run build

echo "📂 Updating frontend_build directory..."
rm -rf ../../frontend_build/*
cp -r dist/* ../../frontend_build/

cd ../../

echo "🐳 Rebuilding containers..."
docker compose up -d --build || { echo "❌ Docker compose failed"; exit 1; }

echo "⏳ Waiting for containers to stabilize..."
sleep 15

echo "📊 Containers running:"
docker compose ps

echo "🔧 Validating system nginx configuration..."
if nginx -t; then
    echo "✅ Nginx config OK. Restarting nginx..."
    systemctl restart nginx
else
    echo "❌ Nginx config test failed. Aborting deployment."
    exit 1
fi

echo "🔍 Checking nginx status..."
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx is running"
else
    echo "❌ Nginx is not running. Check logs!"
    exit 1
fi

echo "🎉 Deployment completed successfully!"

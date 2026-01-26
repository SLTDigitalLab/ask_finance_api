#!/bin/bash
set -euo pipefail

echo "🚀 Starting ASK Finance API deployment..."

# Move to project directory
cd ~/ask-finance || { echo "❌ Directory ~/ask-finance not found"; exit 1; }

# --- GIT UPDATE ---
echo "📦 Fetching latest code from main branch..."
git fetch origin main || { echo "❌ Git fetch failed"; exit 1; }

# Reset local changes to match remote
echo "🔄 Resetting local changes..."
git reset --hard origin/main || { echo "❌ Git reset failed"; exit 1; }

# --- DOCKER CLEANUP ---
echo "🛑 Stopping and removing old containers, networks, and volumes..."
docker compose down -v || echo "⚠️ No containers/networks/volumes to remove, continuing..."

# --- FREE PORTS IF IN USE ---
PORTS=(8000 5432 6333) # Add all exposed ports here
for PORT in "${PORTS[@]}"; do
    if lsof -i :"$PORT" &>/dev/null; then
        echo "⚠️ Port $PORT is in use. Attempting to free it..."
        PID=$(lsof -ti :"$PORT")
        kill -9 $PID || echo "⚠️ Failed to kill process on port $PORT. Deployment may fail."
    fi
done

# --- FRONTEND BUILD ---
echo "💻 Building frontend (Vite)..."
cd client/theaisleai || { echo "❌ Frontend directory not found"; exit 1; }
npm install || { echo "❌ npm install failed"; exit 1; }
npm run build || { echo "❌ Frontend build failed"; exit 1; }

echo "📂 Updating frontend_build directory..."
rm -rf ../../frontend_build/*
cp -r dist/* ../../frontend_build/

cd ../../ || { echo "❌ Failed to return to project root"; exit 1; }

# --- DOCKER BUILD ---
echo "🐳 Rebuilding containers..."
docker compose up -d --build || { echo "❌ Docker compose build failed"; exit 1; }

echo "⏳ Waiting 15s for containers to stabilize..."
sleep 15

echo "📊 Current containers:"
docker compose ps

# --- NGINX CHECK ---
echo "🔧 Validating system nginx configuration..."
if nginx -t; then
    echo "✅ Nginx config OK. Restarting nginx..."
    systemctl restart nginx || { echo "❌ Failed to restart nginx"; exit 1; }
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

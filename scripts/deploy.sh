#!/bin/bash
set -e

echo "Starting ASK Finance API deployment..."

cd ~/ask-finance

echo "Pulling latest code..."
git pull origin main

echo "Stopping containers..."
docker compose down

echo "Building frontend (Vite)..."
cd client/theaisleai
npm install
npm run build

echo "Updating frontend_build directory..."
rm -rf ../../frontend_build/*
cp -r dist/* ../../frontend_build/

cd ../../

echo "Rebuilding containers..."
docker compose up -d --build

echo "Waiting for containers to stabilize..."
sleep 15

echo "Containers running:"
docker compose ps

echo "Validating system nginx configuration..."
if nginx -t; then
  echo "Restarting system nginx..."
  systemctl restart nginx
else
  echo "❌ Nginx config test failed. Aborting deployment."
  exit 1
fi

echo "🔍 Checking nginx status..."
systemctl is-active --quiet nginx && echo "✅ Nginx is running"

echo "✅ Deployment completed successfully!"

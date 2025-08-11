#!/bin/bash

echo "🚀 Deploying updated RAG implementation to VCL server..."

# Copy the updated Gemini service
echo "📁 Copying updated gemini_service.py..."
scp backend/services/gemini_service.py dsingh23@152.7.177.154:/var/www/mini-task/backend/services/

# Restart the backend service
echo "🔄 Restarting backend service..."
ssh dsingh23@152.7.177.154 "sudo systemctl restart mini-task-backend"

# Check service status
echo "📊 Checking service status..."
ssh dsingh23@152.7.177.154 "sudo systemctl status mini-task-backend"

echo "✅ Deployment complete!"
echo "🌐 Test the updated RAG at: http://152.7.177.154:8000"

#!/bin/bash

# Final deployment script for Mini-task application
set -e

echo "🚀 Starting final deployment of Mini-task application..."

# Extract the fixed application
echo "📦 Extracting fixed application..."
cd /var/www
sudo rm -rf mini-task
sudo mkdir mini-task
sudo chown $USER mini-task
cd mini-task
tar -xzf ~/mini-task-app-fixed.tar.gz --strip-components=1

# Set up backend
echo "🐍 Setting up Python backend..."
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚠️  Please create .env file with GEMINI_API_KEY"
    echo "GEMINI_API_KEY=your_api_key_here" > .env
fi

# Set up frontend
echo "⚛️  Setting up React frontend..."
cd ../frontend

# Install Node.js dependencies
npm install

# Build the frontend
echo "🏗️  Building frontend..."
npm run build

# Set up Nginx configuration
echo "🌐 Setting up Nginx..."
sudo tee /etc/nginx/sites-available/mini-task << EOF
server {
    listen 80;
    server_name 152.7.177.154;

    # Frontend
    location / {
        root /var/www/mini-task/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/mini-task /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Create systemd service for backend
echo "🔧 Setting up backend service..."
sudo tee /etc/systemd/system/mini-task-backend.service << EOF
[Unit]
Description=Mini-task Backend API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/var/www/mini-task/backend
Environment=PATH=/var/www/mini-task/backend/venv/bin
ExecStart=/var/www/mini-task/backend/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start services
sudo systemctl daemon-reload
sudo systemctl enable mini-task-backend
sudo systemctl start mini-task-backend

# Check service status
echo "📊 Checking service status..."
sudo systemctl status mini-task-backend --no-pager

echo "✅ Deployment completed!"
echo "🌐 Frontend: http://152.7.177.154"
echo "🔧 Backend API: http://152.7.177.154/api"
echo "📊 Health check: http://152.7.177.154/health"
echo ""
echo "📝 To view logs: sudo journalctl -u mini-task-backend -f"
echo "🔄 To restart: sudo systemctl restart mini-task-backend"

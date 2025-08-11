#!/bin/bash

echo "🚀 Mini-task Application Access Script"
echo "======================================"
echo ""

# Check if ports are available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

echo "Checking port availability..."
check_port 8080
check_port 8001

echo ""
echo "Setting up SSH tunnels..."
echo ""

# Create background SSH tunnels
echo "📡 Creating SSH tunnel for frontend (port 8080)..."
ssh -f -N -L 8080:localhost:80 dsingh23@152.7.177.154

echo "📡 Creating SSH tunnel for backend (port 8001)..."
ssh -f -N -L 8001:localhost:8000 dsingh23@152.7.177.154

echo ""
echo "✅ SSH tunnels established!"
echo ""
echo "🌐 Access your application at:"
echo "   Frontend: http://localhost:8080"
echo "   Backend API: http://localhost:8001"
echo "   Health Check: http://localhost:8001/health"
echo ""
echo "🔧 To stop the tunnels, run:"
echo "   pkill -f 'ssh -f -N -L'"
echo ""
echo "📝 To view logs:"
echo "   ssh dsingh23@152.7.177.154 'sudo journalctl -u mini-task-backend -f'"

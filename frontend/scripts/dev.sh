#!/bin/bash

echo "🚀 Starting Mini-task Frontend in Development Mode"
echo "=================================================="
echo ""
echo "📡 Backend URL: http://localhost:8000"
echo "🌐 Frontend URL: http://localhost:3000"
echo ""
echo "Make sure your backend is running on localhost:8000"
echo ""

# Set environment variable for development
export REACT_APP_USE_PROD_BACKEND=false

# Start the development server
npm start

#!/bin/bash

echo "🚀 Starting Mini-task Frontend with Production Backend"
echo "======================================================"
echo ""
echo "📡 Backend URL: http://152.7.177.154:8000"
echo "🌐 Frontend URL: http://localhost:3000"
echo ""
echo "This will connect to the VCL server backend"
echo ""

# Set environment variable for production backend
export REACT_APP_USE_PROD_BACKEND=true

# Start the development server
npm start

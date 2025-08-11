#!/usr/bin/env python3
"""
Simple CORS Proxy for Mini-task Backend
This allows HTTPS frontend to communicate with HTTP backend
"""

from flask import Flask, request, Response
import requests
import logging
import ssl

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Backend URL
BACKEND_URL = "http://localhost:8000"

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    """Proxy all requests to the backend"""
    try:
        # Construct the full URL
        url = f"{BACKEND_URL}/{path}"
        
        # Get the request method and data
        method = request.method
        headers = {key: value for key, value in request.headers if key.lower() not in ['host', 'content-length']}
        
        # Get request data
        data = request.get_data()
        
        # Make the request to the backend
        logger.info(f"Proxying {method} {url}")
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            params=request.args,
            stream=True
        )
        
        # Create response
        proxy_response = Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
        
        # Add CORS headers
        proxy_response.headers['Access-Control-Allow-Origin'] = '*'
        proxy_response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        proxy_response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return proxy_response
        
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return Response(
            f"Proxy error: {str(e)}",
            status=500,
            headers={'Access-Control-Allow-Origin': '*'}
        )

@app.route('/health')
def health():
    """Health check endpoint"""
    return Response(
        '{"status": "proxy_healthy"}',
        status=200,
        headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}
    )

if __name__ == '__main__':
    logger.info("Starting CORS Proxy on port 8443 with HTTPS")
    
    # SSL context for HTTPS
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')
    
    app.run(host='0.0.0.0', port=8443, debug=False, ssl_context=context)

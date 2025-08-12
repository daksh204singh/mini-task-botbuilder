# TutorBot Backend

FastAPI backend for TutorBot with Gemini API integration.

## Features

- 🤖 Gemini API integration for AI responses
- 💬 Chat endpoint with conversation history
- 🎭 Support for custom personas
- 📊 Response time and token usage tracking
- 🔒 Environment-based configuration
- 🚀 FastAPI with automatic API documentation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:3000
```

### 3. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

## Running the Server

### Development Mode

```bash
python run.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
- `GET /health` - Check server status

### Chat
- `POST /chat` - Send messages and get AI responses

### Models
- `GET /models` - Get available AI models

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Chat API Usage

### Request Format

```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is photosynthesis?",
      "timestamp": "2025-01-11T10:30:00Z"
    },
    {
      "role": "assistant", 
      "content": "Photosynthesis is...",
      "timestamp": "2025-01-11T10:30:05Z"
    }
  ],
  "persona": {
    "bot_name": "ScienceTutor",
    "persona": "You are a helpful science tutor",
    "model": "gemini-2.0-flash-exp"
  }
}
```

### Response Format

```json
{
  "response": "Here's a detailed explanation...",
  "model": "gemini-2.0-flash-exp",
  "response_time": 1.234,
  "tokens_used": 150,
  "conversation_id": "conv_123456",
  "session_id": "sess_123456",
  "context_used": true
}
```

## Error Handling

The API includes comprehensive error handling:
- Invalid API keys
- Network issues
- Rate limiting
- Malformed requests

## Development

### Project Structure

```
backend/
├── main.py              # FastAPI application
├── run.py               # Startup script
├── requirements.txt     # Python dependencies
├── services/
│   ├── __init__.py
│   └── gemini_service.py  # Gemini API service
├── env.example          # Environment template
└── README.md           # This file
```

### Adding New Features

1. Create new service modules in `services/`
2. Add new endpoints in `main.py`
3. Update requirements.txt if needed
4. Test with the API documentation

## Troubleshooting

### Common Issues

1. **API Key Error**: Make sure your Gemini API key is valid and properly set in `.env`
2. **CORS Issues**: Check that `FRONTEND_URL` is correctly set
3. **Port Already in Use**: Change the port in `.env` or kill the existing process

### Logs

The server logs all requests and errors. Check the console output for debugging information.

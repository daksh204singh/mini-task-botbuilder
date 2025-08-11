# Mini Technical Task: Bot Config + Chat

A full-stack web application that allows users to configure a chatbot and interact with it through a chat interface.

## Tech Stack

- **Frontend**: React + TypeScript
- **Backend**: Python + FastAPI
- **LLM Integration**: OpenAI API (with fallback to mocked responses)

## Project Structure

```
Mini-task/
├── frontend/          # React + TypeScript application
├── backend/           # Python FastAPI server
└── README.md         # This file
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. Run the backend server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`

## Features

- **Bot Configuration Form**: Configure bot name, persona, and model selection
- **Chat Interface**: Send messages and receive bot responses
- **LLM Integration**: Real OpenAI API integration with fallback to mocked responses
- **Chat Logging**: Track the last 5 chat interactions with timestamps

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- Additional endpoints will be added as the application develops

## Development Notes

- The application uses CORS to allow frontend-backend communication
- Environment variables are used for configuration
- The backend includes basic error handling and logging structure

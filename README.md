# Mini-task Chatbot — Engineering Report

This document records the design and implementation work behind a conversational AI prototype built under mini-task constraints. The goal was to provide fast, contextually grounded tutoring-style assistance with clear persona control and basic safety.

## Summary

- Built a FastAPI backend and a React (TypeScript) frontend for a chatbot that uses Google Gemini via LangChain.
- Moved from naive full-history prompting to a hybrid of per-conversation vector retrieval and rolling summaries.
- Introduced a system prompt that explicitly encodes bot name/persona and safety guidance.
- Achieved lower latency and better scalability while maintaining higher-level continuity across turns.

## Objectives

- Minimize latency and cost as chat history grows.
- Preserve higher-level conversation continuity without exceeding context limits.
- Allow configurable bot name and persona, while maintaining basic safety.
- Keep the solution small and maintainable within a mini-task scope.

## Iterations and Key Decisions

- Iteration 1: Full-history prompting
  - The client pushed the entire message history to the LLM every turn.
  - Response quality was strong due to full context, but it did not scale. Input sizes grew each turn, increasing latency and token costs, and hitting model context limits.

- Iteration 2: Backend and in-memory vector retrieval (FAISS)
  - Introduced a FastAPI backend and an in-memory `VectorService` using Sentence-Transformers (all-MiniLM-L6-v2) and FAISS.
  - Retrieval injected only the most relevant snippets from earlier messages, reducing prompt size while preserving specific context.
  - This improved latency and made costs predictable; however, retrieval alone missed higher-level discourse (goals, progress, meta-structure of the chat).

- Iteration 3: Rule-based RAG
  - Added heuristics to stitch in higher-level narrative and goals.
  - The approach worked for specific cases but was brittle and hard to extend. Rule growth increased code complexity and maintenance burden.

- Iteration 4: Rolling summaries with LangChain
  - Adopted `ConversationSummaryBufferMemory` to maintain a concise, running summary used as `{history}` in prompts.
  - Combined vector retrieval (precise snippets) with summarized history (higher-level continuity).
  - Integrated with `ConversationChain` and `ChatPromptTemplate` for clearer prompting.

## Prompting and Safety

- System prompt carries identity and safety, with higher authority than user turns. Bot name and persona are injected into the system message, while the human turn carries the current question and retrieved snippets.

```python
# Abbreviated structure used at runtime
(
  "system",
  """You are an AI tutor named {bot_name}, acting as {persona}.\n
Conversation history (summarized as needed):\n{history}\n"""
)
(
  "human",
  "{input}"
)
```

- A lightweight safety layer is encoded in the system prompt to avoid harmful or unqualified advice, keep tone appropriate, and protect privacy. This acts as a guardrail while retaining generality.

## Current Architecture

- FastAPI initializes and holds singletons for three services:
  - `DatabaseService` (SQLite): persists conversations and messages; auto-initializes schema.
  - `VectorService` (FAISS + Sentence-Transformers): maintains a per-conversation in-memory index of recent messages.
  - `ChainService` (LangChain + Gemini): manages prompting, model selection per request, rolling summaries, and post-turn updates.
- For each conversation, `ConversationSummaryBufferMemory` caches a summary that fills `{history}`. On each turn, the vector index returns top-k similar snippets which are appended to the human input as context.
- The baseline model is `gemini-1.5-flash`, with per-request overrides (e.g., `gemini-2.0-flash-exp`) honored when chosen in the persona payload.

## Data Flow per Turn

- Receive latest user message and optional conversation/session identifiers.
- Ensure a conversation exists; persist the message in SQLite.
- Retrieve similar snippets from the per-conversation FAISS index (if any).
- Construct the dynamic prompt: system (bot name, persona, safety, `{history}`) + human (retrieved context + current question).
- Invoke the selected Gemini model through LangChain; return the response.
- In the background, persist the assistant message and update the vector index with the latest messages.

## Tech Stack

- Backend: FastAPI, Uvicorn, Pydantic, python-dotenv
- LLM and orchestration: LangChain, `langchain-google-genai`, Google Gemini
- Retrieval: Sentence-Transformers (all-MiniLM-L6-v2), FAISS, NumPy
- Storage: SQLite (conversations and messages)
- Frontend: React (TypeScript), React Markdown, remark/rehype plugins for math and code rendering

## Environment and Local Setup

The repository contains two applications: `backend/` (FastAPI) and `frontend/` (React + TypeScript). The system was developed and tested on Node 18+ and Python 3.10+.

Backend

```dotenv
# backend/.env
GEMINI_API_KEY=your_google_api_key_here
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:3000
```

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python run.py  # serves at http://localhost:8000
```

Frontend

```bash
cd frontend
npm install
npm run dev  # serves at http://localhost:3000
```

Environment-driven API base URL is resolved in `frontend/src/config.ts` and defaults to `http://localhost:8000` for local development. Markdown, math, and code rendering are enabled in `MessageBubble.tsx`.

## API Overview (for reviewers)

Base URL: `http://localhost:8000`

- GET `/health` → status + model info
- POST `/session` → `{ session_id }`
- POST `/chat` → main endpoint (accepts messages + persona; returns model result and timing)
- GET `/session/{session_id}/conversations` → list conversations
- GET `/conversation/{conversation_id}` → details + messages
- DELETE `/conversation/{conversation_id}` → delete conversation and vectors

## Results

- Latency improved as input sizes stabilized; only selective snippets and a summary are sent.
- Responses retained higher-level continuity via rolling summaries and remained sensitive to local context via retrieval.
- Prompt clarity improved through relocation of bot identity and safety into the system message.

## Known Limitations

- No account system: client-side session/cache determines which conversation a user sees; cache resets make prior threads appear missing in the UI (the backend retains messages).
- Persona safety: bot name/persona are not sanitized; malicious persona text could attempt to override guidance. Additional validation and immutable safety blocks would help.
- Presets for prompting: selecting personas and writing system prompts can be onerous. Quick-pick presets would reduce friction and provide soft guardrails for student scenarios.
- Vector persistence: FAISS indexes are in-memory and per-process; they reset on backend restart. A persistent or shared vector store would improve durability and horizontal scaling.
- Observability and controls: no auth, rate limits, or analytics in place.

## Future Work

- Add user accounts and secure session management; map client sessions to persistent identities.
- Introduce predefined, vetted personas and safety profiles; validate or strip unsafe persona text.
- Persist vector indexes (or use a managed vector DB) for durability and multi-instance deployment.
- Add operational features: rate-limiting, API keys, usage dashboards, and tracing.
- Extend safety with configurable policies per bot and per deployment context.


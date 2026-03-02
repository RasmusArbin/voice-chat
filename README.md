# AI Dealership Call Agent

A voice-based dealership call system built with OpenAI's Agents SDK. It uses Speech-to-Speech (S2S) to handle natural, real-time conversations with clients.

## Features

- **Real-time Voice Calls** with low-latency speech interaction
- **Multi-Agent Architecture** with reception and dealership roles
- **Session Persistence Infrastructure** for future conversation replay support
- **WebSocket Integration** for real-time bidirectional audio streaming
- **Voice Activity Detection** for natural interruption handling
- **Guardrails** for safe, professional responses
- **Language Enforcement** for English or Swedish only

## Project Structure

```
project/
├── docker-compose.yml
├── Dockerfile
├── README.md
├── client/
│   └── index.html
└── server/
    ├── main.py
    ├── dealership_agents.py
    ├── tools.py
    └── requirements.txt
```

## Setup

### Docker

1. Create `.env` in project root:

```bash
OPENAI_API_KEY=your-openai-api-key-here
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

2. Build and run:

```bash
docker-compose build
docker-compose up
```

3. Open `http://localhost:8000`

### Local Development

```bash
python -m venv venv
venv\Scripts\activate
cd server
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Configuration

- `OPENAI_API_KEY` (required): OpenAI API key
- `CORS_ORIGINS` (optional): Comma-separated allowed origins
- `LOG_LEVEL` (optional): `DEBUG`, `INFO`, `WARNING`, `ERROR`

## Dealership Agents

Defined in `server/dealership_agents.py`.

- `reception_agent`: Greets the caller and explains the flow
- `dealership_agent`: Handles needs discovery and follow-up actions

## Tools

Defined in `server/tools.py`.

- `get_dealership_info(location)`
- `check_calendar_availability(date, time_window)`
- `book_meeting(customer_name, date, time, purpose)`

## Endpoints

- `GET /` – client UI
- `GET /health` – health check
- `GET /session/{session_id}/history` – session debug history
- `WS /ws/{session_id}` – realtime audio/call session

## Troubleshooting

- Docker error about `dockerDesktopLinuxEngine` on Windows usually means Docker Desktop is not running.
- Start Docker Desktop and ensure Linux containers/WSL2 engine are enabled.
- If the mic fails, verify browser microphone permissions.

## Notes

- Session history capture is not fully implemented by current SDK event support.
- In production, replace in-memory session storage with Redis or a database.

# AI Dealership Call Agent

A voice-based dealership call system built with OpenAI's Agents SDK. It uses Speech-to-Speech (S2S) to handle natural, real-time conversations with clients.

## Features

- **Real-time Voice Calls** with low-latency speech interaction
- **Multi-Agent Architecture** with reception and dealership roles
- **Stateless Sessions** start fresh on each connection
- **WebSocket Integration** for real-time bidirectional audio streaming
- **Voice Activity Detection** for natural interruption handling
- **Guardrails** for safe, professional responses
- **Language Choice** - Reception asks Swedish or English at start and sticks to it

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
- `WS /ws/{session_id}` – realtime audio/call session

## Troubleshooting

- Docker error about `dockerDesktopLinuxEngine` on Windows usually means Docker Desktop is not running.
- Start Docker Desktop and ensure Linux containers/WSL2 engine are enabled.
- If the mic fails, verify browser microphone permissions.

## Notes

- Sessions are stateless; each connection starts a new call.

## Known Issues / Limitations

- Language switching can be inconsistent; the handoff note is sometimes not honored, so the dealership agent may default to Swedish.
- Handoff can result in silence or delayed speech from the dealership agent in some sessions.
- The dealership agent can apologize after handoff despite prompt guidance.
- Calls must be ended by the user via the UI; there is no automatic call termination.
- Agent interruption can still occur due to background audio or mic sensitivity, especially at session start.
- Duplicate "Agent active" events have been observed after handoff when triggers or timing overlap.

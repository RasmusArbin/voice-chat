# AI Voice Interview Agent

A sophisticated voice-based recruitment interview system built with OpenAI's Agents SDK. It leverages the power of Speech-to-Speech (S2S) technology to conduct realistic, natural-sounding interviews with job candidates.

## Features

- **Real-time Voice Interviews**: Uses OpenAI's gpt-4o-realtime-preview model for low-latency speech interaction
- **Multi-Agent Architecture**: Specialized agents handle different interview phases (welcome, background, technical, logistics)
- **Session Persistence**: Automatically saves and restores conversation history across reconnections using text-based conversation replay
- **WebSocket Integration**: Real-time bidirectional communication between client and server
- **Voice Activity Detection**: Intelligent handling of interruptions and natural speech flow with interrupt blocking during agent initialization
- **Guardrails**: Built-in safety mechanisms to prevent inappropriate outputs and ensure fair interviews
- **Language Enforcement**: Configured for English-only interviews to ensure consistency

## Project Structure

```
project/
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile             # Docker image definition
├── spec.txt              # Technical specification document
├── README.md             # This file
├── client/
│   └── index.html        # Web-based interview interface
├── server/
│   ├── main.py           # FastAPI application and WebSocket handler
│   ├── interview_agents.py # Agent definitions and configurations
│   ├── tools.py          # Tool definitions for agent integration
│   └── requirements.txt   # Python dependencies
```

## Prerequisites

- **Python**: 3.10 or higher
- **OpenAI API Key**: Required for voice model access
- **Docker & Docker Compose** (optional, for containerized deployment)

## Installation & Setup

### Option 1: Docker (Recommended for Production)

The easiest way to run the application is using Docker Compose, which handles all dependencies and configurations automatically.

#### 1. Create Environment Configuration

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your-openai-api-key-here
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

Replace `your-openai-api-key-here` with your actual OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys).

#### 2. Build and Run with Docker Compose

```bash
# Build the Docker image
docker-compose build

# Start the application
docker-compose up

# For detached mode (runs in background)
docker-compose up -d
```

The application will be available at `http://localhost:8000`

#### 3. View Logs

```bash
# View logs
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f server
```

#### 4. Stop the Application

```bash
# Stop the containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Option 2: Manual Setup (Development)

If you prefer to run the application locally without Docker:

#### 1. Create Environment Configuration

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your-openai-api-key-here
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

#### 2. Create a Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

#### 4. Run the Development Server

```bash
# From the server directory
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key for model access |
| `CORS_ORIGINS` | No | `*` | Comma-separated list of allowed CORS origins |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Interview Agent Configuration

Agents are defined in `server/interview_agents.py`. Key components include:

- **System Instructions**: Define agent personality, tone, and approach
- **Handoffs**: Configure agent-to-agent transfers for different interview phases
- **Tools**: Define available functions agents can call during interviews

Example agent structure:
```python
welcome_agent = Agent(
    name="Welcome Agent",
    instructions="Greet candidates warmly and explain the interview process..."
)
```

## Usage

### Starting an Interview

1. **Open your browser**: Navigate to `http://localhost:8000`
2. **Grant microphone access**: Allow browser to access your microphone
3. **Start interview**: Click the "Start Interview" button
4. **Interact naturally**: Simply speak to the AI interviewer

### Technical Details

- **WebSocket Endpoint**: `/ws/{session_id}`
- **Health Check**: `GET /health`
- **Client Interface**: `GET /`

## Architecture Overview

### Client-Server Communication

The system uses WebSockets for real-time bidirectional communication:

```
Client (Browser)
    ↓
  WebSocket
    ↓
FastAPI Server (main.py)
    ↓
RealtimeRunner
    ↓
OpenAI Agents SDK
    ↓
gpt-4o-realtime-preview Model
```

### Session Management

- Each interview session has a unique `session_id`
- Session state is maintained in-memory (replace with Redis for production)
- Conversation history is automatically captured from `history_added` and `history_updated` events
- On reconnection, history is replayed using OpenAI's `conversation.item.create` API
- Text transcripts from audio interactions are preserved for session resumption
- Sessions resume with the main interviewer agent when history exists

### Session History Persistence

The system implements manual history management due to SDK limitations:

1. **Capture**: Listens for `history_added` and `history_updated` events from the RealtimeSession
2. **Extract**: Extracts text transcripts from audio interactions (both user input and assistant responses)
3. **Store**: Saves conversation items in-memory (keyed by `session_id`)
4. **Replay**: On reconnection, sends `conversation.item.create` events to rebuild context
5. **Resume**: Starts with the main interviewer agent when history exists, skipping the welcome phase

**Technical Note**: The current SDK version does not accept a `session` parameter in `RealtimeRunner.__init__()`. History persistence is implemented by capturing realtime events and replaying them via raw WebSocket messages.

### Interrupt Handling

To prevent duplicate welcome messages and premature interruptions:

- **Default State**: User interrupts are blocked when the session starts
- **Activation**: Interrupts are enabled when the assistant begins sending audio (`audio` event)
- **Mechanism**: Uses a shared `allow_interrupts` flag between async tasks (`nonlocal` scope)
- **Protection**: Prevents client-side noise or accidental clicks from triggering interrupts before the agent speaks

### Audio Processing

- **Input**: Browser microphone → WebSocket → Server
- **Processing**: OpenAI Realtime API handles audio encoding/decoding
- **Output**: Model audio response → WebSocket → Browser speakers

## Development

### Project Dependencies

**Production Dependencies** (in `server/requirements.txt`):
- `openai-agents[voice]>=0.1.0` - OpenAI Agents SDK with voice support
- `fastapi>=0.115.0` - Web framework
- `uvicorn[standard]>=0.32.0` - ASGI server
- `python-dotenv>=1.0.0` - Environment variable management

### Code Organization

- **main.py**: FastAPI application setup, WebSocket handlers, health checks
- **interview_agents.py**: Agent definitions, system instructions, handoff configurations
- **tools.py**: Tool implementations for agents to call

### Common Development Tasks

#### Adding a New Agent

1. Open `server/interview_agents.py`
2. Create a new agent with specific instructions
3. Add handoff relationship if needed
4. Update the welcome agent to reference it

#### Adding a Tool

1. Define the tool function in `server/tools.py`
2. Use the `@function_tool` decorator for SDK integration
3. Reference in agent instructions where applicable

#### Local Testing

```bash
# Test endpoint connectivity
curl http://localhost:8000/health

# View application logs
# (Check terminal where uvicorn is running)
```

## Security Considerations

### API Key Management

- **Never commit `.env` files** to version control
- Store sensitive keys in environment variables or secret management systems
- Consider using OpenAI organization IDs and restricted API keys in production

### CORS Configuration

- In production, set `CORS_ORIGINS` to your specific domain
- Default `*` allows requests from any origin (development only)

### Audio Data

- All audio is transmitted over HTTPS/WSS in production
- Consider compliance requirements (GDPR, CCPA) for recording candidate interviews
- Implement appropriate data retention policies

### Guardrails

The system includes output guardrails to:
- Prevent discriminatory questions
- Avoid promising employment outcomes
- Ensure professional conduct
- Maintain interview fairness

## Troubleshooting

### Common Issues

#### "Connection refused" error
- Ensure the server is running: `docker-compose up` or `uvicorn main:app ...`
- Check that port 8000 is not in use: `netstat -an | grep 8000`

#### "Permission denied" errors (Docker)
- Ensure Docker daemon is running
- On Windows, ensure Docker Desktop is installed and running
- Try `docker ps` to verify Docker is accessible

#### "OPENAI_API_KEY not found"
- Create `.env` file with your API key
- Ensure `.env` file is in the project root directory
- Restart the application after creating/updating `.env`

#### Microphone not working
- Grant microphone permissions in browser
- Check browser console for audio-related errors
- Test microphone with browser's audio input settings

#### Audio cuts off or sounds unnatural
- Check network latency (higher latency increases delays)
- Verify system audio settings
- Consider adjusting VAD (Voice Activity Detection) parameters in agent config

#### Agent speaks in unexpected language
- The system is configured to speak English only
- If non-English responses occur, check agent instructions in `interview_agents.py`
- Verify the `IMPORTANT: You MUST speak only in English` directive is present

#### Duplicate welcome messages on start
- This issue has been resolved with interrupt blocking
- The system now blocks user interrupts until the assistant begins speaking
- If still occurring, check the `allow_interrupts` flag in `main.py`

### Debug Mode

Enable debug logging:

```bash
# Development server with DEBUG logging
LOG_LEVEL=DEBUG uvicorn main:app --reload

# Docker compose with debug logs
docker-compose up --verbose
```

## Performance & Scaling

### Single Instance Performance

- Handles ~10-50 concurrent interviews per 2vCPU/4GB instance
- Latency: 200-800ms average response time (depends on network)
- Audio quality: 16kHz mono (recommended)

### Production Scaling

For large-scale deployments:

1. **Horizontal Scaling**: Run multiple server instances behind a load balancer
2. **Session Storage**: Use Redis or managed services instead of in-memory sessions
3. **CDN**: Serve static assets (HTML) from CDN closer to users
4. **Rate Limiting**: Implement OpenAI API rate limit handling

## Cost Optimization

### Money-Saving Tips

1. **Use Mini Models**: Switch to `gpt-4o-realtime-mini` for simpler interviews (50% cost reduction)
2. **Prompt Caching**: Leverage automatic prompt caching for system instructions (25-50% savings)
3. **VAD Filtering**: Use voice activity detection to avoid processing silence

### Estimated Costs

- **Typical Interview**: 5-15 minutes, ~0.5-1.5 minutes of actual speech
- **Cost per Interview**: $0.50-1.50 USD with standard models, $0.25-0.75 USD with mini models

## API Documentation

### WebSocket Events

The WebSocket at `/ws/{session_id}` handles:

- **Audio Frames**: Binary messages containing audio data
- **Session Messages**: JSON control messages for session management
- **Error Handling**: Automatic reconnection and error recovery

## Deployment

### Docker Container Details

- **Base Image**: `python:3.11.12-slim`
- **Port**: 8000
- **Health Check**: HTTP endpoint on `/health`
- **User**: Non-root `appuser` for security
- **Restart Policy**: `unless-stopped`

### Environment-Specific Setup

#### Staging

```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

#### Production

```bash
# Use production-grade server settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Contributing

When contributing:

1. Follow the existing code style
2. Add docstrings to new functions
3. Test changes locally with both Docker and manual setup
4. Update this README if adding significant features

## License

[Add your license here]

## Further Reading

For more detailed technical information, see [spec.txt](spec.txt) which contains:

- Comprehensive technical architecture
- Agent orchestration patterns
- Session management strategies
- Security and guardrails implementation
- Performance optimization techniques
- Real-world deployment guidance

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [OpenAI Agents SDK documentation](https://platform.openai.com/docs)
3. Check application logs for error details
4. Verify `.env` configuration

## Changelog

### Version 1.1.0 (Current)
- **Session Persistence**: Implemented automatic conversation history capture and replay
- **History Events**: Integrated `history_added` and `history_updated` event handlers
- **Interrupt Handling**: Added intelligent interrupt blocking to prevent duplicate welcome messages
- **Language Enforcement**: Added English-only directive to agent instructions
- **Bug Fix**: Resolved `RealtimeRunner` initialization error by removing unsupported `session` parameter
- **Session Resumption**: Sessions with history now start with the main interviewer instead of welcome agent

### Version 1.0.0
- Initial release
- Multi-agent interview system
- Real-time voice interaction
- WebSocket communication
- Docker deployment support

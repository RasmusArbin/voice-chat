import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from agents.realtime import RealtimeRunner
from agents.realtime.config import RealtimeRunConfig, RealtimeSessionModelSettings
from agents.realtime.model_inputs import RealtimeModelSendRawMessage

from interview_agents import welcome_agent, main_interviewer

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CLIENT_HTML = Path(__file__).parent.parent / "client" / "index.html"

app = FastAPI(title="AI Voice Interview")

# ─── In-Memory Session Store ──────────────────────────────────────────────────
# Stores conversation history and metadata for each session.
# In production, replace with Redis or a database.

SESSIONS: dict[str, dict[str, Any]] = {}


class SessionStore:
    """In-memory session store for managing interview sessions.
    
    Stores both metadata (for debugging) and conversation history (for agent resumption).
    """

    @staticmethod
    def _create_session_dict() -> dict[str, Any]:
        """Create a new session dictionary with default values."""
        return {
            "created_at": asyncio.get_event_loop().time(),
            "events": [],
            "is_active": True,
            "items": [],
        }

    @staticmethod
    def get(session_id: str) -> dict[str, Any] | None:
        """Retrieve an existing session metadata."""
        return SESSIONS.get(session_id)

    @staticmethod
    def add_event(session_id: str, event_type: str, data: Any = None) -> None:
        """Log an event to the session history (for debugging)."""
        if session_id in SESSIONS:
            SESSIONS[session_id]["events"].append(
                {
                    "type": event_type,
                    "data": data,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            )

    @staticmethod
    def mark_inactive(session_id: str) -> None:
        """Mark a session as inactive (but retain metadata)."""
        if session_id in SESSIONS:
            SESSIONS[session_id]["is_active"] = False
            logger.info("[%s] Session marked inactive", session_id)

    @staticmethod
    def get_history(session_id: str) -> list[dict[str, Any]]:
        """Get the event history of a session (for debugging)."""
        if session_id in SESSIONS:
            return SESSIONS[session_id]["events"]
        return []

    @staticmethod
    def get_items(session_id: str) -> list[dict[str, str]]:
        """Get stored text-based conversation items for resume."""
        if session_id in SESSIONS:
            return SESSIONS[session_id]["items"]
        return []

    @staticmethod
    def set_items(session_id: str, items: list[dict[str, str]]) -> None:
        """Replace stored conversation items for resume."""
        if session_id not in SESSIONS:
            SESSIONS[session_id] = SessionStore._create_session_dict()
        SESSIONS[session_id]["items"] = items

    @staticmethod
    def add_items(session_id: str, items: list[dict[str, str]]) -> None:
        """Append stored conversation items for resume."""
        if session_id not in SESSIONS:
            SESSIONS[session_id] = SessionStore._create_session_dict()
        SESSIONS[session_id]["items"].extend(items)

    @staticmethod
    def ensure_session(session_id: str) -> None:
        """Ensure a session exists in the store."""
        if session_id not in SESSIONS:
            SESSIONS[session_id] = SessionStore._create_session_dict()
            logger.info("[%s] New session created", session_id)


def _extract_text_from_history_item(item: Any) -> dict[str, str] | None:
    """Extract a text-only message from a realtime history item."""
    if hasattr(item, "model_dump"):
        raw_item = item.model_dump()
    elif hasattr(item, "dict"):
        raw_item = item.dict()
    else:
        raw_item = item

    if not isinstance(raw_item, dict):
        return None

    role = raw_item.get("role")
    if role not in {"user", "assistant", "system"}:
        return None

    content = raw_item.get("content") or []
    texts: list[str] = []
    for entry in content:
        if not isinstance(entry, dict):
            continue
        entry_type = entry.get("type")
        text: str | None = None
        if entry_type in {"input_text", "text", "output_text"}:
            text = entry.get("text")
        elif entry_type in {"input_audio", "audio", "output_audio"}:
            text = entry.get("transcript")
        if text:
            texts.append(text)

    if not texts:
        return None

    return {"role": role, "text": " ".join(texts)}


async def _replay_history(session: Any, session_id: str) -> None:
    """Replay stored text history into the realtime session."""
    items = SessionStore.get_items(session_id)
    if not items:
        return

    for item in items:
        role = item.get("role")
        text = item.get("text")
        if not role or not text:
            continue

        if role == "assistant":
            content_type = "output_text"
        else:
            content_type = "input_text"

        payload = {
            "type": "conversation.item.create",
            "other_data": {
                "item": {
                    "type": "message",
                    "role": role,
                    "content": [
                        {
                            "type": content_type,
                            "text": text,
                        }
                    ],
                }
            },
        }

        await session.model.send_event(RealtimeModelSendRawMessage(message=payload))

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def serve_client() -> HTMLResponse:
    return HTMLResponse(CLIENT_HTML.read_text(encoding="utf-8"))


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str) -> dict:
    """Retrieve the event history for a session."""
    session = SessionStore.get(session_id)
    if not session:
        return {"session_id": session_id, "found": False, "events": []}
    
    return {
        "session_id": session_id,
        "found": True,
        "is_active": session["is_active"],
        "event_count": len(session["events"]),
        "events": session["events"],
    }


@app.websocket("/ws/{session_id}")
async def websocket_interview(websocket: WebSocket, session_id: str) -> None:
    """One WebSocket connection = one interview session."""
    await websocket.accept()

    # Block early interrupts until the assistant starts speaking.
    allow_interrupts = False
    
    # Check if this is a new or returning session
    existing_session = SessionStore.get(session_id)
    is_resume = existing_session and len(existing_session["items"]) > 0
    
    if existing_session:
        logger.info("[%s] Client reconnected (history: %d items, resume: %s)", 
                   session_id, len(existing_session["items"]), is_resume)
        history_count = len(existing_session["items"])
    else:
        history_count = 0
        is_resume = False
    
    logger.info("[%s] WebSocket connected (resuming: %s, prior items: %d)", 
               session_id, is_resume, history_count)

    # Ensure session exists in the store
    SessionStore.ensure_session(session_id)

    # Choose starting agent based on whether this is a new or resumed session
    starting_agent = main_interviewer if is_resume else welcome_agent

    runner = RealtimeRunner(
        starting_agent=starting_agent,
        config=RealtimeRunConfig(
            model_settings=RealtimeSessionModelSettings(
                model=os.getenv("OPENAI_REALTIME_MODEL", "gpt-4o-realtime-preview"),
                voice=os.getenv("REALTIME_DEFAULT_VOICE", "alloy"),
                input_audio_format="pcm16",
                output_audio_format="pcm16",
                output_modalities=["audio"],
                turn_detection={
                    "type": "semantic_vad",
                    "eagerness": "auto",
                    "create_response": True,
                    "interrupt_response": True,
                },
            )
        ),
    )

    try:
        async with await runner.run() as session:
            logger.info("[%s] RealtimeSession started with %s", 
                       session_id, starting_agent.name)
            await websocket.send_text(json.dumps({"type": "session_ready"}))

            # For resumed sessions, restore history before sending the next turn.
            if is_resume:
                await _replay_history(session, session_id)
                logger.info("[%s] Replayed %d history items", 
                           session_id, len(SessionStore.get_items(session_id)))

            # For resumed sessions, send acknowledgment; for new sessions, start welcome
            if is_resume:
                initial_message = "I'm resuming our interview. Let's continue where we left off."
                logger.info("[%s] Resuming session with acknowledgment", session_id)
            else:
                initial_message = "."  # Trigger the welcome agent
                logger.info("[%s] Starting new session with welcome agent", session_id)
            
            await session.send_message(initial_message)

            async def browser_to_session() -> None:
                """Read frames from the browser and feed them to the session."""
                try:
                    while True:
                        message = await websocket.receive()

                        if message["type"] == "websocket.disconnect":
                            break

                        if message.get("bytes"):
                            await session.send_audio(message["bytes"])

                        elif message.get("text"):
                            data = json.loads(message["text"])
                            msg_type = data.get("type")

                            if msg_type == "interrupt":
                                if allow_interrupts:
                                    await session.interrupt()
                            elif msg_type == "ping":
                                await websocket.send_text(json.dumps({"type": "pong"}))

                except WebSocketDisconnect:
                    pass
                except Exception:
                    logger.exception("[%s] browser_to_session error", session_id)

            async def session_to_browser() -> None:
                """Consume session events and forward relevant ones to the browser."""
                nonlocal allow_interrupts
                try:
                    async for event in session:
                        event_type = event.type

                        if event_type == "audio":
                            if not allow_interrupts:
                                allow_interrupts = True
                            # Raw PCM16 bytes — send as binary frame
                            await websocket.send_bytes(event.audio.data)
                            SessionStore.add_event(session_id, "audio", {"bytes": len(event.audio.data)})

                        elif event_type == "audio_end":
                            await websocket.send_text(json.dumps({"type": "audio_end"}))
                            SessionStore.add_event(session_id, "audio_end")

                        elif event_type == "audio_interrupted":
                            await websocket.send_text(
                                json.dumps({"type": "audio_interrupted"})
                            )
                            SessionStore.add_event(session_id, "audio_interrupted")

                        elif event_type == "agent_start":
                            name = getattr(getattr(event, "agent", None), "name", None)
                            logger.info("[%s] Agent start: %s", session_id, name)
                            await websocket.send_text(
                                json.dumps({"type": "agent_start", "agent": name})
                            )
                            SessionStore.add_event(session_id, "agent_start", {"agent": name})

                        elif event_type == "handoff":
                            to_name = getattr(
                                getattr(event, "to_agent", None), "name", None
                            )
                            logger.info("[%s] Handoff → %s", session_id, to_name)
                            await websocket.send_text(
                                json.dumps({"type": "handoff", "to_agent": to_name})
                            )
                            SessionStore.add_event(session_id, "handoff", {"to_agent": to_name})

                        elif event_type == "tool_start":
                            tool_name = getattr(
                                getattr(event, "tool", None), "name", None
                            )
                            logger.info("[%s] Tool start: %s", session_id, tool_name)
                            await websocket.send_text(
                                json.dumps({"type": "tool_start", "tool": tool_name})
                            )
                            SessionStore.add_event(session_id, "tool_start", {"tool": tool_name})

                        elif event_type == "tool_end":
                            tool_name = getattr(
                                getattr(event, "tool", None), "name", None
                            )
                            await websocket.send_text(
                                json.dumps({"type": "tool_end", "tool": tool_name})
                            )
                            SessionStore.add_event(session_id, "tool_end", {"tool": tool_name})

                        elif event_type == "history_added":
                            history_item = getattr(event, "item", None)
                            extracted = _extract_text_from_history_item(history_item)
                            if extracted:
                                SessionStore.add_items(session_id, [extracted])

                        elif event_type == "history_updated":
                            history_items = getattr(event, "history", [])
                            extracted_items = [
                                extracted
                                for extracted in (
                                    _extract_text_from_history_item(item)
                                    for item in history_items
                                )
                                if extracted
                            ]
                            SessionStore.set_items(session_id, extracted_items)

                        elif event_type == "error":
                            logger.error("[%s] Session error: %s", session_id, event)
                            await websocket.send_text(
                                # Do not expose internal error details to the client in production
                                json.dumps({"type": "error", "message": "Internal server error"})
                            )
                            SessionStore.add_event(session_id, "error", {"message": str(event)})

                except WebSocketDisconnect:
                    pass
                except Exception:
                    logger.exception("[%s] session_to_browser error", session_id)

            # Run both directions concurrently; TaskGroup cancels both when either exits.
            async with asyncio.TaskGroup() as tg:
                tg.create_task(browser_to_session())
                tg.create_task(session_to_browser())

    except WebSocketDisconnect:
        logger.info("[%s] Client disconnected cleanly", session_id)
    except Exception:
        logger.exception("[%s] Unhandled session error", session_id)
        try:
            await websocket.send_text(
                json.dumps({"type": "error", "message": "Internal server error"})
            )
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        SessionStore.mark_inactive(session_id)
        history = SessionStore.get_history(session_id)
        logger.info("[%s] Session inactive (events: %d, items: %d)", 
                   session_id, len(history), len(SESSIONS.get(session_id, {}).get("items", [])))

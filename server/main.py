import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from agents.realtime import RealtimeRunner
from agents.realtime.config import RealtimeRunConfig, RealtimeSessionModelSettings

from interview_agents import welcome_agent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CLIENT_HTML = Path(__file__).parent.parent / "client" / "index.html"

app = FastAPI(title="AI Voice Interview")

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


@app.websocket("/ws/{session_id}")
async def websocket_interview(websocket: WebSocket, session_id: str) -> None:
    """One WebSocket connection = one interview session."""
    await websocket.accept()
    logger.info("[%s] Client connected", session_id)

    runner = RealtimeRunner(
        starting_agent=welcome_agent,
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
            logger.info("[%s] RealtimeSession started", session_id)
            await websocket.send_text(json.dumps({"type": "session_ready"}))

            # Kick off the Welcome Agent — without this the model waits
            # indefinitely for the user to speak first.
            await session.send_message(".")

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
                                await session.interrupt()
                            elif msg_type == "ping":
                                await websocket.send_text(json.dumps({"type": "pong"}))

                except WebSocketDisconnect:
                    pass
                except Exception:
                    logger.exception("[%s] browser_to_session error", session_id)

            async def session_to_browser() -> None:
                """Consume session events and forward relevant ones to the browser."""
                try:
                    async for event in session:
                        event_type = event.type

                        if event_type == "audio":
                            # Raw PCM16 bytes — send as binary frame
                            await websocket.send_bytes(event.audio.data)

                        elif event_type == "audio_end":
                            await websocket.send_text(json.dumps({"type": "audio_end"}))

                        elif event_type == "audio_interrupted":
                            await websocket.send_text(
                                json.dumps({"type": "audio_interrupted"})
                            )

                        elif event_type == "agent_start":
                            name = getattr(getattr(event, "agent", None), "name", None)
                            logger.info("[%s] Agent start: %s", session_id, name)
                            await websocket.send_text(
                                json.dumps({"type": "agent_start", "agent": name})
                            )

                        elif event_type == "handoff":
                            to_name = getattr(
                                getattr(event, "to_agent", None), "name", None
                            )
                            logger.info("[%s] Handoff → %s", session_id, to_name)
                            await websocket.send_text(
                                json.dumps({"type": "handoff", "to_agent": to_name})
                            )

                        elif event_type == "tool_start":
                            tool_name = getattr(
                                getattr(event, "tool", None), "name", None
                            )
                            logger.info("[%s] Tool start: %s", session_id, tool_name)
                            await websocket.send_text(
                                json.dumps({"type": "tool_start", "tool": tool_name})
                            )

                        elif event_type == "tool_end":
                            tool_name = getattr(
                                getattr(event, "tool", None), "name", None
                            )
                            await websocket.send_text(
                                json.dumps({"type": "tool_end", "tool": tool_name})
                            )

                        elif event_type == "error":
                            logger.error("[%s] Session error: %s", session_id, event)
                            await websocket.send_text(
                                json.dumps({"type": "error", "message": str(event)})
                            )

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
        logger.info("[%s] Session ended", session_id)

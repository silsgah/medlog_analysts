"""
AI Freight Copilot — Chat API.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.dependencies import get_container

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None


@router.post("")
async def ask_question(request: ChatRequest):
    """
    Send a question to the conversational AI copilot.
    
    Returns an evidence-backed insight response following the executive template.
    """
    container = get_container()
    try:
        message = await container.chat_service.ask(
            question=request.question,
            conversation_id=request.conversation_id,
        )
        return message.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_question(request: ChatRequest):
    """
    Stream a response for a question.
    """
    container = get_container()

    async def event_generator():
        async for chunk in container.chat_service.ask_stream(
            question=request.question,
            conversation_id=request.conversation_id,
        ):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for interactive chat.
    """
    await websocket.accept()
    container = get_container()

    try:
        while True:
            data = await websocket.receive_json()
            question = data.get("question", "")
            conversation_id = data.get("conversation_id")

            if not question:
                continue

            async for chunk in container.chat_service.ask_stream(
                question=question,
                conversation_id=conversation_id,
            ):
                await websocket.send_text(chunk)

            await websocket.send_json({"type": "end"})

    except WebSocketDisconnect:
        pass

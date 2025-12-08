"""Server-Sent Events (SSE) endpoint for real-time updates."""

import asyncio
import json
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict, Any, Set
from datetime import datetime
from auth.middleware import get_current_user

router = APIRouter(prefix="/events", tags=["events"])

# Store for connected clients (in production, use Redis pub/sub)
connected_clients: Set[asyncio.Queue] = set()


async def event_generator(request: Request, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """Generate SSE events for a connected client."""
    try:
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'data': {'timestamp': datetime.utcnow().isoformat()}})}\n\n"
        
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            try:
                # Wait for event with timeout for keep-alive
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                # Send keep-alive ping
                yield f"data: {json.dumps({'type': 'ping', 'data': {'timestamp': datetime.utcnow().isoformat()}})}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        connected_clients.discard(queue)


@router.get("/stream")
async def stream_events(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Stream real-time events to connected clients via SSE."""
    queue: asyncio.Queue = asyncio.Queue()
    connected_clients.add(queue)
    
    return StreamingResponse(
        event_generator(request, queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


async def broadcast_event(event_type: str, data: Dict[str, Any]):
    """Broadcast an event to all connected clients."""
    event = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    for queue in list(connected_clients):
        try:
            await queue.put(event)
        except Exception:
            # Remove disconnected clients
            connected_clients.discard(queue)


def broadcast_event_sync(event_type: str, data: Dict[str, Any]):
    """Synchronous wrapper for broadcasting events (for non-async contexts)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(broadcast_event(event_type, data))
        else:
            loop.run_until_complete(broadcast_event(event_type, data))
    except RuntimeError:
        # No event loop running, create new one
        asyncio.run(broadcast_event(event_type, data))


# Utility functions for common event types
def notify_meeting_complete(meeting_id: str, status: str = "DONE"):
    """Notify clients that meeting processing is complete."""
    broadcast_event_sync("meeting_processing_complete", {
        "meeting_id": meeting_id,
        "status": status,
    })


def notify_meeting_error(meeting_id: str, error_message: str):
    """Notify clients that meeting processing failed."""
    broadcast_event_sync("meeting_processing_error", {
        "meeting_id": meeting_id,
        "error": error_message,
    })


def notify_entity_change(entity_type: str, entity_id: str, action: str, extra_data: dict = None):
    """Notify clients of entity changes (task, risk, project, etc.)."""
    data = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
    }
    if extra_data:
        data.update(extra_data)
    
    event_type = f"{entity_type}_{action}"
    broadcast_event_sync(event_type, data)


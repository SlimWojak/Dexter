"""
Matrix E2EE communication skill for DEXTER.
Pushes bundle alerts and receives human commands.
"""
import os
import asyncio
from typing import Optional

# Matrix SDK (nio)
# pip install matrix-nio

MATRIX_HOMESERVER = os.getenv("MATRIX_HOMESERVER", "https://matrix.org")
MATRIX_USER_ID = os.getenv("MATRIX_USER_ID")  # @dexter:matrix.org
MATRIX_ACCESS_TOKEN = os.getenv("MATRIX_ACCESS_TOKEN")
MATRIX_ROOM_ID = os.getenv("MATRIX_ROOM_ID")  # !roomid:matrix.org


async def send_message(message: str, room_id: str = None) -> dict:
    """
    Send message to Matrix room.
    """
    try:
        from nio import AsyncClient
    except ImportError:
        return {"success": False, "error": "matrix-nio not installed. Run: pip install matrix-nio"}

    room = room_id or MATRIX_ROOM_ID
    if not all([MATRIX_HOMESERVER, MATRIX_USER_ID, MATRIX_ACCESS_TOKEN, room]):
        return {"success": False, "error": "Matrix credentials not configured in .env"}

    client = AsyncClient(MATRIX_HOMESERVER, MATRIX_USER_ID)
    client.access_token = MATRIX_ACCESS_TOKEN

    try:
        response = await client.room_send(
            room_id=room,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": message
            }
        )
        return {"success": True, "event_id": response.event_id}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        await client.close()


async def send_bundle_alert(bundle_id: str, metrics: dict) -> dict:
    """
    Send formatted bundle alert to Matrix.
    """
    video_title = metrics.get('video_title', 'Unknown')[:50]
    extracted = metrics.get('extracted', 0)
    validated = metrics.get('validated', 0)
    rejected = metrics.get('rejected', 0)
    rejection_rate = metrics.get('rejection_rate', 0)
    path = metrics.get('path', 'N/A')

    message = (
        f"**DEXTER BUNDLE CREATED**\n\n"
        f"**ID:** `{bundle_id}`\n"
        f"**Video:** {video_title}...\n"
        f"**Signatures:** {extracted} extracted -> {validated} validated\n"
        f"**Rejected:** {rejected} ({rejection_rate:.1%})\n"
        f"**Path:** `{path}`\n\n"
        f"Reply with:\n"
        f"- `APPROVE {bundle_id}` -- Mark for promotion\n"
        f"- `REJECT {bundle_id}` -- Flag issues\n"
        f"- `REVIEW {bundle_id}` -- Request detailed view"
    )

    return await send_message(message)


async def poll_commands(since_token: str = None) -> list[dict]:
    """
    Poll Matrix room for human commands.
    Returns list of command dicts.
    """
    try:
        from nio import AsyncClient
    except ImportError:
        return []

    if not all([MATRIX_HOMESERVER, MATRIX_USER_ID, MATRIX_ACCESS_TOKEN, MATRIX_ROOM_ID]):
        return []

    client = AsyncClient(MATRIX_HOMESERVER, MATRIX_USER_ID)
    client.access_token = MATRIX_ACCESS_TOKEN

    commands = []
    try:
        # Sync to get recent messages
        sync_response = await client.sync(timeout=5000, since=since_token)

        room_events = sync_response.rooms.join.get(MATRIX_ROOM_ID, {})
        timeline = getattr(room_events, 'timeline', None)

        if timeline:
            for event in timeline.events:
                if hasattr(event, 'body'):
                    body = event.body.strip().upper()
                    if body.startswith(('APPROVE', 'REJECT', 'REVIEW')):
                        parts = body.split()
                        if len(parts) >= 2:
                            commands.append({
                                "action": parts[0],
                                "bundle_id": parts[1],
                                "sender": event.sender,
                                "timestamp": event.server_timestamp
                            })

        return commands
    except Exception:
        return []
    finally:
        await client.close()

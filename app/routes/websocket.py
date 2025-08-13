from aiohttp import web, WSMsgType
from app.database.db import engine
from app.database.models import ChatMembers
from sqlalchemy import select
from app.utils.auth import get_user_from_token, get_jwt_payload
import json
from datetime import datetime


ONLINE_USERS: dict[int, web.WebSocketResponse] = {}


async def websocket_handler(request: web.Request):
    ws = web.WebSocketResponse(autoping=True)
    await ws.prepare(request)

    payload = get_jwt_payload(request)
    if not payload:
        await ws.close()
        return ws

    user_id = int(payload["sub"])
    ONLINE_USERS[user_id] = ws
    print(f"✅ WebSocket подключён: user_id={user_id}")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                # Клиент может прислать ping
                if data.get("type") == "ping":
                    await ws.send_json({"type": "pong"})
                # Больше никаких сообщений от клиента не обрабатываем — всё через REST
            elif msg.type == WSMsgType.ERROR:
                print(f"WebSocket ошибка: {ws.exception()}")
    finally:
        ONLINE_USERS.pop(user_id, None)
        print(f"❌ WebSocket отключён: user_id={user_id}")

    return ws


async def notify_chat_updated(chat_id: int, exclude_user_id: int | None = None):
    """
    Шлёт WS-уведомление 'chat_updated' всем участникам чата, кроме исключённого
    """
    async with engine.connect() as conn:
        result = await conn.execute(
            select(ChatMembers.c.user_id).where(ChatMembers.c.chat_id == chat_id)
        )
        member_ids = [row.user_id for row in result.fetchall()]

    payload = {
        "type": "chat_updated",
        "chat_id": chat_id,
        "ts": datetime.utcnow().isoformat()
    }

    for uid in member_ids:
        if exclude_user_id and uid == exclude_user_id:
            continue
        ws = ONLINE_USERS.get(uid)
        if ws and not ws.closed:
            await ws.send_json(payload)


async def notify_message(chat_id, from_user_id, payload, signature):
    async with engine.connect() as conn:
        members = await conn.execute(
            select(ChatMembers.c.user_id).where(ChatMembers.c.chat_id == chat_id)
        )
        members = members.fetchall()

    for member in members:
        uid = member.user_id
        if uid in ONLINE_USERS and uid != from_user_id:
            await ONLINE_USERS[uid].send_json({
                "type": "message",
                "chat_id": chat_id,
                "from_user_id": from_user_id,
                "payload": payload,
                "signature": signature,
            })


def setup_websocket_routes(app: web.Application):
    app.router.add_get('/ws', websocket_handler)
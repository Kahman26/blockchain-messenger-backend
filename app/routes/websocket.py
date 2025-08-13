from aiohttp import web, WSMsgType
from app.database.db import engine
from app.database.models import ChatMembers
from app.utils.auth import get_user_from_token
import json

connected_clients = {}


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    token = request.query.get("token")
    user = await get_user_from_token(token)
    if not user:
        await ws.send_json({"error": "unauthorized"})
        await ws.close()
        return ws

    user_id = user.user_id
    connected_clients[user_id] = ws
    print(f"🟢 WebSocket подключён: user_id={user_id}")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)

                # ожидаем от клиента: to_user_id, payload, chat_id, signature
                to_user_id = data.get("to_user_id")
                payload = data.get("payload")
                chat_id = data.get("chat_id")
                signature = data.get("signature")

                if not to_user_id or not payload or not chat_id:
                    # можно дополнительно логировать/валидировать
                    continue

                if to_user_id in connected_clients:
                    await connected_clients[to_user_id].send_json({
                        "type": "message",
                        "chat_id": chat_id,
                        "from_user_id": user_id,
                        "payload": payload,
                        "signature": signature,
                    })

            elif msg.type == WSMsgType.ERROR:
                print(f"WebSocket ошибка: {ws.exception()}")
    finally:
        print(f"🔴 WebSocket отключён: user_id={user_id}")
        if user_id in connected_clients:
            del connected_clients[user_id]

    return ws


async def notify_chat_updated(chat_id: int, exclude_user_id: int = None):
    """
    Отправляет событие chat_updated всем участникам чата, кроме exclude_user_id.
    """
    async with engine.connect() as conn:
        result = await conn.execute(
            ChatMembers.select().where(ChatMembers.c.chat_id == chat_id)
        )
        members = result.fetchall()

    for member in members:
        uid = member.user_id
        if uid in connected_clients and uid != exclude_user_id:
            await connected_clients[uid].send_json({
                "type": "chat_updated",
                "chat_id": chat_id
            })


def setup_websocket_routes(app: web.Application):
    app.router.add_get('/ws', websocket_handler)